"""
Module 5 -- Assignment 07: Build an Error-Resilient API

Demonstrates: custom exception classes, global handlers,
business logic guard, consistent JSON error format.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class NotFoundException(Exception):
    def __init__(self, resource: str, identifier: str | int):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' not found")


class DuplicateException(Exception):
    def __init__(self, resource: str, field: str, value: str):
        self.resource = resource
        self.field = field
        self.value = value
        super().__init__(f"{resource} with {field}='{value}' already exists")


class BusinessRuleException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Global handlers
# ---------------------------------------------------------------------------

async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    return JSONResponse(status_code=404, content={
        "error": "not_found",
        "message": str(exc),
        "resource": exc.resource,
        "identifier": str(exc.identifier),
    })


async def duplicate_handler(request: Request, exc: DuplicateException) -> JSONResponse:
    return JSONResponse(status_code=409, content={
        "error": "duplicate",
        "message": str(exc),
        "field": exc.field,
        "value": exc.value,
    })


async def business_rule_handler(request: Request, exc: BusinessRuleException) -> JSONResponse:
    return JSONResponse(status_code=400, content={
        "error": "business_rule_violation",
        "message": exc.detail,
    })


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///./students_v2.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_student_or_404(student_id: int, db: Session) -> Student:
    student = db.get(Student, student_id)
    if not student:
        raise NotFoundException("Student", student_id)
    return student


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Error-Resilient Student API",
    description="Demonstrates custom exceptions and global error handlers.",
    version="0.1.0",
)

app.add_exception_handler(NotFoundException, not_found_handler)
app.add_exception_handler(DuplicateException, duplicate_handler)
app.add_exception_handler(BusinessRuleException, business_rule_handler)

Base.metadata.create_all(bind=engine)


@app.post("/students", response_model=StudentResponse, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    """Create a student. Raises 409 DuplicateException if email exists."""
    if db.query(Student).filter(Student.email == payload.email).first():
        raise DuplicateException("Student", "email", payload.email)
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get student by ID. Raises 404 NotFoundException if missing."""
    return get_student_or_404(student_id, db)


@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """
    Delete student. Business rule guard: active students cannot be deleted.
    PATCH status to 'graduated' or 'withdrawn' first.
    """
    student = get_student_or_404(student_id, db)
    if student.status == "active":
        raise BusinessRuleException(
            "Cannot delete an active student. "
            "Change status to 'graduated' or 'withdrawn' first."
        )
    db.delete(student)
    db.commit()


@app.patch("/students/{student_id}/status", response_model=StudentResponse)
def update_status(student_id: int, status: str, db: Session = Depends(get_db)):
    """Update student status."""
    student = get_student_or_404(student_id, db)
    if status not in ("active", "graduated", "withdrawn"):
        raise BusinessRuleException("Status must be: active, graduated, or withdrawn")
    student.status = status
    db.commit()
    db.refresh(student)
    return student


@app.get("/")
def root():
    return {"message": "Error-Resilient API", "docs": "/docs"}
