"""
Phase 4 — Statistical analysis and figure generation.

Reads data/classified.csv and produces:
  - data/analysis_results.json  (all numbers needed for the paper)
  - data/figures/fig1_prevalence.png
  - data/figures/fig2_by_license.png
  - data/figures/fig3_temporal.png
  - data/figures/fig4_signal_types.png
"""

from __future__ import annotations

import csv
import json
import math
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import ANALYSIS_OUT, CLASSIFIED, FIGURES_DIR

# ── Statistical helpers ───────────────────────────────────────────────────────

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion k/n at confidence level z."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def chi2_goodness_of_fit(observed: list[int], expected_probs: list[float]) -> tuple[float, int]:
    """Chi-square goodness of fit; returns (chi2_stat, degrees_of_freedom)."""
    n = sum(observed)
    chi2 = sum(
        (o - n * e) ** 2 / (n * e)
        for o, e in zip(observed, expected_probs)
        if n * e > 0
    )
    df = len(observed) - 1
    return chi2, df


def logistic_coeff(X: list[list[float]], y: list[int]) -> dict[str, float] | None:
    """
    Minimal gradient-descent logistic regression (no external deps).
    Returns dict of {feature_name: coeff} or None if sklearn available.
    Only used as fallback — prefer sklearn when available.
    """
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler

        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=int)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_arr)
        model = LogisticRegression(max_iter=1000, solver="lbfgs")
        model.fit(X_scaled, y_arr)
        # feature names defined by callers
        return {
            "coefficients": model.coef_[0].tolist(),
            "intercept": float(model.intercept_[0]),
            "classes": model.classes_.tolist(),
        }
    except ImportError:
        return None


# ── Data loading ──────────────────────────────────────────────────────────────

def load(path: str = CLASSIFIED) -> list[dict[str, Any]]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # coerce types
            row["stars"] = int(row["stars"] or 0)
            row["has_repo_robots"] = row["has_repo_robots"] == "True"
            row["has_homepage_robots"] = row["has_homepage_robots"] == "True"
            row["has_llms_txt"] = row["has_llms_txt"] == "True"
            row["tdm_reservation_header"] = row["tdm_reservation_header"] == "True"
            row["x_robots_noai"] = row["x_robots_noai"] == "True"
            row["readme_opt_out_count"] = int(row.get("readme_opt_out_count") or 0)
            row["readme_opt_in_count"] = int(row.get("readme_opt_in_count") or 0)
            row["license_opt_out_count"] = int(row.get("license_opt_out_count") or 0)
            row["license_opt_in_count"] = int(row.get("license_opt_in_count") or 0)
            rows.append(row)
    return rows


# ── Analysis functions ────────────────────────────────────────────────────────

def rq1_prevalence(rows: list[dict]) -> dict[str, Any]:
    """RQ1: What proportion emit any AI consent signal?"""
    n = len(rows)
    counts = Counter(r["class_label"] for r in rows)
    has_signal = counts["OPT_IN"] + counts["OPT_OUT"] + counts["AMBIGUOUS"]
    lo, hi = wilson_ci(has_signal, n)

    result: dict[str, Any] = {
        "n_total": n,
        "n_opt_in": counts["OPT_IN"],
        "n_opt_out": counts["OPT_OUT"],
        "n_ambiguous": counts["AMBIGUOUS"],
        "n_none": counts["NONE"],
        "n_any_signal": has_signal,
        "pct_any_signal": round(100 * has_signal / n, 2) if n else 0,
        "pct_opt_in": round(100 * counts["OPT_IN"] / n, 2) if n else 0,
        "pct_opt_out": round(100 * counts["OPT_OUT"] / n, 2) if n else 0,
        "pct_ambiguous": round(100 * counts["AMBIGUOUS"] / n, 2) if n else 0,
        "pct_none": round(100 * counts["NONE"] / n, 2) if n else 0,
        "wilson_ci_any_signal_95": [round(lo * 100, 2), round(hi * 100, 2)],
    }

    # Chi-square: are the 4 classes equally distributed among signal-present repos?
    signal_counts = [counts["OPT_IN"], counts["OPT_OUT"], counts["AMBIGUOUS"]]
    if sum(signal_counts) > 0:
        chi2, df = chi2_goodness_of_fit(signal_counts, [1 / 3, 1 / 3, 1 / 3])
        result["chi2_direction"] = round(chi2, 4)
        result["chi2_direction_df"] = df
    return result


