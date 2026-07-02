# File: README.md
# Why: Phase 1 sets strict opt-in posture to earn maintainer trust and minimize legal risk.

# Agentic Web3 RAG — Phase 1 (Private Alpha, Opt-in Only)

**Policy**: ingest only domains/projects listed in `data/consents.yaml` with evidence of explicit maintainer consent.

## Quickstart
```bash
cp .env.example .env
make up
make dev
# add your consenting sources in data/consents.yaml and data/sources.yaml
make ingest
make api
Endpoints
POST /query — retrieval-first answer with cited sources (JWT required)

POST /feedback — store helpful/not helpful (placeholder in Phase 1)

GET /healthz, GET /metrics

See GOVERNANCE.md for compliance details.
