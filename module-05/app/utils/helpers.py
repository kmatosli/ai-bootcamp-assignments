"""
utils/helpers.py

Shared helper functions used across routers.
"""
from sqlalchemy.orm import Session

from app.exceptions import NotFoundException
from app.models.decision import Decision
from app.models.user import User


def get_decision_or_404(decision_id: int, db: Session) -> Decision:
    """Return Decision by id or raise NotFoundException (404)."""
    decision = db.get(Decision, decision_id)
    if decision is None:
        raise NotFoundException("Decision", decision_id)
    return decision


def get_user_or_404(user_id: int, db: Session) -> User:
    """Return User by id or raise NotFoundException (404)."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundException("User", user_id)
    return user
