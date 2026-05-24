import pathlib

base = pathlib.Path(r"C:\Users\kmato\OneDrive\Documents\GitHub\portfolio-challenge\ai-bootcamp-assignments\module-06")
base.mkdir(parents=True, exist_ok=True)

files = {}

# ── 1. api_explorer.py ────────────────────────────────────────────────────────
files["api_explorer.py"] = '''"""
api_explorer.py - Module 6: API Explorer
Caduceus Healthcare Equity Platform - Rhenman & Partners
Fetches pharma company data from the SEC EDGAR API.
"""
import requests

BASE = "https://data.sec.gov/submissions/CIK{}.json"
HEADERS = {"User-Agent": "Caduceus Research caduceus@research.com"}

PHASE1 = {
    "Pfizer":              "0000078003",
    "Merck":               "0000310158",
    "Johnson & Johnson":   "0000200406",
}

MISSING = "9999999999"  # does not exist

def fetch_company(name, cik):
    url = BASE.format(cik.zfill(10))
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code == 404:
        print(f"  ERROR 404: Company with CIK {cik} not found.")
        return
    if not r.ok:
        print(f"  ERROR {r.status_code}: {r.text[:100]}")
        return
    data = r.json()
    print(f"  Name:      {data.get(\'name\', \'N/A\')}")
    print(f"  CIK:       {data.get(\'cik\', \'N/A\')}")
    print(f"  SIC:       {data.get(\'sic\', \'N/A\')} - {data.get(\'sicDescription\', \'N/A\')}")
    print(f"  State:     {data.get(\'stateOfIncorporation\', \'N/A\')}")
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    tenk = [f for f in forms if f == "10-K"]
    print(f"  10-K filings on record: {len(tenk)}")

print("=" * 55)
print("Caduceus - SEC EDGAR Company Explorer")
print("=" * 55)

for name, cik in PHASE1.items():
    print(f"\\n{name} (CIK {cik})")
    fetch_company(name, cik)

print(f"\\nMissing CIK test (CIK {MISSING}):")
fetch_company("Unknown", MISSING)

print("\\nDone.")
'''

# ── 2. ai_assistant.py ────────────────────────────────────────────────────────
files["ai_assistant.py"] = '''"""
ai_assistant.py - Module 6: AI Assistant with Context
Caduceus Healthcare Equity Platform - Rhenman & Partners
Context-scoped analyst copilot with customizable system prompt.
"""
import streamlit as st
st.set_page_config(page_title="Caduceus Copilot", page_icon="⚕️", layout="wide")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.title("⚕️ Caduceus Analyst Copilot")
st.caption("Context-scoped AI assistant for healthcare equity research")

with st.sidebar:
    st.header("Copilot Configuration")
    system_prompt = st.text_area(
        "System prompt",
        value="You are a healthcare equity analyst copilot at Rhenman & Partners.",
        height=120,
    )
    st.markdown("**Add context:**")
    if st.checkbox("Phase 1 universe (PFE MRK JNJ ABBV BMY LLY AMGN GILD)"):
        system_prompt += " Focus on the Phase 1 large-cap pharma universe."
    if st.checkbox("Earnings analysis"):
        system_prompt += " Specialise in earnings analysis and beat/miss patterns."
    if st.checkbox("IRA / drug pricing"):
        system_prompt += " Include IRA drug pricing policy context."
    if st.checkbox("Pipeline / clinical trials"):
        system_prompt += " Include pipeline and clinical trial analysis."
    st.divider()
    api_key = st.text_input("Anthropic API key", type="password", placeholder="sk-ant-...")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Ask about healthcare equity...")
if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if api_key:
                try:
                    from anthropic import Anthropic
                    client = Anthropic(api_key=api_key)
                    resp = client.messages.create(
                        model="claude-sonnet-4-20250514", max_tokens=500,
                        system=system_prompt,
                        messages=[{"role": m["role"], "content": m["content"]}
                                  for m in st.session_state["messages"]],
                    )
                    reply = resp.content[0].text
                except Exception as e:
                    reply = f"[API error: {e}] Mock: Regarding '{prompt[:60]}' — in a live environment this retrieves EDGAR and transcript data via pgvector and synthesises a response via Claude."
            else:
                ctx_parts = [p for p in system_prompt.split(".") if p.strip()]
                reply = (f"[Mock Copilot] System: {system_prompt[:80]}...\\n\\n"
                         f"Regarding '{prompt[:80]}': In production this retrieves "
                         f"relevant EDGAR filings and earnings transcripts via pgvector "
                         f"similarity search, then synthesises a response via the Anthropic API.")
        st.write(reply)
        st.session_state["messages"].append({"role": "assistant", "content": reply})
'''

