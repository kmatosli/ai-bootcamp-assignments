"""
Module 5 -- Assignment 04: Database-Backed Notes API

Demonstrates: SQLAlchemy model, SQLite database, session dependency,
persistent storage across restarts.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///./notes.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
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
# Schemas
# ---------------------------------------------------------------------------

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "PFE Q2 2026 Earnings Notes",
                "content": "Vyndaqel beat by 12%. Guidance raised. Paxlovid inline.",
            }
        }
    }


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Notes API",
    description="A database-backed notes API using SQLAlchemy and SQLite.",
    version="0.1.0",
)

Base.metadata.create_all(bind=engine)


@app.post("/notes", response_model=NoteResponse, status_code=201,
          summary="Create a note")
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note and persist it to SQLite."""
    note = Note(**payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@app.get("/notes", response_model=list[NoteResponse],
         summary="List all notes")
def list_notes(db: Session = Depends(get_db)):
    """Return all notes from the database."""
    return db.query(Note).all()


@app.get("/notes/{note_id}", response_model=NoteResponse,
         summary="Get a note by ID")
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Return a single note by ID."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    return note


@app.delete("/notes/{note_id}", status_code=204,
            summary="Delete a note")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note by ID."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    db.delete(note)
    db.commit()


@app.get("/")
def root():
    return {"message": "Notes API (SQLite-backed)", "docs": "/docs"}
