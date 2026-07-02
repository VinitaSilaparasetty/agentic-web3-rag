
File: GOVERNANCE.md
Why: Convert governance into enforceable, code-backed controls.

Phase: alpha / opt-in only

Ingestion allowed only if:

Domain appears in data/consents.yaml with status: approved

Evidence includes contact, proof (URL to email thread/PR/issue), scope paths

Policy engine returns DENY for any non-allowlisted domain.

Provenance stored in payload: url, project, license_hint, consent_ref, crawl_ts, policy_decision.

Purge command (Phase 1): delete by domain or consent_ref (CLI in scripts/purge.py).
