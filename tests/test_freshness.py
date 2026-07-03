"""Tests for apps/common/freshness.py — domain freshness registry."""
import os
import pytest
from apps.common import freshness


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    """Redirect all registry reads/writes to a temp dir."""
    reg_path = str(tmp_path / "freshness.json")
    monkeypatch.setattr(freshness, "REG_PATH", reg_path)


def test_load_returns_empty_dict_when_no_file():
    assert freshness.load() == {}


def test_save_and_load_round_trip():
    freshness.save({"ethereum.org": 1234567890.0})
    reg = freshness.load()
    assert reg == {"ethereum.org": 1234567890.0}


def test_domain_of_url():
    assert freshness.domain_of("https://ethereum.org/en/docs/") == "ethereum.org"


def test_domain_of_bare_domain():
    assert freshness.domain_of("geth.ethereum.org") == "geth.ethereum.org"


def test_domain_of_is_lowercase():
    assert freshness.domain_of("ETHEREUM.ORG") == "ethereum.org"


def test_mark_seen_creates_entry():
    freshness.mark_seen("https://ethereum.org/docs/")
    assert freshness.last_seen("ethereum.org") is not None


def test_last_seen_returns_none_for_unknown():
    assert freshness.last_seen("unknown.example.com") is None


def test_mark_seen_with_explicit_timestamp():
    freshness.mark_seen("myproject.io", ts=1000.0)
    assert freshness.last_seen("myproject.io") == 1000.0


def test_rank_domains_never_seen_first():
    freshness.mark_seen("old.io", ts=500.0)
    result = freshness.rank_domains(["never-seen.io", "old.io"])
    assert result[0][0] == "never-seen.io"
    assert result[0][1] is None
    assert result[1][0] == "old.io"


def test_rank_domains_older_before_newer():
    freshness.mark_seen("old.io", ts=100.0)
    freshness.mark_seen("new.io", ts=9999.0)
    result = freshness.rank_domains(["new.io", "old.io"])
    assert result[0][0] == "old.io"
    assert result[1][0] == "new.io"


def test_rank_domains_deduplicates():
    result = freshness.rank_domains(["eth.io", "eth.io", "https://eth.io/docs"])
    assert len(result) == 1
    assert result[0][0] == "eth.io"
