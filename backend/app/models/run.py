"""
Run model — represents a single agent execution session.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, Text, text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunStatus(str, PyEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Run(Base):
    """A single agent run (execution session)."""

    __tablename__ = "runs"

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
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status"),
        default=RunStatus.RUNNING,
        index=True,
    )
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Aggregated metrics ───────────────────────────
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_spans: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Metadata ─────────────────────────────────────
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    # ── Timestamps ───────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # ── Relationships ────────────────────────────────
    organization = relationship("Organization", back_populates="runs")
    spans = relationship("Span", back_populates="run", lazy="selectin",
                         cascade="all, delete-orphan")
    cost_records = relationship("CostRecord", back_populates="run", lazy="selectin",
                                cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="run", lazy="selectin",
                               cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Run(id={self.id}, agent={self.agent_name}, status={self.status})>"
