"""
Module 5 -- Assignment 10: Polish Your API Documentation

Demonstrates: app metadata, tag descriptions, endpoint docstrings,
json_schema_extra examples, response descriptions on every endpoint.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///./students_docs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    track: Mapped[str] = mapped_column(String(50), nullable=False)
    cohort: Mapped[str] = mapped_column(String(20), nullable=False)
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


# ---------------------------------------------------------------------------
# Schemas with rich examples
# ---------------------------------------------------------------------------

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the student")
    email: str = Field(..., min_length=5, max_length=255, description="Unique student email address")
    track: str = Field(..., min_length=2, max_length=50, description="Bootcamp track (e.g. ai, data_science)")
    cohort: str = Field(..., min_length=2, max_length=20, description="Cohort identifier (e.g. 2026-Q2)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Kathy Matosli",
                "email": "kmatosli@student.ct.edu",
                "track": "ai",
                "cohort": "2026-Q2",
            }
        }
    }


class StudentPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    track: str | None = Field(None, min_length=2, max_length=50)
    cohort: str | None = Field(None, min_length=2, max_length=20)
    status: str | None = Field(None, description="active, graduated, or withdrawn")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "graduated",
                "cohort": "2026-Q2",
            }
        }
    }


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    track: str
    cohort: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Kathy Matosli",
                "email": "kmatosli@student.ct.edu",
                "track": "ai",
                "cohort": "2026-Q2",
                "status": "active",
                "created_at": "2026-05-24T01:00:00Z",
            }
        },
    }


# ---------------------------------------------------------------------------
# App with full metadata
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Coding Temple Student API",
    description="""
## Student Management API

Track students through the Coding Temple AI Bootcamp.

### Features
- Full **CRUD** for student records
- Filter by **track**, **cohort**, and **status**
- Consistent **JSON error format** on all failures
- Ready for **frontend integration**

### Student Lifecycle
`active` -> `graduated` or `withdrawn`
    """,
    version="1.0.0",
    contact={
        "name": "Kathy Matosli",
        "email": "kmatosli@student.ct.edu",
    },
    openapi_tags=[
        {
            "name": "Students",
            "description": "Create, read, update, and delete student records.",
        },
        {
            "name": "Health",
            "description": "API health and status endpoints.",
        },
    ],
)

Base.metadata.create_all(bind=engine)


@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=201,
    tags=["Students"],
    summary="Enroll a new student",
    responses={
        201: {"description": "Student created successfully"},
        409: {"description": "Email address already enrolled"},
        422: {"description": "Validation error -- check required fields"},
    },
)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    """
    Enroll a new student in the bootcamp.

    - **name**: Student's full legal name
    - **email**: Must be unique -- used as the student identifier
    - **track**: The bootcamp track (ai, data_science, web_dev, cybersecurity)
    - **cohort**: The cohort identifier (e.g. 2026-Q2)

    Returns the created student record with assigned ID and timestamp.
    Raises **409** if the email is already enrolled.
    """
    if db.query(Student).filter(Student.email == payload.email).first():
        raise HTTPException(status_code=409, detail=f"Email '{payload.email}' already enrolled")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get(
    "/students",
    response_model=list[StudentResponse],
    tags=["Students"],
    summary="List all students with optional filters",
    responses={200: {"description": "List of students matching the filter criteria"}},
)
def list_students(
    track: str | None = None,
    cohort: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Return all students, optionally filtered by track, cohort, or status.

    - **track**: Filter to a specific bootcamp track
    - **cohort**: Filter to a specific cohort (e.g. 2026-Q2)
    - **status**: Filter by lifecycle status (active, graduated, withdrawn)
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum records to return (max 100)
    """
    q = db.query(Student)
    if track:
        q = q.filter(Student.track == track)
    if cohort:
        q = q.filter(Student.cohort == cohort)
    if status:
        q = q.filter(Student.status == status)
    return q.offset(skip).limit(min(limit, 100)).all()


@app.get(
    "/students/{student_id}",
    response_model=StudentResponse,
    tags=["Students"],
    summary="Get a student by ID",
    responses={
        200: {"description": "Student record"},
        404: {"description": "Student not found"},
    },
)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """
    Return a single student by their numeric ID.

    Raises **404** if no student with the given ID exists.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return student


@app.patch(
    "/students/{student_id}",
    response_model=StudentResponse,
    tags=["Students"],
    summary="Update a student record",
    responses={
        200: {"description": "Updated student record"},
        404: {"description": "Student not found"},
    },
)
def patch_student(student_id: int, payload: StudentPatch, db: Session = Depends(get_db)):
    """
    Partially update a student record. Only provided fields are changed.

    Common use cases:
    - Promote to `graduated` at cohort completion
    - Update `track` if a student switches programs
    - Correct a name or cohort identifier
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.delete(
    "/students/{student_id}",
    status_code=204,
    tags=["Students"],
    summary="Remove a student record",
    responses={
        204: {"description": "Student deleted successfully"},
        404: {"description": "Student not found"},
    },
)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """
    Permanently delete a student record.

    This action cannot be undone. Consider updating status to
    `withdrawn` instead if you need to preserve the record.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    db.delete(student)
    db.commit()


@app.get("/", tags=["Health"], summary="API health check")
def root():
    """Return API status. No authentication required."""
    return {
        "status": "ok",
        "api": "Coding Temple Student API",
        "version": "1.0.0",
        "docs": "/docs",
    }
