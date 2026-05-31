"""
main.py

Caduceus Decision-Support API
==============================
FastAPI application entry point.

Security measures in place:
  - JWT authentication (HS256, 8-hour expiry) on all decision/security endpoints
  - bcrypt password hashing (passlib, cost factor 12)
  - CORS restricted to localhost:8501 (Streamlit) and localhost:3000 (Next.js)
  - Rate limiting via slowapi: login 5/min | POST 20/min | GET 60/min
  - Pydantic field constraints on all input schemas (min/max length, value bounds)
  - Custom exception handlers producing consistent JSON error format
  - No secrets in source -- all config via environment variables
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import create_tables
from app.exceptions import (
    NotFoundException, DuplicateException, ForbiddenException, BadRequestException,
    not_found_handler, duplicate_handler, forbidden_handler, bad_request_handler,
)
from app.routers.auth import router as auth_router, users_router
from app.routers.decisions import router as decisions_router
from app.routers.securities import router as securities_router

settings = get_settings()

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ---------------------------------------------------------------------------
# Lifespan -- create tables on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    description="""
## Caduceus Decision-Support API

Institutional-grade investment decision infrastructure for Rhenman & Partners.

### What this API does
- **Decisions**: Create, track, and evolve investment theses across the Phase 1 pharma universe
- **Securities**: Query the EDGAR-backed financial fact database (read-only)
- **Auth**: JWT-secured analyst sessions (Bloomberg ID integration in v2)

### Phase 1 Universe
PFE · MRK · JNJ · ABBV · BMY · LLY · AMGN · GILD

### AI-Ready
The `/decisions/{id}/suggest` endpoint is a placeholder today.
In Module 7 it will connect to the pgvector evidence store and return
ranked 10-K passages, earnings call excerpts, and FDA filing references
semantically matched to your current thesis.
    """,
    version=settings.app_version,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Register, login, and inspect the authenticated analyst profile.",
        },
        {
            "name": "Users",
            "description": "Analyst profile endpoints.",
        },
        {
            "name": "Decisions",
            "description": "Investment decisions -- analyst-owned, firm-visible, AI-ready.",
        },
        {
            "name": "Securities",
            "description": "Phase 1 universe reference data. Read-only -- the EDGAR pipeline owns writes.",
        },
    ],
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware: CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ---------------------------------------------------------------------------
# Middleware: Rate limiting
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Custom exception handlers
# ---------------------------------------------------------------------------
app.add_exception_handler(NotFoundException, not_found_handler)
app.add_exception_handler(DuplicateException, duplicate_handler)
app.add_exception_handler(ForbiddenException, forbidden_handler)
app.add_exception_handler(BadRequestException, bad_request_handler)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(decisions_router)
app.include_router(securities_router)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"], summary="API health check")
def root():
    """Return API status and version. No authentication required."""
    return {
        "status": "ok",
        "name": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
        "docs": "/docs",
    }
