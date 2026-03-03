"""
Span model — individual operation within an agent run.
OTel-aligned with custom AI semantic conventions.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, Text, text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SpanKind(str, PyEnum):
    """OpenTelemetry-aligned span kinds for AI agents."""
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    RETRIEVER = "retriever"
    CHAIN = "chain"
    EMBEDDING = "embedding"
    RERANKER = "reranker"


class Span(Base):
    """
    A single span within an agent run.
    Represents one operation: LLM call, tool invocation, retrieval, etc.
    """

    __tablename__ = "spans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_span_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Identity ─────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    span_kind: Mapped[SpanKind] = mapped_column(
        Enum(SpanKind, name="span_kind"),
        nullable=False,
        index=True,
    )

    # ── I/O ──────────────────────────────────────────
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── LLM-specific ─────────────────────────────────
    model: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    tokens_prompt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_completion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Performance ──────────────────────────────────
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Error ────────────────────────────────────────
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Metadata ─────────────────────────────────────
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # ── Timestamps ───────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────
    run = relationship("Run", back_populates="spans")
    parent = relationship("Span", remote_side="Span.id", lazy="selectin")
    cost_records = relationship("CostRecord", back_populates="span", lazy="selectin")
    evaluations = relationship("Evaluation", back_populates="span", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Span(id={self.id}, name={self.name}, kind={self.span_kind})>"
