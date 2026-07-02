# ── Stage 1: build ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /build/
RUN pip install --upgrade pip && pip install --no-warn-script-location --prefix=/install .

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . /app

RUN chown -R app:app /app

USER app

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
