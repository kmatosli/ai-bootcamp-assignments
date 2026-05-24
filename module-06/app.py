import streamlit as st
st.set_page_config(page_title="Caduceus", page_icon="⚕️", layout="wide")

import plotly.express as px
import pandas as pd
from api_client import (login, register, get_me, get_decisions,
                        create_decision, set_outcome, get_securities,
                        get_copilot_response, mock_copilot)

CORE_BLUE = "#0F4C81"
BABY_BLUE = "rgb(179,205,224)"
SUGGESTED = {
    "Decisions": ["Summarise open decisions by conviction",
                  "Flag decisions where thesis may have drifted",
                  "Which calls pending outcome longest?"],
    "Earnings":  ["Who reports next in the portfolio?",
                  "Compare our model vs Street for next print",
                  "Which names have a recent miss pattern?"],
    "Portfolio": ["Surface concentration risk by therapeutic area",
                  "Flag sizing vs conviction mismatches",
                  "Score thesis health across positions"],
    "Pipeline":  ["Summarise Phase 3 readouts this quarter",
                  "Flag LOE risk in the next 24 months",
                  "Highest peak sales potential assets?"],
}

for k,v in [("token",None),("user",None),("messages",[]),
            ("scope","Decisions"),("ctx",[]),("api_key",""),("show_reg",False)]:
    if k not in st.session_state: st.session_state[k] = v

def render_login():
    _,c,_ = st.columns([1,2,1])
    with c:
        st.markdown("## ⚕️ Caduceus")
        st.markdown("*Rhenman & Partners · Healthcare Equity Decision-Support*")
        st.divider()
        if not st.session_state["show_reg"]:
            st.subheader("Analyst Login")
            email = st.text_input("Email", placeholder="you@rhenman.com", key="le")
            pw    = st.text_input("Password", type="password", key="lp")
            ca,cb = st.columns(2)
            with ca:
                if st.button("Log in", type="primary", use_container_width=True):
                    if not email or not pw:
                        st.error("Email and password required.")
                    else:
                        with st.spinner("Authenticating..."):
                            data, err = login(email, pw)
                        if err:
                            st.error(f"Login failed: {err}")
                        else:
                            tok = data["access_token"]
                            st.session_state["token"] = tok
                            ud, _ = get_me(tok)
                            st.session_state["user"] = ud or {"name":email,"email":email,"role":"analyst"}
                            st.rerun()
            with cb:
                if st.button("Create account", use_container_width=True):
                    st.session_state["show_reg"] = True
                    st.rerun()
        else:
            st.subheader("Create Account")
            name  = st.text_input("Full name")
            email = st.text_input("Email", key="re")
            pw    = st.text_input("Password", type="password", key="rp")
            role  = st.selectbox("Role", ["analyst","pm","admin"])
            ca,cb = st.columns(2)
            with ca:
                if st.button("Register", type="primary", use_container_width=True):
                    if not all([name,email,pw]):
                        st.error("All fields required.")
                    else:
                        with st.spinner("Creating account..."):
                            data, err = register(name, email, pw, role)
                        if err:
                            st.error(f"Registration failed: {err}")
                        else:
                            tok = data["access_token"]
                            st.session_state["token"] = tok
                            ud, _ = get_me(tok)
                            st.session_state["user"] = ud or {"name":name,"email":email,"role":role}
                            st.session_state["show_reg"] = False
                            st.rerun()
            with cb:
                if st.button("Back to login", use_container_width=True):
                    st.session_state["show_reg"] = False
                    st.rerun()

def render_sidebar():
    u = st.session_state["user"]
    st.sidebar.markdown("## ⚕️ Caduceus")
    st.sidebar.divider()
    st.sidebar.markdown(f"**{u['name']}**")
    st.sidebar.caption(f"{u.get('role','analyst').replace('_',' ').title()} · {u.get('email','')}")
    st.sidebar.divider()
    st.sidebar.markdown("**Copilot scope**")
    st.session_state["scope"] = st.sidebar.selectbox(
        "Surface", list(SUGGESTED.keys()), label_visibility="collapsed")
    st.sidebar.markdown("**Context**")
    opts = ["Phase 1 universe","Beat/miss history","Earnings calendar","IRA exposure"]
    st.session_state["ctx"] = [o for o in opts
                                if st.sidebar.checkbox(o, value=(o=="Phase 1 universe"))]
    st.sidebar.divider()
    with st.sidebar.expander("🔑 Copilot API key"):
        k = st.text_input("key", type="password", value=st.session_state["api_key"],
                          label_visibility="collapsed", placeholder="sk-ant-...")
        st.session_state["api_key"] = k
        st.caption("✓ Live copilot" if k else "Mock responses")
    st.sidebar.divider()
    if st.sidebar.button("Log out", use_container_width=True):
        st.session_state.update({"token":None,"user":None,"messages":[],"api_key":""})
        st.rerun()

