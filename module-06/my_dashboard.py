"""
my_dashboard.py - Module 6: Personal Stats Dashboard
Caduceus Healthcare Equity Platform - Rhenman & Partners
Analyst research progress and coverage dashboard.
"""
import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Analyst Dashboard", page_icon="⚕️",
                   layout="wide", initial_sidebar_state="expanded")

COVERAGE = {
    "PFE":  {"name": "Pfizer",           "analyst": "Kathy",   "conviction": 3, "calls": 8,  "beats": 6},
    "MRK":  {"name": "Merck",            "analyst": "Amennai", "conviction": 4, "calls": 10, "beats": 8},
    "JNJ":  {"name": "J&J",             "analyst": "Amennai", "conviction": 3, "calls": 9,  "beats": 5},
    "ABBV": {"name": "AbbVie",           "analyst": "Camilla", "conviction": 5, "calls": 12, "beats": 12},
    "BMY":  {"name": "Bristol-Myers",    "analyst": "Camilla", "conviction": 4, "calls": 7,  "beats": 7},
    "LLY":  {"name": "Eli Lilly",        "analyst": "Kathy",   "conviction": 4, "calls": 11, "beats": 9},
    "AMGN": {"name": "Amgen",            "analyst": "Hugo",    "conviction": 3, "calls": 6,  "beats": 5},
    "GILD": {"name": "Gilead",           "analyst": "Hugo",    "conviction": 3, "calls": 8,  "beats": 5},
}

with st.sidebar:
    st.header("Filters")
    analyst = st.selectbox("Analyst", ["All", "Kathy", "Amennai", "Camilla", "Hugo"])
    min_conv = st.slider("Min conviction", 1, 5, 1)
    show_beatmiss = st.checkbox("Show beat/miss rate", value=True)

df = pd.DataFrame([
    {"Ticker": k, **v} for k, v in COVERAGE.items()
])
if analyst != "All":
    df = df[df["analyst"] == analyst]
df = df[df["conviction"] >= min_conv]
df["beat_rate"] = (df["beats"] / df["calls"] * 100).round(1)

st.title("⚕️ Caduceus Coverage Dashboard")
st.caption("Analyst research tracker — Rhenman & Partners")

total   = len(df)
avg_conv = round(df["conviction"].mean(), 1) if not df.empty else 0
avg_beat = round(df["beat_rate"].mean(), 1)  if not df.empty else 0
high_conv = len(df[df["conviction"] >= 4])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Names covered", total)
c2.metric("Avg conviction", avg_conv, delta=f"{avg_conv - 3:+.1f} vs neutral")
c3.metric("High conviction", high_conv)
c4.metric("Avg beat rate", f"{avg_beat}%")

tab1, tab2 = st.tabs(["Overview", "Detail"])

with tab1:
    if not df.empty:
        fig = px.bar(df, x="Ticker", y="conviction",
                     color="conviction",
                     color_continuous_scale=["rgb(179,205,224)", "#0F4C81"],
                     title="Conviction by Name")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                          paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.dataframe(df[["Ticker","name","analyst","conviction","calls","beats","beat_rate"]],
                 use_container_width=True, hide_index=True)
    if show_beatmiss:
        with st.expander("Beat/miss methodology"):
            st.write("Beat = EPS surprise > +2%. Miss = EPS surprise < -2%. "
                     "In-line = within ±2%. Source: yfinance historical earnings_dates. "
                     "Data covers Q1 2020 through Q1 2026 (24 quarters).")
