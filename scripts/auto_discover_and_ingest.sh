#!/usr/bin/env bash
set -euo pipefail

# --- config ---
: "${QDRANT_URL:=http://127.0.0.1:6333}"
: "${QCOLL:=web3_docs_staging}"
: "${PROJECT:=ethereum}"    # generic tag; per-URL inference also happens in the ingester
: "${VENV:=.venv}"          # path to your venv

if [ -d "$VENV" ]; then
  . "$VENV/bin/activate"
fi

echo "==> Discovery (respecting SOURCES + robots)"
python scripts/discover_web3_sources.py > /tmp/web3_urls.txt

echo "==> Build NDJSON (policy-enforced: link-only/snippet/fulltext)"
python scripts/build_ndjson_from_urls.py < /tmp/web3_urls.txt > /tmp/web3.ndjson

echo "==> Ingest into Qdrant: $QCOLL"
python scripts/ndjson_to_qdrant.py --collection "$QCOLL" --project "$PROJECT" < /tmp/web3.ndjson

echo "==> Count:"
curl -s -X POST "$QDRANT_URL/collections/$QCOLL/points/count" \
  -H 'Content-Type: application/json' -d '{"exact":true}' | /usr/bin/python3 -m json.tool
