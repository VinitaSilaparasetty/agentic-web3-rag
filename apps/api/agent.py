import os
from typing import List, Dict, Any
from openai import OpenAI

DEFAULT_MODEL = os.getenv("ASSIST_MODEL", "gpt-4o-mini")
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL") or None,
)

SYSTEM_PROMPT = """You are a senior developer assistant.
You will be given: (a) the user's problem and (b) retrieved documentation chunks (title/url/snippet/full text).
Your job:
1) Synthesize concise, correct guidance.
2) Provide minimal code snippets where appropriate.
3) Suggest concrete troubleshooting steps when the user mentions errors.
4) Cite sources inline as [n] and include a final sources array with url + title.

Return ONLY JSON with keys:
{
  "brief_answer": string,
  "snippets": [{"language": string, "filename": string|null, "code": string}][],
  "steps": [string][],
  "sources": [{"title": string, "url": string}][],
  "notes": string
}
Keep it concise and actionable.
"""

def build_context(query: str, docs: List[Dict[str, Any]], max_chars: int = 14000) -> str:
    # Keep the most relevant docs first and trim total size
    buf = []
    used = 0
    for i, d in enumerate(docs, start=1):
        title = d.get("source_id") or d.get("url") or f"doc-{i}"
        url = d.get("url") or ""
        text = d.get("text") or d.get("snippet") or ""
        chunk = f"[{i}] {title}\nURL: {url}\n{text}\n---\n"
        if used + len(chunk) > max_chars:
            break
        buf.append(chunk)
        used += len(chunk)
    return (
        f"User query:\n{query}\n\n"
        "Retrieved docs (ordered by relevance):\n" + "".join(buf)
    )

def run_assistant(query: str, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    context = build_context(query, docs)
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
    )
    return resp.choices[0].message.model_dump()["content"]  # JSON string

