# File: pipelines/source_loader.py
# Why: Merge file/ENV/STDIN manifests to support operators and webhook triggers.
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

import yaml

Manifest = dict[str, Any]


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _validate(m: Manifest) -> Manifest:
    if not isinstance(m, dict) or "version" not in m or "sources" not in m:
        raise ValueError("Invalid manifest: expected {version, sources}.")
    return m


def _load_file(path: str) -> Manifest | None:
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return _validate(yaml.safe_load(f))


def _load_env(key: str = "SOURCES_JSON") -> Manifest | None:
    raw = os.getenv(key)
    if not raw:
        return None
    return _validate(json.loads(raw))


def _load_stdin() -> Manifest | None:
    if sys.stdin.isatty():
        return None
    raw = sys.stdin.read().strip()
    if not raw:
        return None
    try:
        return _validate(json.loads(raw))
    except Exception:
        return _validate(yaml.safe_load(raw))


def _dedupe(srcs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen, out = set(), []
    for s in srcs:
        k = f"{s.get('type')}:{s.get('url') or s.get('cid') or s.get('path')}"
        h = _sha(k)
        if h in seen:
            continue
        seen.add(h)
        out.append(s)
    return out


def load_sources(manifest_path: str | None) -> Manifest:
    file_m = _load_file(manifest_path)
    env_m = _load_env()
    stdin_m = _load_stdin()
    sources = []
    for m in [file_m, env_m, stdin_m]:
        if m:
            sources.extend(m.get("sources", []))
    if not sources:
        raise SystemExit("No sources provided; Phase 1 requires explicit curated sources.")
    return {"version": 1, "sources": _dedupe(sources)}
