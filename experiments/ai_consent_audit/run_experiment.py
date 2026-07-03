"""
Main experiment runner.

Usage:
  python run_experiment.py --pilot        # n=200, ~15 min
  python run_experiment.py                # n=1000, ~90 min
  python run_experiment.py --scan-only    # re-scan after resuming
  python run_experiment.py --analyse-only # re-run analysis on existing data
"""

from __future__ import annotations

import sys
import time

from config import CLASSIFIED, PILOT_SAMPLE, REPOS_RAW, SIGNALS_RAW, TARGET_SAMPLE


def main() -> None:
    pilot = "--pilot" in sys.argv
    scan_only = "--scan-only" in sys.argv
    analyse_only = "--analyse-only" in sys.argv

    n = PILOT_SAMPLE if pilot else TARGET_SAMPLE
    label = "PILOT" if pilot else "FULL"

    print(f"\n{'='*60}", flush=True)
    print(f"  EU AI Act Consent Signal Audit — {label} RUN (n={n})", flush=True)
    print(f"{'='*60}\n", flush=True)

    t0 = time.time()

    if not analyse_only and not scan_only:
        print("Phase 1/4 — Sampling repositories from GitHub API...", flush=True)
        import github_sampler
        github_sampler.sample(target=n, pilot=pilot)
        print(f"  Done in {time.time()-t0:.0f}s\n", flush=True)

    if not analyse_only:
        t1 = time.time()
        print("Phase 2/4 — Scanning repos for compliance signals...", flush=True)
        import signal_scanner
        signal_scanner.run(repos_path=REPOS_RAW, out_path=SIGNALS_RAW)
        print(f"  Done in {time.time()-t1:.0f}s\n", flush=True)

    t2 = time.time()
    print("Phase 3/4 — Classifying signals...", flush=True)
    import classifier
    classifier.run(signals_path=SIGNALS_RAW, out_path=CLASSIFIED)
    print(f"  Done in {time.time()-t2:.0f}s\n", flush=True)

    t3 = time.time()
    print("Phase 4/4 — Statistical analysis + figures...", flush=True)
    import analysis
    analysis.run()
    print(f"  Done in {time.time()-t3:.0f}s\n", flush=True)

    total = time.time() - t0
    print(f"\n{'='*60}", flush=True)
    print(f"  Experiment complete in {total/60:.1f} minutes", flush=True)
    print("  Results  : experiments/ai_consent_audit/data/analysis_results.json", flush=True)
    print("  Figures  : experiments/ai_consent_audit/data/figures/", flush=True)
    print(f"  Raw data : {CLASSIFIED}", flush=True)
    print(f"{'='*60}\n", flush=True)


if __name__ == "__main__":
    main()
