# Governance Policy

**agentic-web3-rag** · Aevoxis Solutions · info@aevoxis.de
**Status:** Active (alpha / opt-in only)
**Last updated:** 2026-07-02

---

## Principle

This project operates on a **deny-by-default** model. No content is ever ingested, indexed, or returned unless the domain has been explicitly approved through the consent process described below.

---

## 1. Consent gate

Ingestion is permitted only when **all** of the following conditions are met:

1. The domain appears in `data/consents.yaml` with `status: approved`.
2. The entry includes a `proof` field — a verifiable link (GitHub issue, email thread, PR) from the maintainer granting consent.
3. The entry includes a `scope` block defining permitted include/exclude paths.
4. The consent has not been revoked.

The consent registry is enforced in code by `policies/consent_registry.py`. Any domain not in the registry returns `DENY` at ingest time — the crawler skips the URL entirely and logs a `CONSENT_DENIED` event.

---

## 2. Provenance stored per chunk

Every vector in the Qdrant index stores the following provenance fields in its payload:

| Field | Description |
|-------|-------------|
| `url` | Canonical URL of the source page |
| `project` | Project name (e.g. `ethereum`, `geth`) |
| `source` | Domain of the source (e.g. `geth.ethereum.org`) |
| `license` | SPDX license identifier of the source content |
| `consent_proof` | URL to the consent issue/evidence |
| `crawl_ts` | ISO-8601 timestamp of when the page was crawled |
| `policy_decision` | `ALLOW` or `DENY` (DENY entries are never indexed) |

---

## 3. Display policy enforcement

At query time, every result passes through `apps/common/compliance.py:apply_display_policy()`, which enforces the display tier selected by the domain maintainer:

| Policy | What is returned |
|--------|-----------------|
| `link-only` | URL and title only — no text excerpt |
| `snippet` | URL, title, up to 320 characters of text |
| `fulltext` | URL, title, full extracted chunk text |

The default for any domain not in the registry (which should never be reached due to the consent gate) is `link-only`.

---

## 4. Revocation and purge

When a maintainer revokes consent:

1. Their domain is set to `status: revoked` in `data/consents.yaml`.
2. All Qdrant vectors matching the domain are deleted using `scripts/purge.py --domain <domain>`.
3. All chunked text and metadata files referencing the domain are removed from `data/processed/` and `data/vectors/`.
4. Deletion is completed within **48 hours** of the revocation request.
5. A confirmation is sent to the maintainer by email or GitHub issue comment.

The original consent issue remains visible on GitHub as a public transparency record (marked as revoked).

---

## 5. robots.txt compliance

Before crawling any URL the ingest pipeline:

1. Fetches and parses `robots.txt` for the domain.
2. Checks the configured user-agent (`USER_AGENT` env var, default: `web3-rag-bot/0.1`).
3. Skips any path listed as `Disallow`.
4. Skips any page returning `X-Robots-Tag: noai` or `X-Robots-Tag: noindex` HTTP headers.
5. Skips any page with a `tdm-reservation: 1` header (W3C TDM Reservation Protocol).

---

## 6. Audit trail

All ingestion decisions are logged to stdout in structured JSON with fields:
`event`, `domain`, `url`, `decision`, `reason`, `timestamp`.

Recommended log retention: **90 days** for operational compliance review.

---

## 7. Roles and responsibilities

| Role | Responsible party |
|------|------------------|
| Data controller (GDPR) | Aevoxis Solutions |
| Consent intake review | Vinita Silaparasetty (info@aevoxis.de) |
| Takedown execution | Vinita Silaparasetty (within 48h of request) |
| Policy code changes | Must be reviewed and approved before merge |

---

## 8. Review cadence

This governance policy is reviewed every **6 months** or immediately following:
- Any material change in applicable EU law
- Any takedown dispute or legal challenge
- Any security incident affecting the index
