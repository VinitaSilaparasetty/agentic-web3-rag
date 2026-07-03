"""
Samples n=200 non-Web3 general OSS repos from GitHub for the comparison population.

Uses topics that explicitly exclude blockchain/web3 content:
  python, javascript, cli, machine-learning, data-science, api, framework, library

Writes to data/comparison_repos_raw.jsonl and data/comparison_signals_raw.jsonl
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests

from config import (
    DATA_DIR, GITHUB_API_DELAY, GITHUB_SEARCH_DELAY,
    MIN_PUSHED, MIN_STARS, REQUEST_TIMEOUT,
)
from github_sampler import _repo_record, _license_spdx, _classify_license_stratum
import signal_scanner

TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
}

COMPARISON_TOPICS = [
    "python", "javascript", "cli", "framework",
    "machine-learning", "data-science", "api", "library",
]

# Exclude any repo that is also tagged web3/blockchain
EXCLUDE_TOPICS = {
    "ethereum", "web3", "blockchain", "solidity", "defi",
    "hardhat", "foundry", "wagmi", "ethers", "layer2",
    "bitcoin", "crypto", "nft", "dao", "token",
}

COMPARISON_REPOS = f"{DATA_DIR}/comparison_repos_raw.jsonl"
COMPARISON_SIGNALS = f"{DATA_DIR}/comparison_signals_raw.jsonl"
COMPARISON_CLASSIFIED = f"{DATA_DIR}/comparison_classified.csv"
TARGET = 200


def _search_page(query: str, page: int) -> dict:
    time.sleep(GITHUB_SEARCH_DELAY)
    r = requests.get(
        "https://api.github.com/search/repositories",
        headers=HEADERS,
        params={"q": query, "sort": "stars", "order": "desc",
                "per_page": 100, "page": page},
        timeout=15,
    )
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
        time.sleep(max(reset - time.time() + 5, 10))
        return _search_page(query, page)
    r.raise_for_status()
    return r.json()


def sample() -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    existing: set[int] = set()
    if Path(COMPARISON_REPOS).exists():
        for line in Path(COMPARISON_REPOS).read_text().splitlines():
            if line.strip():
                existing.add(json.loads(line)["repo_id"])

    collected = list(existing)
    print(f"[comparison-sampler] resuming — {len(existing)} already collected; target={TARGET}")

    with open(COMPARISON_REPOS, "a", encoding="utf-8") as f:
        for topic in COMPARISON_TOPICS:
            if len(collected) >= TARGET:
                break
            print(f"  topic={topic} n={len(collected)}")
            for page in range(1, 4):
                if len(collected) >= TARGET:
                    break
                try:
                    result = _search_page(
                        f"topic:{topic} stars:>={MIN_STARS} pushed:>{MIN_PUSHED} "
                        f"fork:false archived:false",
                        page,
                    )
                except Exception as e:
                    print(f"  [error] {e}")
                    break

                for repo in result.get("items", []):
                    if len(collected) >= TARGET:
                        break
                    if repo["id"] in existing:
                        continue
                    # Exclude repos that overlap with Web3 topics
                    repo_topics = set(repo.get("topics", []))
                    if repo_topics & EXCLUDE_TOPICS:
                        continue
                    existing.add(repo["id"])
                    collected.append(repo["id"])
                    rec = _repo_record(repo)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    time.sleep(GITHUB_API_DELAY)

    print(f"[comparison-sampler] done — {len(collected)} repos in {COMPARISON_REPOS}")


def scan() -> None:
    signal_scanner.run(
        repos_path=COMPARISON_REPOS,
        out_path=COMPARISON_SIGNALS,
    )


def classify() -> None:
    import classifier
    classifier.run(
        signals_path=COMPARISON_SIGNALS,
        out_path=COMPARISON_CLASSIFIED,
    )


if __name__ == "__main__":
    sample()
    scan()
    classify()
