"""
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
                         headers={"Authorization": f"Bearer {st.session_state['token']}"}, timeout=10)
        return (r.json(), None) if r.ok else (None, r.text)
    except Exception as e:
        return None, "Backend unreachable — is the API running on localhost:8000?"

def api_post(path, payload):
    try:
        r = requests.post(f"{API}{path}",
                          headers={"Authorization": f"Bearer {st.session_state['token']}"},
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
    st.sidebar.markdown(f"**{u.get('name', 'Analyst')}**")
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
            st.write(f"**{d['ticker']}** {d['action']} — conviction {d['conviction']}/5 — {d['outcome']}")

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
