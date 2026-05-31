"""
Module 5 -- Assignment 05: Complete CRUD for a Student Database

Demonstrates: 6 CRUD endpoints, duplicate 409, 404 helper,
PUT full replace, PATCH partial update, DELETE 204.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
from datetime import datetime, timezone
from enum import Enum
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///./students.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    track: Mapped[str] = mapped_column(String(50), nullable=False)
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
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return student


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TrackEnum(str, Enum):
    ai = "ai"
    data_science = "data_science"
    web_dev = "web_dev"
    cybersecurity = "cybersecurity"


class StatusEnum(str, Enum):
    active = "active"
    graduated = "graduated"
    withdrawn = "withdrawn"


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    track: TrackEnum
    status: StatusEnum = StatusEnum.active

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Kathy Matosli",
                "email": "kmatosli@student.ct.edu",
                "track": "ai",
                "status": "active",
            }
        }
    }


class StudentUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    track: TrackEnum
    status: StatusEnum


class StudentPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    track: TrackEnum | None = None
    status: StatusEnum | None = None


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    track: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Student Database API",
    description="Complete CRUD for a student database with SQLAlchemy and SQLite.",
    version="0.1.0",
)

Base.metadata.create_all(bind=engine)


@app.post("/students", response_model=StudentResponse, status_code=201,
          summary="Create a student",
          responses={409: {"description": "Email already registered"}})
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student. Raises 409 if email already exists."""
    existing = db.query(Student).filter(Student.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Email '{payload.email}' already registered")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students", response_model=list[StudentResponse],
         summary="List all students")
def list_students(
    track: TrackEnum | None = None,
    status: StatusEnum | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List students with optional track/status filters and pagination."""
    q = db.query(Student)
    if track:
        q = q.filter(Student.track == track.value)
    if status:
        q = q.filter(Student.status == status.value)
    return q.offset(skip).limit(limit).all()


@app.get("/students/{student_id}", response_model=StudentResponse,
         summary="Get a student by ID",
         responses={404: {"description": "Student not found"}})
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Return a single student by ID."""
    return get_student_or_404(student_id, db)


@app.put("/students/{student_id}", response_model=StudentResponse,
         summary="Full replacement update",
         responses={404: {"description": "Student not found"}})
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    """Fully replace a student record. All fields required."""
    student = get_student_or_404(student_id, db)
    for field, value in payload.model_dump().items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.patch("/students/{student_id}", response_model=StudentResponse,
           summary="Partial update",
           responses={404: {"description": "Student not found"}})
def patch_student(student_id: int, payload: StudentPatch, db: Session = Depends(get_db)):
    """Partially update a student. Only provided fields are changed."""
    student = get_student_or_404(student_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.delete("/students/{student_id}", status_code=204,
            summary="Delete a student",
            responses={404: {"description": "Student not found"}})
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student by ID."""
    student = get_student_or_404(student_id, db)
    db.delete(student)
    db.commit()


@app.get("/")
def root():
    return {"message": "Student Database API", "docs": "/docs"}
