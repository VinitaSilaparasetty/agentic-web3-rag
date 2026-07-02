#!/usr/bin/env python3
from __future__ import annotations
import os, sys, json, argparse
from typing import Any, Dict, Optional
from pathlib import Path
import requests
import yaml

ALLOWED_CODE_LICENSES = {
    "MIT","Apache-2.0","BSD-2-Clause","BSD-3-Clause","ISC",
    "Unlicense","CC0-1.0","MPL-2.0","EPL-2.0",
    "LGPL-2.1-only","LGPL-2.1-or-later","LGPL-3.0-only","LGPL-3.0-or-later",
}
ALLOWED_DOC_LICENSES = {
    "CC-BY-4.0","CC-BY-3.0","CC-BY-2.5","CC0-1.0",
    "MIT","Apache-2.0","BSD-2-Clause","BSD-3-Clause","ISC","MPL-2.0","EPL-2.0",
}
EXCLUDED_LICENSES = {
    "GPL-2.0-only","GPL-2.0-or-later","GPL-3.0-only","GPL-3.0-or-later",
    "AGPL-3.0-only","AGPL-3.0-or-later",
    "CC-BY-SA-4.0","CC-BY-SA-3.0","CC-BY-SA-2.5",
    "CC-BY-ND-4.0","CC-BY-ND-3.0","CC-BY-ND-2.5",
}

def is_allowed_spdx(spdx: Optional[str], *, for_docs: bool) -> bool:
    if not spdx: return False
    if spdx in EXCLUDED_LICENSES: return False
    return spdx in (ALLOWED_DOC_LICENSES if for_docs else ALLOWED_CODE_LICENSES)

GITHUB = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Accept":"application/vnd.github+json"}
if TOKEN: HEADERS["Authorization"] = f"Bearer {TOKEN}"

def gh_get(url: str) -> Any:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def enrich_row(row: Dict[str, Any]) -> bool:
    repo = row.get("repo")
    if not repo or "/" not in repo: return False
    owner, name = repo.split("/", 1)
    try:
        lic = gh_get(f"{GITHUB}/repos/{owner}/{name}/license")
    except Exception:
        lic = None
    spdx = lname = lurl = None
    if lic and lic.get("license"):
        spdx = lic["license"].get("spdx_id")
        lname = lic["license"].get("name")
        lurl = lic.get("html_url")
    if not spdx:
        meta = gh_get(f"{GITHUB}/repos/{owner}/{name}")
        L = meta.get("license") or {}
        spdx, lname, lurl = L.get("spdx_id"), L.get("name"), L.get("url")

    changed = False
    for k,v in (("license_spdx", spdx), ("license_name", lname), ("license_url", lurl)):
        if v and row.get(k) != v:
            row[k] = v; changed = True

    ok = is_allowed_spdx(spdx, for_docs=True)
    if row.get("license_ok") != bool(ok):
        row["license_ok"] = bool(ok); changed = True
    return changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="path", default="data/sources.yaml")
    args = ap.parse_args()

    p = Path(args.path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {"sources": []}
    changed = False
    for row in data.get("sources", []):
        try:
            if enrich_row(row): changed = True
        except Exception as e:
            sys.stderr.write(f"warn: enrich failed for {row.get('repo')}: {e}\n")
    if changed:
        p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(json.dumps({"updated": True, "path": str(p)}))
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
