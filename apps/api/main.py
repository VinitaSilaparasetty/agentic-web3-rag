from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from apps.api.assist_helper import assist_answer
from apps.api.embeddings_local import embed_query
from apps.common.compliance import apply_display_policy
from models.config import settings

app = FastAPI(
    title="Agentic Web3 RAG API",
    version="0.1.0",
    description="Vector-search and RAG over consent-gated Web3 documentation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def _build_project_filter(project: Optional[Union[str, Sequence[str]]]) -> Optional[Filter]:
    if not project:
        return None
    parts = [project] if isinstance(project, str) else list(project)
    values: List[str] = []
    for item in parts:
        for token in str(item or "").split(","):
            token = token.strip()
            if token and token not in values:
                values.append(token)
    if not values:
        return None
    should: List[FieldCondition] = [
        cond
        for v in values
        for cond in (
            FieldCondition(key="project", match=MatchValue(value=v)),
            FieldCondition(key="projects", match=MatchAny(any=[v])),
        )
    ]
    return Filter(should=should)


def _enrich(d: dict) -> dict:
    u = d.get("url") or ""
    try:
        pr = urlparse(u)
        d.setdefault("source", pr.netloc)
        if not d.get("title"):
            seg = (pr.path.rstrip("/").split("/")[-1] or pr.netloc).strip()
            if seg:
                d["title"] = seg.replace("-", " ").title()
    except Exception:
        d.setdefault("source", "")
        d.setdefault("title", "")
    return d


def _dedupe(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[tuple, dict] = {}
    for d in rows or []:
        u = d.get("url") or ""
        try:
            pr = urlparse(u)
            key = (pr.netloc.lower(), pr.path.rstrip("/"), pr.query)
            has_anchor = bool(pr.fragment)
        except Exception:
            key = (u, "", "")
            has_anchor = False
        prev = seen.get(key)
        if prev is None:
            seen[key] = d
        elif has_anchor and not bool(urlparse(prev.get("url") or "").fragment):
            seen[key] = d
    return list(seen.values())


def _vector_search(
    q: str,
    k: int,
    project: Optional[Sequence[str]],
    offset: int = 0,
    collection: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query_vector = embed_query(q)
    payload_filter = _build_project_filter(project)
    coll = collection or settings.qdrant_alias_active
    res = _client.query_points(
        collection_name=coll,
        query=query_vector,
        limit=k,
        offset=offset,
        query_filter=payload_filter,
        with_payload=True,
        with_vectors=False,
    ).points
    out: List[Dict[str, Any]] = []
    for p in res:
        pl = dict(p.payload or {})
        pl["score"] = p.score
        pl.setdefault("url", pl.get("source_url"))
        out.append(pl)
    return out


@app.get("/", include_in_schema=False)
def root():
    return {"ok": True, "message": "Agentic Web3 RAG API — see /docs"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/search")
def search_api(
    q: str,
    k: int = 5,
    project: Optional[List[str]] = Query(None),
    offset: int = 0,
    collection: Optional[str] = None,
):
    raw = _vector_search(q=q, k=k, project=project, offset=offset, collection=collection)
    safe = [apply_display_policy(r) for r in raw]
    safe = _dedupe(safe)
    safe = [_enrich(d) for d in safe]
    return {"results": safe}


@app.post("/assist")
def assist_api(body: dict):
    q = (body.get("q") or "").strip()
    if not q:
        raise HTTPException(status_code=422, detail="Field 'q' is required.")
    k = int(body.get("k", 5))
    project = body.get("project")
    offset = int(body.get("offset", 0))
    collection = body.get("collection")
    docs = _vector_search(q=q, k=k, project=project, offset=offset, collection=collection)
    safe = [apply_display_policy(d) for d in docs]
    safe = _dedupe(safe)
    safe = [_enrich(d) for d in safe]
    answer = assist_answer(q, safe)
    return {"query": q, "results": safe, "answer": answer}


def main() -> None:
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    main()
