"""
Module 5 -- Assignment 09: Write Tests for Your Student API

The main application -- identical to 05-student-crud but
structured for pytest with TestClient.

Run tests: pytest tests/ -v
Run app:   uvicorn main:app --reload
"""
from datetime import datetime, timezone
from enum import Enum
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

DATABASE_URL = "sqlite:///./students_test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
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


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    track: str = Field(..., min_length=2, max_length=50)


class StudentPatch(BaseModel):
    name: str | None = None
    track: str | None = None
    status: str | None = None


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    track: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


app = FastAPI(title="Student API with Tests", version="0.1.0")

Base.metadata.create_all(bind=engine)


@app.post("/students", response_model=StudentResponse, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students", response_model=list[StudentResponse])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).all()


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return get_student_or_404(student_id, db)


@app.patch("/students/{student_id}", response_model=StudentResponse)
def patch_student(student_id: int, payload: StudentPatch, db: Session = Depends(get_db)):
    student = get_student_or_404(student_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = get_student_or_404(student_id, db)
    db.delete(student)
    db.commit()
