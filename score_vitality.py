"""
Score the vitality of every meeting occurrence.
"""

import json
import math
import re
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"

DECISION_PATTERNS = [
    r"let'?s ship",
    r"\bwe decided\b",
    r"action item",
    r"I'?ll take",
    r"by friday",
    r"by next week",
    r"\bwe agreed\b",
    r"owner:",
    r"\bAI:",
    r"next step",
]
DECISION_RE = re.compile("|".join(DECISION_PATTERNS), re.IGNORECASE)


def speaker_distribution_score(speaker_seconds: dict) -> float:
    total = sum(speaker_seconds.values())
    if total == 0:
        return 0.0
    probs = [s / total for s in speaker_seconds.values() if s > 0]
    n = len(probs)
    if n <= 1:
        return 0.0
    ent = -sum(p * math.log(p) for p in probs)
    max_ent = math.log(n)
    return 100 * (ent / max_ent)


def decision_density_score(transcript: list, duration_min: int) -> float:
    decisions = sum(1 for line in transcript if DECISION_RE.search(line["text"]))
    density = decisions / max(duration_min, 1)
    # 0.1 decisions/min ≈ 3 in 30 min → ~100 score
    return min(100.0, density * 1000)


def topic_focus_score(transcript: list, agenda_keywords: list) -> float:
    """
    Bag-of-words cosine between transcript term frequencies and the agenda.
    Numpy-free implementation.
    """
    if not transcript or not agenda_keywords:
        return 0.0
    text = " ".join(line["text"].lower() for line in transcript)
    tokens = re.findall(r"[a-z]+", text)
    if not tokens:
        return 0.0
    from collections import Counter
    tf = Counter(tokens)
    agenda_set = set(k.lower() for k in agenda_keywords)
    # Cosine-like: share of mass on agenda terms
    on_topic = sum(tf[k] for k in agenda_set if k in tf)
    total = sum(tf.values())
    return min(100.0, 100 * on_topic / total)


def attention_score(late_pct, camera_off_pct, multitask_pct) -> float:
    return max(0.0, 100 - (50 * late_pct + 30 * camera_off_pct + 20 * multitask_pct))


def vitality(meeting: dict) -> dict:
    d = speaker_distribution_score(meeting["speaker_seconds"])
    de = decision_density_score(meeting["transcript"], meeting["duration_minutes"])
    t = topic_focus_score(meeting["transcript"], meeting["agenda_keywords"])
    a = attention_score(meeting["late_pct"], meeting["camera_off_pct"], meeting["multitask_pct"])
    composite = 0.30 * d + 0.30 * de + 0.20 * t + 0.20 * a
    return {
        "series_id": meeting["series_id"],
        "title": meeting["title"],
        "occurrence": meeting["occurrence"],
        "date": meeting["date"],
        "distribution": round(d, 1),
        "decision_density": round(de, 1),
        "topic_focus": round(t, 1),
        "attention": round(a, 1),
        "vitality": round(composite, 1),
    }


def main():
    meetings = json.loads((DATA / "meetings.json").read_text())
    scores = [vitality(m) for m in meetings]
    (DATA / "vitality_scores.json").write_text(json.dumps(scores, indent=2))

    import csv
    with open(DATA / "vitality_scores.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(scores[0].keys()))
        writer.writeheader()
        writer.writerows(scores)
    print(f"Scored {len(scores)} occurrences.")

    # Summarize by series
    from collections import defaultdict
    by_series = defaultdict(list)
    for s in scores:
        by_series[s["series_id"]].append(s["vitality"])
    print("\nMean vitality by series:")
    for sid, vs in by_series.items():
        title = next(s["title"] for s in scores if s["series_id"] == sid)
        print(f"  {sid}  {title:<28s}  mean={sum(vs)/len(vs):5.1f}  first={vs[0]:5.1f}  last={vs[-1]:5.1f}")


if __name__ == "__main__":
    main()