def rq2_direction(rows: list[dict]) -> dict[str, Any]:
    """RQ2: Signal direction breakdown among repos that have any signal."""
    signal_rows = [r for r in rows if r["class_label"] != "NONE"]
    n = len(signal_rows)
    if n == 0:
        return {"n_with_signal": 0}

    counts = Counter(r["class_label"] for r in signal_rows)

    # Signal sub-types
    signal_types: Counter = Counter()
    for r in signal_rows:
        for part in r.get("signal_type", "").split(";"):
            p = part.strip()
            if p:
                # normalise to category
                if "robots.txt" in p.lower():
                    signal_types["robots.txt"] += 1
                elif "llms.txt" in p.lower():
                    signal_types["llms.txt"] += 1
                elif "x-robots" in p.lower() or "tdm" in p.lower():
                    signal_types["HTTP header"] += 1
                elif "readme" in p.lower():
                    signal_types["README keyword"] += 1
                elif "license" in p.lower():
                    signal_types["LICENSE keyword"] += 1
                else:
                    signal_types["other"] += 1

    return {
        "n_with_signal": n,
        "n_opt_in": counts["OPT_IN"],
        "n_opt_out": counts["OPT_OUT"],
        "n_ambiguous": counts["AMBIGUOUS"],
        "pct_opt_in_of_signal": round(100 * counts["OPT_IN"] / n, 2),
        "pct_opt_out_of_signal": round(100 * counts["OPT_OUT"] / n, 2),
        "pct_ambiguous_of_signal": round(100 * counts["AMBIGUOUS"] / n, 2),
        "signal_mechanism_counts": dict(signal_types.most_common()),
    }


def rq3_predictors(rows: list[dict]) -> dict[str, Any]:
    """RQ3: What repo characteristics predict having any signal?"""
    # Logistic regression: DV = has_signal (binary)
    # IVs: log1p(stars), license_stratum (one-hot), age_years, has_homepage
    y = [1 if r["class_label"] != "NONE" else 0 for r in rows]
    now = datetime.now(UTC)

    def age(r: dict) -> float:
        try:
            dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            return (now - dt).days / 365.25
        except Exception:
            return 0.0

    feature_names = ["log1p_stars", "has_homepage", "age_years",
                     "is_permissive", "is_copyleft", "is_no_license"]

    X = []
    for r in rows:
        X.append([
            math.log1p(r["stars"]),
            1.0 if r.get("homepage") else 0.0,
            age(r),
            1.0 if r.get("license_stratum") == "permissive" else 0.0,
            1.0 if r.get("license_stratum") == "copyleft" else 0.0,
            1.0 if r.get("license_stratum") == "no_license" else 0.0,
        ])

    lr_result = logistic_coeff(X, y)

    # Stratified prevalence by license
    by_license: dict[str, Any] = {}
    strata = ["permissive", "copyleft", "no_license", "other"]
    for st in strata:
        sub = [r for r in rows if r.get("license_stratum") == st]
        if not sub:
            continue
        k = sum(1 for r in sub if r["class_label"] != "NONE")
        lo, hi = wilson_ci(k, len(sub))
        by_license[st] = {
            "n": len(sub),
            "n_with_signal": k,
            "pct": round(100 * k / len(sub), 2),
            "wilson_ci_95": [round(lo * 100, 2), round(hi * 100, 2)],
        }

    # Stratified by stars quartile
    sorted_stars = sorted(r["stars"] for r in rows)
    q25 = sorted_stars[len(sorted_stars) // 4]
    q75 = sorted_stars[3 * len(sorted_stars) // 4]
    by_stars = {}
    for label, cond in [("low_stars", lambda s: s < q25),
                         ("mid_stars", lambda s: q25 <= s < q75),
                         ("high_stars", lambda s: s >= q75)]:
        sub = [r for r in rows if cond(r["stars"])]
        k = sum(1 for r in sub if r["class_label"] != "NONE")
        by_stars[label] = {
            "n": len(sub), "n_with_signal": k,
            "pct": round(100 * k / len(sub), 2) if sub else 0,
        }

    return {
        "logistic_regression": lr_result,
        "feature_names": feature_names,
        "prevalence_by_license_stratum": by_license,
        "prevalence_by_stars_quartile": by_stars,
        "q25_stars": q25,
        "q75_stars": q75,
    }


def rq4_temporal(rows: list[dict]) -> dict[str, Any]:
    """RQ4: Is signal adoption increasing around EU AI Act enforcement dates?"""
    # EU AI Act key dates
    key_dates = {
        "euaia_entry_into_force": "2024-08-01",
        "euaia_general_provisions": "2025-02-02",
        "euaia_art50_applies": "2026-08-02",
    }

    # Repo creation by quarter (how many new repos include signals at creation)
    by_quarter: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "with_signal": 0})
    for r in rows:
        try:
            dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            qkey = f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
            by_quarter[qkey]["total"] += 1
            if r["class_label"] != "NONE":
                by_quarter[qkey]["with_signal"] += 1
        except Exception:
            pass

    quarterly = {
        k: {
            **v,
            "pct": round(100 * v["with_signal"] / v["total"], 2) if v["total"] else 0,
        }
        for k, v in sorted(by_quarter.items())
    }

    return {
        "key_enforcement_dates": key_dates,
        "signal_prevalence_by_creation_quarter": quarterly,
        "note": (
            "Full temporal analysis (ITS with enforcement-date breakpoints) requires "
            "larger N to fit broken-stick regression. See paper appendix."
        ),
    }


