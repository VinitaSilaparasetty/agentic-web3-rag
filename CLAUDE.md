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

## Current state (as of 2026-07-03)

- **Index seeded with 7 vectors** from 4 Aevoxis OSS repos (pr-automation-agent,
  spec-drift_chronometer, agentic-web3-rag, multi-agent-audit-poc). `display_policy: fulltext`
  for all (self-owned).
- **Version:** 0.1.0 (Alpha) — **published on PyPI** (`pip install agentic-web3-rag`).
- **CI:** GitHub Actions `ci.yml` runs on every push/PR (59 tests, Python 3.11 + 3.12,
  Docker build check). Coverage threshold is 30% (actual ~34%). The Qdrant service
  container health-check was moved from in-container curl (which failed — Qdrant image
  has no curl) to a runner-side wait loop.

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

## Experiment: EU AI Act Consent Signal Audit

An empirical research study living in `experiments/ai_consent_audit/`. **Do not delete
this directory** — it contains the full dataset and paper for a publishable study.

### What it measures

Prevalence of machine-readable TDM opt-out signals (DSM Directive Art. 4) and voluntary
AI opt-in signals (llms.txt) across GitHub OSS repositories, in the context of EU AI Act
Art. 53(1)(c) compliance obligations.

### Status (as of 2026-07-03)

- **Web3 cohort:** 200 repos — sampled, scanned, classified, analysed. Complete.
- **General-OSS comparison cohort:** 200 repos — complete (finished 2026-07-03).
- **Paper:** `experiments/ai_consent_audit/data/paper.md` — full results written.
- **Next:** Full n=1,000 run + inter-rater reliability coding for journal submission.

### Key findings

| Finding | Value |
|---------|-------|
| Web3 DSM opt-out rate | 6.5% (95% CI [3.8%, 10.8%]) |
| Web3 llms.txt opt-in rate | 27.0% |
| General-OSS opt-in rate | 17.5% (p=0.03 vs. Web3) |
| W3C tdm-reservation header adoption | **0%** in both populations |
| Strongest signal predictor | Has dedicated docs site (logistic β=1.52) |

### Running the experiment

```bash
# Always run from the project root — DATA_DIR is relative to cwd
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)   # loads GITHUB_TOKEN — required for API rate limits

# Pilot run (n=200, ~15 min)
cd experiments/ai_consent_audit && python run_experiment.py --pilot

# Resume comparison cohort scan only
PYTHONPATH=experiments/ai_consent_audit python -c "
import sys; sys.path.insert(0, 'experiments/ai_consent_audit')
from comparison_sampler import scan, classify; scan(); classify()
"

# Re-run analysis + figures only
PYTHONPATH=experiments/ai_consent_audit python -c "
import sys; sys.path.insert(0, 'experiments/ai_consent_audit')
import analysis; analysis.run()
"
```

**Critical:** Run all scripts from the **project root** (`/path/to/agentic-web3-rag`),
not from inside `experiments/ai_consent_audit/`. `DATA_DIR = "experiments/ai_consent_audit/data"`
is a relative path — running from the wrong directory creates a nested duplicate data
directory at `experiments/ai_consent_audit/experiments/ai_consent_audit/data/` and
writes results there instead of the canonical location.

### Experiment file map

| File | Purpose |
|------|---------|
| `experiments/ai_consent_audit/config.py` | All parameters — sample sizes, keywords, paths, delays |
| `experiments/ai_consent_audit/github_sampler.py` | Phase 1 — sample Web3 repos from GitHub API |
| `experiments/ai_consent_audit/signal_scanner.py` | Phase 2 — fetch robots.txt, llms.txt, headers, README/LICENSE per repo |
| `experiments/ai_consent_audit/classifier.py` | Phase 3 — classify each repo as OPT_IN / OPT_OUT / AMBIGUOUS / NONE |
| `experiments/ai_consent_audit/analysis.py` | Phase 4 — Wilson CIs, logistic regression, figures |
| `experiments/ai_consent_audit/comparison_sampler.py` | General-OSS comparison cohort (same phases, different topics) |
| `experiments/ai_consent_audit/data/paper.md` | Full paper (Pandoc Markdown + BibTeX) |
| `experiments/ai_consent_audit/data/references.bib` | Bibliography |
| `experiments/ai_consent_audit/data/figures/` | PNG figures (fig1–fig4) |
| `experiments/ai_consent_audit/data/classified.csv` | Web3 cohort — one row per repo with class label |
| `experiments/ai_consent_audit/data/comparison_classified.csv` | General-OSS cohort — same schema |

### Reproducibility

The experiment has two tiers of reproducibility:

**Fully reproducible (deterministic from committed data):**
Phases 3 and 4 — classifier and analysis — read only the committed JSONL/CSV files
and produce identical outputs on any machine:
```bash
PYTHONPATH=experiments/ai_consent_audit python -c "
import sys; sys.path.insert(0, 'experiments/ai_consent_audit')
import classifier, analysis
classifier.run('experiments/ai_consent_audit/data/signals_raw.jsonl',
               'experiments/ai_consent_audit/data/classified.csv')
classifier.run('experiments/ai_consent_audit/data/comparison_signals_raw.jsonl',
               'experiments/ai_consent_audit/data/comparison_classified.csv')
analysis.run()
"
```

**Snapshot, not exactly reproducible:**
Phases 1 and 2 — sampling and scanning — are point-in-time:
- **Sampling** queries GitHub Search API sorted by stars, which shifts daily. A fresh
  run will return a different repo set than the committed `repos_raw.jsonl`.
- **Scanning** hits live URLs; robots.txt / llms.txt content changes over time.

The committed raw data files (`*_raw.jsonl`, `*_signals_raw.jsonl`) are the authoritative
snapshot (collected 2026-07-02/03). The paper's reported numbers derive from these files.
Anyone can verify the numbers by re-running phases 3–4 against the committed data.

---

## What's NOT done yet (next session priorities)

- [ ] DPA registration with German supervisory authority (non-code, must do before go-live)
- [ ] Set `CORS_ORIGINS` to actual frontend domain in production `.env`
- [ ] `/metrics` Prometheus endpoint (optional, needed for production observability)
- [ ] Increase test coverage toward 40%+ (add integration tests for pipeline code with live Qdrant)
- [ ] Invite external Web3 maintainers to opt in via the README consent button
- [ ] Experiment: full n=1,000 Web3 run + IRR coding for journal submission
