from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from fastembed import TextEmbedding

CHUNKS_PATH = Path("data/processed/chunks.jsonl")
OUT_PATH    = Path("data/vectors/embeddings.json")
MODEL_ID    = "sentence-transformers/all-MiniLM-L6-v2"

def _read_chunks(path: Path) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                # required fields
                cid = d["id"]
                txt = d["text"]
                chunks.append({
                    "id": cid,
                    "text": txt,
                    "project": d.get("project"),
                    "url": d.get("url"),
                    "source_id": d.get("source_id"),
                })
    return chunks

def _coerce_vectors(vecs) -> List[List[float]]:
    out: List[List[float]] = []
    for v in vecs:
        try:
            vv = v.tolist()  # numpy/onnxruntime style
        except Exception:
            vv = list(v)
        out.append([float(x) for x in vv])
    return out

def main() -> None:
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError("No preprocessed docs found; run preprocess first.")

    chunks = _read_chunks(CHUNKS_PATH)
    texts  = [c["text"] for c in chunks]
    ids    = [c["id"]   for c in chunks]

    emb = TextEmbedding(model_name=MODEL_ID)
    vecs = list(emb.embed(texts))
    vectors = _coerce_vectors(vecs)

    if not vectors:
        raise RuntimeError("No vectors produced.")
    dim = len(vectors[0])

    payload_refs = [
        {"id": c["id"], "url": c.get("url"), "project": c.get("project")}
        for c in chunks
    ]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "model": MODEL_ID,
        "dim": dim,
        "ids": ids,
        "vectors": vectors,
        "payload_refs": payload_refs
    }, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {OUT_PATH} with {len(vectors)} vectors (dim={dim}).")

if __name__ == "__main__":
    main()
