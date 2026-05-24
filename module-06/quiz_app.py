"""
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