def render_dashboard():
    with st.spinner("Loading decisions..."):
        decisions, err = get_decisions(st.session_state["token"])
    if err:
        st.error(f"Could not load decisions: {err}"); return
    if not decisions:
        st.info("No decisions yet. Use the Decisions tab to record your first call."); return
    df = pd.DataFrame(decisions)
    total=len(df); open_d=len(df[df["status"]=="open"])
    high_c=len(df[df["conviction"]>=4]); validated=len(df[df["outcome"]=="validated"])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Decisions", total)
    c2.metric("Open", open_d)
    c3.metric("High Conviction ≥4", high_c)
    c4.metric("Validated", validated, delta=f"{round(validated/total*100)}%" if total else None)
    st.divider()
    st.subheader("Decision Registry")
    cols = [c for c in ["id","ticker","action","conviction","outcome","status","created_at"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)
    st.divider()
    cl,cr = st.columns(2)
    with cl:
        cc = df["conviction"].value_counts().reindex(range(1,6),fill_value=0).reset_index()
        cc.columns = ["Conviction","Count"]
        fig = px.bar(cc, x="Conviction", y="Count", color="Count",
                     color_continuous_scale=[BABY_BLUE,CORE_BLUE],
                     title="Decisions by Conviction Level")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        ac = df["action"].value_counts().reset_index()
        ac.columns = ["Action","Count"]
        cmap={"Buy":"#3F7D5C","Add":"#7FBFC2","Hold":"#7A8499","Trim":"#B8853A","Sell":"#A54A3A"}
        fig2 = px.pie(ac, names="Action", values="Count", color="Action",
                      color_discrete_map=cmap, title="Decision Actions")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

def render_decisions():
    token = st.session_state["token"]
    cf,ca = st.columns(2)
    with cf:
        st.subheader("Record a Decision")
        with st.spinner("Loading universe..."):
            secs, _ = get_securities(token)
        tickers = ([s["ticker"] for s in secs] if secs
                   else ["PFE","MRK","JNJ","ABBV","BMY","LLY","AMGN","GILD"])
        ticker = st.selectbox("Ticker", tickers)
        action = st.selectbox("Action", ["Buy","Add","Hold","Trim","Sell"])
        conv   = st.slider("Conviction", 1, 5, 3)
        rat    = st.text_area("Rationale",
                              placeholder="What is your thesis? What evidence supports this call?",
                              height=150)
        if st.button("Submit Decision", type="primary", use_container_width=True):
            if len(rat.strip()) < 10:
                st.warning("Rationale must be at least 10 characters.")
            else:
                with st.spinner("Recording..."):
                    res, err = create_decision(token, {
                        "ticker":ticker,"action":action,"conviction":conv,
                        "rationale":rat,"evidence_ids":[],
                        "workflow_breadcrumb":["Caduceus Dashboard"]})
                if err: st.error(f"Failed: {err}")
                else:   st.success(f"✓ {ticker} {action} (conviction {conv}/5) recorded")
    with ca:
        st.subheader("Set Decision Outcome")
        with st.spinner("Loading open decisions..."):
            open_d, err = get_decisions(token, status="open")
        if err:
            st.error(f"Could not load: {err}")
        elif not open_d:
            st.info("No open decisions to update.")
        else:
            opts = {f"#{d['id']} — {d['ticker']} {d['action']} (conv {d['conviction']})": d["id"]
                    for d in open_d}
            sel  = st.selectbox("Select decision", list(opts.keys()))
            out  = st.radio("Outcome",["validated","invalidated","superseded"],horizontal=True)
            note = st.text_input("Notes", placeholder="What proved the call right or wrong?")
            if st.button("Record Outcome", use_container_width=True):
                with st.spinner("Updating..."):
                    res, err = set_outcome(token, opts[sel], out, note or None)
                if err: st.error(f"Failed: {err}")
                else:   st.success(f"✓ Outcome: {out}")

def render_copilot():
    scope   = st.session_state["scope"]
    context = st.session_state["ctx"]
    api_key = st.session_state["api_key"]
    st.caption(f"**Scope: {scope}** · {'Live AI' if api_key else 'Mock responses'} · "
               f"Change scope and context in the sidebar.")
    actions = SUGGESTED.get(scope, [])
    cols = st.columns(len(actions))
    for i,a in enumerate(actions):
        if cols[i].button(a, use_container_width=True, key=f"sa{i}"):
            st.session_state["messages"].append({"role":"user","content":a})
            st.rerun()
    st.divider()
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    prompt = st.chat_input(f"Ask about {scope.lower()}...")
    if prompt:
        st.session_state["messages"].append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if api_key:
                    msgs = [{"role":m["role"],"content":m["content"]}
                            for m in st.session_state["messages"]]
                    reply, err = get_copilot_response(api_key, scope, msgs, context)
                    if err: reply = mock_copilot(scope, prompt, context)
                else:
                    reply = mock_copilot(scope, prompt, context)
            st.write(reply)
            st.session_state["messages"].append({"role":"assistant","content":reply})
    if st.session_state["messages"]:
        if st.button("Clear conversation", use_container_width=True):
            st.session_state["messages"] = []
            st.rerun()

def main():
    if not st.session_state["token"]:
        render_login(); return
    render_sidebar()
    st.markdown("## ⚕️ Caduceus Decision Dashboard")
    st.caption("*Rhenman & Partners · Healthcare Equity Decision-Support Platform*")
    t1,t2,t3 = st.tabs(["📊 Dashboard","📋 Decisions","🤖 Copilot"])
    with t1: render_dashboard()
    with t2: render_decisions()
    with t3: render_copilot()

main()
