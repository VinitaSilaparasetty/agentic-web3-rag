# Privacy Notice

**Controller:** Aevoxis Solutions · info@aevoxis.de
**Last updated:** 2026-07-02

This notice is provided in accordance with Articles 13 and 14 of the EU General Data Protection Regulation (GDPR) (Regulation 2016/679).

---

## 1. Who we are

Aevoxis Solutions is the data controller for personal data processed in connection with the **agentic-web3-rag** project.

Contact: info@aevoxis.de

---

## 2. What personal data we collect and why

### 2a. Consent to Index submissions

When a Web3 documentation maintainer submits a "Consent to Index" issue on GitHub, we process:

| Data | Purpose | Legal basis |
|------|---------|-------------|
| GitHub username and profile URL | Identity of the consenting party; non-repudiation of consent | GDPR Art. 6(1)(b) — performance of a contract / pre-contractual steps |
| Timestamp of issue submission | Consent record integrity | GDPR Art. 6(1)(b) |
| IP address (recorded by GitHub) | Fraud prevention; identity verification | GDPR Art. 6(1)(f) — legitimate interest |
| Content of the consent form | Defining the scope and terms of the indexing licence | GDPR Art. 6(1)(b) |
| Email address (if provided in issue) | Correspondence about consent scope, policy changes, or takedowns | GDPR Art. 6(1)(b) |

We do **not** use this data for marketing, profiling, or any purpose other than managing the indexing consent relationship.

### 2b. API usage

The agentic-web3-rag API (`/search`, `/assist`, `/health`) does not require authentication and does not collect or store personal data about API callers by default.

If you deploy the API with server-side logging enabled, web server access logs (IP address, timestamp, query string) may be generated. These are subject to your own GDPR obligations as a data controller.

### 2c. Web UI

The Next.js web UI (`webui/`) does not set tracking cookies or send data to third parties. Standard Next.js may set a session-scoped cookie for hot-reload in development mode; this cookie is not present in production builds.

---

## 3. Third-country transfers

Consent issues are stored on **GitHub** (GitHub, Inc., a Microsoft subsidiary, USA). GitHub acts as a data processor under a Data Processing Agreement that includes Standard Contractual Clauses (SCCs) under GDPR Art. 46(2)(c), providing an adequate level of protection for transfers from the EEA to the USA.

For details see: [GitHub's Data Protection Agreement](https://github.com/customer-terms/github-data-protection-agreement)

---

## 4. Retention periods

| Data | Retention |
|------|-----------|
| Consent issue (GitHub) | Kept indefinitely as a public transparency record, even after revocation. The issue is marked as revoked. |
| Embeddings and vector index derived from consented content | Deleted within **48 hours** of revocation (see CONSENT.md §5) |
| Chunked text and metadata in `data/` | Deleted within **48 hours** of revocation |
| API access logs (if enabled by deployer) | Recommended maximum: 90 days |

---

## 5. Your rights under GDPR

As a data subject you have the following rights under Chapter III of the GDPR:

- **Art. 15 — Access:** Request a copy of personal data we hold about you.
- **Art. 16 — Rectification:** Request correction of inaccurate data.
- **Art. 17 — Erasure:** Request deletion of your data (where legally permissible; consent issue records may need to be retained for legal accountability).
- **Art. 18 — Restriction:** Request that we restrict processing while a dispute is resolved.
- **Art. 20 — Portability:** Receive your data in a structured, machine-readable format.
- **Art. 21 — Objection:** Object to processing based on legitimate interest (Art. 6(1)(f)).

To exercise any of these rights, email: **info@aevoxis.de** with subject "GDPR Request — [right you are exercising]". We will respond within **30 days**.

---

## 6. Right to lodge a complaint

If you believe we are processing your personal data in violation of the GDPR, you have the right to lodge a complaint with the supervisory authority responsible for your place of residence. The lead supervisory authority for Aevoxis Solutions (Germany) is:

**Landesbeauftragte für Datenschutz und Informationsfreiheit Baden-Württemberg** (or the authority in your EU member state).

Federal Commissioner for Data Protection and Freedom of Information (BfDI): https://www.bfdi.bund.de

---

## 7. Automated decision-making

We do not use personal data for automated decision-making or profiling within the meaning of GDPR Art. 22.

---

## 8. Security

We implement appropriate technical and organisational measures to protect personal data against accidental loss, destruction, unauthorised access, or disclosure, in accordance with GDPR Art. 32.

---

## 9. Changes to this notice

Material changes will be announced via a commit to this file and (where applicable) via a comment on open consent issues, with at least **30 days** notice before taking effect.
