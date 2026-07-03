"""
Phase 1 — Repository sampling.

Queries GitHub Search API for active Web3 repositories, collects metadata,
and saves to data/repos_raw.jsonl (one JSON object per line, idempotent).
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import requests
from config import (
    DATA_DIR,
    GITHUB_API_DELAY,
    GITHUB_SEARCH_DELAY,
    MIN_PUSHED,
    MIN_STARS,
    PILOT_SAMPLE,
    REPOS_RAW,
    SEARCH_TOPICS,
    TARGET_SAMPLE,
)

TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
}


def _get(url: str, params: dict | None = None) -> dict[str, Any]:
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait = max(reset - time.time() + 5, 10)
        print(f"  [rate-limit] sleeping {wait:.0f}s", flush=True)
        time.sleep(wait)
        return _get(url, params)
    r.raise_for_status()
    return r.json()


def _search_page(query: str, page: int) -> dict[str, Any]:
    time.sleep(GITHUB_SEARCH_DELAY)
    return _get(
        "https://api.github.com/search/repositories",
        params={"q": query, "sort": "stars", "order": "desc", "per_page": 100, "page": page},
    )


def _license_spdx(repo: dict) -> str | None:
    lic = repo.get("license") or {}
    return (lic.get("spdx_id") or "").strip() or None


def _classify_license_stratum(spdx: str | None) -> str:
    from config import LICENSE_STRATA
    if not spdx:
        return "no_license"
    for stratum, ids in LICENSE_STRATA.items():
        if spdx in ids:
            return stratum
    return "other"


def _repo_record(repo: dict) -> dict[str, Any]:
    spdx = _license_spdx(repo)
    return {
        "repo_id": repo["id"],
        "full_name": repo["full_name"],
        "owner": repo["owner"]["login"],
        "name": repo["name"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "created_at": repo["created_at"],
        "pushed_at": repo["pushed_at"],
        "license_spdx": spdx,
        "license_stratum": _classify_license_stratum(spdx),
        "homepage": (repo.get("homepage") or "").strip() or None,
        "description": (repo.get("description") or "").strip() or None,
        "topics": repo.get("topics", []),
        "language": repo.get("language"),
        "size_kb": repo.get("size", 0),
        "default_branch": repo.get("default_branch", "main"),
        "archived": repo.get("archived", False),
        "fork": repo.get("fork", False),
    }


def _existing_full_names(path: str) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.add(json.loads(line)["full_name"])
            except Exception:
                pass
    return out


def _iter_topic_repos(topic: str, max_per_topic: int = 300) -> Iterator[dict[str, Any]]:
    query = (
        f"topic:{topic} stars:>={MIN_STARS} pushed:>{MIN_PUSHED} "
        f"fork:false archived:false"
    )
    page = 1
    seen = 0
    while seen < max_per_topic:
        try:
            result = _search_page(query, page)
        except Exception as e:
            print(f"  [search error] {e}", flush=True)
            break
        items = result.get("items", [])
        if not items:
            break
        for repo in items:
            if seen >= max_per_topic:
                break
            yield repo
            seen += 1
        if len(items) < 100:
            break
        page += 1


def sample(target: int = TARGET_SAMPLE, pilot: bool = False) -> list[dict[str, Any]]:
    n = PILOT_SAMPLE if pilot else target
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    existing = _existing_full_names(REPOS_RAW)
    print(f"[sampler] resuming — {len(existing)} repos already collected; target={n}", flush=True)

    collected: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    # Load already-collected to respect dedup
    if existing:
        for line in Path(REPOS_RAW).read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                seen_ids.add(rec["repo_id"])
                collected.append(rec)

    with open(REPOS_RAW, "a", encoding="utf-8") as f:
        for topic in SEARCH_TOPICS:
            if len(collected) >= n:
                break
            print(f"[sampler] topic={topic} collected={len(collected)}", flush=True)
            for repo in _iter_topic_repos(topic, max_per_topic=200):
                if len(collected) >= n:
                    break
                if repo["id"] in seen_ids:
                    continue
                if repo.get("fork") or repo.get("archived"):
                    continue
                seen_ids.add(repo["id"])
                rec = _repo_record(repo)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                collected.append(rec)
                time.sleep(GITHUB_API_DELAY)

    print(f"[sampler] done — {len(collected)} repos saved to {REPOS_RAW}", flush=True)
    return collected


if __name__ == "__main__":
    pilot = "--pilot" in sys.argv
    sample(pilot=pilot)
