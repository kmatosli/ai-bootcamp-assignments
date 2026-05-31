"""
Module 5 -- Assignment 06: Build a Library Search API

Demonstrates: query parameters, Enum filters, text search,
skip/limit pagination, sort_by parameter.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
from enum import Enum
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="Library Search API",
    description="Search and filter a book catalog with query parameters and pagination.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GenreEnum(str, Enum):
    fiction = "fiction"
    non_fiction = "non_fiction"
    science = "science"
    finance = "finance"
    healthcare = "healthcare"
    technology = "technology"


class Book(BaseModel):
    id: int
    title: str
    author: str
    genre: str
    year: int
    available: bool = True


# ---------------------------------------------------------------------------
# Sample data (in-memory catalog)
# Applied to Caduceus: books map to research reports and filings
# ---------------------------------------------------------------------------

BOOKS: list[dict] = [
    {"id": 1, "title": "The Innovator's Dilemma", "author": "Clayton Christensen", "genre": "finance", "year": 2011, "available": True},
    {"id": 2, "title": "Bad Pharma", "author": "Ben Goldacre", "genre": "healthcare", "year": 2013, "available": True},
    {"id": 3, "title": "The Emperor of All Maladies", "author": "Siddhartha Mukherjee", "genre": "healthcare", "year": 2010, "available": False},
    {"id": 4, "title": "Flash Boys", "author": "Michael Lewis", "genre": "finance", "year": 2014, "available": True},
    {"id": 5, "title": "The Big Short", "author": "Michael Lewis", "genre": "finance", "year": 2010, "available": True},
    {"id": 6, "title": "Python for Data Analysis", "author": "Wes McKinney", "genre": "technology", "year": 2022, "available": True},
    {"id": 7, "title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "genre": "science", "year": 2011, "available": False},
    {"id": 8, "title": "The Gene", "author": "Siddhartha Mukherjee", "genre": "healthcare", "year": 2016, "available": True},
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/books", response_model=list[Book], summary="Search the book catalog")
def search_books(
    search: str | None = Query(None, min_length=1, max_length=100, description="Search by title or author"),
    genre: GenreEnum | None = Query(None, description="Filter by genre"),
    min_year: int | None = Query(None, ge=1900, le=2100, description="Minimum publication year"),
    max_year: int | None = Query(None, ge=1900, le=2100, description="Maximum publication year"),
    available: bool | None = Query(None, description="Filter by availability"),
    sort_by: str = Query("id", description="Sort by: id, title, year"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(10, ge=1, le=50, description="Results per page, max 50"),
):
    """
    Search the book catalog with multiple optional filters.

    - **search**: partial match on title or author (case-insensitive)
    - **genre**: filter to a specific genre
    - **min_year / max_year**: filter by publication year range
    - **available**: filter by availability
    - **sort_by**: sort results by id, title, or year
    - **skip / limit**: paginate results
    """
    results = BOOKS.copy()

    if search:
        s = search.lower()
        results = [b for b in results if s in b["title"].lower() or s in b["author"].lower()]
    if genre:
        results = [b for b in results if b["genre"] == genre.value]
    if min_year is not None:
        results = [b for b in results if b["year"] >= min_year]
    if max_year is not None:
        results = [b for b in results if b["year"] <= max_year]
    if available is not None:
        results = [b for b in results if b["available"] == available]

    if sort_by == "title":
        results.sort(key=lambda b: b["title"])
    elif sort_by == "year":
        results.sort(key=lambda b: b["year"])

    return results[skip: skip + limit]


@app.get("/books/{book_id}", response_model=Book, summary="Get a book by ID")
def get_book(book_id: int):
    """Return a single book by ID."""
    from fastapi import HTTPException
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return book


@app.get("/")
def root():
    return {"message": "Library Search API", "total_books": len(BOOKS), "docs": "/docs"}
