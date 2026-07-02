# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.1.0] — 2026-07-02

### Added
- FastAPI backend with `GET /health`, `GET /search`, `POST /assist` endpoints
- Dense vector search over consent-gated Web3 documentation via Qdrant
- `fastembed` (ONNX-based) embeddings — no PyTorch or GPU required
- Deny-by-default consent registry (`policies/consent_registry.py`) — only approved domains are indexed
- Display policy enforcement per domain (`link-only` / `snippet` / `fulltext`)
- Consent-to-index click-wrap framework via GitHub issue template (eIDAS Simple Electronic Signature)
- GDPR-compliant privacy notice (`PRIVACY.md`)
- EU AI Act Art. 50 transparency: `/assist` returns `ai_generated: true` and `X-AI-Generated` header
- Structured JSON request logging with per-request `X-Request-Id` header
- Input validation: `k` capped at 20, `q` capped at 2,000 characters
- Next.js web UI for interactive search
- Docker Compose stack (Qdrant v1.12.1, Postgres)
- Multi-stage Dockerfile with non-root user and `HEALTHCHECK`
- CI workflow: tests on Python 3.11 and 3.12, Docker build check on every push/PR
- PyPI Trusted Publisher release workflow (OIDC, no stored token)
- CLI entry points: `web3rag-api` and `web3rag-ingest`
- AGPL-3.0 licence with commercial licensing option via info@aevoxis.de

### Fixed
- Migrated from deprecated `QdrantClient.search()` to `query_points()` (qdrant-client ≥ 1.12)
- Replaced `sentence-transformers` (broken with NumPy 2.x) with `fastembed`
- CORS configuration: removed invalid `allow_credentials=True` + `allow_origins=["*"]` combination

[Unreleased]: https://github.com/VinitaSilaparasetty/agentic-web3-rag/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/VinitaSilaparasetty/agentic-web3-rag/releases/tag/v0.1.0
