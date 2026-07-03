#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import requests
import yaml

ALLOWED_CODE_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Unlicense",
    "CC0-1.0",
    "MPL-2.0",
    "EPL-2.0",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
}
ALLOWED_DOC_LICENSES = {
    "CC-BY-4.0",
    "CC-BY-3.0",
    "CC-BY-2.5",
    "CC0-1.0",
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "MPL-2.0",
    "EPL-2.0",
}
EXCLUDED_LICENSES = {
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "CC-BY-SA-4.0",
    "CC-BY-SA-3.0",
    "CC-BY-SA-2.5",
    "CC-BY-ND-4.0",
    "CC-BY-ND-3.0",
    "CC-BY-ND-2.5",
}


def is_allowed_spdx(spdx: str | None, *, for_docs: bool) -> bool:
    if not spdx:
        return False
    if spdx in EXCLUDED_LICENSES:
        return False
    base = ALLOWED_DOC_LICENSES if for_docs else ALLOWED_CODE_LICENSES
    return spdx in base


GITHUB = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def gh_get(url: str, params: dict[str, Any] | None = None) -> Any:
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("x-ratelimit-reset")
        if reset:
            wait = max(0, int(reset) - int(time.time()) + 2)
            time.sleep(min(wait, 10))
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def gh_search_repos(
    q: str, sort: str = "stars", order: str = "desc", per_page: int = 50, pages: int = 2
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        data = gh_get(
            f"{GITHUB}/search/repositories",
            params={"q": q, "sort": sort, "order": order, "per_page": per_page, "page": page},
        )
        items += data.get("items", [])
        if len(data.get("items", [])) < per_page:
            break
    return items


def gh_repo_license(owner: str, repo: str) -> tuple[str | None, str | None, str | None]:
    try:
        lic = gh_get(f"{GITHUB}/repos/{owner}/{repo}/license")
        spdx = (lic.get("license") or {}).get("spdx_id")
        name = (lic.get("license") or {}).get("name")
        url = lic.get("html_url")
        return spdx, name, url
    except requests.HTTPError:
        meta = gh_get(f"{GITHUB}/repos/{owner}/{repo}")
        lic = meta.get("license") or {}
        return lic.get("spdx_id"), lic.get("name"), lic.get("url")


def guess_docs_url(repo: dict[str, Any]) -> str | None:
    homepage = (repo.get("homepage") or "").strip()
    if homepage and any(
        t in homepage.lower()
        for t in ("docs", "readthedocs", "vercel.app", "netlify.app", "site", "org", "dev")
    ):
        return homepage
    owner = repo["owner"]["login"]
    name = repo["name"]
    return homepage or f"https://{owner.lower()}.github.io/{name}/"


QUERY_SETS = [
    "web3 language:TypeScript stars:>=200",
    "web3 language:Rust stars:>=200",
    "web3 framework stars:>=100",
    "topic:ethereum stars:>=200",
    "topic:solidity stars:>=200",
    "topic:ethersjs stars:>=100",
    "topic:web3js stars:>=100",
    "topic:rollup stars:>=100",
    "topic:solana language:Rust stars:>=200",
    "topic:polkadot stars:>=200",
    "org:ethereum stars:>=50",
    "org:eth-brownie stars:>=50",
    "org:ethers-io stars:>=50",
    "org:Foundry-RS stars:>=50",
    "org:hardhatjs stars:>=50",
    "org:OpenZeppelin stars:>=50",
    "org:ChainSafe stars:>=50",
]


def discover(limit: int) -> list[dict[str, Any]]:
    seen, repos = set(), []
    for q in QUERY_SETS:
        res = gh_search_repos(q, pages=3, per_page=50)
        for r in res:
            key = r["full_name"].lower()
            if key in seen:
                continue
            seen.add(key)
            repos.append(r)
            if len(repos) >= limit:
                return repos
    return repos[:limit]


SRC_PATH = Path("data/sources.yaml")


def load_sources() -> dict[str, Any]:
    if SRC_PATH.exists():
        return yaml.safe_load(SRC_PATH.read_text(encoding="utf-8")) or {"sources": []}
    return {"sources": []}


def dump_sources(doc: dict[str, Any]) -> None:
    SRC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SRC_PATH.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")


def upsert_source(doc: dict[str, Any], entry: dict[str, Any]) -> None:
    key = entry.get("repo") or entry.get("url")
    for s in doc["sources"]:
        if key and s.get("repo") == entry.get("repo"):
            s.update(entry)
            return
        if key and s.get("url") == entry.get("url"):
            s.update(entry)
            return
    doc["sources"].append(entry)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--project-tag", default=None)
    args = ap.parse_args()

    repos = discover(args.limit)
    out = load_sources()
    added = 0

    for r in repos:
        owner = r["owner"]["login"]
        name = r["name"]
        spdx, lname, lurl = gh_repo_license(owner, name)
        docs_url = guess_docs_url(r)
        license_ok = is_allowed_spdx(spdx, for_docs=True)

        entry = {
            "type": "website",
            "url": docs_url,
            "project": args.project_tag or owner.lower(),
            "repo": f"{owner}/{name}",
            "license_spdx": spdx,
            "license_name": lname,
            "license_url": lurl,
            "license_ok": bool(license_ok),
        }
        if not docs_url:
            entry["type"] = "github_repo"
            entry["url"] = f"https://github.com/{owner}/{name}"

        if spdx and license_ok:
            upsert_source(out, entry)
            added += 1

    dump_sources(out)
    print(json.dumps({"candidates": len(repos), "added": added, "path": str(SRC_PATH)}, indent=2))


if __name__ == "__main__":
    main()
