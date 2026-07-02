from __future__ import annotations

import json
from functools import lru_cache

from models.config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)


@lru_cache(maxsize=1)
def _qdrant():
    from qdrant_client import QdrantClient
    return QdrantClient(url=settings.qdrant_url)


def evaluate() -> dict:
    from qdrant_client.http import models as qm

    EMB = _model()
    Q = _qdrant()

    qs = [
        "What is an ERC-20 token?",
        "How are gas fees calculated on Ethereum?",
    ]
    passed = 0
    for q in qs:
        v = EMB.encode([q], normalize_embeddings=True)[0].tolist()
        res = Q.search(
            settings.qdrant_alias_active,
            query_vector=v,
            limit=5,
            with_vectors=False,
            search_params=qm.SearchParams(hnsw_ef=128, exact=False),
        )
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