# ── 3. my_frontend.py ────────────────────────────────────────────────────────
files["my_frontend.py"] = '''"""
my_frontend.py - Module 6: Connect to Module 5 Task Manager
Caduceus Healthcare Equity Platform - Rhenman & Partners
Streamlit frontend connecting to the Caduceus Decision API.
"""
import streamlit as st
import requests

st.set_page_config(page_title="Caduceus Frontend", page_icon="⚕️", layout="wide")

API = "http://localhost:8000"

if "token" not in st.session_state: st.session_state["token"] = None
if "user"  not in st.session_state: st.session_state["user"]  = None

def api_login(email, password):
    try:
        r = requests.post(f"{API}/auth/login",
                          json={"email": email, "password": password}, timeout=10)
        return (r.json(), None) if r.ok else (None, "Invalid credentials.")
    except Exception as e:
        return None, str(e)

def api_get(path):
    try:
        r = requests.get(f"{API}{path}",
                         headers={"Authorization": f"Bearer {st.session_state[\'token\']}"}, timeout=10)
        return (r.json(), None) if r.ok else (None, r.text)
    except Exception as e:
        return None, "Backend unreachable — is the API running on localhost:8000?"

def api_post(path, payload):
    try:
        r = requests.post(f"{API}{path}",
                          headers={"Authorization": f"Bearer {st.session_state[\'token\']}"},
                          json=payload, timeout=10)
        return (r.json(), None) if r.ok else (None, str(r.json().get("detail", r.text)))
    except Exception as e:
        return None, "Backend unreachable — is the API running on localhost:8000?"

if not st.session_state["token"]:
    st.title("⚕️ Caduceus")
    st.subheader("Login")
    email = st.text_input("Email")
    pw    = st.text_input("Password", type="password")
    if st.button("Log in", type="primary"):
        data, err = api_login(email, pw)
        if err:
            st.error(err)
        else:
            st.session_state["token"] = data["access_token"]
            ud, _ = api_get("/auth/users/me")
            st.session_state["user"] = ud or {"name": email, "email": email}
            st.rerun()
else:
    u = st.session_state["user"] or {}
    st.sidebar.markdown(f"**{u.get(\'name\', \'Analyst\')}**")
    st.sidebar.caption(u.get("email", ""))
    if st.sidebar.button("Logout"):
        st.session_state["token"] = None
        st.session_state["user"]  = None
        st.rerun()

    st.title("⚕️ Caduceus Decision Tracker")

    decisions, err = api_get("/decisions")
    if err:
        st.error(f"Backend error: {err}")
    else:
        decisions = decisions or []
        total     = len(decisions)
        completed = len([d for d in decisions if d.get("outcome") == "validated"])
        c1, c2 = st.columns(2)
        c1.metric("Total Decisions", total)
        c2.metric("Validated", completed)

        st.subheader("Decision List")
        for d in decisions:
            st.write(f"**{d[\'ticker\']}** {d[\'action\']} — conviction {d[\'conviction\']}/5 — {d[\'outcome\']}")

    st.divider()
    st.subheader("Add Decision")
    ticker = st.selectbox("Ticker", ["PFE","MRK","JNJ","ABBV","BMY","LLY","AMGN","GILD"])
    action = st.selectbox("Action", ["Buy","Add","Hold","Trim","Sell"])
    conv   = st.slider("Conviction", 1, 5, 3)
    rat    = st.text_area("Rationale", placeholder="Investment thesis...")
    if st.button("Submit", type="primary"):
        if len(rat.strip()) < 10:
            st.warning("Rationale must be at least 10 characters.")
        else:
            res, err = api_post("/decisions", {
                "ticker": ticker, "action": action, "conviction": conv,
                "rationale": rat, "evidence_ids": [], "workflow_breadcrumb": ["Frontend"]})
            if err: st.error(err)
            else:   st.success(f"Decision recorded: {ticker} {action}")
            st.rerun()
'''

