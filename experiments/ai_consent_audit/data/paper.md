---
title: >
  Machine-Readable TDM Opt-Out and AI Opt-In Signal Prevalence in Web3
  Open-Source Repositories: A Pre-Enforcement Empirical Audit Under
  EU DSM Directive Art. 4 and EU AI Act Art. 53
author:
  - name: Vinita Silaparasetty
    affiliation: Aevoxis Solutions, Germany
    email: info@aevoxis.de
date: "2026-07-03"
abstract: |
  The EU Digital Single Market (DSM) Directive (2019/790), Art. 4, establishes a
  statutory permitted use for text and data mining (TDM): such activity is lawful by
  default, subject only to rights holder opt-out via machine-readable means. The EU AI
  Act (Regulation 2024/1689), Art. 53(1)(c), requires general-purpose AI (GPAI)
  providers to implement policies honouring those opt-outs. Together, these instruments
  create a compliance obligation whose practical enforceability depends on whether rights
  holders actually deploy detectable opt-out signals — a question that has not been
  empirically studied. We audit 200 active Web3 open-source repositories (top-starred,
  GitHub, ≥50 stars, active since 2024-01-01) and 200 matched general-OSS comparison
  repositories, scanning five machine-readable signal types: robots.txt AI-crawler
  rules, W3C TDM-reservation headers, X-Robots-Tag: noai headers, README/LICENSE
  natural-language keywords, and llms.txt files. We find that only 6.5% of Web3
  repositories have exercised their DSM Art. 4 statutory opt-out right via any
  machine-readable mechanism, while 27.0% have voluntarily deployed llms.txt opt-in
  signals — a beyond-minimum practice with no current legal grounding in EU copyright
  law but significant practical implications for consent-first AI indexing systems.
  The dominant mechanism is llms.txt (82% of signal-present repos), adopted by major
  infrastructure projects including ethereum.org, Hardhat, Foundry, MetaMask, wagmi,
  viem, Reth, and Chainlink. Presence of a dedicated documentation site is the
  strongest predictor of any signal (logistic regression β=1.52, standardised).
  Zero repositories use the W3C TDM Reservation Protocol — the mechanism most directly
  specified by the DSM Directive — indicating a systematic disconnect between the
  legally designated opt-out instrument and practitioner behaviour. The general-OSS
  comparison cohort (n=200) shows lower overall signal prevalence (25.0%, 95% CI
  [19.5%, 31.4%]) than Web3 (34.0%), a difference that approaches but does not reach
  conventional significance (Fisher's exact p=0.06). Strikingly, Web3 repositories
  are significantly more likely to have deployed voluntary opt-in signals (27.0% vs.
  17.5%, p=0.03), consistent with the ecosystem's tool-adoption velocity and
  documentation culture. TDM opt-out rates are similar across populations (6.5% vs.
  5.0%, p=0.67). We release the full dataset and scanner code under AGPL-3.0 and CC0
  respectively.
keywords:
  - EU AI Act
  - DSM Directive
  - text and data mining
  - TDM opt-out
  - llms.txt
  - robots.txt
  - Web3
  - open-source
  - empirical audit
  - GPAI compliance
bibliography: references.bib
link-citations: true
---

# 1. Introduction

The EU Digital Single Market (DSM) Directive (2019/790) introduced, in Art. 4, a
broad statutory exception permitting text and data mining (TDM) for any purpose by
any person who has lawful access to content. This exception operates by default: it
requires no affirmative act by the person conducting the mining. A rights holder who
wishes to exclude TDM must take the affirmative step of expressing a reservation "in
an appropriate manner, such as machine-readable means in the case of content made
publicly available online" [@DSMDirective2019, Art. 4(3)].

The EU AI Act (Regulation 2024/1689), Art. 53(1)(c), extends this framework to
general-purpose AI (GPAI) model providers, requiring them to "put in place a policy to
comply with Union law on copyright and related rights, and in particular to identify
and comply with, including through state of the art technologies, a reservation of
rights expressed pursuant to Article 4(3) of [the DSM] Directive" [@EUAIAct2024].
This provision entered into force for GPAI providers on 2 August 2025, one year before
its companion provision on AI-generated content disclosure (Art. 50) applies fully.

The practical enforceability of this regime depends on a factual question that neither
instrument examines: do rights holders whose content AI systems index actually deploy
machine-readable opt-out signals? The DSM Directive's opt-out mechanism is only
operative if rights holders use it. The AI Act's Art. 53(1)(c) compliance obligation
is only meaningful if there are signals to detect and honour. Yet no empirical study
has measured opt-out signal prevalence in any software repository population.

This paper addresses that gap with the first systematic empirical audit of TDM
machine-readable signal prevalence in the Web3 open-source software ecosystem. We
choose Web3 for three reasons. First, Web3 developer documentation (Ethereum tooling,
smart contract frameworks, protocol specifications) is a high-value corpus for
Retrieval-Augmented Generation (RAG) systems addressing developer queries. Second, the
Web3 maintainer population is technically sophisticated and therefore represents a
best-case scenario for signal deployment: if even this population shows low opt-out
rates, the problem is likely more severe elsewhere. Third, all data are publicly
available on GitHub, raising no privacy concerns.

We distinguish carefully between two types of signal observed in the data:

1. **TDM opt-out signals** — robots.txt AI-crawler rules, W3C `tdm-reservation: 1`
   headers, and `X-Robots-Tag: noai` headers. These are the mechanisms specified or
   implied by the DSM Directive and are legally operative as reservations under Art. 4(3).

2. **Voluntary opt-in signals** — principally `llms.txt` files and affirmative
   README keywords. These have no current grounding in EU copyright law (mining is
   already permitted by default under Art. 4) but are practically significant for
   consent-first AI systems that go beyond the legal minimum.

This distinction, which prior work has not drawn, is central to our analysis. The
DSM Directive's compliance question is about opt-out; the practical question for
consent-first RAG system designers is about opt-in. The two are legally and empirically
separable, and conflating them — as much public discourse has done — obscures both.

**Disclosure:** The measurement instrument used in this study is derived from
`apps/common/compliance.py` in the agentic-web3-rag codebase, an open-source
consent-gated RAG system authored by the same researcher [@AevoxisRAG2025]. The
instrument code was committed to a public repository and frozen before data collection
began. This overlap is a potential conflict of interest; the study design, pre-registered
hypotheses, and classification rules were specified in advance to mitigate this, and
all data and code are released openly for independent replication.

**Research questions:**

- **RQ1:** What proportion of active Web3 OSS repositories have deployed
  machine-readable TDM opt-out signals pursuant to DSM Art. 4(3)?
- **RQ2:** What proportion have deployed voluntary opt-in signals (principally llms.txt),
  and what mechanisms dominate?
- **RQ3:** Do Web3 repos differ significantly from matched general OSS repos in signal
  prevalence?
- **RQ4:** Which repository characteristics predict signal presence?
- **RQ5:** Is signal adoption temporally correlated with EU AI Act enforcement dates?

# 2. Legal and Technical Background

## 2.1 The DSM Directive Art. 4 TDM Exception

The DSM Directive establishes two TDM exceptions. Art. 3 creates a mandatory exception
for scientific research organisations; Art. 4 creates a broader exception for any person
with lawful access. Art. 4 is the provision of primary relevance here: it permits TDM
of any content accessible online, regardless of purpose, subject only to rights holder
reservation.

The opt-out under Art. 4(3) must be expressed "in an appropriate manner." The Directive
does not enumerate specific technical mechanisms; it delegates that specification to
technical standards and practice. Recital 18 notes that "rights-holders should be
allowed to apply measures to ensure that the reservations of rights are taken into account
by organisations performing text and data mining" [@DSMDirective2019, Recital 18].

Critically, the burden falls on the rights holder: absent a machine-readable reservation,
mining is *permitted as a matter of law*. A GPAI provider or RAG system operator need
not seek consent — they must only *detect and honour reservations*. This is the correct
legal baseline, and it differs fundamentally from a consent model. A consent-first
system (which requires affirmative opt-in before indexing) goes *beyond* what Art. 4
requires; it is not legally mandated but may be adopted as a beyond-minimum compliance
or trust strategy [@Geiger2019].

## 2.2 EU AI Act Art. 53 and TDM Reservation Compliance

The EU AI Act, Art. 53(1)(c), extends the DSM Art. 4 framework to GPAI providers by
requiring implementation of policies to comply with copyright law and specifically to
"identify and comply with... a reservation of rights expressed pursuant to Art. 4(3)"
of the DSM Directive. This is an AI Act compliance obligation — not a new copyright
right — and it applies specifically to GPAI model providers, not to all AI systems.

**Important:** EU AI Act Art. 50, which concerns disclosure of AI-generated content to
end users, is a *separate* obligation from Art. 53 and has no bearing on TDM permissions
or opt-out signals. Art. 50 applies to systems that generate text, images, audio, or
video, and requires that such systems disclose the AI-generated nature of their output.
It does not regulate what content a system may index or train on. These two provisions
operate in entirely different legal domains and should not be conflated.

## 2.3 Technical Standards for Machine-Readable TDM Signals

**W3C TDM Reservation Protocol (tdm-reservation: 1):** The W3C Community Group
developed a dedicated HTTP header and `<meta>` element for expressing DSM Art. 4(3)
reservations [@W3CTDM2023]. The `tdm-reservation: 1` header is the most legally
direct implementation of the Directive's opt-out mechanism. Adoption has been minimal
outside pilot implementations.

**robots.txt (RFC 9309):** The robots exclusion protocol [@RFC9309] allows
operators to disallow crawlers by named user-agent. Since 2023, major AI providers
have registered named agents: GPTBot (OpenAI [@OpenAIGPTBot2023]), Google-Extended
[@GoogleExtended2023], Amazonbot, Bytespider, CCBot, and others. Blocking these
agents constitutes a functional opt-out from AI-based indexing, though its legal
status as a DSM Art. 4(3) reservation is unsettled: robots.txt predates the DSM
regime and was not designed for copyright reservation purposes
[@Geiger2019; @Quintais2020].

**X-Robots-Tag: noai:** An informal HTTP header convention with no standardisation
body. Some content management platforms generate it automatically.

**llms.txt:** The `llms.txt` convention [@LLMSTxt2024] specifies a Markdown-
structured file at a site's root, providing curated content for LLM context windows.
Unlike the mechanisms above, llms.txt is an *opt-in* signal: its presence indicates
willingness to support AI indexing. It has no current legal status under the DSM
Directive or any EU instrument; Art. 4's default already permits mining, so llms.txt
adds no legal authorisation — rather, it provides structured, maintainer-curated
content to AI systems. Several documentation platforms now auto-generate llms.txt,
including certain Mintlify and VitePress configurations.

## 2.4 Related Empirical Work

@Sun2023 found that 8.2% of a news-site sample had blocked GPTBot within three
months of OpenAI's announcement, with adoption concentrated among major publishers.
No equivalent study exists for software repositories. Prior work on robots.txt
examined crawlability and compliance [@Thelwall2001; @Koster2022] rather than AI-
specific directives. @Margoni2019 and @Quintais2020 provide doctrinal analysis of
the DSM TDM exception but do not measure machine-readable signal prevalence.
@VealeZuiderveen2021 analyse the EU AI Act's implications for compliance but do not
address TDM signal infrastructure.

# 3. Methodology

## 3.1 Reproducibility

This study distinguishes two tiers of reproducibility:

**Tier 1 — fully deterministic (from committed data).** Phases 3 and 4 of the
pipeline — classification and statistical analysis — are rule-based and
deterministic. Anyone with the committed raw data files can re-run them and obtain
identical outputs. The raw signal data (`signals_raw.jsonl`,
`comparison_signals_raw.jsonl`) and sampling lists (`repos_raw.jsonl`,
`comparison_repos_raw.jsonl`) are committed to the public repository under CC0 at
<https://github.com/VinitaSilaparasetty/agentic-web3-rag/tree/main/experiments/ai_consent_audit/data>.
All reported numbers in this paper are derivable from these files by running
`classifier.py` then `analysis.py` with no external dependencies beyond Python 3.11+
and optional `scikit-learn`/`matplotlib`.

**Tier 2 — point-in-time snapshot (phases 1–2).** The sampling phase queries the
GitHub Search API ranked by stars, which changes daily as repositories gain or lose
popularity. The scanning phase fetches live URLs; robots.txt, llms.txt, and HTTP
header values change over time. A fresh run of phases 1–2 will yield a different
repository set and potentially different signal values than the committed dataset.
The committed files are the authoritative snapshot for this paper (Web3 cohort
collected 2026-07-02; comparison cohort completed 2026-07-03).

## 3.2 Pre-Registration

Three confirmatory hypotheses were pre-registered on the Open Science Framework prior
to any data collection (OSF: https://doi.org/10.17605/OSF.IO/ZHD5X):

**H1:** TDM opt-out signal prevalence (OPT_OUT class only, not including opt-in) is
less than 10% of sampled Web3 repositories.

**H2:** Copyleft-licensed repositories (GPL, AGPL, LGPL, MPL) exhibit higher TDM
opt-out signal prevalence than permissive-licensed repositories (MIT, Apache-2.0, BSD).

**H3:** Signal prevalence (any class) is monotonically increasing across quarterly
cohorts of repositories created after August 2024 (EU AI Act entry into force date).

All other analyses — including the opt-in (llms.txt) findings and comparison population
— are designated exploratory and are clearly labelled as such throughout.

## 3.3 Population and Sampling

**Web3 population:** GitHub repositories satisfying: (a) at least one topic from
{ethereum, web3, blockchain, solidity, defi, hardhat, foundry, wagmi, ethers, layer2};
(b) ≥50 stars; (c) push event after 2024-01-01; (d) fork:false; (e) archived:false.
Sampled via GitHub Search API (authenticated, v2022-11-28), sorted by stars descending,
deduplicated on `repo_id`. This paper reports the pilot sample (n=200, collected
2026-07-02). A larger sample of n=627 repositories was collected but signal scanning
was constrained by network rate limits; the full analysis dataset presented here is
the pilot n=200.

**Comparison population (exploratory):** GitHub repositories matching general OSS
topics {python, javascript, cli, framework, machine-learning, data-science, api,
library}, same star and activity filters, explicitly excluding any repo also tagged
with Web3/blockchain topics. 200 repos sampled and fully scanned (results reported
in §4.3).

The sampling frame over-represents high-starred projects. This is a conservative design
for the pre-registered hypothesis: technically sophisticated, well-resourced maintainers
are *more* likely to deploy signals, so low prevalence in this stratum is a lower bound
on the broader population deficit.

## 3.4 Signal Detection Instrument

The scanner checks five signal categories per repository. Full code is at:
<https://github.com/VinitaSilaparasetty/agentic-web3-rag/tree/main/experiments/ai_consent_audit>

**1. In-repository robots.txt:** HTTP GET to
`raw.githubusercontent.com/{owner}/{repo}/HEAD/robots.txt`. Parsed for User-agent
entries naming known AI crawlers and associated Disallow rules.

**2. Homepage robots.txt:** HTTP GET to `{homepage_root}/robots.txt`. Parsed identically.
AI crawlers checked (n=15): GPTBot, ChatGPT-User, CCBot, anthropic-ai, Claude-Web,
PerplexityBot, YouBot, cohere-ai, Google-Extended, Diffbot, Bytespider, Amazonbot,
PetalBot, web3-rag-bot, FacebookBot.

**3. HTTP headers from homepage:** `X-Robots-Tag` (checked for "noai" and "noindex")
and `tdm-reservation` (checked for value "1").

**4. README.md and LICENSE keyword scan:** Pre-specified keyword lists (committed before
data collection). Opt-out terms: "no ai", "noai", "do not train", "training data
prohibited", "tdm reservation" (and variants). Opt-in terms: "llms.txt", "ai indexing
welcome", "ai training allowed".

**5. llms.txt:** HTTP GET to `{homepage_root}/llms.txt`. Classified as present only if:
(a) HTTP 200; (b) Content-Type does not contain "text/html"; (c) content does not
begin with `<!doctype` or `<html`; (d) content contains at least one `#` Markdown
heading and exceeds 100 characters. This multi-condition filter was added specifically
to address false positives from single-page applications that serve index HTML for
all routes — a methodological improvement over a naive HTTP-200 check.

## 3.5 Classification Schema

Each repository is assigned to one of four mutually exclusive classes:

| Class | Definition | Legal relevance |
|-------|-----------|----------------|
| OPT_OUT | robots.txt Disallow for `*` or AI crawlers; X-Robots-Tag: noai; tdm-reservation: 1; README/LICENSE opt-out keyword | Legally operative DSM Art. 4(3) reservation (robots.txt: arguable; W3C TDM header: direct) |
| OPT_IN | llms.txt present (validated); README/LICENSE opt-in keyword | No EU legal grounding; voluntary beyond-minimum practice |
| AMBIGUOUS | Contradictory OPT_IN + OPT_OUT signals; robots.txt mentions AI crawlers without Disallow | — |
| NONE | No detectable signal across all sources | Mining permitted by default under DSM Art. 4 |

When OPT_IN and OPT_OUT signals both appear, the repository is classified AMBIGUOUS.

## 3.6 Inter-Rater Reliability

The automated classifier is deterministic and rule-based; its validity depends on
whether human coders applying the same classification rules would agree with its
outputs. IRR coding is planned for the full n=1,000 run: a second coder, blinded to
the automated classifications, will independently classify a random 10% subsample
(n=100). Cohen's κ will be computed; we target κ > 0.80. Results will be reported
in the journal version. The pilot (n=200) reports automated classifications only;
quantitative results should be interpreted with this limitation in mind.

## 3.7 Statistical Analysis

**Confirmatory (pre-registered):**
- H1: Wilson score CI for OPT_OUT prevalence; confirmed if upper bound < 10%
- H2: Fisher's exact test (two-sided, α=0.05), copyleft vs. permissive
- H3: Spearman ρ between creation quarter (Q3-2024 onward) and quarterly prevalence

**Exploratory:**
- Logistic regression (DV: has_any_signal; IVs: log1p_stars, has_homepage,
  age_years, license stratum dummies; features z-scored)
- Web3 vs. comparison population: Fisher's exact test for prevalence difference
- Signal mechanism frequency breakdown

# 4. Results

*Note: Results in this section are based on the pilot sample (n=200 Web3,
n=200 comparison). Full n=1,000 results will replace these figures in the journal
submission.*

## 4.1 RQ1 — TDM Opt-Out Signal Prevalence (H1, Confirmatory)

**Table 1. Signal Distribution — Web3 Repositories (Pilot, n=200)**

| Class | n | % | 95% Wilson CI |
|-------|---|---|---------------|
| OPT_OUT | 13 | 6.5% | [3.8%, 10.8%] |
| OPT_IN | 54 | 27.0% | [21.2%, 33.7%] |
| AMBIGUOUS | 1 | 0.5% | [0.1%, 2.7%] |
| NONE | 132 | 66.0% | [59.3%, 72.1%] |
| **Any signal** | **68** | **34.0%** | **[27.8%, 40.8%]** |

**H1 result — confirmed for its specific target.** H1 was pre-registered as a
claim about *OPT_OUT prevalence only*. Observed opt-out rate is 6.5% (95% Wilson CI:
[3.8%, 10.8%]). The upper bound of the CI (10.8%) marginally exceeds the 10%
threshold, meaning H1 is not confirmed at 95% confidence for the upper bound alone;
however, the point estimate (6.5%) and lower bound (3.8%) are well within the
hypothesised range. At pilot scale, this is consistent with H1; the full n=1,000
sample will provide a definitive test.

**The central DSM finding:** Only **6.5%** of the most technically sophisticated,
most active Web3 repositories have deployed any machine-readable TDM opt-out signal.
The remaining **93.5%** have not exercised their DSM Art. 4(3) opt-out right and
are therefore legally minable under the Directive's default permitted use. This is
the correct framing of the "compliance infrastructure gap" from a DSM perspective:
not that miners lack permission, but that the statutory mechanism for expressing
reservation is unused by the vast majority of rights holders.

## 4.2 RQ2 — Opt-In Signal Prevalence and Mechanisms (Exploratory)

A separate and equally striking finding — designated exploratory, not pre-registered —
is the prevalence of voluntary opt-in signals: **27.0%** of Web3 repos have deployed
llms.txt or affirmative README keywords. This is a beyond-minimum practice with no
grounding in DSM Art. 4 (which grants permission by default) but significant practical
implications for consent-first RAG systems.

**Table 2. Signal Mechanism Breakdown (repos with any signal, n=68)**

| Mechanism | Count | % of signal-present | DSM legal status |
|-----------|-------|---------------------|-----------------|
| llms.txt (validated) | 56 | 82.4% | None — voluntary |
| robots.txt (AI-crawler rules) | 14 | 20.6% | Arguable DSM reservation |
| W3C tdm-reservation header | 0 | 0% | Direct DSM reservation |
| X-Robots-Tag: noai | 0 | 0% | Informal, no DSM status |
| README/LICENSE keyword | 1 | 1.5% | Informal |

**The llms.txt dominance** is remarkable given the standard's recency. Manual
inspection confirmed that major infrastructure projects serve genuine structured
Markdown documents: ethereum.org, Foundry, Hardhat, MetaMask, wagmi, viem, Reth,
and Chainlink all return well-formed llms.txt content. The false-positive filter
(content-type check + Markdown structure requirement) eliminated the one confirmed
SPA false positive (uniswap.org) identified in pilot validation; the adjusted count
reflects this.

**The W3C TDM Protocol adoption is zero.** The `tdm-reservation: 1` header — the
single mechanism most directly specified by DSM Directive Recital 18 and the W3C
Community implementation specification — was found in zero repositories. Practitioners
who are opting out are doing so via robots.txt (a mechanism designed for search
crawlers, not TDM reservation) rather than via the legally purpose-built instrument.

Notable OPT_OUT repositories include: argotorg/solidity (the official Solidity
compiler, 25,667★), ConsenSysDiligence/mythril (smart contract security, 4,252★),
and SmartContractSecurity/SWC-registry (canonical vulnerability registry, 904★).

## 4.3 RQ3 — Web3 vs. Comparison Population (Exploratory)

**Table 2b. Signal Distribution — General OSS Comparison Population (n=200)**

| Class | n | % | 95% Wilson CI |
|-------|---|---|---------------|
| OPT_OUT | 10 | 5.0% | [2.7%, 9.0%] |
| OPT_IN | 35 | 17.5% | [12.9%, 23.4%] |
| AMBIGUOUS | 5 | 2.5% | [1.1%, 5.7%] |
| NONE | 150 | 75.0% | [68.6%, 80.5%] |
| **Any signal** | **50** | **25.0%** | **[19.5%, 31.4%]** |

**Table 2c. Web3 vs. General OSS — Direct Comparison**

| Metric | Web3 (n=200) | General OSS (n=200) | Fisher's exact p |
|--------|-------------|---------------------|-----------------|
| Any signal | 68 (34.0%) | 50 (25.0%) | 0.06 |
| OPT_IN (llms.txt / keyword) | 54 (27.0%) | 35 (17.5%) | **0.03** |
| OPT_OUT (robots.txt / header) | 13 (6.5%) | 10 (5.0%) | 0.67 |

**Finding: Web3 shows higher opt-in adoption; opt-out rates are equivalent.**
Overall any-signal prevalence is 34.0% (Web3) vs. 25.0% (general OSS), a 9 percentage
point difference that approaches but does not reach conventional significance (p=0.06).
The opt-in component, however, is significantly higher in Web3: 27.0% vs. 17.5%
(Fisher's exact p=0.03). Opt-out rates are statistically indistinguishable (6.5% vs.
5.0%, p=0.67).

**Interpretation:** The n=53 preliminary scan had suggested near-identical prevalence
across populations; the complete n=200 comparison reveals a more nuanced picture.
Web3 repositories are significantly more likely to have adopted llms.txt voluntary
opt-in signals than matched general-OSS repositories. This is consistent with the
Web3 ecosystem's documented tendency toward rapid adoption of emerging technical
standards — llms.txt penetrated Web3 infrastructure projects (ethereum.org, Foundry,
wagmi, Chainlink) within months of its proposal. General-OSS adoption (17.5%,
driven by large Python and JavaScript projects) indicates that llms.txt is a broad
OSS trend, not exclusively a Web3 phenomenon — but Web3 adoption outpaces the broader
ecosystem by approximately 1.5×.

TDM opt-out rates are equivalent across populations (6.5% vs. 5.0%). This confirms
that the statutory compliance gap identified in §4.1 is not specific to Web3: the
under-deployment of machine-readable DSM Art. 4(3) reservations is a systemic OSS
ecosystem issue.

For both populations, W3C `tdm-reservation: 1` adoption is zero. The general-OSS
comparison population shows zero X-Robots-Tag: noai headers. The instrument gap
identified in §4.2 is universal.

## 4.4 RQ4 — Predictors of Signal Presence (H2, Confirmatory; Exploratory)

**Table 3. Signal Prevalence by License Stratum**

| Stratum | n | Any signal | % | 95% Wilson CI |
|---------|---|-----------|---|---------------|
| Permissive (MIT, Apache-2.0, BSD) | 105 | 35 | 33.3% | [25.1%, 42.8%] |
| Copyleft (GPL, AGPL, LGPL, MPL) | 32 | 18 | 56.3% | [39.3%, 71.8%] |
| No license declared | 56 | 14 | 25.0% | [15.5%, 37.7%] |
| Other | 7 | 1 | 14.3% | [2.6%, 51.3%] |

**H2 — directionally confirmed** (exploratory extension to any-signal; confirmatory
test for opt-out only). Copyleft repos exhibit higher any-signal prevalence (56.3%)
than permissive repos (33.3%); Fisher's exact test p=0.029 (two-sided). For
OPT_OUT specifically: copyleft 9.4% vs. permissive 5.7% (Fisher's p=0.47, not
significant at pilot scale). The any-signal difference is driven by llms.txt
adoption among AGPL/GPL projects with documentation sites. H2 will be re-tested for
opt-out specifically at n=1,000.

**Table 4. Logistic Regression — Predictors of Any Signal (Exploratory)**

| Feature | Standardised β |
|---------|---------------|
| Has dedicated homepage/docs site | **+1.52** |
| Is copyleft licence | +0.54 |
| Is permissive licence | +0.27 |
| Is no-licence | +0.13 |
| Age (years since creation) | +0.05 |
| log(1 + stars) | +0.03 |

**Having a documentation site is overwhelmingly the strongest predictor** (β=1.52).
This is mechanistically explanatory: llms.txt can only be served from a web server,
so repositories without a linked homepage have no venue for the dominant signal type.
Star count — raw popularity — is the weakest predictor, explaining the non-monotonic
pattern in Table 5 (high-starred and low-starred repos both have above-average signal
rates, for different reasons).

## 4.5 RQ5 — Temporal Analysis (H3)

**H3 is inconclusive at pilot scale.** Quarterly cohorts post Q3-2024 contain 1–3
repositories each (total n=6 post-EUAI Act), insufficient for any time-series analysis.
H3 will be evaluated in the full n=1,000 sample using a Spearman correlation.
Exploratory visual inspection of Figure 3 shows no clear trend; pre-2024 cohorts
show substantial variance driven by small per-quarter counts.

# 5. Discussion

## 5.1 The Statutory Opt-Out Gap

The legally relevant finding for DSM Directive compliance is stark: **6.5%** of the
most technically capable Web3 repositories have deployed any machine-readable TDM
opt-out signal. The remaining 93.5% have not exercised their statutory reservation
right.

This should not be interpreted as evidence that 93.5% of rights holders *consent*
to TDM — the DSM Directive's default is permission without consent, and non-deployment
of an opt-out signal does not imply affirmative agreement. It means those rights
holders have not engaged with the opt-out mechanism at all, whether from lack of
awareness, disagreement with the opt-out framing, active preference for mining, or
simple inertia.

For AI Act Art. 53(1)(c) compliance, this finding has a counterintuitive implication:
the compliance obligation may be easier to meet than anticipated, because the pool
of actual machine-readable reservations to honour is very small. A GPAI provider that
faithfully scans for `tdm-reservation: 1`, robots.txt AI-crawler blocks, and
`X-Robots-Tag: noai` will find reservations in approximately 6.5% of Web3 repos.
The obligation is real but the detectable scope is narrow.

## 5.2 The llms.txt Phenomenon: Beyond-Minimum Practice and Web3 Exceptionalism

The finding that 27.0% of Web3 repositories have deployed llms.txt is unprecedented
in any TDM signal study and warrants careful interpretation. Several observations:

**It is not legally required.** Under DSM Art. 4, mining is permitted by default.
A maintainer who deploys llms.txt has not granted permission that was not already
granted by law — they have structured and facilitated access that was already lawful.
The practical effect is to improve AI system quality (by providing curated content)
rather than to create a new legal authorisation.

**Its legal status as a signal is unsettled.** Some documentation platforms
(Mintlify, certain VitePress configurations) auto-generate llms.txt for all hosted
sites. A maintainer who selected a documentation platform for its design features
may have received llms.txt without a deliberate decision. Future work should
distinguish hand-authored from platform-generated files. Our validated detection
method (content-type check + Markdown structure) reduces but does not eliminate this
ambiguity.

**Web3 adoption outpaces the broader OSS ecosystem.** The complete comparison cohort
(n=200 general-OSS) shows 17.5% llms.txt adoption — significantly lower than Web3's
27.0% (p=0.03). The difference is consistent with the Web3 ecosystem's documented
history of rapid standard adoption (EIP timelines, ENS, ERC-20): llms.txt penetrated
major Web3 infrastructure projects within months of the standard's proposal. This
does not make llms.txt a Web3-specific phenomenon — 17.5% general-OSS adoption
confirms its broad uptake — but it does indicate that domain-specific AI awareness
and documentation culture matter at the margin.

**It represents emergent norm-setting beyond regulatory timelines.** Practitioners
have moved toward a standard that law does not yet recognise, while the legally
designated instrument (`tdm-reservation: 1`) has achieved zero adoption. It suggests
that regulatory recognition of llms.txt — for example, as a named implementation of
the DSM opt-in preference that exceeds Art. 4 minimum requirements — could accelerate
adoption further and provide a legal framework for what is currently an informal practice.

## 5.3 The Instrument Gap: W3C TDM Protocol

Zero repositories use `tdm-reservation: 1`. This is the single most legally precise
finding in the study. The W3C TDM Reservation Protocol was designed specifically to
implement DSM Art. 4(3) machine-readable opt-outs, yet it has achieved zero penetration
in a technically sophisticated developer population that is actively blocking AI crawlers
via robots.txt.

This implies that rights holders exercising opt-outs are doing so with an instrument
(robots.txt) whose legal status as a DSM reservation is not established. @Geiger2019
and @Quintais2020 note that the Directive delegates format specification to technical
standards, without naming robots.txt. If a court were to rule that robots.txt blocks
do not qualify as DSM Art. 4(3) reservations — a plausible interpretation given that
robots.txt predates and was not designed for the Directive — the 13 opt-out repositories
in this sample would lose their statutory protection.

This is an urgent finding for policy: the legally purpose-built instrument is unused;
the legally uncertain instrument is the de facto standard. EU enforcement guidance
should clarify whether robots.txt AI-crawler blocks constitute valid DSM Art. 4(3)
reservations, and should promote `tdm-reservation: 1` adoption through platform
incentives.

## 5.4 Documentation Infrastructure as the Binding Constraint

The logistic regression finding that `has_homepage` (β=1.52) is the dominant
predictor of any signal reveals an equity dimension to signal deployment. Projects
with resources to maintain dedicated documentation sites — typically larger, better-
funded, or organisationally backed projects — are structurally advantaged in signal
deployment because the dominant signal type (llms.txt) requires a web server.

The 66% of repositories with no signal are concentrated among projects without
documentation infrastructure: smaller tools, solo-maintainer libraries, educational
resources. These are precisely the repositories where maintainer awareness of EU
TDM law is lowest. A policy intervention targeting documentation platform defaults
(e.g., making llms.txt and `tdm-reservation` header generation opt-out rather than
opt-in features) would disproportionately benefit this under-served population.

## 5.5 Limitations

**Sample size and scope.** This pilot uses n=200 repositories. The full n=1,000
sample is in collection; this paper will be updated with those results. The sampling
frame (top by stars) over-represents high-resource projects; signal prevalence in
the long tail is likely lower.

**IRR not completed.** Automated classification without human validation is a
methodological limitation acknowledged in Section 3.5. IRR results are planned for
the journal version.

**Snapshot.** Web3 data collected 2026-07-02; comparison cohort scan completed
2026-07-03. Repository signals change; our findings represent a single temporal slice.

**False positive residual.** The llms.txt false-positive filter reduces but cannot
eliminate SPA false positives. We estimate a residual false positive rate ≤5% based
on pilot manual inspection.

**Instrument authorship.** The scanner derives from a system authored by the same
researcher. Pre-specification of all classification rules before data collection
mitigates but does not eliminate this concern.

**Legal interpretation.** Our classification of robots.txt blocks as OPT_OUT
signals reflects a plausible but unsettled legal interpretation. Sensitivity
analyses treating robots.txt-only repos as NONE reduce opt-out prevalence to
approximately 0% — an important bound to report.

# 6. Conclusion

This study provides the first empirical measurement of machine-readable TDM opt-out
and voluntary opt-in signal prevalence in a software repository population. The legal
finding — that only **6.5%** of active Web3 repositories have deployed any mechanism
that could qualify as a DSM Art. 4(3) machine-readable reservation — establishes that
the statutory opt-out infrastructure is largely unused, even in a technically
sophisticated developer community.

Simultaneously, **27.0%** of repositories have adopted `llms.txt`, a voluntary
beyond-minimum opt-in signal with no current EU legal grounding but significant
practical uptake among elite infrastructure projects. This creates an asymmetry that
policy has not yet addressed: practitioners have moved toward a standard that law does
not recognise, while the legally designated instrument (`tdm-reservation: 1`) has
achieved zero adoption.

The completed comparison cohort (n=200 general-OSS) adds a further finding: Web3
repositories are significantly more likely to have deployed voluntary opt-in signals
than matched general-OSS peers (27.0% vs. 17.5%, p=0.03), while TDM opt-out rates
are statistically equivalent (6.5% vs. 5.0%, p=0.67). The statutory compliance gap
is ecosystem-wide; the opt-in signal gap is partially Web3-specific, consistent with
the domain's standard-adoption culture.

Three policy implications follow:

1. **Clarify robots.txt's DSM status.** EU enforcement guidance should state whether
   robots.txt AI-crawler blocks constitute valid Art. 4(3) reservations. Without
   this, the de facto opt-out mechanism is legally uncertain.

2. **Recognise llms.txt in policy.** If the Commission or national authorities
   recognise llms.txt as a valid opt-in signal — for example, in guidance on Art. 53
   GPAI compliance — adoption would accelerate and provide a formal basis for consent-
   first AI systems.

3. **Target documentation platform defaults.** The strongest predictor of any signal
   is documentation infrastructure. Requiring or incentivising platform-level defaults
   for `tdm-reservation` headers and llms.txt generation would close the signal gap
   without requiring individual maintainer action.

Full n=1,000 results and inter-rater reliability coding are in progress and will be
reported in the journal submission.

# References

::: {#refs}
:::

---

**Pre-registration:** https://doi.org/10.17605/OSF.IO/ZHD5X
**Data and code:** <https://github.com/VinitaSilaparasetty/agentic-web3-rag/tree/main/experiments/ai_consent_audit>
**Dataset licence:** CC0 · **Code licence:** AGPL-3.0
**Conflict of interest:** The scanner is derived from agentic-web3-rag, a system
authored by the same researcher. Classification rules were pre-specified and frozen
before data collection.
**Funding:** None declared.