# ── Figure generation ─────────────────────────────────────────────────────────

def _try_figures(rows: list[dict], results: dict[str, Any]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[analysis] matplotlib not available — skipping figures", flush=True)
        return

    Path(FIGURES_DIR).mkdir(parents=True, exist_ok=True)
    COLORS = {
        "OPT_IN": "#2ecc71",
        "OPT_OUT": "#e74c3c",
        "AMBIGUOUS": "#f39c12",
        "NONE": "#bdc3c7",
    }

    # ── Fig 1: Overall class distribution (pie) ───────────────────────────────
    r1 = results["rq1_prevalence"]
    labels = ["OPT_IN", "OPT_OUT", "AMBIGUOUS", "NONE"]
    sizes = [r1[f"n_{lbl.lower()}"] for lbl in labels]
    colors = [COLORS[lbl] for lbl in labels]
    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors, autopct=lambda p: f"{p:.1f}%" if p > 1 else "",
        startangle=140, pctdistance=0.78,
    )
    for at in autotexts:
        at.set_fontsize(10)
    ax.legend(
        wedges, [f"{lbl} (n={s})" for lbl, s in zip(labels, sizes)],
        loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=11,
    )
    ax.set_title(
        f"AI Consent Signal Distribution in Web3 OSS Repositories (n={r1['n_total']})",
        fontsize=13, pad=16,
    )
    plt.tight_layout()
    plt.savefig(f"{FIGURES_DIR}/fig1_prevalence.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  [figures] fig1_prevalence.png", flush=True)

    # ── Fig 2: Prevalence by license stratum (grouped bar) ────────────────────
    by_lic = results["rq3_predictors"]["prevalence_by_license_stratum"]
    if by_lic:
        strata = list(by_lic.keys())
        pcts = [by_lic[s]["pct"] for s in strata]
        ns = [by_lic[s]["n"] for s in strata]
        ci_lo = [by_lic[s]["wilson_ci_95"][0] for s in strata]
        ci_hi = [by_lic[s]["wilson_ci_95"][1] for s in strata]
        err = [[p - lo for p, lo in zip(pcts, ci_lo)],
               [hi - p for p, hi in zip(pcts, ci_hi)]]
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(strata, pcts, color="#3498db", alpha=0.8, edgecolor="white")
        ax.errorbar(range(len(strata)), pcts, yerr=err, fmt="none",
                    color="black", capsize=4, linewidth=1.5)
        for bar, n in zip(bars, ns):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"n={n}", ha="center", va="bottom", fontsize=9)
        ax.set_xlabel("License stratum", fontsize=12)
        ax.set_ylabel("% repos with any AI consent signal", fontsize=12)
        ax.set_title("Signal Prevalence by License Type (95% Wilson CI)", fontsize=13)
        ax.set_ylim(0, max(pcts) * 1.4 + 5)
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{FIGURES_DIR}/fig2_by_license.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("  [figures] fig2_by_license.png", flush=True)

    # ── Fig 3: Temporal — quarterly signal adoption ──────────────────────────
    quarters = results["rq4_temporal"]["signal_prevalence_by_creation_quarter"]
    if len(quarters) >= 3:
        qs = list(quarters.keys())
        totals = [quarters[q]["total"] for q in qs]
        signals = [quarters[q]["with_signal"] for q in qs]
        x = range(len(qs))
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.bar(x, totals, color="#bdc3c7", label="Total repos", alpha=0.6)
        ax1.bar(x, signals, color="#3498db", label="Repos with signal", alpha=0.9)
        ax2 = ax1.twinx()
        pcts_q = [quarters[q]["pct"] for q in qs]
        ax2.plot(x, pcts_q, "o-", color="#e74c3c", linewidth=2, markersize=5,
                 label="Signal %")

        # EU AI Act milestones
        milestone_map = {
            "euaia_entry_into_force": ("2024-Q3", "#9b59b6", "EUAIA in force\nAug 2024"),
            "euaia_general_provisions": ("2025-Q1", "#e67e22", "General provisions\nFeb 2025"),
        }
        for _, (qkey, color, label) in milestone_map.items():
            if qkey in qs:
                xi = qs.index(qkey)
                ax1.axvline(xi, color=color, linestyle="--", alpha=0.8, linewidth=1.5)
                ax1.text(xi + 0.1, ax1.get_ylim()[1] * 0.9, label,
                         color=color, fontsize=8, va="top")

        ax1.set_xticks(list(x))
        ax1.set_xticklabels(qs, rotation=45, ha="right", fontsize=8)
        ax1.set_ylabel("Repository count", fontsize=11)
        ax2.set_ylabel("Signal prevalence (%)", fontsize=11, color="#e74c3c")
        ax2.tick_params(axis="y", labelcolor="#e74c3c")
        ax1.set_title("Signal Adoption Over Time by Repo Creation Quarter", fontsize=13)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
        plt.tight_layout()
        plt.savefig(f"{FIGURES_DIR}/fig3_temporal.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("  [figures] fig3_temporal.png", flush=True)

    # ── Fig 4: Signal mechanism breakdown (horizontal bar) ────────────────────
    mech = results["rq2_direction"].get("signal_mechanism_counts", {})
    if mech:
        mechs = list(mech.keys())
        vals = [mech[m] for m in mechs]
        fig, ax = plt.subplots(figsize=(8, max(3, len(mechs) * 0.7 + 1)))
        bars = ax.barh(mechs, vals, color="#16a085", alpha=0.85)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    str(v), va="center", fontsize=10)
        ax.set_xlabel("Number of repos", fontsize=12)
        ax.set_title("Signal Mechanisms Observed (repos with any signal)", fontsize=13)
        ax.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{FIGURES_DIR}/fig4_signal_types.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("  [figures] fig4_signal_types.png", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def run(classified_path: str = CLASSIFIED, out_path: str = ANALYSIS_OUT) -> dict[str, Any]:
    rows = load(classified_path)
    print(f"[analysis] loaded {len(rows)} classified repos", flush=True)

    results = {
        "metadata": {
            "n": len(rows),
            "generated_at": datetime.now(UTC).isoformat(),
            "source": Path(classified_path).name,
        },
        "rq1_prevalence": rq1_prevalence(rows),
        "rq2_direction": rq2_direction(rows),
        "rq3_predictors": rq3_predictors(rows),
        "rq4_temporal": rq4_temporal(rows),
    }

    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[analysis] results saved to {out_path}", flush=True)

    print("[analysis] generating figures...", flush=True)
    _try_figures(rows, results)

    return results


if __name__ == "__main__":
    results = run()

    # Print summary table
    r1 = results["rq1_prevalence"]
    r2 = results["rq2_direction"]
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           ANALYSIS SUMMARY                                   ║
╠══════════════════════════════════════════════════════════════╣
║  Total repos analysed : {r1['n_total']:5d}                            ║
║  Any signal           : {r1['n_any_signal']:5d}  ({r1['pct_any_signal']:5.1f}%)                   ║
║  95% Wilson CI        : [{r1['wilson_ci_any_signal_95'][0]:.1f}%, {r1['wilson_ci_any_signal_95'][1]:.1f}%]                   ║
╠══════════════════════════════════════════════════════════════╣
║  OPT_IN               : {r1['n_opt_in']:5d}  ({r1['pct_opt_in']:5.1f}%)                   ║
║  OPT_OUT              : {r1['n_opt_out']:5d}  ({r1['pct_opt_out']:5.1f}%)                   ║
║  AMBIGUOUS            : {r1['n_ambiguous']:5d}  ({r1['pct_ambiguous']:5.1f}%)                   ║
║  NONE                 : {r1['n_none']:5d}  ({r1['pct_none']:5.1f}%)                   ║
╚══════════════════════════════════════════════════════════════╝
""")
