# File: tests/test_consent_gate.py
# Why: Guardrail to ensure ingestion never bypasses consent in Phase 1.
from policies.consent_registry import ConsentRegistry


def test_allowlist_required():
    reg = ConsentRegistry("data/consents.yaml")
    ok, reason = reg.is_allowed("ethereum.org", "/en/developers/docs/gas/")
    assert ok is True
