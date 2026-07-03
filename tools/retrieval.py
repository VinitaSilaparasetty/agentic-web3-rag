from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient

from models.config import settings

_client = QdrantClient(url=settings.qdrant_url)


def search_dense(collection: str, vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
    res = _client.query_points(
        collection_name=collection,
        query=vector,
        limit=top_k,
        with_vectors=False,
        with_payload=True,
    ).points
    return [{"score": r.score, "payload": r.payload, "id": r.id} for r in res]
