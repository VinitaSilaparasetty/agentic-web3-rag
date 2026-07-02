# CLAUDE.md — agentic-web3-rag

Semantic search and AI-assisted answers over consent-gated Web3 documentation.
Owner: Vinita Silaparasetty · Aevoxis Solutions · info@aevoxis.de
GitHub: https://github.com/VinitaSilaparasetty/agentic-web3-rag
PyPI: https://pypi.org/project/agentic-web3-rag/

---

## What this project does

A FastAPI + Qdrant RAG (Retrieval-Augmented Generation) system that lets developers search
Web3 documentation (Ethereum, Solidity, Geth, etc.) using natural language. Every source
ingested requires explicit written consent from the maintainer — deny by default.

---

## Current state (as of 2026-07-02)

- **Index is empty.** `data/consents.yaml` and `data/sources.yaml` both have empty lists.
  No domains have been consented yet. The ingest pipeline will skip everything until a real
  consent arrives via the GitHub issue template.
- **Version:** 0.1.0 (Alpha) — not yet published to PyPI. The release workflow is wired
  but the manual steps to publish haven't been triggered.
- **CI:** GitHub Actions `ci.yml` runs on every push/PR (14 tests, Python 3.11 + 3.12,
  Docker build check).

---

## Architecture

```
Web3 maintainer submits consent issue on GitHub
        ↓
data/consents.yaml  ←  add domain + proof URL
data/sources.yaml   ←  add URL + consent_proof URL
        ↓
make ingest   (pipelines/ingest.py — fetches + extracts text via trafilatura)
        ↓
python -m pipelines.preprocess  (chunks text)
        ↓
python -m pipelines.embed       (fastembed, model: sentence-transformers/all-MiniLM-L6-v2, dim=384)
        ↓
python -m pipelines.index       (upserts vectors into Qdrant collection)
        ↓
FastAPI :8080  ←  GET /search  POST /assist  GET /health
        ↓
Next.js webui :3000  (webui/)
```

---

## Critical technical decisions (do not revert without reading this)

| Decision | Reason |
|----------|--------|
| `fastembed` instead of `sentence-transformers` | PyTorch 2.2.2 + NumPy 2.x are incompatible; fastembed is ONNX-based, no GPU needed |
| `query_points()` instead of `search()` | `search()` was removed in qdrant-client v1.12; `query_points()` is the replacement |
| Qdrant pinned to `v1.12.1` in docker-compose | Was on `:latest`; a major release silently broke the API once |
| `allow_credentials=False` in CORS | CORS spec rejects `allow_credentials=True` + `allow_origins=["*"]` combination |
| `k` capped at 20, `q` at 2000 chars | Prevents in-process embedding model DoS |
| EU AI Act Art. 50 header on `/assist` | `/assist` returns `ai_generated: true` + `X-AI-Generated: true` header; deployers must surface this |
| GitHub issue = eIDAS Simple Electronic Signature | Legally admissible consent record under eIDAS Art. 25(1); documented in CONSENT.md §9 |

---

## Key files

| File | Purpose |
|------|---------|
| `apps/api/main.py` | FastAPI app — search, assist, health, CORS, request logging, input validation |
| `apps/api/embeddings_local.py` | fastembed wrapper with `@lru_cache` lazy loader |
| `apps/api/assist_helper.py` | Answer generation — special-case paths → OpenAI → structured fallback |
| `apps/common/compliance.py` | Display policy enforcement (link-only/snippet/fulltext) per domain |
| `policies/consent_registry.py` | Consent gate — reads `data/consents.yaml`, fail-closed |
| `models/config.py` | pydantic-settings `Settings` — all env vars with defaults |
| `pipelines/ingest.py` | Fetch + extract content for consented sources only |
| `data/consents.yaml` | Approved domains — currently empty, awaiting real consents |
| `data/sources.yaml` | URLs to ingest — currently empty |
| `data/processed/` | Chunked markdown output from ingest (gitignored contents) |
| `data/vectors/embeddings.json` | Local embedding cache (gitignored) |
| `CONSENT.md` | Terms for maintainers who want to opt in |
| `PRIVACY.md` | GDPR Art. 13/14 privacy notice |
| `LEGAL.md` | Attribution, takedown process, EU AI Act notice, robots.txt policy |
| `GOVERNANCE.md` | Consent gate rules, provenance fields, revocation/purge procedure |
| `.github/ISSUE_TEMPLATE/consent_to_index.md` | Opt-in form — submission = eIDAS SES |
| `.github/workflows/ci.yml` | CI: test + lint + Docker build on every push |
| `.github/workflows/release.yml` | PyPI Trusted Publisher release (triggers on GitHub Release publish) |
| `infra/docker/api/Dockerfile` | Multi-stage build, non-root user, HEALTHCHECK |

