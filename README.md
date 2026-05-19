# Meeting Half-Life Analyzer — Prototype

## Quick start

```bash
pip install -r requirements.txt
python generate_synthetic_meetings.py
python score_vitality.py
python half_life.py
streamlit run dashboard.py
```

## Files
- `SPEC.md` — implementation spec
- `generate_synthetic_meetings.py` — 6 recurring series × 26 weekly occurrences; 2 series engineered to decay
- `score_vitality.py` — four-component vitality scorer
- `half_life.py` — exponential decay fit + kill/keep/restructure recommendation
- `dashboard.py` — Streamlit dashboard
