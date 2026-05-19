"""
Streamlit dashboard for the Meeting Half-Life Analyzer.

Run with: streamlit run dashboard.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt

BASE = Path(__file__).parent
DATA = BASE / "data"


@st.cache_data
def load():
    scores = pd.read_csv(DATA / "vitality_scores.csv")
    with open(DATA / "half_life_report.json") as f:
        report = json.load(f)
    return scores, report


def main():
    st.set_page_config(page_title="Meeting Half-Life Analyzer", layout="wide")
    st.title("Meeting Half-Life Analyzer")
    st.caption("Quantify the vitality of every recurring meeting and forecast its decay.")

    scores, report = load()

    st.subheader("Quarterly Health Report")
    df = pd.DataFrame(report).sort_values("current_vitality")

    def emoji(rec):
        if rec.startswith("KILL"):
            return "🛑 " + rec
        if rec.startswith("RESTRUCTURE"):
            return "⚠️ " + rec
        return "✅ " + rec

    df["recommendation"] = df["recommendation"].map(emoji)
    st.dataframe(
        df[["series_id", "title", "first_vitality", "current_vitality",
            "half_life_weeks", "r2_of_fit", "recommendation"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Vitality trajectory by series")
    chart = (
        alt.Chart(scores)
        .mark_line(point=True)
        .encode(
            x=alt.X("occurrence:Q", title="Week #"),
            y=alt.Y("vitality:Q", scale=alt.Scale(domain=[0, 100])),
            color="title:N",
        )
        .properties(height=380)
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Component drill-down")
    series = st.selectbox("Pick a series", scores["title"].unique())
    sub = scores[scores["title"] == series]
    long = sub.melt(
        id_vars=["occurrence", "title"],
        value_vars=["distribution", "decision_density", "topic_focus", "attention"],
        var_name="component", value_name="score",
    )
    sub_chart = (
        alt.Chart(long)
        .mark_line(point=True)
        .encode(
            x=alt.X("occurrence:Q"),
            y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100])),
            color="component:N",
        )
        .properties(height=320)
    )
    st.altair_chart(sub_chart, use_container_width=True)


if __name__ == "__main__":
    main()
