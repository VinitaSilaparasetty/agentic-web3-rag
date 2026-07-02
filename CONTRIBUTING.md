# Contributing

Thank you for your interest in contributing to **agentic-web3-rag**.

## Ground rules

- All contributions must be compatible with the AGPL-3.0 licence.
- The consent-gate is non-negotiable: no PR may weaken the deny-by-default ingestion model.
- Open an issue before starting large changes so we can align on approach.

## Development setup

```bash
git clone https://github.com/VinitaSilaparasetty/agentic-web3-rag.git
cd agentic-web3-rag
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Start Qdrant:

```bash
docker compose up -d qdrant
```

## Running tests

```bash
pytest                   # run all tests with coverage
make lint                # ruff lint check
make fmt                 # ruff auto-format
```

CI runs on every PR: tests must pass on Python 3.11 and 3.12, and the Docker build must succeed.

## Pull request checklist

- [ ] Tests added or updated for any changed behaviour
- [ ] `ruff check .` passes with no errors
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Consent gate untouched (or strengthened only)
- [ ] No secrets committed (`.env` is gitignored; use `.env.example`)

## Reporting bugs

Use the [bug report template](https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/new?template=bug_report.md).

## Requesting features

Use the [feature request template](https://github.com/VinitaSilaparasetty/agentic-web3-rag/issues/new?template=feature_request.md).

## Code of Conduct

Be respectful, constructive, and assume good intent. Harassment of any kind is not tolerated.
