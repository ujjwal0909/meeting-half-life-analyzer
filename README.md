# Meeting Half-Life Analyzer (MHL)

> Quantifies the vitality of every recurring meeting in your organization and forecasts when each one will be effectively dead — so managers have the data to kill zombie meetings.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Status: Prototype](https://img.shields.io/badge/status-prototype-orange.svg)](#)

---

## The problem

Every organization is haunted by **zombie recurring meetings** — they started with a purpose, but six months later three people are checking email, two are on mute, and the agenda is *"round-table updates."* These meetings cost the global economy billions of hours per year. They survive because:

- Productivity tools count meeting *hours*, not meeting *value*.
- Transcript apps (Otter, Fireflies) summarize content but don't measure trajectory.
- Engagement surveys are gameable and infrequent.
- Nobody has objective data to defend killing a meeting that a senior leader insists is useful.

No tool measures the *decay curve* of a recurring meeting series.

## The hypothesis

The vitality of a recurring meeting decays predictably along four measurable dimensions:

1. **Speaker distribution entropy** — is it a real conversation, or one person monologuing?
2. **Decision density** — how many decisions or commitments per minute?
3. **Topic focus** — does the conversation match the stated agenda?
4. **Attention** — late-joins, camera-off rate, multitasking signals.

If we measure those, we can compute a meeting's **half-life** — the number of weeks until its vitality drops below a usable threshold — and recommend KILL, RESTRUCTURE, or KEEP.

---

## What this repo contains

A working prototype that:

1. **Generates 156 synthetic meeting occurrences** across 6 recurring series over 26 weeks. Two series are engineered to decay (zombie meetings) so the recommender can be validated.
2. **Scores every occurrence** on the four vitality dimensions, producing a 0–100 composite.
3. **Fits an exponential decay** to each series' vitality timeline to estimate its half-life.
4. **Recommends KILL / RESTRUCTURE / KEEP** based on current vitality and projected half-life.
5. **Renders an interactive Streamlit dashboard** with the quarterly health report and per-series drill-downs.

On the demo dataset, the recommender correctly flags the 2 engineered zombie meetings (KILL + RESTRUCTURE) and KEEP-s the 4 healthy ones — 100% precision and recall.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate 6 recurring meeting series × 26 weeks of occurrences
python generate_synthetic_meetings.py

# 3. Score every occurrence on the four vitality components
python score_vitality.py

# 4. Fit decay curves, compute half-lives, generate KILL/RESTRUCTURE/KEEP recs
python half_life.py

# 5. Launch the dashboard
streamlit run dashboard.py
```

Dashboard opens at `http://localhost:8501`. Stop with `Ctrl+C`.

---

## Sample output

The half-life run prints a quarterly health report:

```
Series  Title                         First    Now        k   HL(wk)   R²  Recommendation
------------------------------------------------------------------------------------------
S01     Eng Weekly Sync                81.8   81.2  -0.0003   inf   0.00  KEEP — healthy
S02     Roadmap Review                 77.9   81.3  -0.0025   inf   0.13  KEEP — healthy
S03     Status Round-Table             79.8   53.5   0.0368   18.8  0.63  RESTRUCTURE
S04     Design Critique                68.7   80.1  -0.0044   inf   0.17  KEEP — healthy
S05     Old All-Hands Prep             80.3   31.5   0.0413   16.8  0.74  KILL — collapsed
S06     Incident Postmortem            79.6   77.9   0.0001   inf   0.01  KEEP — healthy
```

Read this as: kill S05, shrink or move S03 to async, leave the rest alone.

---

## Project structure

```
project3_meeting_half_life/
├── SPEC.md                          # Implementation-ready specification
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── generate_synthetic_meetings.py   # 6 series × 26 weeks; 2 series engineered to decay
├── score_vitality.py                # Four-component vitality scorer
├── half_life.py                     # Exponential decay fit + recommender
├── dashboard.py                     # Streamlit dashboard
└── data/
    ├── meetings.json                # Full occurrence data + transcripts
    ├── meetings_index.csv
    ├── vitality_scores.csv
    ├── vitality_scores.json
    └── half_life_report.json
```

---

## How it works

### 1. Vitality components (each 0–100)

**Speaker distribution** — Shannon entropy of speaking time, normalized to the maximum possible entropy for the attendee count:

```
H = -Σ p_i × log(p_i)
distribution_score = 100 × H / log(n_speakers)
```

Low entropy = one person dominates = unhealthy.

**Decision density** — Decisions per minute, detected via regex patterns like *"let's ship," "owner:", "by Friday," "action item."* Three decisions in 30 minutes ≈ 100 score.

**Topic focus** — Share of transcript word mass that hits agenda keywords. High focus = the meeting is doing what it claims.

**Attention** — Composite penalty:

```
attention_score = 100 − 50×late_pct − 30×camera_off_pct − 20×multitask_pct
```

### 2. Composite vitality

```
vitality = 0.30 × distribution
         + 0.30 × decision_density
         + 0.20 × topic_focus
         + 0.20 × attention
```

### 3. Half-life estimation

Fit an exponential decay to the vitality time series via log-linear regression:

```
V(t) = V₀ × exp(-k × t)
half_life_weeks = ln(2) / k
```

Reported alongside R² so you know whether the trend is real or noise.

### 4. Recommendation logic

```
if vitality < 35           → KILL — already collapsed
if HL < 12 and V < 55      → KILL — will be dead within a quarter
if HL < 24 and V < 65      → RESTRUCTURE — shrink or async
else                       → KEEP — healthy
```

---

## Tech stack

- **Python 3.10+**
- **numpy, pandas** — data wrangling
- **Streamlit + Altair** — dashboard
- Standard library only for entropy + regex (no ML deps required)

---

## What's in `SPEC.md`

A full implementation-ready specification including:

- Detailed problem framing
- Success metrics (precision on kill-recommendations, time-saved per team)
- Data sources (Google Calendar, Microsoft Graph, Zoom transcripts, Otter, Fireflies)
- Detailed scoring algorithms and weights
- Bayesian half-life update for short histories
- Architecture diagram
- 10-sprint roadmap to MVP
- Privacy considerations (per-org isolation, no cross-org sharing)

Open [`SPEC.md`](./SPEC.md) for the full document.

---

## Production extensions

The prototype operates on synthetic transcripts. The real product needs:

- **OAuth integration** — Google Calendar + Microsoft Graph to enumerate recurring series.
- **Transcript ingestion** — native Zoom, Teams, and Meet transcripts; Otter / Fireflies API for higher quality.
- **Decision classifier** — fine-tuned text classifier instead of regex (regex is the prototype baseline).
- **Embedding-based topic focus** — sentence transformers for cosine similarity to agenda, not just bag-of-words.
- **Manager dashboard + quarterly PDF report**.

---

## Why this is hard to game

The score is for managers and aggregated across the team — individual speaker stats are never surfaced outside the aggregate. A meeting can't "fake" decision density without actually making decisions. A team can't "fake" topic focus without actually staying on agenda.

---

## Limitations

- Synthetic data doesn't capture the full nuance of real conversations (sarcasm, code-switching, side discussions).
- The decision classifier is regex-based in the prototype — real meetings need a small fine-tuned model.
- The four-component weighting (30/30/20/20) is a starting prior; production tuning would A/B test weights per org.

---

## Roadmap

- [ ] Google Calendar OAuth integration
- [ ] Native Zoom transcript ingester
- [ ] Otter / Fireflies adapters
- [ ] Fine-tuned decision classifier
- [ ] Sentence-transformer topic-focus model
- [ ] Quarterly PDF health report generator
- [ ] Per-org baseline calibration

---

## License

MIT
