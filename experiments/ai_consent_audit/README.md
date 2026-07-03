# EU AI Act Consent Signal Audit

Empirical study measuring machine-readable TDM opt-out and AI opt-in signal adoption
across GitHub open-source repositories.

**Paper:** [`data/paper.md`](data/paper.md)  
**Pre-registration:** https://doi.org/10.17605/OSF.IO/ZHD5X  
**Author:** Vinita Silaparasetty, Aevoxis Solutions

---

## Key findings (n=200 Web3, n=200 general-OSS)

| Signal | Web3 repos | General-OSS |
|--------|-----------|-------------|
| Any DSM Art. 4 opt-out | 6.5% | 5.0% |
| llms.txt opt-in | **27.0%** | 17.5% (p=0.03) |
| W3C `tdm-reservation: 1` | 0% | 0% |

## Reproducing the classification + analysis

The raw scan data is committed. Phases 3–4 (classify + analyse) are fully deterministic:

```bash
# From the project root (agentic-web3-rag/)
source .venv/bin/activate   # or: pip install -e ".[dev]"

PYTHONPATH=experiments/ai_consent_audit python -c "
import sys; sys.path.insert(0, 'experiments/ai_consent_audit')
import classifier, analysis
classifier.run()
classifier.run(
    signals_path='experiments/ai_consent_audit/data/comparison_signals_raw.jsonl',
    out_path='experiments/ai_consent_audit/data/comparison_classified.csv',
)
analysis.run()
"
```

Expected output:
- Web3: OPT_IN=54 (27%), OPT_OUT=13 (6.5%), AMBIGUOUS=1, NONE=132
- General-OSS: OPT_IN=35 (17.5%), OPT_OUT=10, AMBIGUOUS=5, NONE=150
- Figures written to `data/figures/`

## Running a fresh scan (Tier 2 — point-in-time, needs GitHub token)

Fresh scans will return different repos (GitHub Search results shift daily) and
different signal readings (live URLs change). This is expected and documented in
the paper's §3.1 Reproducibility section.

```bash
# Prerequisites
cp .env.example .env
# Add your GitHub Personal Access Token to .env:
# GITHUB_TOKEN=ghp_...

source .venv/bin/activate
export $(grep -v '^#' .env | xargs)

# Run from project root
PYTHONPATH=experiments/ai_consent_audit \
  python experiments/ai_consent_audit/run_experiment.py --pilot
```

## File map

| File | Purpose |
|------|---------|
| `config.py` | All parameters — sample sizes, keywords, paths, delays |
| `github_sampler.py` | Phase 1 — sample repos from GitHub Search API |
| `signal_scanner.py` | Phase 2 — fetch robots.txt, llms.txt, headers, README/LICENSE |
| `classifier.py` | Phase 3 — classify each repo as OPT_IN / OPT_OUT / AMBIGUOUS / NONE |
| `analysis.py` | Phase 4 — Wilson CIs, Fisher's exact test, logistic regression, figures |
| `comparison_sampler.py` | General-OSS comparison cohort (phases 1–3 bundled) |
| `run_experiment.py` | Orchestrates all phases |
| `data/paper.md` | Full academic paper (Pandoc Markdown) |
| `data/references.bib` | BibTeX bibliography |
| `data/classified.csv` | Web3 cohort classifications |
| `data/comparison_classified.csv` | General-OSS cohort classifications |
| `data/signals_raw.jsonl` | Web3 raw scan output (committed snapshot) |
| `data/comparison_signals_raw.jsonl` | General-OSS raw scan output (committed snapshot) |
| `data/figures/` | Generated PNG figures (fig1–fig4) |

## License

Scanner code and dataset: CC0 (public domain) / AGPL-3.0 (same as parent repo).
