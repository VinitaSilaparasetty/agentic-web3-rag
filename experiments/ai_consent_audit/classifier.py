"""
Phase 3 — Classification.

Reads signals_raw.jsonl and applies a deterministic rule-based classifier
to assign each repo to one of four classes:

  OPT_IN     — explicit, positive consent to AI indexing
  OPT_OUT    — explicit refusal of AI indexing / TDM
  AMBIGUOUS  — signals present but contradictory or unclear
  NONE       — no detectable signal

Also assigns a sub-type describing *which* signal triggered the classification.

Writes data/classified.csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from config import CLASSIFIED, SIGNALS_RAW

# ── Classification rules ──────────────────────────────────────────────────────

def _has_opt_out_robots(robots: dict | None) -> bool:
    if not robots:
        return False
    return bool(robots.get("blocks_all_crawlers") or robots.get("blocks_ai_crawlers"))


def _has_opt_in_robots(robots: dict | None) -> bool:
    """llms.txt or a robots.txt explicitly *allowing* a recognised AI crawler."""
    if not robots:
        return False
    # We detect opt-in only via presence of llms.txt (robots.txt is passive)
    return False


def _keyword_opt_out(kw_dict: dict) -> bool:
    return bool(kw_dict.get("opt_out_keywords"))


def _keyword_opt_in(kw_dict: dict) -> bool:
    return bool(kw_dict.get("opt_in_keywords"))


def classify(sig: dict[str, Any]) -> tuple[str, str]:
    """
    Returns (class_label, signal_type).

    class_label : OPT_IN | OPT_OUT | AMBIGUOUS | NONE
    signal_type : free text description of the triggering signal(s)
    """
    opt_out_signals: list[str] = []
    opt_in_signals: list[str] = []

    # ── OPT-OUT signals ──────────────────────────────────────────────────────
    if sig.get("tdm_reservation_header"):
        opt_out_signals.append("tdm-reservation HTTP header")

    if sig.get("x_robots_noai"):
        opt_out_signals.append("X-Robots-Tag: noai/noindex HTTP header")

    repo_robots = sig.get("repo_robots_txt") or {}
    home_robots = sig.get("homepage_robots_txt") or {}

    if _has_opt_out_robots(repo_robots):
        crawlers = repo_robots.get("blocks_ai_crawlers", [])
        if repo_robots.get("blocks_all_crawlers"):
            opt_out_signals.append("repo robots.txt: Disallow:/ for *")
        if crawlers:
            opt_out_signals.append(f"repo robots.txt: blocks AI crawlers {crawlers[:3]}")

    if _has_opt_out_robots(home_robots):
        crawlers = home_robots.get("blocks_ai_crawlers", [])
        if home_robots.get("blocks_all_crawlers"):
            opt_out_signals.append("homepage robots.txt: Disallow:/ for *")
        if crawlers:
            opt_out_signals.append(f"homepage robots.txt: blocks AI crawlers {crawlers[:3]}")

    readme_kw = sig.get("readme_keywords", {})
    license_kw = sig.get("license_keywords", {})

    if _keyword_opt_out(readme_kw):
        opt_out_signals.append(f"README keyword: {readme_kw['opt_out_keywords'][:2]}")

    if _keyword_opt_out(license_kw):
        opt_out_signals.append(f"LICENSE keyword: {license_kw['opt_out_keywords'][:2]}")

    # ── OPT-IN signals ───────────────────────────────────────────────────────
    if sig.get("has_llms_txt"):
        opt_in_signals.append("llms.txt present at homepage")

    if _keyword_opt_in(readme_kw):
        opt_in_signals.append(f"README keyword: {readme_kw['opt_in_keywords'][:2]}")

    if _keyword_opt_in(license_kw):
        opt_in_signals.append(f"LICENSE keyword: {license_kw['opt_in_keywords'][:2]}")

    # ── Classification logic ──────────────────────────────────────────────────
    has_out = bool(opt_out_signals)
    has_in = bool(opt_in_signals)

    if has_in and has_out:
        return "AMBIGUOUS", f"contradictory: opt-in=[{opt_in_signals[0]}] opt-out=[{opt_out_signals[0]}]"
    if has_out:
        return "OPT_OUT", "; ".join(opt_out_signals)
    if has_in:
        return "OPT_IN", "; ".join(opt_in_signals)

    # Secondary: does homepage robots.txt mention AI crawlers at all (even without Disallow:/) ?
    if home_robots.get("has_ai_specific_rules") or repo_robots.get("has_ai_specific_rules"):
        # Has AI-specific rules but not a full block — treat as AMBIGUOUS
        return "AMBIGUOUS", "robots.txt mentions AI crawlers but no full disallow"

    return "NONE", "no detectable AI consent signal"


# ── Main ──────────────────────────────────────────────────────────────────────

FIELDS = [
    "repo_id", "full_name", "stars", "created_at", "pushed_at",
    "license_spdx", "license_stratum", "language", "homepage",
    "class_label", "signal_type",
    "has_repo_robots", "repo_robots_blocks_all", "repo_robots_blocks_ai_count",
    "has_homepage_robots", "homepage_robots_blocks_all", "homepage_robots_blocks_ai_count",
    "has_llms_txt", "tdm_reservation_header", "x_robots_noai",
    "readme_opt_out_count", "readme_opt_in_count",
    "license_opt_out_count", "license_opt_in_count",
]


def run(signals_path: str = SIGNALS_RAW, out_path: str = CLASSIFIED) -> None:
    signals = [
        json.loads(line)
        for line in Path(signals_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(f"[classifier] classifying {len(signals)} repos", flush=True)

    rows = []
    for sig in signals:
        label, sig_type = classify(sig)
        rr = sig.get("repo_robots_txt") or {}
        hr = sig.get("homepage_robots_txt") or {}
        row = {
            "repo_id": sig["repo_id"],
            "full_name": sig["full_name"],
            "stars": sig["stars"],
            "created_at": sig["created_at"],
            "pushed_at": sig["pushed_at"],
            "license_spdx": sig.get("license_spdx") or "",
            "license_stratum": sig.get("license_stratum") or "",
            "language": sig.get("language") or "",
            "homepage": sig.get("homepage") or "",
            "class_label": label,
            "signal_type": sig_type,
            "has_repo_robots": bool(rr),
            "repo_robots_blocks_all": bool(rr.get("blocks_all_crawlers")),
            "repo_robots_blocks_ai_count": len(rr.get("blocks_ai_crawlers", [])),
            "has_homepage_robots": bool(hr),
            "homepage_robots_blocks_all": bool(hr.get("blocks_all_crawlers")),
            "homepage_robots_blocks_ai_count": len(hr.get("blocks_ai_crawlers", [])),
            "has_llms_txt": bool(sig.get("has_llms_txt")),
            "tdm_reservation_header": bool(sig.get("tdm_reservation_header")),
            "x_robots_noai": bool(sig.get("x_robots_noai")),
            "readme_opt_out_count": len((sig.get("readme_keywords") or {}).get("opt_out_keywords", [])),
            "readme_opt_in_count": len((sig.get("readme_keywords") or {}).get("opt_in_keywords", [])),
            "license_opt_out_count": len((sig.get("license_keywords") or {}).get("opt_out_keywords", [])),
            "license_opt_in_count": len((sig.get("license_keywords") or {}).get("opt_in_keywords", [])),
        }
        rows.append(row)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    from collections import Counter
    counts = Counter(r["class_label"] for r in rows)
    total = len(rows)
    print(f"\n[classifier] Results (n={total}):")
    for label in ("OPT_IN", "OPT_OUT", "AMBIGUOUS", "NONE"):
        n = counts[label]
        print(f"  {label:12s}: {n:4d} ({100*n/total:.1f}%)")
    print(f"  Saved to {out_path}", flush=True)


if __name__ == "__main__":
    run()
