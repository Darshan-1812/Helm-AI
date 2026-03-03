"""
Evaluation model — quality scoring for agent responses.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, ForeignKey, DateTime, Text, text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EvalType(str, PyEnum):
    """Types of quality evaluation."""
    HALLUCINATION = "hallucination"
    FAITHFULNESS = "faithfulness"
    CORRECTNESS = "correctness"
    RELEVANCE = "relevance"
    TOXICITY = "toxicity"
    CUSTOM = "custom"


class Evaluation(Base):
    """Quality evaluation result for a span or run."""

    __tablename__ = "evaluations"

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

    # ── Evaluation data ──────────────────────────────
    eval_type: Mapped[EvalType] = mapped_column(
        Enum(EvalType, name="eval_type"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # ── Timestamps ───────────────────────────────────
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # ── Relationships ────────────────────────────────
    run = relationship("Run", back_populates="evaluations")
    span = relationship("Span", back_populates="evaluations")

    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, type={self.eval_type}, score={self.score})>"
