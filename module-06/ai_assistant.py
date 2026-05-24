"""
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
                reply = (f"[Mock Copilot] System: {system_prompt[:80]}...\n\n"
                         f"Regarding '{prompt[:80]}': In production this retrieves "
                         f"relevant EDGAR filings and earnings transcripts via pgvector "
                         f"similarity search, then synthesises a response via the Anthropic API.")
        st.write(reply)
        st.session_state["messages"].append({"role": "assistant", "content": reply})
