"""
models/decision.py

Decision model -- the primary analyst-owned resource.
One decision per analyst per ticker (unique constraint).
Decisions are never hard-deleted; status transitions to 'closed'.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        UniqueConstraint("analyst_id", "ticker", name="uq_analyst_ticker"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    analyst_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)        # long / short / watch
    conviction: Mapped[str] = mapped_column(String(10), nullable=False)       # high / medium / low
    status: Mapped[str] = mapped_column(String(20), default="active")         # active / closed / watchlist
    thesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_target: Mapped[float | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    analyst: Mapped["User"] = relationship("User", lazy="select")  # type: ignore
