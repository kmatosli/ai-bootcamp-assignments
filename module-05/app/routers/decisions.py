"""
routers/decisions.py

Decision endpoints -- the primary analyst-owned resource.

All endpoints are protected (require valid JWT).
Any analyst can read all decisions (firm-wide view).
Only the authoring analyst can PATCH/DELETE their own decision.

Endpoints:
  POST   /decisions                  -- create a decision
  GET    /decisions                  -- list with filters + pagination
  GET    /decisions/{id}             -- get a specific decision
  PUT    /decisions/{id}             -- full replacement update
  PATCH  /decisions/{id}            -- partial update
  DELETE /decisions/{id}            -- close (soft-delete guard on active decisions)
  POST   /decisions/{id}/suggest    -- AI-ready placeholder (RAG in Module 7)
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import DuplicateException, ForbiddenException, BadRequestException
from app.models.decision import Decision
from app.models.user import User
from app.schemas.decision import (
    DecisionCreate, DecisionUpdate, DecisionPatch,
    DecisionResponse, SuggestResponse,
)
from app.utils.auth import get_current_user
from app.utils.helpers import get_decision_or_404
from app.utils.background import log_activity

router = APIRouter(prefix="/decisions", tags=["Decisions"])


@router.post(
    "",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new investment decision",
    responses={
        409: {"description": "Decision for this ticker already exists for this analyst"},
        422: {"description": "Validation error"},
    },
)
def create_decision(
    payload: DecisionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new investment decision for the authenticated analyst.

    - **ticker**: 2-5 uppercase letters (e.g. PFE, ABBV, MRK)
    - **direction**: long, short, or watch
    - **conviction**: high, medium, or low
    - **thesis**: Optional free-text thesis (max 2000 chars)
    - **price_target**: Optional price target in USD
    - One decision per analyst per ticker -- raises 409 if duplicate
    """
    existing = (
        db.query(Decision)
        .filter(Decision.analyst_id == current_user.id, Decision.ticker == payload.ticker)
        .first()
    )
    if existing:
        raise DuplicateException("Decision", "ticker", payload.ticker)

    decision = Decision(
        analyst_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    background_tasks.add_task(
        log_activity,
        action="CREATE_DECISION",
        analyst_id=current_user.id,
        analyst_email=current_user.email,
        resource_type="decision",
        resource_id=decision.id,
        detail=f"ticker={decision.ticker} direction={decision.direction} conviction={decision.conviction}",
    )
    return decision


@router.get(
    "",
    response_model=list[DecisionResponse],
    summary="List decisions with optional filters",
)
def list_decisions(
    ticker: str | None = Query(None, min_length=1, max_length=5, description="Filter by ticker"),
    direction: str | None = Query(None, description="long / short / watch"),
    conviction: str | None = Query(None, description="high / medium / low"),
    status: str | None = Query(None, description="active / closed / watchlist"),
    analyst_id: int | None = Query(None, description="Filter by analyst (leave blank for all)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List investment decisions across the firm with optional filters.

    All authenticated analysts can see the full firm worklist.
    Use **analyst_id** to filter to a specific analyst's coverage.
    Results are paginated via **skip** and **limit** (max 100 per page).
    """
    q = db.query(Decision)
    if ticker:
        q = q.filter(Decision.ticker == ticker.upper())
    if direction:
        q = q.filter(Decision.direction == direction)
    if conviction:
        q = q.filter(Decision.conviction == conviction)
    if status:
        q = q.filter(Decision.status == status)
    if analyst_id:
        q = q.filter(Decision.analyst_id == analyst_id)
    return q.order_by(Decision.updated_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{decision_id}",
    response_model=DecisionResponse,
    summary="Get a specific decision by ID",
    responses={404: {"description": "Decision not found"}},
)
def get_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single investment decision by its ID.

    Any authenticated analyst can view any decision (firm-wide visibility).
    Raises 404 if the decision does not exist.
    """
    return get_decision_or_404(decision_id, db)


@router.put(
    "/{decision_id}",
    response_model=DecisionResponse,
    summary="Full replacement update of a decision",
    responses={
        403: {"description": "You can only update your own decisions"},
        404: {"description": "Decision not found"},
    },
)
def update_decision(
    decision_id: int,
    payload: DecisionUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fully replace a decision's content. All fields required.

    Only the authoring analyst can update a decision.
    Raises 403 if another analyst attempts to update.
    """
    decision = get_decision_or_404(decision_id, db)
    if decision.analyst_id != current_user.id:
        raise ForbiddenException("update another analyst's decision")

    for field, value in payload.model_dump().items():
        setattr(decision, field, value)
    db.commit()
    db.refresh(decision)

    background_tasks.add_task(
        log_activity,
        action="UPDATE_DECISION",
        analyst_id=current_user.id,
        analyst_email=current_user.email,
        resource_type="decision",
        resource_id=decision_id,
        detail=f"full update on ticker={decision.ticker}",
    )
    return decision


@router.patch(
    "/{decision_id}",
    response_model=DecisionResponse,
    summary="Partial update of a decision",
    responses={
        403: {"description": "You can only update your own decisions"},
        404: {"description": "Decision not found"},
    },
)
def patch_decision(
    decision_id: int,
    payload: DecisionPatch,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update a decision. Only provided fields are changed.

    Common use: update conviction or thesis after a catalyst event.
    Only the authoring analyst can patch a decision.
    """
    decision = get_decision_or_404(decision_id, db)
    if decision.analyst_id != current_user.id:
        raise ForbiddenException("update another analyst's decision")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(decision, field, value)
    db.commit()
    db.refresh(decision)

    background_tasks.add_task(
        log_activity,
        action="PATCH_DECISION",
        analyst_id=current_user.id,
        analyst_email=current_user.email,
        resource_type="decision",
        resource_id=decision_id,
        detail=f"fields updated: {list(payload.model_dump(exclude_unset=True).keys())}",
    )
    return decision


@router.delete(
    "/{decision_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Close a decision (soft guard on active decisions)",
    responses={
        400: {"description": "Cannot delete an active decision -- close it first"},
        403: {"description": "You can only delete your own decisions"},
        404: {"description": "Decision not found"},
    },
)
def delete_decision(
    decision_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a decision.

    Business logic guard: active decisions cannot be deleted directly.
    PATCH status to 'closed' or 'watchlist' first, then delete.
    Only the authoring analyst can delete a decision.
    """
    decision = get_decision_or_404(decision_id, db)
    if decision.analyst_id != current_user.id:
        raise ForbiddenException("delete another analyst's decision")
    if decision.status == "active":
        raise BadRequestException(
            "Cannot delete an active decision. "
            "PATCH status to 'closed' or 'watchlist' first."
        )

    db.delete(decision)
    db.commit()

    background_tasks.add_task(
        log_activity,
        action="DELETE_DECISION",
        analyst_id=current_user.id,
        analyst_email=current_user.email,
        resource_type="decision",
        resource_id=decision_id,
        detail=f"ticker={decision.ticker} was deleted",
    )


@router.post(
    "/{decision_id}/suggest",
    response_model=SuggestResponse,
    summary="AI-ready suggest endpoint (RAG placeholder)",
    responses={404: {"description": "Decision not found"}},
)
def suggest(
    decision_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return evidence-backed thesis suggestions for this decision.

    **Current status**: Placeholder -- returns a structured stub response.

    **Module 7**: This endpoint will connect to the pgvector evidence store
    and return relevant 10-K passages, earnings call excerpts, and FDA filings
    ranked by semantic similarity to the current thesis.

    **Module 8**: Will add Claude API integration for synthesis and citation.
    """
    decision = get_decision_or_404(decision_id, db)

    background_tasks.add_task(
        log_activity,
        action="SUGGEST_REQUEST",
        analyst_id=current_user.id,
        analyst_email=current_user.email,
        resource_type="decision",
        resource_id=decision_id,
    )

    return SuggestResponse(
        decision_id=decision.id,
        ticker=decision.ticker,
        suggestion=(
            f"Evidence retrieval for {decision.ticker} is not yet active. "
            "Module 7 will wire pgvector semantic search here, returning "
            "ranked 10-K passages, earnings call excerpts, and FDA filing references "
            "relevant to your current thesis."
        ),
        source="placeholder",
        note="This endpoint becomes the RAG retrieval gateway in Module 7.",
    )
