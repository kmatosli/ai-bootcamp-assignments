"""
explore.py - Module 6: Topic Exploration App
Caduceus Healthcare Equity Platform - Rhenman & Partners
Interactive pharma valuation explorer using 5+ widget types.
"""
import streamlit as st

st.set_page_config(page_title="Pharma Explorer", page_icon="⚕️", layout="wide")

st.title("⚕️ Pharma Valuation Explorer")
st.header("Build your own DCF assumptions")
st.caption("Rhenman & Partners - Caduceus interactive tool")

ticker    = st.selectbox("Select company", ["LLY", "PFE", "MRK", "JNJ", "ABBV", "BMY", "AMGN", "GILD"])
rev_growth = st.slider("Revenue CAGR (%)", min_value=-5, max_value=25, value=8)
margin     = st.slider("EBIT margin (%)", min_value=5, max_value=50, value=28)
wacc       = st.number_input("WACC (%)", min_value=5.0, max_value=15.0, value=8.0, step=0.5)
years      = st.radio("Projection horizon", [3, 5, 10], horizontal=True)
catalysts  = st.multiselect("Key catalysts", ["Earnings beat", "Pipeline readout",
                             "FDA approval", "IRA resolution", "M&A", "Guidance raise"])
thesis     = st.text_area("Thesis notes", placeholder="Why do you like or dislike this name?")
include_tv = st.checkbox("Include terminal value", value=True)

BASE_REV = {"LLY": 45, "PFE": 58, "MRK": 60, "JNJ": 88,
            "ABBV": 56, "BMY": 47, "AMGN": 33, "GILD": 28}

rev = BASE_REV.get(ticker, 40)
rev_proj = rev * ((1 + rev_growth / 100) ** years)
ebit_proj = rev_proj * margin / 100
nopat = ebit_proj * 0.79
tv = (nopat * (1 + 0.025) / (wacc / 100 - 0.025)) if include_tv else 0
dcf_value = (nopat / (1 + wacc / 100) ** (years / 2)) + (tv / (1 + wacc / 100) ** years)

st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Projected revenue", f"${rev_proj:.1f}B", delta=f"+{rev_growth}% CAGR")
c2.metric("Projected NOPAT", f"${nopat:.1f}B", delta=f"{margin}% margin")
c3.metric("DCF value indication", f"${dcf_value:.1f}B")

if catalysts:
    st.success(f"Key catalysts identified: {', '.join(catalysts)}")
if thesis:
    st.info(f"Thesis: {thesis}")

st.progress(min(int(rev_growth * 4), 100))
st.caption(f"Revenue growth confidence indicator — {rev_growth}% CAGR over {years} years")
