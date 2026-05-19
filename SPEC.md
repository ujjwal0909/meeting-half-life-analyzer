# Project 3: Meeting Half-Life Analyzer (MHL)
### Implementation-Ready Specification

---

## 1. Problem Statement

Every organization has *zombie recurring meetings* — they started with purpose, but six months later three people are checking email and the agenda is "round-table updates." They are never killed because nobody can quantify their decline.

**Hypothesis:** The vitality of a recurring meeting decays predictably along measurable dimensions (speaker entropy, decision density, topic drift, attention). We can compute a meeting's *half-life* — the time until its vitality drops below a useful threshold — and give managers data to defend killing it.

## 2. Why This Hasn't Been Solved

- Calendar tools count hours, not value.
- Transcript tools (Otter, Fireflies) summarize content but don't measure trajectory.
- Engagement surveys are gameable and infrequent.
- No tool quantifies the *decay curve* of a recurring meeting series.

## 3. Success Metrics

| Metric | Target |
| --- | --- |
| Precision on "this meeting should be killed" recommendation | ≥ 75% |
| Median time saved per team per quarter | ≥ 4 hours |
| Manager-reported usefulness | ≥ 4/5 |
| Half-life forecast error (predicted vs. observed) | ≤ 30 days |

## 4. Data Sources

| Source | Signal |
| --- | --- |
| Google Calendar / Microsoft Graph | Meeting series ID, recurrence pattern, attendees, accept/decline |
| Zoom/Meet/Teams native transcripts | Per-speaker time, decision keywords |
| Otter.ai / Fireflies API | Higher-quality transcripts when available |
| Calendar events meta | Late-joins (joinedAt vs. start), camera-on count (Teams API) |

## 5. Vitality Score (0-100)

Composite of four sub-scores, each 0-100:

### 5.1 Speaker Distribution Entropy
H(speakers) normalized to max entropy. Low entropy = one person monologuing.

```
ent = -Σ p_i log(p_i)         # p_i = fraction of speaking time
ent_norm = ent / log(n_speakers)
distribution_score = 100 * ent_norm
```

### 5.2 Decision Density
Count of decisions/commitments per minute. Detected via regex + classifier on transcript:

```
decision_keywords = [
  "we'll go with", "let's ship", "decided", "owner:", "AI:", "action item",
  "by friday", "by next week", "I'll take", "we agreed",
]
density = decisions / duration_minutes
density_score = min(100, density * 33)  # 3 decisions / 30 min ≈ healthy
```

### 5.3 Topic Drift
Cosine similarity between the meeting's transcript embedding and the
stated agenda (or the first 5 minutes if no agenda). Low similarity =
drift. We invert: high score = on-topic.

### 5.4 Attention Proxies
- Late-join rate (% attendees joining > 2 min late)
- Camera-on rate
- Multitasking proxy: long silences when not the speaker (Otter exposes per-speaker active periods)

```
attention_score = 100 - 0.5*late_pct - 0.3*camera_off_pct - 0.2*multitask_pct
```

### 5.5 Composite

```
vitality = 0.30 * distribution
         + 0.30 * decision_density
         + 0.20 * topic_focus
         + 0.20 * attention
```

## 6. Half-Life Estimation

For a recurring meeting series, fit an exponential decay to the vitality time series:

```
V(t) = V_0 * exp(-k * t)
half_life_days = ln(2) / k
```

If half-life < 90 days and current vitality < 50 → recommend kill or
restructure.

Use Bayesian update for short histories — wide prior, narrow as N grows.

## 7. Architecture

```
Calendar OAuth ──► Series Index (Postgres)
Transcripts ──────► Transcript Store (S3)
                          │
                          ▼
                  Feature Extractor (per occurrence)
                          │
                          ▼
                  Vitality Time Series
                          │
                          ▼
                  Decay Model + Recommender
                          │
                          ▼
                  Quarterly Health Report
```

## 8. Sprint Roadmap (10 weeks)

| Sprint | Deliverable |
| --- | --- |
| 1 | Synthetic transcripts + entropy/density scoring |
| 2 | Topic-drift via sentence embeddings |
| 3 | Half-life curve fitting + recommender |
| 4 | Calendar OAuth + series index |
| 5 | Native Zoom transcript ingester |
| 6 | Otter/Fireflies adapters |
| 7 | Manager dashboard (vitality + recommendations) |
| 8 | Quarterly health report PDF generator |
| 9 | Privacy review + per-attendee opt-out |
| 10 | Beta with 5 engineering orgs |

## 9. Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| Privacy of transcripts | All processing per-org; never cross-org. Aggregate-only benchmarks. |
| Bias against high-context async cultures | Calibrate per-org baselines. Some orgs do useful slow meetings. |
| Decision classifier false negatives | Combine regex + small fine-tuned classifier; ask user to confirm low-vitality findings before recommending kill. |
| Managers gaming the system | The score is for managers, not employees. Don't surface individual speaker stats outside aggregates. |

## 10. Out of Scope (Phase 1)

- One-off meetings (no recurrence = no decay curve)
- All-hands / town halls (different dynamics)
- Customer-facing meetings (different objectives)
