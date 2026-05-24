"""
utils/background.py

Background task: log analyst activity asynchronously.
Never blocks the API response -- fires after the response is sent.
Seed of the nightly reconciliation audit trail.
"""
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.activity_log import ActivityLog


def log_activity(
    action: str,
    analyst_id: int | None = None,
    analyst_email: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
) -> None:
    """
    Write an activity log entry to the database.
    Called via FastAPI BackgroundTasks -- runs after the response is returned.
    Uses its own database session (independent of the request session).
    """
    db: Session = SessionLocal()
    try:
        entry = ActivityLog(
            analyst_id=analyst_id,
            analyst_email=analyst_email,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            detail=detail,
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
