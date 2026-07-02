# Why: Guardrail to ensure the consent gate correctly allows consented domains
# and blocks everything else. Must stay green whenever consents.yaml changes.
from policies.consent_registry import ConsentRegistry


def test_consented_domain_allowed():
    reg = ConsentRegistry("data/consents.yaml")
    ok, reason = reg.is_allowed("github.com", "/VinitaSilaparasetty/pr-automation-agent")
    assert ok is True


def test_unconsented_domain_blocked():
    reg = ConsentRegistry("data/consents.yaml")
    ok, reason = reg.is_allowed("ethereum.org", "/en/developers/docs/")
    assert ok is False
    assert reason == "domain_not_allowlisted"


def test_out_of_scope_path_blocked():
    reg = ConsentRegistry("data/consents.yaml")
    # issues/ is in exclude_paths for github.com/VinitaSilaparasetty/pr-automation-agent
    ok, reason = reg.is_allowed("github.com", "/VinitaSilaparasetty/pr-automation-agent/issues/1")
    assert ok is False
    assert reason == "path_out_of_scope"


def test_display_policy_read_from_consent():
    reg = ConsentRegistry("data/consents.yaml")
    policy = reg.display_policy_for("github.com")
    assert policy == "fulltext"


def test_unknown_domain_returns_link_only():
    reg = ConsentRegistry("data/consents.yaml")
    policy = reg.display_policy_for("unknown.example.com")
    assert policy == "link-only"
