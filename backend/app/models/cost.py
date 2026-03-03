"""
Cost record model — granular cost tracking per span/run.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CostRecord(Base):
    """Tracks cost for individual spans and aggregates for runs."""

    __tablename__ = "cost_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    span_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Cost data ────────────────────────────────────
    model: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    tokens_prompt: Mapped[int] = mapped_column(Integer, default=0)
    tokens_completion: Mapped[int] = mapped_column(Integer, default=0)
    tokens_total: Mapped[int] = mapped_column(Integer, default=0)
    cost_prompt: Mapped[float] = mapped_column(Float, default=0.0)
    cost_completion: Mapped[float] = mapped_column(Float, default=0.0)
    cost_total: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Timestamps ───────────────────────────────────
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # ── Relationships ────────────────────────────────
    run = relationship("Run", back_populates="cost_records")
    span = relationship("Span", back_populates="cost_records")

    def __repr__(self) -> str:
        return f"<CostRecord(id={self.id}, model={self.model}, cost={self.cost_total})>"
