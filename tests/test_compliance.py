"""Tests for apps/common/compliance.py — display policy and snippet logic."""
from unittest.mock import patch

from apps.common.compliance import (
    DEFAULT_SNIPPET_CHARS,
    _domain_for,
    apply_display_policy,
    policy_for_url,
    trim_snippet,
)

# ── trim_snippet ──────────────────────────────────────────────────────────────

def test_trim_snippet_short_string_unchanged():
    assert trim_snippet("hello world", 50) == "hello world"


def test_trim_snippet_long_string_truncated():
    text = "word " * 100  # 500 chars
    result = trim_snippet(text, 20)
    assert result.endswith("…")
    assert len(result) <= 21  # 20 chars + ellipsis


def test_trim_snippet_empty_string():
    assert trim_snippet("") == ""


def test_trim_snippet_collapses_whitespace():
    result = trim_snippet("hello    world\n\nfoo", 100)
    assert "  " not in result


# ── _domain_for ───────────────────────────────────────────────────────────────

def test_domain_for_simple():
    assert _domain_for("https://ethereum.org/en/docs/") == "ethereum.org"


def test_domain_for_subdomain():
    assert _domain_for("https://geth.ethereum.org/docs/") == "geth.ethereum.org"


def test_domain_for_github():
    assert _domain_for("https://github.com/VinitaSilaparasetty/pr-automation-agent") == "github.com"


# ── policy_for_url — _SOURCES overrides ──────────────────────────────────────

def test_policy_for_url_ethereum_returns_snippet():
    pol = policy_for_url("https://ethereum.org/en/developers/docs/")
    assert pol.cache_policy == "snippet"
    assert pol.allowed is True


def test_policy_for_url_geth_matches_ethereum_org_entry():
    # geth.ethereum.org.endswith("ethereum.org") is True, so it matches the
    # ethereum.org entry (snippet) before reaching the geth-specific entry.
    # This is a known ordering quirk in _SOURCES; the payload-first path in
    # apply_display_policy() bypasses it entirely for consented sources.
    pol = policy_for_url("https://geth.ethereum.org/docs/getting-started/private-net")
    assert pol.cache_policy == "snippet"


def test_policy_for_url_unknown_defaults_to_link_only():
    with patch("apps.common.compliance.github_policy_for", return_value=None):
        pol = policy_for_url("https://totally-unknown-web3-site.io/docs/")
    assert pol.cache_policy == "link-only"


# ── apply_display_policy — payload-first resolution ──────────────────────────

def test_apply_display_policy_fulltext_from_payload():
    rec = {
        "url": "https://github.com/VinitaSilaparasetty/pr-automation-agent",
        "display_policy": "fulltext",
        "text": "The quick brown fox",
        "title": "PR Automation Agent",
        "score": 0.9,
        "project": "pr-automation-agent",
        "source_id": "pr-automation-agent-readme",
    }
    out = apply_display_policy(rec)
    assert out["text"] == "The quick brown fox"
    assert out["snippet"] is not None


def test_apply_display_policy_snippet_from_payload():
    rec = {
        "url": "https://github.com/example/repo",
        "display_policy": "snippet",
        "text": "word " * 200,
        "title": "Example Repo",
        "score": 0.8,
        "project": "example",
        "source_id": "example-readme",
    }
    out = apply_display_policy(rec)
    assert out["text"] is None
    assert out["snippet"] is not None
    assert len(out["snippet"]) <= DEFAULT_SNIPPET_CHARS + 1  # +1 for ellipsis


def test_apply_display_policy_link_only_from_payload():
    rec = {
        "url": "https://github.com/example/proprietary",
        "display_policy": "link-only",
        "text": "Secret content",
        "title": "Proprietary",
        "score": 0.5,
        "project": "proprietary",
        "source_id": "proprietary",
    }
    out = apply_display_policy(rec)
    assert out["text"] is None
    assert out["snippet"] is None
    assert "note" in out


def test_apply_display_policy_falls_back_to_url_policy():
    rec = {
        "url": "https://ethereum.org/en/docs/",
        "text": "Ethereum documentation content.",
        "title": "Ethereum Docs",
        "score": 0.7,
        "project": "ethereum",
        "source_id": "ethereum-docs",
        # No display_policy field — should fall through to URL lookup
    }
    out = apply_display_policy(rec)
    # ethereum.org is in _SOURCES as "snippet"
    assert out["text"] is None
    assert out["snippet"] is not None


def test_apply_display_policy_empty_record():
    out = apply_display_policy({})
    assert out["url"] == ""
    assert out["text"] is None
    assert out["snippet"] is None


def test_apply_display_policy_preserves_url_and_title():
    rec = {
        "url": "https://github.com/VinitaSilaparasetty/agentic-web3-rag",
        "display_policy": "fulltext",
        "text": "some content",
        "title": "agentic-web3-rag",
        "score": 0.95,
        "project": "agentic-web3-rag",
        "source_id": "agentic-web3-rag-readme",
    }
    out = apply_display_policy(rec)
    assert out["url"] == rec["url"]
    assert out["title"] == "agentic-web3-rag"
    assert out["score"] == 0.95
    assert out["project"] == "agentic-web3-rag"


def test_apply_display_policy_snippet_uses_existing_snippet_field():
    rec = {
        "url": "https://github.com/example/repo",
        "display_policy": "snippet",
        "snippet": "pre-computed snippet text",
        "text": "much longer full text body",
        "title": "Repo",
        "score": 0.6,
        "project": "example",
        "source_id": "repo",
    }
    out = apply_display_policy(rec)
    assert out["snippet"] == "pre-computed snippet text"
    assert out["text"] is None
