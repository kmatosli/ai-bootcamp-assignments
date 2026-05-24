"""
schemas/decision.py

Pydantic schemas for Decision.
Separate schemas for Create, Update (partial), and Response.
Ticker validation: 2-5 uppercase letters.
"""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.schemas.common import DirectionEnum, ConvictionEnum, StatusEnum


class DecisionCreate(BaseModel):
    ticker: str = Field(..., min_length=2, max_length=5, description="Ticker symbol e.g. PFE, ABBV")
    direction: DirectionEnum
    conviction: ConvictionEnum
    thesis: str | None = Field(None, max_length=2000)
    price_target: float | None = Field(None, gt=0, le=10000)
    notes: str | None = Field(None, max_length=1000)

    @field_validator("ticker")
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.isalpha():
            raise ValueError("Ticker must contain only letters")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticker": "PFE",
                "direction": "long",
                "conviction": "high",
                "thesis": "Paxlovid revenue stabilizing; Vyndaqel ramp underappreciated by market.",
                "price_target": 32.50,
                "notes": "Watch Q3 earnings for GTN commentary.",
            }
        }
    }


class DecisionUpdate(BaseModel):
    """Full replacement update -- all fields required."""
    direction: DirectionEnum
    conviction: ConvictionEnum
    status: StatusEnum
    thesis: str | None = Field(None, max_length=2000)
    price_target: float | None = Field(None, gt=0, le=10000)
    notes: str | None = Field(None, max_length=1000)


class DecisionPatch(BaseModel):
    """Partial update -- all fields optional."""
    direction: DirectionEnum | None = None
    conviction: ConvictionEnum | None = None
    status: StatusEnum | None = None
    thesis: str | None = Field(None, max_length=2000)
    price_target: float | None = Field(None, gt=0, le=10000)
    notes: str | None = Field(None, max_length=1000)


class DecisionResponse(BaseModel):
    id: int
    analyst_id: int
    ticker: str
    direction: str
    conviction: str
    status: str
    thesis: str | None
    price_target: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "analyst_id": 1,
                "ticker": "PFE",
                "direction": "long",
                "conviction": "high",
                "status": "active",
                "thesis": "Paxlovid revenue stabilizing; Vyndaqel ramp underappreciated by market.",
                "price_target": 32.50,
                "notes": "Watch Q3 earnings for GTN commentary.",
                "created_at": "2026-05-21T10:00:00Z",
                "updated_at": "2026-05-21T10:00:00Z",
            }
        },
    }


class SuggestResponse(BaseModel):
    decision_id: int
    ticker: str
    suggestion: str
    source: str
    note: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "decision_id": 1,
                "ticker": "PFE",
                "suggestion": "RAG pipeline not yet active. Module 7 will wire pgvector + Claude API here.",
                "source": "placeholder",
                "note": "This endpoint will return evidence-backed thesis suggestions in Module 7.",
            }
        }
    }
