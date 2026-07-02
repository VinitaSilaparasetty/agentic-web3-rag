from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List

from models.config import settings
from tools.retrieval import search_dense


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)


async def run_agent(query: str, top_k: int = 5) -> Dict[str, Any]:
    vec = _model().encode([query], normalize_embeddings=True)[0].tolist()
    hits = search_dense(settings.qdrant_alias_active, vec, top_k=top_k)
    bullets: List[str] = []
    for h in hits:
        p = h["payload"]
        src = p.get("url") or p.get("source", "")
        title = p.get("title") or src
        bullets.append(f"- [{title}]({src})")
    answer = (
        "**What:** Concise explanation derived from authorised docs.\n\n"
        "**How:** Follow the referenced doc pages; code snippets live in the linked sources.\n\n"
        "**Sources:**\n" + ("\n".join(bullets) if bullets else "_No sources found._")
    )
    return {"answer": answer, "sources": hits}
