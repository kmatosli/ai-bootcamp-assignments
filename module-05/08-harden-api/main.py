"""
Module 5 -- Assignment 08: Harden Your API

Demonstrates: CORS middleware, slowapi rate limiting,
input length constraints on Pydantic schemas, 429 response.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs

Security measures:
  - CORS restricted to localhost:8501 and localhost:3000
  - Rate limiting: POST 5/min, GET 30/min (strict for demo purposes)
  - Input length caps on all schemas
  - No secrets in source code
"""
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

# ---------------------------------------------------------------------------
# Schemas with length constraints
# ---------------------------------------------------------------------------

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    track: str = Field(..., min_length=2, max_length=50)
    notes: str | None = Field(None, max_length=500)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Kathy Matosli",
                "email": "kmatosli@student.ct.edu",
                "track": "ai",
                "notes": "Module 5 student",
            }
        }
    }


class StudentResponse(StudentCreate):
    id: int


# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------

_db: dict[int, dict] = {}
_next_id = 1


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Hardened Student API",
    description="""
## Security Measures

- **CORS**: Restricted to localhost:8501 (Streamlit) and localhost:3000 (Next.js)
- **Rate limiting**: POST 5/min | GET 30/min via slowapi
- **Input constraints**: All fields have min/max length limits
- **No hardcoded secrets**: All config via environment variables
    """,
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000",
                   "http://127.0.0.1:8501", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.post("/students", response_model=StudentResponse, status_code=201,
          summary="Create a student (rate limited: 5/min)")
@limiter.limit("5/minute")
def create_student(request: Request, payload: StudentCreate):
    """Create a student. Rate limited to 5 requests per minute."""
    global _next_id
    student = {"id": _next_id, **payload.model_dump()}
    _db[_next_id] = student
    _next_id += 1
    return student


@app.get("/students", response_model=list[StudentResponse],
         summary="List students (rate limited: 30/min)")
@limiter.limit("30/minute")
def list_students(request: Request):
    """List all students. Rate limited to 30 requests per minute."""
    return list(_db.values())


@app.get("/")
def root():
    return {
        "message": "Hardened API",
        "security": ["CORS", "rate_limiting", "input_constraints"],
        "docs": "/docs",
    }
