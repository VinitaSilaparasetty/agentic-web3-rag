"""Experiment configuration — single source of truth for all parameters."""

# ── Population definition ────────────────────────────────────────────────────
SEARCH_TOPICS = [
    "ethereum", "web3", "blockchain", "solidity", "defi",
    "hardhat", "foundry", "wagmi", "ethers", "layer2",
]
MIN_STARS = 50
MIN_PUSHED = "2024-01-01"     # at least one push since Jan 2024 = active repo
TARGET_SAMPLE = 1000          # target N after stratification
PILOT_SAMPLE = 200            # fast pilot run

# ── Stratification strata (license SPDX groups) ──────────────────────────────
LICENSE_STRATA = {
    "permissive":  ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense"],
    "copyleft":    ["GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0"],
    "no_license":  ["NOASSERTION", None, ""],
    "other":       [],  # catch-all
}

# ── Known AI crawler user-agents (for robots.txt analysis) ───────────────────
AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "CCBot", "anthropic-ai", "Claude-Web",
    "PerplexityBot", "YouBot", "cohere-ai", "Google-Extended", "Diffbot",
    "Bytespider", "omgili", "PetalBot", "web3-rag-bot", "Amazonbot",
    "FacebookBot", "ia_archiver", "SemrushBot", "DataForSeoBot",
]

# ── Signal detection keywords ─────────────────────────────────────────────────
OPT_OUT_KEYWORDS = [
    "no ai", "no-ai", "noai", "not for ai",
    "do not train", "do not use for training",
    "training data prohibited", "ai training prohibited",
    "not for machine learning", "not for llm",
    "ai generated content prohibited", "tdm reservation",
    "opt out of ai", "opt-out of ai",
]

OPT_IN_KEYWORDS = [
    "llms.txt", "ai indexing welcome", "available for ai training",
    "opt in to ai", "opt-in to ai", "machine readable consent",
    "ai training allowed", "training data allowed",
    "freely available for ai", "index this project",
]

# ── HTTP request config ───────────────────────────────────────────────────────
REQUEST_TIMEOUT = 10
USER_AGENT = "web3-rag-research-bot/1.0 (academic research; contact info@aevoxis.de)"

# ── Rate limiting (GitHub API: 5000/hr authenticated = ~83/min) ──────────────
GITHUB_API_DELAY = 0.75        # seconds between core API calls
GITHUB_SEARCH_DELAY = 2.0      # seconds between search API calls (30/min limit)
HTTP_DELAY = 0.5               # seconds between external HTTP calls

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = "experiments/ai_consent_audit/data"
REPOS_RAW = f"{DATA_DIR}/repos_raw.jsonl"
SIGNALS_RAW = f"{DATA_DIR}/signals_raw.jsonl"
CLASSIFIED = f"{DATA_DIR}/classified.csv"
ANALYSIS_OUT = f"{DATA_DIR}/analysis_results.json"
FIGURES_DIR = f"{DATA_DIR}/figures"
