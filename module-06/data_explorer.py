"""
data_explorer.py - Module 6: Data Explorer
Caduceus Healthcare Equity Platform - Rhenman & Partners
Fetches and explores SEC EDGAR financial facts for Phase 1 pharma.
"""
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Caduceus Data Explorer", page_icon="⚕️", layout="wide")

PHASE1 = {
    "PFE": "0000078003", "MRK": "0000310158", "JNJ": "0000200406",
    "ABBV": "0001551152", "BMY": "0000014272", "LLY": "0000059478",
    "AMGN": "0000318154", "GILD": "0000882095",
}
HEADERS = {"User-Agent": "Caduceus Research caduceus@research.com"}

@st.cache_data(ttl=3600)
def fetch_company_info(cik):
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.ok:
        return r.json()
    return None

st.title("⚕️ Caduceus Data Explorer")
st.caption("SEC EDGAR company data for Phase 1 pharma universe")

with st.sidebar:
    st.header("Filters")
    ticker_filter = st.text_input("Filter by ticker", placeholder="e.g. LLY")
    show_filings  = st.checkbox("Show recent filing counts", value=True)

rows = []
with st.spinner("Fetching SEC EDGAR data..."):
    for ticker, cik in PHASE1.items():
        if ticker_filter and ticker_filter.upper() not in ticker:
            continue
        data = fetch_company_info(cik)
        if data:
            filings = data.get("filings", {}).get("recent", {})
            forms   = filings.get("form", [])
            rows.append({
                "Ticker":   ticker,
                "Name":     data.get("name", "N/A"),
                "SIC":      data.get("sicDescription", "N/A"),
                "State":    data.get("stateOfIncorporation", "N/A"),
                "10-K":     forms.count("10-K"),
                "10-Q":     forms.count("10-Q"),
                "8-K":      forms.count("8-K"),
            })

if not rows:
    st.warning("No data returned.")
    st.stop()

df = pd.DataFrame(rows)

total   = len(df)
states  = df["State"].nunique()
avg_10k = round(df["10-K"].mean(), 1)

c1, c2, c3 = st.columns(3)
c1.metric("Companies", total)
c2.metric("States of Incorporation", states)
c3.metric("Avg 10-K filings", avg_10k)

st.divider()
st.subheader("Company Registry")
st.dataframe(df, use_container_width=True, hide_index=True)

if show_filings:
    st.divider()
    st.subheader("Filing Counts by Company")
    import plotly.express as px
    fig = px.bar(df, x="Ticker", y=["10-K","10-Q","8-K"],
                 barmode="group", title="SEC Filings by Type",
                 color_discrete_sequence=["#0F4C81","rgb(104,137,192)","rgb(179,205,224)"])
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
