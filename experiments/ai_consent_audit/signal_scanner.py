"""
Phase 2 — Signal scanning.

For each sampled repo, fetches:
  - robots.txt (repo root via raw.githubusercontent.com + homepage if present)
  - llms.txt (homepage if present)
  - README.md (via GitHub API)
  - LICENSE file (via GitHub API)
  - HTTP response headers from homepage

Saves raw signals to data/signals_raw.jsonl (idempotent — skips already-scanned repos).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from config import (
    AI_CRAWLERS,
    DATA_DIR,
    GITHUB_API_DELAY,
    HTTP_DELAY,
    OPT_IN_KEYWORDS,
    OPT_OUT_KEYWORDS,
    REPOS_RAW,
    REQUEST_TIMEOUT,
    SIGNALS_RAW,
    USER_AGENT,
)

TOKEN = os.getenv("GITHUB_TOKEN", "")
GH_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
}
HTTP_HEADERS = {"User-Agent": USER_AGENT}


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _gh_get(url: str) -> Optional[Dict]:
    try:
        r = requests.get(url, headers=GH_HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - time.time() + 5, 10)
            print(f"  [rate-limit] sleeping {wait:.0f}s", flush=True)
            time.sleep(wait)
            return _gh_get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _http_get(url: str) -> Optional[requests.Response]:
    try:
        r = requests.get(
            url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        return r
    except Exception:
        return None


def _decode_content(gh_file_obj: Optional[Dict]) -> str:
    if not gh_file_obj:
        return ""
    content = gh_file_obj.get("content", "")
    encoding = gh_file_obj.get("encoding", "base64")
    try:
        if encoding == "base64":
            return base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="replace")
        return content
    except Exception:
        return ""


# ── robots.txt parsing ────────────────────────────────────────────────────────

def _parse_robots(text: str) -> Dict[str, Any]:
    """
    Returns:
      blocks_all_crawlers: bool — Disallow: / for User-agent: *
      blocks_ai_crawlers: list[str] — named AI UAs that are disallowed
      has_ai_specific_rules: bool — any rule referencing an AI crawler
      raw_text: str
    """
    if not text:
        return {
            "blocks_all_crawlers": False,
            "blocks_ai_crawlers": [],
            "has_ai_specific_rules": False,
            "raw_text": "",
        }

    current_agents: list[str] = []
    blocks_all = False
    blocks_ai: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if lower.startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            if agent == "*":
                current_agents = ["*"]
            else:
                current_agents = [agent]
        elif lower.startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path in ("/", "/*"):
                if "*" in current_agents:
                    blocks_all = True
                for a in current_agents:
                    if a != "*" and any(a.lower() == ai.lower() for ai in AI_CRAWLERS):
                        if a not in blocks_ai:
                            blocks_ai.append(a)

    has_ai_rules = any(
        any(ai.lower() in line.lower() for ai in AI_CRAWLERS)
        for line in text.splitlines()
        if not line.strip().startswith("#")
    )

    return {
        "blocks_all_crawlers": blocks_all,
        "blocks_ai_crawlers": blocks_ai,
        "has_ai_specific_rules": has_ai_rules,
        "raw_text": text[:4000],  # cap storage
    }


# ── Keyword scanning ──────────────────────────────────────────────────────────

def _scan_keywords(text: str) -> Dict[str, Any]:
    lower = text.lower()
    found_opt_out = [kw for kw in OPT_OUT_KEYWORDS if kw in lower]
    found_opt_in = [kw for kw in OPT_IN_KEYWORDS if kw in lower]
    return {
        "opt_out_keywords": found_opt_out,
        "opt_in_keywords": found_opt_in,
    }


# ── Per-repo scanning ─────────────────────────────────────────────────────────

def scan_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    full_name = repo["full_name"]
    owner = repo["owner"]
    name = repo["name"]
    branch = repo.get("default_branch", "main")
    homepage = repo.get("homepage") or ""

    result: Dict[str, Any] = {
        "repo_id": repo["repo_id"],
        "full_name": full_name,
        "license_spdx": repo.get("license_spdx"),
        "license_stratum": repo.get("license_stratum"),
        "stars": repo["stars"],
        "created_at": repo["created_at"],
        "pushed_at": repo["pushed_at"],
        "homepage": homepage or None,
        "language": repo.get("language"),
        # signal fields (filled below)
        "repo_robots_txt": None,
        "homepage_robots_txt": None,
        "homepage_llms_txt": None,
        "homepage_headers": {},
        "readme_keywords": {},
        "license_keywords": {},
        "has_llms_txt": False,
        "tdm_reservation_header": False,
        "x_robots_noai": False,
    }

    # 1. robots.txt in the repo itself (some projects put one there)
    raw_url = f"https://raw.githubusercontent.com/{full_name}/{branch}/robots.txt"
    r = _http_get(raw_url)
    time.sleep(HTTP_DELAY)
    if r and r.status_code == 200:
        result["repo_robots_txt"] = _parse_robots(r.text)

    # 2. README.md
    time.sleep(GITHUB_API_DELAY)
    readme_obj = _gh_get(f"https://api.github.com/repos/{full_name}/readme")
    readme_text = _decode_content(readme_obj)
    result["readme_keywords"] = _scan_keywords(readme_text)

    # 3. LICENSE file
    time.sleep(GITHUB_API_DELAY)
    license_candidates = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
    license_text = ""
    for lf in license_candidates:
        obj = _gh_get(f"https://api.github.com/repos/{full_name}/contents/{lf}")
        if obj and isinstance(obj, dict) and obj.get("type") == "file":
            license_text = _decode_content(obj)
            time.sleep(GITHUB_API_DELAY)
            break
        time.sleep(0.3)
    result["license_keywords"] = _scan_keywords(license_text)

    # 4. Homepage signals (robots.txt, llms.txt, HTTP headers)
    if homepage and homepage.startswith("http"):
        parsed = urlparse(homepage)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # robots.txt
        time.sleep(HTTP_DELAY)
        r_robots = _http_get(f"{base}/robots.txt")
        if r_robots and r_robots.status_code == 200:
            result["homepage_robots_txt"] = _parse_robots(r_robots.text)

        # llms.txt (emerging standard for structured AI opt-in)
        time.sleep(HTTP_DELAY)
        r_llms = _http_get(f"{base}/llms.txt")
        if r_llms and r_llms.status_code == 200:
            content_type = r_llms.headers.get("Content-Type", "").lower()
            text_content = r_llms.text.strip()
            # Reject SPAs returning HTML for all routes (false positive guard)
            is_html = (
                "text/html" in content_type
                or text_content.lower().startswith("<!doctype")
                or text_content.lower().startswith("<html")
            )
            # Require Markdown structure: at least one # heading and >100 chars
            has_markdown = "#" in text_content and len(text_content) > 100
            if not is_html and has_markdown:
                result["has_llms_txt"] = True
                result["homepage_llms_txt"] = text_content[:2000]
                result["llms_txt_content_type"] = content_type

        # HTTP headers from homepage
        time.sleep(HTTP_DELAY)
        r_home = _http_get(homepage)
        if r_home:
            hdrs = dict(r_home.headers)
            result["homepage_headers"] = {
                k: v for k, v in hdrs.items()
                if k.lower() in (
                    "x-robots-tag", "tdm-reservation", "content-type",
                    "x-content-type-options", "server"
                )
            }
            xrt = hdrs.get("X-Robots-Tag", hdrs.get("x-robots-tag", "")).lower()
            result["x_robots_noai"] = "noai" in xrt or "noindex" in xrt
            tdm = hdrs.get("tdm-reservation", hdrs.get("Tdm-Reservation", "")).strip()
            result["tdm_reservation_header"] = tdm == "1"

    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def _already_scanned(path: str) -> set[int]:
    p = Path(path)
    if not p.exists():
        return set()
    out: set[int] = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.add(json.loads(line)["repo_id"])
            except Exception:
                pass
    return out


def run(repos_path: str = REPOS_RAW, out_path: str = SIGNALS_RAW) -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    repos = [
        json.loads(l) for l in Path(repos_path).read_text().splitlines() if l.strip()
    ]
    scanned = _already_scanned(out_path)
    todo = [r for r in repos if r["repo_id"] not in scanned]
    print(
        f"[scanner] {len(repos)} repos total; {len(scanned)} already scanned; "
        f"{len(todo)} to scan",
        flush=True,
    )

    with open(out_path, "a", encoding="utf-8") as f:
        for i, repo in enumerate(todo, 1):
            print(
                f"  [{i}/{len(todo)}] {repo['full_name']} ({repo['stars']}★)",
                flush=True,
            )
            try:
                sig = scan_repo(repo)
                f.write(json.dumps(sig, ensure_ascii=False) + "\n")
                f.flush()
            except Exception as e:
                print(f"  [error] {repo['full_name']}: {e}", flush=True)

    print(f"[scanner] done — signals saved to {out_path}", flush=True)


if __name__ == "__main__":
    run()
