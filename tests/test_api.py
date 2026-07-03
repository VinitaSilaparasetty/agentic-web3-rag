"""API endpoint tests using FastAPI's test client (no live Qdrant required)."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app, raise_server_exceptions=True)


# ── /health ──────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ── /search input validation ──────────────────────────────────────────────────

def test_search_missing_q():
    r = client.get("/search")
    assert r.status_code == 422


def test_search_q_too_long():
    r = client.get("/search", params={"q": "x" * 2001})
    assert r.status_code == 422


def test_search_k_too_large():
    with patch("apps.api.main.embed_query", return_value=[0.0] * 384), \
         patch("apps.api.main._client") as mock_client:
        mock_client.query_points.return_value = MagicMock(points=[])
        r = client.get("/search", params={"q": "test", "k": 100})
    assert r.status_code == 422


def test_search_k_zero():
    with patch("apps.api.main.embed_query", return_value=[0.0] * 384), \
         patch("apps.api.main._client") as mock_client:
        mock_client.query_points.return_value = MagicMock(points=[])
        r = client.get("/search", params={"q": "test", "k": 0})
    assert r.status_code == 422


def test_search_returns_results_shape():
    fake_point = MagicMock()
    fake_point.score = 0.9
    fake_point.payload = {
        "url": "https://ethereum.org/en/developers/docs/",
        "project": "ethereum",
        "text": "Some content",
    }
    with patch("apps.api.main.embed_query", return_value=[0.0] * 384), \
         patch("apps.api.main._client") as mock_client:
        mock_client.query_points.return_value = MagicMock(points=[fake_point])
        r = client.get("/search", params={"q": "how does gas work", "k": 1})
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert isinstance(body["results"], list)


# ── /assist input validation ───────────────────────────────────────────────────

def test_assist_missing_q():
    r = client.post("/assist", json={})
    assert r.status_code == 422


def test_assist_empty_q():
    r = client.post("/assist", json={"q": "   "})
    assert r.status_code == 422


def test_assist_q_too_long():
    r = client.post("/assist", json={"q": "x" * 2001})
    assert r.status_code == 422


def test_assist_k_too_large():
    r = client.post("/assist", json={"q": "test", "k": 9999})
    assert r.status_code == 422


def test_assist_returns_ai_generated_flag():
    fake_point = MagicMock()
    fake_point.score = 0.8
    fake_point.payload = {"url": "https://ethereum.org/", "project": "ethereum"}
    with patch("apps.api.main.embed_query", return_value=[0.0] * 384), \
         patch("apps.api.main._client") as mock_client:
        mock_client.query_points.return_value = MagicMock(points=[fake_point])
        r = client.post("/assist", json={"q": "what is gas"})
    assert r.status_code == 200
    body = r.json()
    assert body["ai_generated"] is True
    assert "answer" in body
    assert "results" in body
    assert r.headers.get("x-ai-generated") == "true"


# ── X-Request-Id header ───────────────────────────────────────────────────────

def test_request_id_header_present():
    r = client.get("/health")
    assert "x-request-id" in r.headers
