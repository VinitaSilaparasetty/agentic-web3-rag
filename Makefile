# File: Makefile
# Why: One-liners reduce setup friction during opt-in pilot.
.PHONY: dev up down api ingest eval test fmt

dev:
	python -m venv .venv && . .venv/bin/activate && pip install -e .

up:
	docker-compose up -d --build

down:
	docker-compose down -v

api:
	. .venv/bin/activate && uvicorn apps.api.main:app --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8080} --reload

ingest:
	. .venv/bin/activate && python -m pipelines.ingest_entry --sources $${SOURCES:-data/sources.yaml}

eval:
	. .venv/bin/activate && python -m pipelines.eval_retrieval

test:
	. .venv/bin/activate && pytest
