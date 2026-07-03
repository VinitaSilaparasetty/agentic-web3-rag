"""
File: pipelines/ingest_entry.py
Why:
- Be lenient on input: accept either explicit dict items or plain URL strings in data/sources.yaml.
- Still enforce Phase-1 consent via pipelines.ingest.run_ingest (allowlist gate).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

from pipelines.ingest import run_ingest  # expects list[dict]


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "source"

def _coerce_item(x):
    # Accept either dict-like or string URL
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        u = urlparse(x)
        host = u.hostname or "unknown"
        project = host.split(".")[0] if "." in host else host
        return {
            "kind": "website",
            "id": _slug(f"{project}-{u.path or 'root'}"),
            "project": _slug(project),
            "url": x,
            # consent_proof optional here; Phase-1 still requires allowlist in consents.yaml
        }
    raise TypeError(f"Unsupported sources item type: {type(x)}")

def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sources", required=True, help="path to YAML with key 'sources' or a list")
    args = p.parse_args(argv)

    src_path = Path(args.sources)
    if not src_path.exists():
        raise FileNotFoundError(f"sources file not found: {src_path}")

    data = yaml.safe_load(src_path.read_text(encoding="utf-8")) or {}
    # Support either {sources: [...]} or top-level list
    raw = data.get("sources") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        print("No sources found in YAML (expected 'sources: [...]' or a list).", file=sys.stderr)
        sys.exit(1)

    manifest = [_coerce_item(x) for x in raw]
    written = run_ingest(manifest)
    print(json.dumps({"written": [str(p) for p in written]}, indent=2))

if __name__ == "__main__":
    main()
