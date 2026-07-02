import os
import urllib.parse
from dataclasses import dataclass
from typing import Optional

import requests

DEFAULT_SNIPPET_CHARS = int(os.getenv("SNIPPET_CHARS", "320"))


@dataclass
class Policy:
    allowed: bool
    license: str
    cache_policy: str  # "link-only" | "snippet" | "fulltext"
    snippet_chars: int = DEFAULT_SNIPPET_CHARS


_SOURCES = {
    "ethereum.org": Policy(True, "CC BY 4.0", "snippet", DEFAULT_SNIPPET_CHARS),
    "geth.ethereum.org": Policy(True, "All rights reserved / site ToS", "link-only", DEFAULT_SNIPPET_CHARS),
}


def _domain_for(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()


def trim_snippet(text: str, n: int = DEFAULT_SNIPPET_CHARS) -> str:
    if not text:
        return ""
    s = " ".join(text.split())
    return s[:n] + ("…" if len(s) > n else "")


def robots_allowed(url: str, ua: str = "web3-rag-bot") -> bool:
    """Block if the site's robots.txt has Disallow: / for our UA or *."""
    try:
        p = urllib.parse.urlparse(url)
        robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
        r = requests.get(robots_url, timeout=8)
        if r.status_code != 200:
            return True
        ua_applies = True
        for line in r.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("user-agent:"):
                curr = line.split(":", 1)[1].strip()
                ua_applies = (curr == "*") or (curr.lower() == ua.lower())
            elif line.lower().startswith("disallow:") and ua_applies:
                path = line.split(":", 1)[1].strip()
                if path == "/":
                    return False
        return True
    except Exception:
        return True


def github_policy_for(url: str) -> Optional[Policy]:
    """Query GitHub's license API for the repo and return a Policy, or None."""

    def _infer_owner_repo(u: str):
        p = urllib.parse.urlparse(u)
        host = (p.netloc or "").lower()
        path = (p.path or "").strip("/")

        if host == "github.com":
            parts = [x for x in path.split("/") if x]
            if len(parts) >= 2:
                return parts[0], parts[1]

        if host == "raw.githubusercontent.com":
            parts = [x for x in path.split("/") if x]
            if len(parts) >= 2:
                return parts[0], parts[1]

        if host.endswith(".github.io"):
            owner = host[: -len(".github.io")]
            parts = [x for x in path.split("/") if x]
            if owner and parts:
                return owner, parts[0]
            if owner:
                return owner, f"{owner}.github.io"
        return None, None

    owner, repo = _infer_owner_repo(url)
    if not owner or not repo:
        return None

    api = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        r = requests.get(api, headers=headers, timeout=12)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    lic = (data.get("license") or {}).get("spdx_id") or "Unknown"

    fulltext_ok = {"CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0"}
    snippet_ok = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "MPL-2.0", "Unlicense", "ISC"}

    extra_full = {x.strip() for x in os.getenv("FULLTEXT_LICENSES", "").split(",") if x.strip()}
    extra_snip = {x.strip() for x in os.getenv("SNIPPET_LICENSES", "").split(",") if x.strip()}
    fulltext_ok |= extra_full
    snippet_ok |= extra_snip

    if lic in fulltext_ok:
        return Policy(True, lic, "fulltext", DEFAULT_SNIPPET_CHARS)
    if lic in snippet_ok:
        return Policy(True, lic, "snippet", DEFAULT_SNIPPET_CHARS)
    return None


def policy_for_url(url: str) -> Policy:
    """
    Resolution order:
      1) Per-domain _SOURCES overrides
      2) GitHub repo license gate (if applicable)
      3) Safe default: CACHE_POLICY_DEFAULT (usually 'link-only')
    """
    host = _domain_for(url)

    for domain, pol in _SOURCES.items():
        if host.endswith(domain):
            return pol

    gh_pol = github_policy_for(url)
    if gh_pol is not None:
        return gh_pol

    return Policy(True, "Unknown", os.getenv("CACHE_POLICY_DEFAULT", "link-only"), DEFAULT_SNIPPET_CHARS)


def apply_display_policy(rec: dict) -> dict:
    """Return a UI-safe view of a search/assist record based on its URL policy.

    - link-only: keep url + best-effort title; drop snippet/text; add note
    - snippet: keep url + title + trimmed snippet; drop full text
    - fulltext: keep everything including text
    """
    url = (rec or {}).get("url") or ""
    pol = policy_for_url(url)
    out = {
        "url": url,
        "title": rec.get("title"),
        "license": rec.get("license"),
        "score": rec.get("score"),
        "project": rec.get("project"),
        "source_id": rec.get("source_id"),
    }

    if pol.cache_policy == "link-only":
        out.update({"snippet": None, "text": None, "note": "Content protected under license/ToS; link only."})
        return out

    snippet_chars = getattr(pol, "snippet_chars", DEFAULT_SNIPPET_CHARS)
    src_snippet = rec.get("snippet")
    src_text = rec.get("text")
    safe_snippet = src_snippet or (trim_snippet(src_text or "", snippet_chars) if src_text else None)
    out["snippet"] = safe_snippet
    out["text"] = src_text if pol.cache_policy == "fulltext" else None
    return out