# ── 4. data_explorer.py ──────────────────────────────────────────────────────
files["data_explorer.py"] = '''"""
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
'''

# ── 5. my_dashboard.py ───────────────────────────────────────────────────────
files["my_dashboard.py"] = '''"""
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
'''

# ── 6. quiz_app.py ───────────────────────────────────────────────────────────
files["quiz_app.py"] = '''"""
quiz_app.py - Module 6: Stateful Quiz App
Caduceus Healthcare Equity Platform - Rhenman & Partners
Healthcare equity analyst knowledge quiz.
"""
import streamlit as st

st.set_page_config(page_title="Caduceus Quiz", page_icon="⚕️")

QUESTIONS = [
    {
        "q": "What does PDUFA stand for?",
        "options": ["Prescription Drug User Fee Act", "Public Drug Utility Framework Act",
                    "Pharmaceutical Data Uniformity Filing Act", "Prescription Drug Unified Filing Authority"],
        "answer": "Prescription Drug User Fee Act",
        "explanation": "PDUFA sets the FDA review timeline — typically 10-12 months for standard review."
    },
    {
        "q": "Which metric best captures a pharma company earnings surprise direction?",
        "options": ["EPS Surprise %", "Revenue growth YoY", "P/E ratio", "Days to cover"],
        "answer": "EPS Surprise %",
        "explanation": "EPS Surprise % measures actual vs consensus estimate — the core beat/miss signal."
    },
    {
        "q": "What is the IRA drug pricing negotiation threshold for small molecules?",
        "options": ["7 years post-approval", "9 years post-approval",
                    "12 years post-approval", "5 years post-approval"],
        "answer": "9 years post-approval",
        "explanation": "The IRA allows Medicare negotiation of small molecules 9 years post-approval, biologics 13 years."
    },
    {
        "q": "In the Caduceus materiality scorer, what does a higher daysToCatalyst value mean?",
        "options": ["More urgent", "Less urgent", "Higher conviction", "Lower portfolio weight"],
        "answer": "Less urgent",
        "explanation": "daysToCatalyst counts days until the event. Fewer days = more urgent = higher materiality score."
    },
    {
        "q": "Which data source is canonical for financial facts in Caduceus?",
        "options": ["Yahoo Finance", "Morningstar", "SEC EDGAR XBRL", "Bloomberg"],
        "answer": "SEC EDGAR XBRL",
        "explanation": "SEC EDGAR is the authoritative source — Yahoo Finance is used only for validation and market data."
    },
]

for k, v in [("q_idx", 0), ("score", 0), ("answered", False), ("done", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

st.title("⚕️ Caduceus Analyst Quiz")
st.caption("Test your healthcare equity knowledge")

if st.session_state["done"]:
    st.success(f"Quiz complete! Score: {st.session_state['score']}/{len(QUESTIONS)}")
    pct = round(st.session_state["score"] / len(QUESTIONS) * 100)
    st.metric("Final score", f"{pct}%")
    if st.button("Restart", type="primary"):
        st.session_state.update({"q_idx": 0, "score": 0, "answered": False, "done": False})
        st.rerun()
else:
    idx = st.session_state["q_idx"]
    q   = QUESTIONS[idx]
    st.progress((idx) / len(QUESTIONS))
    st.caption(f"Question {idx + 1} of {len(QUESTIONS)} | Score: {st.session_state['score']}")
    st.subheader(q["q"])
    choice = st.radio("Select your answer", q["options"], key=f"q{idx}", index=None)
    if st.button("Submit", type="primary", disabled=st.session_state["answered"]):
        if choice is None:
            st.warning("Please select an answer.")
        else:
            st.session_state["answered"] = True
            if choice == q["answer"]:
                st.success("Correct!")
                st.session_state["score"] += 1
            else:
                st.error(f"Incorrect. The answer is: **{q['answer']}**")
            st.info(f"Explanation: {q['explanation']}")
    if st.session_state["answered"]:
        if st.button("Next question"):
            st.session_state["q_idx"] += 1
            st.session_state["answered"] = False
            if st.session_state["q_idx"] >= len(QUESTIONS):
                st.session_state["done"] = True
            st.rerun()
'''

