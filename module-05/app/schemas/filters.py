"""
schemas/filters.py

Query parameter schemas for list endpoints.
Used for worklist screening and universe filtering.
"""
from pydantic import BaseModel, Field
from app.schemas.common import ConvictionEnum, StatusEnum, DirectionEnum


class DecisionFilters(BaseModel):
    ticker: str | None = Field(None, min_length=1, max_length=5, description="Filter by ticker symbol")
    direction: DirectionEnum | None = None
    conviction: ConvictionEnum | None = None
    status: StatusEnum | None = None
    analyst_id: int | None = None
    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(20, ge=1, le=100, description="Results per page, max 100")


class SecurityFilters(BaseModel):
    sector: str | None = Field(None, max_length=100)
    therapeutic_area: str | None = Field(None, max_length=100)
    universe_phase: str | None = Field(None, max_length=20)
    search: str | None = Field(None, min_length=1, max_length=100, description="Search by ticker or name")
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
