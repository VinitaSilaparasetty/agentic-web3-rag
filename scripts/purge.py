# File: scripts/purge.py
# Why: Fast removal reassures partners; alpha keeps it simple (by domain).
from __future__ import annotations
import argparse, pathlib, shutil


def main():
    parser = argparse.ArgumentParser(description="Purge local artifacts by domain key")
    parser.add_argument("--domain", required=True)
    args = parser.parse_args()
    # Pragmatic purge: remove matching files from samples/processed/vectors by name hash presence.
    root_dirs = ["data/samples", "data/processed", "data/vectors"]
    removed = 0
    for rd in root_dirs:
        p = pathlib.Path(rd)
        if not p.exists():
            continue
        for f in p.glob("*.md") if rd.endswith("samples") else p.glob("*.jsonl"):
            if args.domain in f.read_text(encoding="utf-8"):
                f.unlink(missing_ok=True)
                removed += 1
    print(f"purged_files={removed}")


if __name__ == "__main__":
    main()
