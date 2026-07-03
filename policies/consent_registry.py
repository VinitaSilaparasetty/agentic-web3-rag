# File: policies/consent_registry.py
# Why: Treat consent as a first-class artifact; fail-closed if missing.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Consent:
    project: str
    domain: str
    status: str
    proof: str
    include_paths: list[str]
    exclude_paths: list[str]
    display_policy: str = "link-only"  # link-only | snippet | fulltext


class ConsentRegistry:
    def __init__(self, path: str = "data/consents.yaml"):
        p = Path(path)
        if not p.exists():
            # We fail-closed here to avoid accidental ingestion without explicit consent.
            raise FileNotFoundError("consents.yaml not found; Phase 1 requires explicit allowlist.")
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        self._items: dict[str, Consent] = {}
        for c in data.get("consents", []):
            if c.get("status") != "approved":
                continue
            domain = c["domain"].lower()
            self._items[domain] = Consent(
                project=c["project"],
                domain=domain,
                status=c["status"],
                proof=c["proof"],
                include_paths=c.get("scope", {}).get("include_paths", []),
                exclude_paths=c.get("scope", {}).get("exclude_paths", []),
                display_policy=c.get("display_policy", "link-only"),
            )

    def is_allowed(self, domain: str, path: str) -> tuple[bool, str]:
        d = domain.lower()
        if d not in self._items:
            return False, "domain_not_allowlisted"
        consent = self._items[d]
        ok_inc = (not consent.include_paths) or any(path.startswith(p) for p in consent.include_paths)
        ok_exc = all(not path.startswith(p) for p in consent.exclude_paths)
        if ok_inc and ok_exc:
            return True, consent.proof
        return False, "path_out_of_scope"

    def display_policy_for(self, domain: str) -> str:
        c = self._items.get(domain.lower())
        return c.display_policy if c else "link-only"

    def evidence_for(self, domain: str) -> str | None:
        c = self._items.get(domain.lower())
        return c.proof if c else None
