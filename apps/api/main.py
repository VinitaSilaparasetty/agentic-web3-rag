from __future__ import annotations

import logging
import os
import time
import uuid
from collections.abc import Sequence
from typing import Annotated, Any
from urllib.parse import urlparse

import structlog
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from apps.api.assist_helper import assist_answer
from apps.api.embeddings_local import embed_query
from apps.common.compliance import apply_display_policy
from models.config import settings

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger()

_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

app = FastAPI(
    title="Agentic Web3 RAG API",
    version="0.1.0",
    description="Vector-search and RAG over consent-gated Web3 documentation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,   # must be False when allow_origins includes "*"
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)

_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

_MAX_K = 20
_MAX_Q_CHARS = 2_000


@app.middleware("http")
async def _request_logging(request: Request, call_next):
    req_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    log.info(
        "request",
        req_id=req_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        ms=elapsed_ms,
    )
    response.headers["X-Request-Id"] = req_id
    return response


def _build_project_filter(project: str | Sequence[str] | None) -> Filter | None:
    if not project:
        return None
    parts = [project] if isinstance(project, str) else list(project)
    values: list[str] = []
    for item in parts:
        for token in str(item or "").split(","):
            token = token.strip()
            if token and token not in values:
                values.append(token)
    if not values:
        return None
    should: list[FieldCondition] = [
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


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple, dict] = {}
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
    project: Sequence[str] | None,
    offset: int = 0,
    collection: str | None = None,
) -> list[dict[str, Any]]:
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
    out: list[dict[str, Any]] = []
    for p in res:
        pl = dict(p.payload or {})
        pl["score"] = p.score
        pl.setdefault("url", pl.get("source_url"))
        out.append(pl)
    return out


def _validated_k(k: int) -> int:
    if k < 1:
        raise HTTPException(status_code=422, detail="k must be >= 1")
    if k > _MAX_K:
        raise HTTPException(status_code=422, detail=f"k must be <= {_MAX_K}")
    return k


def _validated_q(q: str) -> str:
    q = q.strip()
    if not q:
        raise HTTPException(status_code=422, detail="q must not be empty")
    if len(q) > _MAX_Q_CHARS:
        raise HTTPException(status_code=422, detail=f"q must be <= {_MAX_Q_CHARS} characters")
    return q


@app.get("/", include_in_schema=False)
def root():
    return {"ok": True, "message": "Agentic Web3 RAG API — see /docs"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/search")
def search_api(
    q: Annotated[str, Query(max_length=_MAX_Q_CHARS)],
    k: int = 5,
    project: list[str] | None = Query(None),
    offset: int = 0,
    collection: str | None = None,
):
    q = _validated_q(q)
    k = _validated_k(k)
    raw = _vector_search(q=q, k=k, project=project, offset=offset, collection=collection)
    safe = [apply_display_policy(r) for r in raw]
    safe = _dedupe(safe)
    safe = [_enrich(d) for d in safe]
    return {"results": safe}


@app.post("/assist")
def assist_api(body: dict, response: Response):
    q = _validated_q(body.get("q") or "")
    k = _validated_k(int(body.get("k", 5)))
    project = body.get("project")
    offset = int(body.get("offset", 0))
    collection = body.get("collection")
    docs = _vector_search(q=q, k=k, project=project, offset=offset, collection=collection)
    safe = [apply_display_policy(d) for d in docs]
    safe = _dedupe(safe)
    safe = [_enrich(d) for d in safe]
    answer = assist_answer(q, safe)
    # EU AI Act Art. 50 — disclose AI-generated content to callers
    response.headers["X-AI-Generated"] = "true"
    response.headers["X-AI-Model"] = "openai/gpt-4o-mini" if _use_openai() else "rule-based"
    return {"query": q, "results": safe, "answer": answer, "ai_generated": True}


def _use_openai() -> bool:
    return os.getenv("ASSIST_USE_OPENAI", "false").lower() in ("1", "true", "yes")


def main() -> None:
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    main()
