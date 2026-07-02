.PHONY: dev up down api ingest eval test fmt lint

dev:
	python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

up:
	docker compose up -d qdrant

down:
	docker compose down -v

api:
	. .venv/bin/activate && uvicorn apps.api.main:app --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8080} --reload

ingest:
	. .venv/bin/activate && python -m pipelines.ingest_entry --sources $${SOURCES:-data/sources.yaml}

eval:
	. .venv/bin/activate && python -m pipelines.eval_retrieval

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check .

fmt:
	. .venv/bin/activate && ruff format .

docker-build:
	docker build -f infra/docker/api/Dockerfile -t web3rag-api .
