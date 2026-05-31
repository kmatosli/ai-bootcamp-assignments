# Caduceus Decision-Support API

FastAPI backend for the Caduceus healthcare equity decision-support platform.
Built for Rhenman & Partners — Module 5 capstone, Coding Temple AI Bootcamp.

## Setup

```bash
cd decision-app
python -m pip install -r requirements.txt
cp .env.example .env          # fill in values
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for the Swagger UI.

## Project structure

```
decision-app/
├── app/
│   ├── main.py           # FastAPI app, middleware, routers, exception handlers
│   ├── config.py         # Settings from environment variables
│   ├── database.py       # SQLAlchemy engine, session, Base
│   ├── exceptions.py     # Custom exception classes + global handlers
│   ├── models/
│   │   ├── user.py       # User model (analyst seats)
│   │   ├── decision.py   # Decision model (primary analyst-owned resource)
│   │   └── activity_log.py
│   ├── schemas/
│   │   ├── common.py     # Shared enums (Direction, Conviction, Status)
│   │   ├── user.py       # UserCreate, UserResponse, TokenResponse
│   │   ├── decision.py   # DecisionCreate/Update/Patch/Response, SuggestResponse
│   │   └── filters.py    # Query parameter schemas
│   ├── routers/
│   │   ├── auth.py       # POST /auth/register, POST /auth/login, GET /users/me
│   │   ├── decisions.py  # Full CRUD + /suggest stub
│   │   └── securities.py # GET /securities (read-only reference data)
│   └── utils/
│       ├── auth.py       # JWT + bcrypt helpers, get_current_user dependency
│       ├── helpers.py    # get_decision_or_404, get_user_or_404
│       └── background.py # Activity log background task
└── tests/
    ├── conftest.py       # SQLite test DB, client fixture, auth_headers, sample_decision
    ├── test_auth.py      # 7 auth tests
    └── test_decisions.py # 13 decision CRUD tests
```

## Running tests

```bash
pytest tests/ -v
```

All 20 tests should pass.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | No | Register analyst, return JWT |
| POST | /auth/login | No | Login, return JWT |
| GET | /users/me | Yes | Analyst profile |
| POST | /decisions | Yes | Create decision |
| GET | /decisions | Yes | List decisions (firm-wide) |
| GET | /decisions/{id} | Yes | Get specific decision |
| PUT | /decisions/{id} | Yes | Full update (own decisions only) |
| PATCH | /decisions/{id} | Yes | Partial update (own decisions only) |
| DELETE | /decisions/{id} | Yes | Delete (must be closed first) |
| POST | /decisions/{id}/suggest | Yes | AI-ready stub (RAG in Module 7) |
| GET | /securities | Yes | List universe securities |
| GET | /securities/{ticker} | Yes | Get specific security |

## Security

- JWT authentication (HS256, 8-hour expiry)
- bcrypt password hashing
- CORS restricted to localhost:8501 (Streamlit) and localhost:3000 (Next.js)
- Rate limiting: login 5/min, POST 20/min, GET 60/min
- Pydantic field constraints on all input schemas
- Custom exception handlers with consistent JSON error format
- All config via environment variables — no hardcoded secrets

## Phase 1 Universe

PFE · MRK · JNJ · ABBV · BMY · LLY · AMGN · GILD
