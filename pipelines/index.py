"""
File: pipelines/index.py
Why: Source-of-truth fix — join on chunk `id` and carry full payloads during upsert.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from models.config import settings

# ---- Paths / constants -------------------------------------------------------

EMBED_PATH = Path("data/vectors/embeddings.json")
CHUNKS_PATH = Path("data/processed/chunks.jsonl")
COLL = settings.qdrant_collection_staging
QDRANT_URL = settings.qdrant_url


# ---- IO helpers --------------------------------------------------------------

def _load_embeddings(path: Path) -> tuple[list[str], list[list[float]], int]:
    """
    Reads embeddings sidecar written by pipelines.embed:
      {
        "model": "...",
        "dim": 384,
        "ids": [...],              # same order as vectors
        "vectors": [[...], ...]    # list[list[float]]
      }
    """
    blob = json.loads(path.read_text(encoding="utf-8"))
    ids: list[str] = list(blob["ids"])
    vecs: list[list[float]] = []
    for v in blob["vectors"]:
        # Robustly coerce numpy arrays / lists to plain list[float]
        try:
            vv = v.tolist()  # type: ignore[attr-defined]
        except Exception:
            vv = list(v)
        vecs.append([float(x) for x in vv])
    dim: int = int(blob["dim"])
    return ids, vecs, dim


def _load_chunks_by_id(path: Path) -> dict[str, dict[str, Any]]:
    """
    Reads chunks.jsonl into a dict keyed by its 'id'.
    """
    if not path.exists():
        raise FileNotFoundError(
            "No chunks found; run `python -m pipelines.preprocess` first."
        )
    out: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            k = str(d["id"])
            out[k] = d
    return out


# ---- Qdrant helpers ----------------------------------------------------------

def _ensure_collection(client: QdrantClient, coll: str, dim: int) -> None:
    """
    Create the collection if needed with a single default vector @ dim, cosine distance.
    """
    if client.collection_exists(coll):
        return
    client.create_collection(
        collection_name=coll,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )


def _to_point_id(raw_id: str) -> str:
    """
    Qdrant point IDs must be unsigned int or UUID. Many pipelines use short hex ids.
    We map any non-UUID string to a stable UUIDv5 to keep determinism across runs.
    """
    s = str(raw_id)
    # Already a UUID?
    try:
        return str(uuid.UUID(s))
    except Exception:
        pass
    # Otherwise, deterministically derive a UUIDv5 from the raw id
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"web3rag:{s}"))


def _lookup_chunk(by_id: dict[str, dict[str, Any]], eid: str) -> dict[str, Any] | None:
    """
    Try to find the chunk record by exact id; if not present, retry by stripping hyphens.
    """
    if eid in by_id:
        return by_id[eid]
    dehyphen = eid.replace("-", "")
    return by_id.get(dehyphen)


# ---- Main --------------------------------------------------------------------

def main() -> None:
    if not EMBED_PATH.exists():
        raise FileNotFoundError(
            "No embeddings.json found; run `python -m pipelines.embed` first."
        )

    ids, vectors, dim = _load_embeddings(EMBED_PATH)
    by_chunk_id = _load_chunks_by_id(CHUNKS_PATH)

    client = QdrantClient(url=QDRANT_URL)
    _ensure_collection(client, COLL, dim)

    points: list[PointStruct] = []
    for i, eid in enumerate(ids):
        vec = vectors[i]
        pid = _to_point_id(eid)
        ch = _lookup_chunk(by_chunk_id, eid)

        payload: dict[str, Any] = {"uid": eid}
        if ch:
            # Carry full payload fields from chunks.jsonl
            payload.update({
                "text": ch.get("text", ""),
                "project": ch.get("project"),
                "url": ch.get("url"),
                "source_id": ch.get("source_id"),
                "display_policy": ch.get("display_policy", "link-only"),
                "cid": ch.get("cid"),
                "commit": ch.get("commit"),
            })
        else:
            # Ensure text exists for previews, even if empty
            payload.setdefault("text", "")

        points.append(PointStruct(id=pid, vector=vec, payload=payload))

    client.upsert(collection_name=COLL, points=points, wait=True)
    print(f"Upserted {len(points)} points with full payloads into '{COLL}' (dim={dim}).")


if __name__ == "__main__":
    main()


def _load_chunks_by_uid(path: str = "data/processed/chunks.jsonl"):
    by = {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("No chunks found; run `python -m pipelines.preprocess` first.")
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            uid = d.get("uid") or d.get("id")
            if uid:
                by[str(uid)] = d
    return by
