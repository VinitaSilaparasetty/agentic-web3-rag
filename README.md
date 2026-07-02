<div align="center">

# 🔍 agentic-web3-rag

**Semantic search and AI-assisted answers over consent-gated Web3 documentation.**

[![PyPI version](https://img.shields.io/pypi/v/agentic-web3-rag?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/agentic-web3-rag/)
[![Python](https://img.shields.io/pypi/pyversions/agentic-web3-rag?logo=python&logoColor=white)](https://pypi.org/project/agentic-web3-rag/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Release](https://github.com/VinitaSilaparasetty/agentic-web3-rag/actions/workflows/release.yml/badge.svg)](https://github.com/VinitaSilaparasetty/agentic-web3-rag/actions/workflows/release.yml)
[![GitHub issues](https://img.shields.io/github/issues/VinitaSilaparasetty/agentic-web3-rag)](https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues)

---

Ask natural-language questions about Ethereum, Solidity, Geth, and the broader Web3 ecosystem — get structured answers with cited sources, powered by a local embedding model and Qdrant vector search. Every source ingested requires explicit maintainer consent.

[Installation](#installation) · [Quickstart](#quickstart) · [API Reference](#api-reference) · [Architecture](#architecture) · [Configuration](#configuration) · [Contributing](#contributing)

</div>

---

## ✨ Features

- **Semantic search** over Web3 docs using `fastembed` + Qdrant (no GPU required)
- **AI-assisted answers** with structured output and cited sources
- **Consent-first ingestion** — only indexes domains with explicit maintainer approval
- **Display policy enforcement** — respects license terms (link-only / snippet / fulltext) per domain
- **FastAPI backend** with OpenAPI docs at `/docs`
- **Next.js web UI** for interactive search
- **CLI entry points** — `web3rag-api` and `web3rag-ingest`
- **Docker Compose** stack for one-command local setup

---

## 📸 Screenshots

<div align="center">

**Web UI — search interface**
![Web3 Docs Search UI](docs/screenshots/web-ui.png)

**Live search result for `eth_getBalance`**
![Search result](docs/screenshots/search-result.png)

**OpenAPI interactive docs (`/docs`)**
![API docs](docs/screenshots/api-docs.png)

</div>

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Web3 Sources                        │
│         (ethereum.org, geth.ethereum.org, …)            │
└────────────────────────┬────────────────────────────────┘
                         │  consent gate (consents.yaml)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Ingest Pipeline                        │
│  ingest → preprocess → embed (fastembed) → index        │
│                         │                               │
│              data/processed/   data/vectors/            │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Qdrant    │  vector store
                  │  :6333      │  (Docker)
                  └──────┬──────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI  :8080                         │
│   GET  /search   — dense vector search + policy filter  │
│   POST /assist   — retrieval + structured answer        │
│   GET  /health   — liveness check                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Next.js Web UI     │
              │      :3000           │
              └──────────────────────┘
```

---

## 📦 Installation

**Requirements:** Python 3.11+, Docker

```bash
pip install agentic-web3-rag
```

With optional OpenAI-powered answers:
```bash
pip install "agentic-web3-rag[openai]"
```

For local development:
```bash
git clone https://github.com/VinitaSilaparasetty/agentic-web3-rag.git
cd agentic-web3-rag
pip install -e ".[dev]"
```

---

## 🚀 Quickstart

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your keys:
#   OPENAI_API_KEY=...   (optional — only needed for LLM-assisted answers)
#   GITHUB_TOKEN=...     (optional — raises GitHub API rate limits for discovery)
```

### 2. Start Qdrant

```bash
docker compose up -d qdrant
```

### 3. Run the ingest pipeline

```bash
# Ingest → chunk → embed → index (all four steps)
web3rag-ingest --sources data/sources.yaml
python -m pipelines.preprocess
python -m pipelines.embed
python -m pipelines.index
```

Or use Make:
```bash
make ingest   # runs ingest step
make dev      # creates venv + installs deps
make up       # starts Docker stack
make api      # starts API server
make test     # runs test suite
make eval     # runs retrieval smoke eval
```

### 4. Start the API

```bash
web3rag-api
# → http://localhost:8080
# → http://localhost:8080/docs  (OpenAPI)
```

### 5. (Optional) Start the Web UI

```bash
cd webui
npm install
npm run dev
# → http://localhost:3000
```

---

## 🔌 API Reference

### `GET /health`
Liveness check.
```bash
curl http://localhost:8080/health
# {"ok": true}
```

---

### `GET /search`
Dense vector search over indexed docs.

| Parameter    | Type     | Default | Description                              |
|-------------|----------|---------|------------------------------------------|
| `q`          | `string` | —       | **Required.** Natural-language query     |
| `k`          | `int`    | `5`     | Number of results to return (max 10)     |
| `project`    | `string` | —       | Filter by project (e.g. `ethereum,geth`) |
| `collection` | `string` | —       | Override Qdrant collection name          |
| `offset`     | `int`    | `0`     | Pagination offset                        |

```bash
curl "http://localhost:8080/search?q=how+do+I+call+eth_getBalance&k=3&project=geth"
```

```json
{
  "results": [
    {
      "url": "https://geth.ethereum.org/docs/interacting-with-geth/rpc",
      "title": "Rpc",
      "snippet": "JSON-RPC Server — Interacting with Geth requires sending requests...",
      "score": 0.82,
      "project": "geth",
      "source": "geth.ethereum.org"
    }
  ]
}
```

---

### `POST /assist`
Retrieval-augmented answer with cited sources.

```bash
curl -X POST http://localhost:8080/assist \
  -H "Content-Type: application/json" \
  -d '{"q": "how do I call eth_getBalance in geth", "k": 3}'
```

**Body parameters:**

| Field        | Type     | Default | Description                          |
|-------------|----------|---------|--------------------------------------|
| `q`          | `string` | —       | **Required.** Developer question     |
| `k`          | `int`    | `5`     | Docs to retrieve                     |
| `project`    | `string` | —       | Project filter (`ethereum`, `geth`)  |
| `collection` | `string` | —       | Override Qdrant collection           |
| `offset`     | `int`    | `0`     | Pagination offset                    |

```json
{
  "query": "how do I call eth_getBalance in geth",
  "answer": "### Enable JSON-RPC in geth\n...\n**References**\n- Rpc (geth.ethereum.org) → https://...",
  "results": [...]
}
```

---

## ⚙️ Configuration

All settings are read from environment variables (or `.env`). Copy `.env.example` to get started.

| Variable                    | Default                              | Description                                      |
|----------------------------|--------------------------------------|--------------------------------------------------|
| `QDRANT_URL`               | `http://localhost:6333`              | Qdrant server URL                                |
| `QDRANT_API_KEY`           | —                                    | Qdrant API key (for Qdrant Cloud)                |
| `QDRANT_ALIAS_ACTIVE`      | `web3_docs_active`                   | Active collection alias queried by the API       |
| `QDRANT_COLLECTION_STAGING`| `web3_docs_staging`                  | Staging collection written to by the pipeline    |
| `EMBEDDING_MODEL`          | `sentence-transformers/all-MiniLM-L6-v2` | fastembed model used for indexing and query  |
| `OPENAI_API_KEY`           | —                                    | Enables LLM-assisted answers in `/assist`        |
| `ASSIST_USE_OPENAI`        | `false`                              | Set to `true` to enable OpenAI answers           |
| `ASSIST_OPENAI_MODEL`      | `gpt-4o-mini`                        | OpenAI model for assisted answers                |
| `GITHUB_TOKEN`             | —                                    | Raises GitHub API rate limit for source discovery|
| `USER_AGENT`               | `web3-rag-bot/0.1`                   | HTTP user-agent used during ingestion            |
| `CACHE_POLICY_DEFAULT`     | `link-only`                          | Default display policy for unknown domains       |
| `SNIPPET_CHARS`            | `320`                                | Max characters in returned snippets              |
| `API_HOST`                 | `0.0.0.0`                            | API bind address                                 |
| `API_PORT`                 | `8080`                               | API port                                         |
| `JWT_SECRET`               | `dev-secret-change-me`               | Secret for JWT smoke tokens (change in prod)     |

---

## 🙋 Web3 Maintainers — Opt In

If you maintain Web3 documentation and want it indexed, click the button below. It takes 2 minutes and you can revoke at any time.

<div align="center">

[![Opt in to indexing](https://img.shields.io/badge/Opt%20In%20to%20Indexing-%E2%9C%85%20Submit%20Consent-brightgreen?style=for-the-badge&logo=github)](https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/new?template=consent_to_index.md&title=Consent+to+Index%3A+%5Byour-project-name%5D)

</div>

By submitting the form you agree to the [Consent to Index terms](CONSENT.md). Your GitHub account identity and submission timestamp are recorded as the consent record. You can revoke at any time by commenting "REVOKE" on your issue or emailing info@aevoxis.de — all indexed content is removed within 48 hours.

---

## 📋 Adding Your Own Sources

### 1. Get consent from the doc maintainer

Ask the maintainer to submit the opt-in form above, or raise an issue on their repo pointing them to it. Save the link to their consent issue as proof.

### 2. Add the domain to `data/consents.yaml`

```yaml
consents:
  - status: approved
    domain: yourdocs.example.com
    project: yourproject
    proof: "https://github.com/yourorg/yourrepo/issues/123"
    scope:
      include_paths:
        - /docs/
      exclude_paths: []
```

### 3. Add the URL to `data/sources.yaml`

```yaml
sources:
  - kind: website
    id: yourproject-docs
    project: yourproject
    url: https://yourdocs.example.com/docs/
    consent_proof: "https://github.com/yourorg/yourrepo/issues/123"
```

### 4. Re-run the pipeline

```bash
web3rag-ingest --sources data/sources.yaml
python -m pipelines.preprocess
python -m pipelines.embed
python -m pipelines.index
```

---

## 🐳 Docker

A full Docker Compose stack is included:

```bash
docker compose up -d          # starts Qdrant (+ Postgres)
docker compose down -v        # stops and removes volumes
```

To build and run the API in Docker:

```bash
docker build -f infra/docker/api/Dockerfile -t web3rag-api .
docker run -p 8080:8080 --env-file .env web3rag-api
```

---

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest
```

Run the retrieval smoke eval (requires a running Qdrant with indexed data):

```bash
python -m pipelines.eval_retrieval
```

---

## 📜 Consent & Governance

This project operates on a **deny-by-default** consent model:

- Only domains listed as `approved` in `data/consents.yaml` are ever ingested
- Each entry requires a `proof` link (GitHub issue, email, PR) from the maintainer
- Display policy per domain is enforced at query time (`link-only` / `snippet` / `fulltext`)
- Takedown requests are honoured within 48 hours — see [LEGAL.md](LEGAL.md)
- Full policy details in [GOVERNANCE.md](GOVERNANCE.md)

---

## 🤝 Contributing

Contributions are welcome. Please open an issue before submitting a large PR.

```bash
git clone https://github.com/VinitaSilaparasetty/agentic-web3-rag.git
cd agentic-web3-rag
pip install -e ".[dev]"
pytest
```

- Bug reports → [open an issue](https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/new?template=bug_report.md)
- Feature requests → [open an issue](https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/new?template=feature_request.md)

---

## 💼 Commercial Licensing

This software is licensed under **AGPL-3.0**. For commercial use, enterprise deployment, or white-label licensing:

📧 **info@aevoxis.de**

---

## 📄 License

Copyright © 2025 Vinita Silaparasetty, Aevoxis Solutions.
Licensed under the [GNU Affero General Public License v3.0](LICENSE).
