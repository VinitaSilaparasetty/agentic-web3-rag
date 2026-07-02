from __future__ import annotations

import json
from functools import lru_cache

from models.config import settings

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=MODEL_ID)


@lru_cache(maxsize=1)
def _qdrant():
    from qdrant_client import QdrantClient
    return QdrantClient(url=settings.qdrant_url)


def evaluate() -> dict:
    model = _model()
    Q = _qdrant()

    qs = [
        "What is an ERC-20 token?",
        "How are gas fees calculated on Ethereum?",
    ]
    passed = 0
    for q in qs:
        vectors = list(model.embed([q]))
        v = [float(x) for x in vectors[0]]
        res = Q.query_points(
            collection_name=settings.qdrant_alias_active,
            query=v,
            limit=5,
            with_vectors=False,
        ).points
        ok = any(
            "ERC-20" in (r.payload.get("text", "")) or "gas" in (r.payload.get("text", ""))
            for r in res
        )
        passed += 1 if ok else 0
    return {"passed": passed, "total": len(qs), "recall": passed / len(qs)}


def main() -> None:
    res = evaluate()
    print(json.dumps(res))
    if res["recall"] < 0.5:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
