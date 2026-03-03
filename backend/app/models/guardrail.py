"""
Guardrail & Alert models — active reliability enforcement.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, ForeignKey, DateTime, Boolean, Text, text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RuleType(str, PyEnum):
    """Types of guardrail rules."""
    COST_LIMIT = "cost_limit"
    LOOP_DETECTION = "loop_detection"
    LATENCY_BUDGET = "latency_budget"
    QUALITY_GATE = "quality_gate"
    TOKEN_LIMIT = "token_limit"


class GuardrailAction(str, PyEnum):
    """Actions to take when a guardrail fires."""
    ALERT = "alert"
    BLOCK = "block"
    KILL = "kill"


class AlertSeverity(str, PyEnum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class GuardrailConfig(Base):
    """Configurable guardrail rules per organization."""

    __tablename__ = "guardrail_configs"

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

    # ── Rule definition ──────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(
        Enum(RuleType, name="rule_type"), nullable=False
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    action: Mapped[GuardrailAction] = mapped_column(
        Enum(GuardrailAction, name="guardrail_action"),
        default=GuardrailAction.ALERT,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # ── Notification channels ────────────────────────
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notification_channels: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, default=list,
        comment='List of channel configs: [{"type": "slack", "webhook_url": "..."}, {"type": "email", "to": "..."}]',
    )

    # ── Timestamps ───────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<GuardrailConfig(name={self.name}, type={self.rule_type})>"


class Alert(Base):
    """Alerts fired by guardrails."""

    __tablename__ = "alerts"

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
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    guardrail_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guardrail_configs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Alert data ───────────────────────────────────
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity"),
        default=AlertSeverity.WARNING,
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # ── Timestamps ───────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity})>"
