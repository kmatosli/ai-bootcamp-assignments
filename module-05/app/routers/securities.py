"""
routers/securities.py

Securities endpoints -- read-only reference data.
The data pipeline owns writes; the API exposes reads only.
Prevents dual-write corruption of canonical reference data.

Endpoints:
  GET /securities        -- list with filters (sector, TA, search)
  GET /securities/{ticker} -- get a specific security
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import NotFoundException
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/securities", tags=["Securities"])


@router.get(
    "",
    summary="List Phase 1 universe securities with optional filters",
)
def list_securities(
    search: str | None = Query(None, min_length=1, max_length=10, description="Search by ticker or name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List securities in the Caduceus Phase 1 universe.

    Read-only -- the EDGAR pipeline owns all writes to this data.
    Optionally filter by **search** (matches ticker or company name).
    Paginate via **skip** and **limit**.
    """
    # Query the financial_facts table to derive the security list
    # (The formal security master table is a Phase 1+ deliverable)
    sql = text("""
        SELECT DISTINCT ticker,
               MIN(fiscal_year) as earliest_year,
               MAX(fiscal_year) as latest_year,
               COUNT(DISTINCT accession_number) as filing_count
        FROM financial_facts
        WHERE (:search IS NULL OR ticker ILIKE :search_pattern)
        GROUP BY ticker
        ORDER BY ticker
        LIMIT :limit OFFSET :skip
    """)
    result = db.execute(sql, {
        "search": search,
        "search_pattern": f"%{search}%" if search else None,
        "limit": limit,
        "skip": skip,
    }).mappings().all()

    return [dict(r) for r in result]


@router.get(
    "/{ticker}",
    summary="Get a specific security by ticker",
    responses={404: {"description": "Security not found"}},
)
def get_security(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return summary data for a specific security in the Phase 1 universe.

    Raises 404 if the ticker has no data in the financial_facts table.
    """
    ticker = ticker.upper()
    sql = text("""
        SELECT ticker,
               COUNT(DISTINCT accession_number) as filing_count,
               MIN(fiscal_year) as earliest_year,
               MAX(fiscal_year) as latest_year,
               COUNT(*) as fact_count
        FROM financial_facts
        WHERE ticker = :ticker
        GROUP BY ticker
    """)
    result = db.execute(sql, {"ticker": ticker}).mappings().first()
    if not result:
        raise NotFoundException("Security", ticker)
    return dict(result)
