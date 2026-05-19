"""
Fit exponential-decay curves to each series' vitality timeline and
estimate the half-life. Produces a kill/keep/restructure recommendation.
"""

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

BASE = Path(__file__).parent
DATA = BASE / "data"


def fit_exponential(occurrence_idx: list, vitality: list):
    """
    Fit V(t) = V0 * exp(-k * t)  via log-linear regression.
    Returns (V0, k, half_life_in_occurrences, slope, r2).
    """
    x = np.array(occurrence_idx, dtype=float)
    y = np.array(vitality, dtype=float)
    # Use only positive vitality
    mask = y > 1
    x, y = x[mask], y[mask]
    if len(x) < 4:
        return None
    log_y = np.log(y)
    # Linear regression
    n = len(x)
    x_mean = x.mean()
    y_mean = log_y.mean()
    slope = ((x - x_mean) * (log_y - y_mean)).sum() / ((x - x_mean) ** 2).sum()
    intercept = y_mean - slope * x_mean
    V0 = math.exp(intercept)
    k = -slope
    pred = intercept + slope * x
    ss_res = ((log_y - pred) ** 2).sum()
    ss_tot = ((log_y - y_mean) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    if k > 1e-6:
        half_life = math.log(2) / k
    else:
        half_life = float("inf")
    return {"V0": V0, "k": k, "half_life_occurrences": half_life, "r2": r2}


def recommend(current_vitality: float, half_life_occurrences: float) -> str:
    if current_vitality < 35:
        return "KILL — vitality already collapsed."
    if half_life_occurrences < 12 and current_vitality < 55:
        return "KILL — will be dead within a quarter."
    if half_life_occurrences < 24 and current_vitality < 65:
        return "RESTRUCTURE — shrink attendees or convert to async."
    return "KEEP — meeting is healthy."


def main():
    scores = json.loads((DATA / "vitality_scores.json").read_text())
    by_series = defaultdict(list)
    for s in scores:
        by_series[s["series_id"]].append(s)
    for sid in by_series:
        by_series[sid].sort(key=lambda r: r["occurrence"])

    report = []
    for sid, series in by_series.items():
        title = series[0]["title"]
        fit = fit_exponential(
            [s["occurrence"] for s in series],
            [s["vitality"] for s in series],
        )
        if fit is None:
            continue
        current = series[-1]["vitality"]
        hl_weeks = fit["half_life_occurrences"]
        hl_days = hl_weeks * 7 if math.isfinite(hl_weeks) else None
        rec = recommend(current, hl_weeks)
        report.append({
            "series_id": sid,
            "title": title,
            "current_vitality": current,
            "first_vitality": series[0]["vitality"],
            "decay_rate_k": round(fit["k"], 4),
            "half_life_weeks": round(hl_weeks, 1) if math.isfinite(hl_weeks) else None,
            "half_life_days": round(hl_days, 1) if hl_days else None,
            "r2_of_fit": round(fit["r2"], 3),
            "recommendation": rec,
        })

    (DATA / "half_life_report.json").write_text(json.dumps(report, indent=2))
    print(f"{'Series':<6}  {'Title':<28}  {'First':>5}  {'Now':>5}  {'k':>7}  {'HL (wk)':>8}  {'R²':>5}  Recommendation")
    print("-" * 110)
    for r in report:
        hl = f"{r['half_life_weeks']:.1f}" if r["half_life_weeks"] is not None else "inf"
        print(
            f"{r['series_id']:<6}  {r['title']:<28}  {r['first_vitality']:>5.1f}  "
            f"{r['current_vitality']:>5.1f}  {r['decay_rate_k']:>7.4f}  {hl:>8}  "
            f"{r['r2_of_fit']:>5.2f}  {r['recommendation']}"
        )


if __name__ == "__main__":
    main()
