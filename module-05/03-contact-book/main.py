"""
Module 5 -- Assignment 03: Build a Validated Contact Book API

Demonstrates: Pydantic field validation, Enum fields, optional fields,
Create/Update/Response schema separation, 422 validation errors.

Run with: uvicorn main:app --reload
Visit:     http://localhost:8000/docs
"""
from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

app = FastAPI(
    title="Contact Book API",
    description="A validated contact book demonstrating Pydantic field validators and Enums.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ContactTypeEnum(str, Enum):
    analyst = "analyst"
    pm = "pm"
    investor = "investor"
    management = "management"


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(None, max_length=20)
    contact_type: ContactTypeEnum
    company: str = Field(..., min_length=1, max_length=100)
    notes: str | None = Field(None, max_length=500)

    @field_validator("phone")
    @classmethod
    def phone_digits_only(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            if not cleaned.isdigit():
                raise ValueError("Phone must contain only digits, spaces, hyphens, or parentheses")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Henrik Rhenman",
                "email": "henrik@rhenman.com",
                "phone": "+46-8-123-4567",
                "contact_type": "pm",
                "company": "Rhenman & Partners",
                "notes": "CIO and Founder",
            }
        }
    }


class ContactUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    contact_type: ContactTypeEnum | None = None
    company: str | None = Field(None, min_length=1, max_length=100)
    notes: str | None = Field(None, max_length=500)


class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    contact_type: str
    company: str
    notes: str | None


# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------

_db: dict[int, dict] = {}
_next_id = 1


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/contacts", response_model=ContactResponse, status_code=201,
          summary="Create a new contact")
def create_contact(payload: ContactCreate):
    """Create a new contact with full validation."""
    global _next_id
    contact = {"id": _next_id, **payload.model_dump()}
    _db[_next_id] = contact
    _next_id += 1
    return contact


@app.get("/contacts", response_model=list[ContactResponse],
         summary="List all contacts")
def list_contacts(contact_type: ContactTypeEnum | None = None):
    """List all contacts, optionally filtered by type."""
    contacts = list(_db.values())
    if contact_type:
        contacts = [c for c in contacts if c["contact_type"] == contact_type.value]
    return contacts


@app.get("/contacts/{contact_id}", response_model=ContactResponse,
         summary="Get a contact by ID")
def get_contact(contact_id: int):
    """Return a single contact by ID. Raises 404 if not found."""
    if contact_id not in _db:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return _db[contact_id]


@app.patch("/contacts/{contact_id}", response_model=ContactResponse,
           summary="Partially update a contact")
def update_contact(contact_id: int, payload: ContactUpdate):
    """Partially update a contact. Only provided fields are changed."""
    if contact_id not in _db:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        _db[contact_id][field] = value
    return _db[contact_id]


@app.delete("/contacts/{contact_id}", status_code=204,
            summary="Delete a contact")
def delete_contact(contact_id: int):
    """Delete a contact by ID."""
    if contact_id not in _db:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    del _db[contact_id]


@app.get("/")
def root():
    return {"message": "Contact Book API", "docs": "/docs"}
