import json
import os
import re
import textwrap

import requests

OPENAI_MODEL = os.getenv("ASSIST_OPENAI_MODEL", "gpt-4o-mini")
USE_OPENAI = os.getenv("ASSIST_USE_OPENAI", "false").lower() in ("1", "true", "yes")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _chunks_for_prompt(docs: list[dict], maxn: int = 5) -> list[dict]:
    out = []
    for d in docs:
        if len(out) >= maxn:
            break
        # respect policy: do not pass full 'text' when link-only content was enforced upstream
        # use at most snippet if present; otherwise text
        s = (d.get("snippet") or d.get("text") or "").strip()
        if not s:
            continue
        out.append(
            {
                "url": d.get("url"),
                "title": d.get("title"),
                "source": d.get("source"),
                "snippet": s[:1200],  # conservative cap for prompt size
            }
        )
    return out


def _special_case_geth_eth_getBalance(q: str, docs: list[dict]) -> str | None:
    ql = q.lower()
    if ("geth" in ql or "go-ethereum" in ql) and ("eth_getbalance" in ql or "getbalance" in ql):
        # Minimal, license-safe instructions synthesized without quoting doc text
        lines = []
        lines.append("### Enable JSON-RPC in geth")
        lines.append(
            "1. Start geth with HTTP JSON-RPC enabled (limit to local / trusted networks):"
        )
        lines.append("")
        lines.append("```bash")
        lines.append("geth \\")
        lines.append("  --http \\")
        lines.append("  --http.addr 127.0.0.1 \\")
        lines.append("  --http.port 8545 \\")
        lines.append("  --http.api eth,net,web3")
        lines.append("```")
        lines.append("")
        lines.append("### Call `eth_getBalance`")
        lines.append(
            "Use a JSON-RPC POST to `http://127.0.0.1:8545` with a target address and block tag:"
        )
        lines.append("")
        lines.append("```bash")
        lines.append("curl -s http://127.0.0.1:8545 -H 'Content-Type: application/json' -d '")
        lines.append(
            '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0xYourAddressHere","latest"],"id":1}'
        )
        lines.append("'")
        lines.append("```")
        lines.append("")
        lines.append(
            "**Why this works:** `eth_getBalance` returns the account balance (in wei) at the given block tag. Use `latest` for the head of the chain or a hex block number like `0xA`. Convert wei to ETH by dividing by 1e18."
        )
        # cite sources list
        srcs = []
        seen = set()
        for d in docs:
            u = d.get("url")
            if u and u not in seen:
                seen.add(u)
                title = d.get("title") or d.get("source") or u
                dom = (d.get("source") or "").strip()
                srcs.append(f"- {title} ({dom}) → {u}")
            if len(srcs) >= 5:
                break
        if srcs:
            lines.append("")
            lines.append("**References**")
            lines.extend(srcs)
        return "\n".join(lines)
    return None


def _fallback_structured_summary(q: str, docs: list[dict]) -> str:
    # Build simple bullet summary from top 2–3 snippets (no direct quotes; short abstractions)
    bullets = []
    for d in docs:
        if len(bullets) >= 3:
            break
        s = (d.get("snippet") or d.get("text") or "").strip()
        if not s:
            continue
        # Turn first sentence into a compact bullet-like paraphrase
        sent = re.split(r"(?<=[.!?])\s+", s)[0]
        sent = re.sub(r"\s+", " ", sent).strip()
        if not sent:
            continue
        bullets.append(f"- {sent}")
    parts = ["### Answer (summary)", *bullets]
    # add sources
    srcs, seen = [], set()
    for d in docs:
        u = d.get("url")
        if u and u not in seen:
            seen.add(u)
            title = d.get("title") or d.get("source") or u
            dom = (d.get("source") or "").strip()
            srcs.append(f"- {title} ({dom}) → {u}")
        if len(srcs) >= 5:
            break
    if srcs:
        parts.append("\n**References**")
        parts.extend(srcs)
    return "\n".join(parts)


def _openai_answer(q: str, docs: list[dict]) -> str:
    # Robust no-external-dep OpenAI call via requests
    if not OPENAI_API_KEY:
        return ""
    chunks = _chunks_for_prompt(docs, maxn=5)
    prompt = textwrap.dedent(f"""
    You are a concise web3 documentation assistant. Question: {q!r}

    Using ONLY the information and context below, produce:
    1) A short, direct answer in 2–4 bullet points.
    2) If useful, ONE compact code block (bash, curl, or language snippet).
    3) A short "Why this works" line.
    4) Then a "References" list (title + domain + URL) from the provided chunks.

    Context (JSON lines of chunks with title/source/snippet/url):
    {json.dumps(chunks, ensure_ascii=False)}
    """).strip()

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        return (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
    except Exception:
        return ""


def assist_answer(q: str, docs: list[dict]) -> str:
    # 1) Specific path for common geth+eth_getBalance debugging
    s = _special_case_geth_eth_getBalance(q, docs)
    if s:
        return s

    # 2) LLM path (optional)
    if USE_OPENAI:
        s = _openai_answer(q, docs)
        if s:
            return s

    # 3) Fallback: structured summary from top snippets
    return _fallback_structured_summary(q, docs)


# Back-compat alias for older imports
def _assist_answer(q, docs):
    return assist_answer(q, docs)
