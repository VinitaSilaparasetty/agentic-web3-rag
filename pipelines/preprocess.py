"""
File: pipelines/preprocess.py
Purpose: read processed *.md files, parse optional JSON front-matter,
chunk body text, and write data/processed/chunks.jsonl
Each chunk carries: id, text, project, url, source_id (file stem), plus passthroughs.
"""
from __future__ import annotations

from pathlib import Path
import json, hashlib, re
from typing import Dict, Iterable, Tuple

PROCESSED_DIR = Path("data/processed")
OUT_PATH      = Path("data/processed/chunks.jsonl")

FRONT_RE = re.compile(r"^\s*---\s*\n(?P<json>\{.*?\})\s*\n---\s*\n?", re.S)

def _parse_front_matter(raw: str) -> Tuple[Dict, str]:
    """
    Front-matter is JSON wrapped between --- lines.
    Returns (meta, body). If none, meta={}, body=raw.
    """
    m = FRONT_RE.match(raw)
    if not m:
        return {}, raw
    try:
        meta = json.loads(m.group("json"))
    except Exception:
        meta = {}
    body = raw[m.end():]
    return meta, body

def _paragraph_chunks(text: str, max_len: int = 1200) -> Iterable[str]:
    # simple paragraph-based chunking with length guard
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    buf = []
    size = 0
    for p in paras:
        if size + len(p) + (2 if buf else 0) > max_len and buf:
            yield "\n\n".join(buf)
            buf, size = [], 0
        buf.append(p)
        size += len(p) + (2 if buf else 0)
    if buf:
        yield "\n\n".join(buf)

def _stable_id(source_id: str, text: str) -> str:
    h = hashlib.md5()
    h.update(source_id.encode("utf-8"))
    h.update(b"\x00")
    h.update(text.encode("utf-8"))
    return h.hexdigest()[:24]  # short, deterministic

def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_PATH.open("w", encoding="utf-8")

    total = files = 0
    for fp in sorted(PROCESSED_DIR.glob("*.md")):
        raw = fp.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(raw)

        # Carry through metadata (normalize keys we care about)
        project = meta.get("project")
        url     = meta.get("source_url") or meta.get("url")
        source_id = fp.stem  # file name without suffix

        display_policy = meta.get("display_policy", "link-only")

        for chunk in _paragraph_chunks(body):
            cid = _stable_id(source_id, chunk)
            rec = {
                "id": cid,
                "text": chunk,
                "project": project,
                "url": url,
                "source_id": source_id,
                "display_policy": display_policy,
                # optional passthroughs if present in front-matter
                "cid": meta.get("cid"),
                "commit": meta.get("commit"),
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            total += 1
        files += 1

    out.close()
    print(f"Wrote {OUT_PATH} with {total} chunks from {files} files.")
if __name__ == "__main__":
    main()
