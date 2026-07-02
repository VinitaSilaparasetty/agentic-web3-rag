# File: tools/retrieval.py
# Why: Keep runtime simple; dense-only search is sufficient for alpha.
from __future__ import annotations
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from models.config import settings

_client = QdrantClient(url=settings.qdrant_url)


def search_dense(collection: str, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    res = _client.search(
        collection_name=collection,
        query_vector=vector,
        limit=top_k,
        with_vectors=False,
        search_params=qm.SearchParams(hnsw_ef=128, exact=False),
    )
    return [{"score": r.score, "payload": r.payload, "id": r.id} for r in res]