---

## Running locally

```bash
# 1. Environment
cp .env.example .env          # fill in OPENAI_API_KEY if you want LLM answers
source .venv/bin/activate     # .venv already created; or: make dev

# 2. Start Qdrant
docker compose up -d qdrant   # pinned to v1.12.1

# 3. Ingest (only once real consents exist in data/consents.yaml)
make ingest
python -m pipelines.preprocess
python -m pipelines.embed
python -m pipelines.index

# 4. API
make api                      # → http://localhost:8080
                              # → http://localhost:8080/docs

# 5. Web UI (optional)
cd webui && cp .env.local.example .env.local && npm run dev  # → http://localhost:3000
```

---

## Adding a new consented source

1. Maintainer submits opt-in via:
   https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/new?template=consent_to_index.md

2. Add to `data/consents.yaml`:
   ```yaml
   consents:
     - status: approved
       domain: docs.example.com
       project: example
       proof: "https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/N"
       scope:
         include_paths: [/docs/]
         exclude_paths: []
   ```

3. Add to `data/sources.yaml`:
   ```yaml
   sources:
     - kind: website
       id: example-docs
       project: example
       url: https://docs.example.com/docs/
       consent_proof: "https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/N"
   ```

4. Run `make ingest` → preprocess → embed → index

---

## Tests

```bash
pytest                   # 14 tests — all should pass
make lint                # ruff check
make fmt                 # ruff format
```

Tests are in `tests/` and use FastAPI `TestClient` with mocked Qdrant — no live services needed.
Coverage target: 40% minimum (enforced in CI).

---

## Releasing to PyPI

Three manual steps before triggering:
1. Create `pypi` environment in GitHub repo Settings → Environments
2. Add Trusted Publisher on pypi.org (GitHub OIDC, no stored token)
3. Create a GitHub Release tagged `v0.1.0` — the `release.yml` workflow fires automatically

---

## EU / Legal status

| Regulation | Status |
|-----------|--------|
| GDPR | PRIVACY.md written; data controller = Aevoxis Solutions; **still need to register with German DPA before go-live** |
| EU AI Act Art. 50 | `/assist` discloses `ai_generated: true` in body + header |
| DSM Directive Art. 4 (TDM) | Consent model is opt-in — exceeds the opt-out minimum |
| eIDAS | GitHub issue consent = Simple Electronic Signature |
| AGPL-3.0 | Dual-licensed — commercial use via info@aevoxis.de |

---

## Environment variables (see .env.example for full list)

| Variable | Default | Notes |
|----------|---------|-------|
| `QDRANT_URL` | `http://localhost:6333` | |
| `QDRANT_API_KEY` | — | Only needed for Qdrant Cloud |
| `OPENAI_API_KEY` | — | Optional; enables LLM answers in /assist |
| `ASSIST_USE_OPENAI` | `false` | Set `true` to use OpenAI |
| `JWT_SECRET` | `dev-secret-change-me` | **Change in production** |
| `CORS_ORIGINS` | `*` | Set to your frontend domain in production |

---

## What's NOT done yet (next session priorities)

- [ ] DPA registration with German supervisory authority (non-code, must do before go-live)
- [ ] Set `CORS_ORIGINS` to actual frontend domain in production `.env`
- [ ] `/metrics` Prometheus endpoint (optional, needed for production observability)
- [ ] Increase test coverage above 40% baseline (currently thin on pipeline and compliance code)
- [ ] Publish v0.1.0 to PyPI (three manual steps above)
