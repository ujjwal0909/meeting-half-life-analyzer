"""
Generate synthetic recurring meeting data: 6 series, ~26 weekly occurrences each.
Two of the series are designed to decay (zombie meetings).
Outputs per-occurrence transcripts (small) and per-occurrence metadata.
"""

import json
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(7)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

SERIES = [
    # id, title, attendees, decay (True/False), agenda_keywords
    ("S01", "Eng Weekly Sync",     ["alex", "bao", "cara", "dev", "eli", "fae"], False,
     ["sprint", "deploy", "incident", "roadmap", "blocker"]),
    ("S02", "Roadmap Review",       ["alex", "cara", "gail", "han"],             False,
     ["roadmap", "quarter", "milestone", "scope", "trade-off"]),
    ("S03", "Status Round-Table",   ["alex", "bao", "cara", "dev", "eli", "fae", "gail", "han"], True,
     ["update", "status", "yesterday", "today", "blocker"]),
    ("S04", "Design Critique",      ["bao", "dev", "iris"],                      False,
     ["mockup", "flow", "user", "spec", "iteration"]),
    ("S05", "Old All-Hands Prep",   ["alex", "gail", "han", "jay"],              True,
     ["agenda", "slides", "talking", "deck"]),
    ("S06", "Incident Postmortem",  ["bao", "cara", "dev", "eli"],               False,
     ["incident", "root cause", "action item", "owner", "timeline"]),
]

DECISION_PHRASES = [
    "let's ship this",
    "we decided to",
    "action item:",
    "I'll take that",
    "by Friday we will",
    "we agreed on",
    "owner: alex",
    "AI: ship",
    "next step is",
]

FILLER_PHRASES = [
    "yeah",
    "uh",
    "I think maybe",
    "right",
    "so basically",
    "no comments from me",
    "I have nothing to add",
    "same as last week",
    "still working on it",
    "no updates",
]


def make_occurrence(series, occurrence_index, total_occurrences):
    sid, title, attendees, decays, agenda = series

    # Decay parameter — zombie meetings get worse over time
    progress = occurrence_index / total_occurrences
    if decays:
        vitality_target = 85 * (1 - progress) ** 1.3 + 8
    else:
        vitality_target = 70 + random.gauss(0, 6)
    vitality_target = max(5, min(95, vitality_target))

    # Speaker time: healthy meeting -> roughly equal across attendees.
    # Unhealthy: one person dominates.
    n = len(attendees)
    if decays and progress > 0.3:
        # one person monopolizes
        weights = [10 if i == 0 else random.uniform(0.5, 2) for i in range(n)]
    else:
        weights = [random.uniform(0.8, 1.2) for _ in range(n)]
    total_w = sum(weights)
    speaker_seconds = {a: int((w / total_w) * 1800) for a, w in zip(attendees, weights)}  # 30 min

    # Decision lines depend on health
    n_decisions = int(random.gauss((vitality_target / 100) * 6, 1))
    n_decisions = max(0, n_decisions)
    n_filler = int(20 - 12 * (vitality_target / 100))

    transcript = []
    for _ in range(n_decisions):
        speaker = random.choice(attendees)
        line = random.choice(DECISION_PHRASES) + " " + random.choice(agenda)
        transcript.append({"speaker": speaker, "text": line})
    for _ in range(n_filler):
        speaker = random.choice(attendees)
        line = random.choice(FILLER_PHRASES)
        # Healthier meetings still mention agenda topics
        if random.random() < (vitality_target / 100):
            line += " about " + random.choice(agenda)
        transcript.append({"speaker": speaker, "text": line})
    random.shuffle(transcript)

    # Attention proxies
    if decays and progress > 0.5:
        late_pct = random.uniform(0.3, 0.6)
        camera_off_pct = random.uniform(0.5, 0.9)
        multitask_pct = random.uniform(0.4, 0.7)
    else:
        late_pct = random.uniform(0.0, 0.2)
        camera_off_pct = random.uniform(0.1, 0.4)
        multitask_pct = random.uniform(0.0, 0.2)

    return {
        "series_id": sid,
        "title": title,
        "occurrence": occurrence_index,
        "attendees": attendees,
        "speaker_seconds": speaker_seconds,
        "transcript": transcript,
        "duration_minutes": 30,
        "agenda_keywords": agenda,
        "late_pct": round(late_pct, 3),
        "camera_off_pct": round(camera_off_pct, 3),
        "multitask_pct": round(multitask_pct, 3),
    }


def main():
    start = date(2025, 11, 3)  # Monday
    all_meetings = []
    for series in SERIES:
        for week in range(26):
            occ_date = start + timedelta(weeks=week)
            occ = make_occurrence(series, week, 26)
            occ["date"] = occ_date.isoformat()
            all_meetings.append(occ)

    out_file = OUT / "meetings.json"
    out_file.write_text(json.dumps(all_meetings, indent=2))

    # Also write a slim metadata CSV for indexing
    import csv
    with open(OUT / "meetings_index.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["series_id", "title", "occurrence", "date", "duration_minutes"])
        writer.writeheader()
        for m in all_meetings:
            writer.writerow({k: m[k] for k in ["series_id", "title", "occurrence", "date", "duration_minutes"]})
    print(f"Wrote {len(all_meetings)} meeting occurrences across {len(SERIES)} series.")
    decaying = [s[0] for s in SERIES if s[3] is True]
    print(f"Series marked as DECAYING (zombies): {decaying}")


if __name__ == "__main__":
    main()
