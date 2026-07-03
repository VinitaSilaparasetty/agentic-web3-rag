import json
import os
import sys
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client import models as qm

# Reuse your local embedder (MiniLM or whatever you wired)
from apps.api.embeddings_local import embed_query

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
DEFAULT_COLLECTION = os.getenv("QCOLL") or os.getenv("QDRANT_COLLECTION") or os.getenv("QDRANT_ALIAS_ACTIVE")
DEFAULT_PROJECT = os.getenv("PROJECT")

def stable_id(url: str) -> str:
    # Stable, valid Qdrant ID derived from URL
    # UUIDv5 (namespace URL) ensures a valid UUID string and reproducible ID
    return str(uuid.uuid5(uuid.NAMESPACE_URL, url))

def  choose_text_for_embedding(rec: dict[str, Any]) -> str:
    # Respect policy: prefer full text if present, else snippet, else title
    if rec.get("text"):
        return rec["text"]
    if rec.get("snippet"):
        return rec["snippet"]
    # For link-only, title only is OK to make the item searchable
    return rec.get("title") or rec.get("url") or ""

def ensure_collection(client: QdrantClient, coll: str, dim: int):
    info = None
    try:
        info = client.get_collection(coll)
    except Exception:
        info = None
    if info is None:
        client.create_collection(
            collection_name=coll,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )

def batcher(iterable, n=64):
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Pipe NDJSON -> Qdrant upsert with local embeddings")
    ap.add_argument("--collection", default=DEFAULT_COLLECTION, help="Target Qdrant collection")
    ap.add_argument("--project", default=DEFAULT_PROJECT, help="Project tag to set on payloads (optional)")
    ap.add_argument("--dry-run", action="store_true", help="Compute vectors but don't upsert")
    ap.add_argument("--batch", type=int, default=64, help="Upsert batch size")
    args = ap.parse_args()

    if not args.collection:
        print("ERROR: No collection specified. Use --collection or set QCOLL/QDRANT_COLLECTION/QDRANT_ALIAS_ACTIVE.", file=sys.stderr)
        sys.exit(2)

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Peek first line to determine embedding dimension
    buf = []
    first = sys.stdin.readline()
    if not first:
        print("No input on stdin", file=sys.stderr)
        sys.exit(0)
    try:
        rec = json.loads(first)
    except Exception as e:
        print(f"Bad NDJSON line: {e}", file=sys.stderr)
        sys.exit(1)

    emb_text = choose_text_for_embedding(rec)
    vec = embed_query(emb_text or "placeholder")
    dim = len(vec)
    ensure_collection(client, args.collection, dim)

    buf.append(rec)
    # Stream rest
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            buf.append(json.loads(line))
        except Exception as e:
            print(f"Skipping bad line: {e}", file=sys.stderr)

    upserts = 0
    for batch in batcher(buf, n=args.batch):
        points = []
        for item in batch:
            url = item.get("url") or ""
            text_for_vec = choose_text_for_embedding(item)
            vector = embed_query(text_for_vec or "placeholder")

            payload = {
                "url": url,
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "text": item.get("text"),
                "license": item.get("license"),
                "project": args.project or infer_project(url),
                "source_id": infer_source_id(url),
            }

            points.append(
                qm.PointStruct(
                    id=stable_id(url),
                    vector=vector,
                    payload=payload,
                )
            )
        if args.dry_run:
            upserts += len(points)
            continue
        client.upsert(collection_name=args.collection, points=points)
        upserts += len(points)

    print(json.dumps({"upserted": upserts, "collection": args.collection, "dim": dim}, ensure_ascii=False))

def infer_project(url: str) -> str:
    host = (url.split("//", 1)[-1].split("/", 1)[0] or "").lower()
    if host.endswith("ethereum.org"):
        return "ethereum"
    if host.endswith("geth.ethereum.org"):
        return "geth"
    return host or "general"

def infer_source_id(url: str) -> str:
    # compact, filesystem-safe source id
    return stable_id(url)[:24]

if __name__ == "__main__":
    main()
