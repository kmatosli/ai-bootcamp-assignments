# Module 6 Capstone - Caduceus AI Dashboard

Course: Coding Temple AI Bootcamp, Module 6
Platform: Caduceus Healthcare Equity Decision-Support
Firm: Rhenman & Partners, Stockholm

## What This Is

A Streamlit AI dashboard for healthcare equity analysts. Analysts log in, record investment decisions with conviction scores and rationale, track outcomes, and interact with a context-scoped AI copilot.

## Rubric Coverage

| Category | Points | Implementation |
|---|---|---|
| Authentication | 15 | Login/register, JWT in session_state, user in sidebar, logout |
| Dashboard View | 20 | 4 st.metric(), st.dataframe(), 2 st.plotly_chart() |
| Data Interaction | 20 | Thesis check form (POST), outcome setter (PATCH) |
| AI Feature | 20 | Context-scoped copilot, Anthropic API or mock fallback |
| Layout & UX | 15 | set_page_config, sidebar, 3 tabs, error handling, spinners |
| Code Quality | 10 | Centralized api_client.py, session state init, functions |

## Setup

Step 1 - Start the Module 5 backend

    cd ../module-05
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Verify at http://localhost:8000/docs

Step 2 - Run the dashboard

    cd ../module-06
    pip install -r requirements.txt
    streamlit run app.py

Opens at http://localhost:8501

## First Run

1. Click Create account on the login screen
2. Register with any name, email, password, role: analyst
3. Dashboard loads immediately

## Using the Dashboard

Dashboard tab - Decision metrics, registry table, conviction and action charts. All data pulled live from the API.

Decisions tab - Record a new investment call (POST) and set outcomes on existing decisions (PATCH).

Copilot tab - Context-scoped AI assistant. Select scope and context in the sidebar. Add your Anthropic API key (sk-ant-...) in the sidebar expander for live responses. Without a key the mock demonstrates the context-aware architecture.

## Architecture

    module-06/
        app.py           Streamlit frontend
        api_client.py    All API calls - centralized, never scattered in app.py
        requirements.txt
        README.md

    module-05/           FastAPI backend - must be running on localhost:8000
        app/
            main.py
            routers/     auth, decisions, securities
            models/
            schemas/
            utils/

All business logic lives behind the API. Streamlit only renders and collects input.

## Presentation Script (5 minutes)

Demo (2 min): Log in, Decisions tab: record a decision, set an outcome, Dashboard: show metrics update, Copilot: change scope, ask a question.

Architecture (1 min): Streamlit frontend talking to FastAPI. All API calls go through api_client.py. JWT from Module 5 powers login. The copilot changes its system prompt based on the selected scope.

Challenge (1 min): Keeping Streamlit thin. Every time I wanted logic in app.py I asked whether it belonged behind the API. Decision validation and AI suggestion are FastAPI endpoints - Streamlit only renders.

What I would improve (1 min): Streamlit is a teaching surface. The same FastAPI backend powers a React frontend built for institutional use with a workflow spine that captures the analytical path behind each decision. Streamlit is the delivery layer for this rubric; React is the production direction.