# ── 7. explore.py ────────────────────────────────────────────────────────────
files["explore.py"] = '''"""
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
'''

# ── 8. live_search.html ──────────────────────────────────────────────────────
files["live_search.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Caduceus - Live Search</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 24px; background: #f7f8fa; color: #2C333E; }
    h1 { color: #0F4C81; }
    input { width: 100%; padding: 10px 14px; font-size: 16px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; margin-bottom: 8px; }
    #count { font-size: 13px; color: #7A8499; margin-bottom: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
    .card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
    .card h3 { margin: 0 0 6px; font-size: 15px; color: #0F4C81; }
    .card p { margin: 2px 0; font-size: 13px; color: #7A8499; }
    .tag { display: inline-block; background: #EEF2FF; color: #0F4C81; border-radius: 4px; padding: 2px 8px; font-size: 11px; margin-top: 8px; }
    #status { color: #7A8499; font-style: italic; }
    .error { color: #A54A3A; }
  </style>
</head>
<body>
  <h1>⚕️ Caduceus Company Search</h1>
  <p>Search Phase 1 pharma universe via JSONPlaceholder (demo data)</p>
  <input type="text" id="search" placeholder="Search by name or email..." oninput="filterCards()">
  <div id="count"></div>
  <div id="status">Loading companies...</div>
  <div class="grid" id="grid"></div>

  <script>
    let allUsers = [];

    async function loadUsers() {
      try {
        const resp = await fetch("https://jsonplaceholder.typicode.com/users");
        if (!resp.ok) throw new Error("Fetch failed: " + resp.status);
        allUsers = await resp.json();
        // Remap to pharma context
        const tickers = ["PFE","MRK","JNJ","ABBV","BMY","LLY","AMGN","GILD","NVO","AZN"];
        allUsers = allUsers.map((u, i) => ({
          ...u,
          ticker: tickers[i] || "N/A",
          name: u.company.name,
          email: u.username.toLowerCase() + "@rhenman.com",
          role: u.company.bs.split(" ")[0],
        }));
        document.getElementById("status").textContent = "";
        renderCards(allUsers);
      } catch (e) {
        document.getElementById("status").innerHTML = `<span class="error">Error loading data: ${e.message}</span>`;
      }
    }

    function renderCards(users) {
      const grid = document.getElementById("grid");
      const count = document.getElementById("count");
      count.textContent = `Showing ${users.length} of ${allUsers.length} companies`;
      grid.innerHTML = users.map(u => `
        <div class="card">
          <h3>${u.ticker} &mdash; ${u.name}</h3>
          <p>${u.email}</p>
          <p>${u.address.city}, ${u.address.zipcode}</p>
          <span class="tag">${u.role}</span>
        </div>
      `).join("");
    }

    function filterCards() {
      const q = document.getElementById("search").value.toLowerCase();
      const filtered = allUsers.filter(u =>
        u.name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        u.ticker.toLowerCase().includes(q)
      );
      renderCards(filtered);
    }

    loadUsers();
  </script>
</body>
</html>
'''

# ── 9. dashboard.html ────────────────────────────────────────────────────────
files["dashboard.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Caduceus - Mini Dashboard</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 24px; background: #f7f8fa; color: #2C333E; }
    h1 { color: #0F4C81; margin-bottom: 4px; }
    .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }
    .stat { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; text-align: center; }
    .stat .num { font-size: 36px; font-weight: 700; color: #0F4C81; }
    .stat .lbl { font-size: 13px; color: #7A8499; margin-top: 4px; }
    .toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
    input { flex: 1; padding: 9px 13px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
    button { padding: 9px 18px; background: #0F4C81; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
    button:hover { background: #0a3561; }
    button.secondary { background: white; color: #0F4C81; border: 1px solid #0F4C81; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; }
    th { background: #0F4C81; color: white; padding: 10px 14px; text-align: left; font-size: 13px; }
    td { padding: 10px 14px; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .badge.pending    { background: #fff3cd; color: #856404; }
    .badge.validated  { background: #d4edda; color: #155724; }
    .badge.open       { background: #cce5ff; color: #004085; }
    #updated { font-size: 12px; color: #7A8499; margin-top: 8px; }
    .error { color: #A54A3A; padding: 12px; background: #f8d7da; border-radius: 6px; }
  </style>
</head>
<body>
  <h1>⚕️ Caduceus Decision Dashboard</h1>
  <p style="color:#7A8499;margin-top:0">Rhenman &amp; Partners &mdash; connecting to localhost:8000</p>

  <div class="stats">
    <div class="stat"><div class="num" id="stat-total">-</div><div class="lbl">Total Decisions</div></div>
    <div class="stat"><div class="num" id="stat-open">-</div><div class="lbl">Open</div></div>
    <div class="stat"><div class="num" id="stat-validated">-</div><div class="lbl">Validated</div></div>
  </div>

  <div class="toolbar">
    <input type="text" id="new-ticker" placeholder="Ticker (e.g. LLY)">
    <input type="text" id="new-rat" placeholder="Rationale (min 10 chars)">
    <button onclick="addDecision()">Add Decision</button>
    <button class="secondary" onclick="refreshAll()">Refresh</button>
  </div>
  <div id="error-msg"></div>
  <div id="updated"></div>

  <table>
    <thead><tr><th>ID</th><th>Ticker</th><th>Action</th><th>Conviction</th><th>Outcome</th><th>Status</th></tr></thead>
    <tbody id="tbody"><tr><td colspan="6" style="color:#7A8499;text-align:center">Loading...</td></tr></tbody>
  </table>

  <script>
    const API = "http://localhost:8000";
    let token = localStorage.getItem("caduceus_token") || null;

    function showError(msg) {
      document.getElementById("error-msg").innerHTML = `<div class="error">${msg}</div>`;
    }
    function clearError() { document.getElementById("error-msg").innerHTML = ""; }

    async function ensureToken() {
      if (token) return token;
      const email = prompt("Email:");
      const pw    = prompt("Password:");
      const r = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({email, password: pw})
      });
      if (!r.ok) { showError("Login failed"); return null; }
      const d = await r.json();
      token = d.access_token;
      localStorage.setItem("caduceus_token", token);
      return token;
    }

    async function loadDecisions() {
      const tok = await ensureToken();
      if (!tok) return;
      try {
        const r = await fetch(`${API}/decisions`, {headers: {"Authorization": `Bearer ${tok}`}});
        if (r.status === 401) { token = null; localStorage.removeItem("caduceus_token"); loadDecisions(); return; }
        const data = await r.json();
        document.getElementById("stat-total").textContent = data.length;
        document.getElementById("stat-open").textContent = data.filter(d => d.status === "open").length;
        document.getElementById("stat-validated").textContent = data.filter(d => d.outcome === "validated").length;
        const tbody = document.getElementById("tbody");
        if (!data.length) {
          tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#7A8499">No decisions yet.</td></tr>`;
          return;
        }
        tbody.innerHTML = data.map(d => `
          <tr>
            <td>${d.id}</td>
            <td><strong>${d.ticker}</strong></td>
            <td>${d.action}</td>
            <td>${d.conviction}/5</td>
            <td><span class="badge ${d.outcome}">${d.outcome}</span></td>
            <td><span class="badge ${d.status}">${d.status}</span></td>
          </tr>`).join("");
        clearError();
      } catch(e) {
        showError("Backend unreachable — is the API running on localhost:8000?");
      }
    }

    async function addDecision() {
      const tok = await ensureToken();
      if (!tok) return;
      const ticker = document.getElementById("new-ticker").value.trim().toUpperCase();
      const rat    = document.getElementById("new-rat").value.trim();
      if (!ticker || rat.length < 10) { showError("Ticker and rationale (10+ chars) required."); return; }
      try {
        const r = await fetch(`${API}/decisions`, {
          method: "POST",
          headers: {"Content-Type":"application/json","Authorization":`Bearer ${tok}`},
          body: JSON.stringify({ticker, action:"Buy", conviction:3, rationale:rat,
                                evidence_ids:[], workflow_breadcrumb:["HTML Dashboard"]})
        });
        if (!r.ok) { showError(await r.text()); return; }
        document.getElementById("new-ticker").value = "";
        document.getElementById("new-rat").value = "";
        clearError();
        await refreshAll();
      } catch(e) { showError("Backend unreachable."); }
    }

    async function refreshAll() {
      await loadDecisions();
      document.getElementById("updated").textContent =
        "Last updated: " + new Date().toLocaleTimeString();
    }

    refreshAll();
  </script>
</body>
</html>
'''

# ── 10. portfolio.html ───────────────────────────────────────────────────────
files["portfolio.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kathy Matosli - Portfolio</title>
  <link rel="stylesheet" href="portfolio-styles.css">
</head>
<body>
  <header>
    <h1>Kathy Matosli</h1>
    <p class="tagline">Quant Developer &mdash; Healthcare Equity &mdash; Rhenman &amp; Partners</p>
    <nav>
      <a href="#about">About</a>
      <a href="#projects">Projects</a>
      <a href="#skills">Skills</a>
    </nav>
  </header>

  <main>
    <section id="about">
      <h2>About</h2>
      <p>
        I am a Quant Developer specialising in healthcare equity decision-support infrastructure.
        My work sits at the intersection of financial data engineering, AI-assisted analysis,
        and institutional investment processes. I am currently building Caduceus, a decision-support
        platform for the analysts and portfolio managers at Rhenman &amp; Partners, a Stockholm-based
        long/short healthcare equity fund.
      </p>
      <p>
        Previously I worked across capital markets data and financial services. I am completing
        the Coding Temple AI Bootcamp while delivering Caduceus as a real production system.
      </p>
    </section>

    <section id="projects">
      <h2>Projects</h2>
      <div class="project-grid">
        <article>
          <h3>Caduceus Decision-Support Platform</h3>
          <p>
            A full-stack healthcare equity platform for Rhenman &amp; Partners. Ingests data from
            19 sources including SEC EDGAR, FDA Orange Book, Purple Book, and CT.gov. Features
            a FastAPI backend, Streamlit dashboard, and React frontend with a decision registry,
            AI copilot, and materiality-ranked attention queue.
          </p>
        </article>
        <article>
          <h3>Caduceus Decision API (Module 5)</h3>
          <p>
            Production-grade FastAPI backend with JWT authentication, full CRUD on the decision
            registry, soft-delete never-delete pattern, activity logging background tasks,
            and 20 passing pytest tests. Deployed with SQLite for development and Supabase
            Postgres for production.
          </p>
        </article>
        <article>
          <h3>Catalyst Events Puller</h3>
          <p>
            A yfinance-powered earnings calendar puller that loads forward-looking and historical
            earnings dates for the Phase 1 pharma universe into Supabase. Implements the Wall
            Street Horizon LERI methodology — detecting late reporters as a negative surprise
            signal. 200 rows loaded covering 24 quarters per ticker.
          </p>
        </article>
      </div>
    </section>

    <section id="skills">
      <h2>Skills</h2>
      <ul>
        <li>Python &mdash; FastAPI, SQLAlchemy, Pandas, yfinance, edgartools</li>
        <li>Data Engineering &mdash; SEC EDGAR XBRL, FDA APIs, CT.gov, Supabase / PostgreSQL</li>
        <li>AI / ML &mdash; Anthropic Claude API, RAG pipelines, pgvector, prompt engineering</li>
        <li>Frontend &mdash; Streamlit, React / TypeScript, TanStack Router, Plotly</li>
        <li>DevOps &mdash; Git, Docker, Alembic migrations, GitHub Actions</li>
        <li>Finance &mdash; Healthcare equity analysis, DCF / SOTP valuation, EDGAR XBRL</li>
      </ul>
    </section>
  </main>

  <footer>
    <p>&copy; 2026 Kathy Matosli &mdash; Caduceus / Rhenman &amp; Partners</p>
  </footer>
</body>
</html>
'''

# ── 11. portfolio-styles.css ─────────────────────────────────────────────────
files["portfolio-styles.css"] = '''/* Caduceus brand system */
:root {
  --ink:       #2C333E;
  --core-blue: #0F4C81;
  --provence:  rgb(104,137,192);
  --baby-blue: rgb(179,205,224);
  --bg:        #F7F8FA;
  --card-bg:   #FFFFFF;
  --border:    #E2E8F0;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: "Inter", system-ui, sans-serif;
  background: var(--bg);
  color: var(--ink);
  line-height: 1.6;
}

/* Header */
header {
  background: var(--ink);
  color: white;
  padding: 48px 24px 32px;
  text-align: center;
}

header h1 {
  font-size: 2.8rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: white;
}

.tagline {
  color: var(--baby-blue);
  font-size: 1.1rem;
  margin-top: 8px;
}

nav {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 32px;
}

nav a {
  color: var(--baby-blue);
  text-decoration: none;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  transition: color 0.2s;
}

nav a:hover { color: white; }

/* Main content */
main {
  max-width: 900px;
  margin: 0 auto;
  padding: 48px 24px;
}

section {
  margin-bottom: 56px;
}

section h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--core-blue);
  border-bottom: 3px solid var(--core-blue);
  padding-bottom: 8px;
  margin-bottom: 24px;
}

section p {
  margin-bottom: 16px;
  color: var(--ink);
}

/* Project grid */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}

article {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  transition: box-shadow 0.2s;
}

article:hover {
  box-shadow: 0 4px 16px rgba(15,76,129,0.1);
}

article h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--core-blue);
  margin-bottom: 10px;
}

article p {
  font-size: 0.9rem;
  color: #5A6478;
  margin: 0;
}

/* Skills */
ul {
  list-style: none;
  padding: 0;
}

ul li {
  padding: 10px 14px;
  border-left: 3px solid var(--core-blue);
  margin-bottom: 10px;
  background: var(--card-bg);
  border-radius: 0 6px 6px 0;
  font-size: 0.95rem;
}

/* Footer */
footer {
  background: var(--ink);
  color: var(--baby-blue);
  text-align: center;
  padding: 20px;
  font-size: 0.85rem;
}
'''

# Write all files
written = []
for fname, content in files.items():
    fpath = base / fname
    fpath.write_text(content, encoding="utf-8")
    written.append(fname)
    print(f"  wrote {fname} ({len(content.splitlines())} lines)")

print(f"\nDone. {len(written)} files written to {base}")
