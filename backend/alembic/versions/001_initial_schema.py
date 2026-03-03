"""Initial schema — all 7 tables

Revision ID: 001
Revises: None
Create Date: 2026-03-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Organizations ────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("api_key", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("plan", sa.String(32), server_default="free"),
        sa.Column("settings", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Runs ─────────────────────────────────────────
    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_name", sa.String(255), nullable=False, index=True),
        sa.Column("status", sa.Enum("running", "completed", "failed", "timeout", name="run_status"), server_default="running"),
        sa.Column("input_text", sa.Text, nullable=True),
        sa.Column("output_text", sa.Text, nullable=True),
        sa.Column("total_tokens", sa.Integer, server_default="0"),
        sa.Column("total_cost", sa.Float, server_default="0.0"),
        sa.Column("total_spans", sa.Integer, server_default="0"),
        sa.Column("latency_ms", sa.Float, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("error_type", sa.String(128), nullable=True),
        sa.Column("metadata_", postgresql.JSONB, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Spans ────────────────────────────────────────
    op.create_table(
        "spans",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("parent_span_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("span_kind", sa.Enum("agent", "llm", "tool", "retriever", "chain", "embedding", "reranker", "guardrail", name="span_kind"), nullable=False),
        sa.Column("input_data", sa.Text, nullable=True),
        sa.Column("output_data", sa.Text, nullable=True),
        sa.Column("model", sa.String(128), nullable=True, index=True),
        sa.Column("tokens_prompt", sa.Integer, nullable=True),
        sa.Column("tokens_completion", sa.Integer, nullable=True),
        sa.Column("tokens_total", sa.Integer, nullable=True),
        sa.Column("cost", sa.Float, nullable=True),
        sa.Column("latency_ms", sa.Float, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("error_type", sa.String(128), nullable=True),
        sa.Column("attributes", postgresql.JSONB, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Cost Records ─────────────────────────────────
    op.create_table(
        "cost_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("span_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model", sa.String(128), nullable=False, index=True),
        sa.Column("tokens_prompt", sa.Integer, server_default="0"),
        sa.Column("tokens_completion", sa.Integer, server_default="0"),
        sa.Column("tokens_total", sa.Integer, server_default="0"),
        sa.Column("cost_prompt", sa.Float, server_default="0.0"),
        sa.Column("cost_completion", sa.Float, server_default="0.0"),
        sa.Column("cost_total", sa.Float, server_default="0.0"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Evaluations ──────────────────────────────────
    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("span_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("eval_type", sa.String(64), nullable=False, index=True),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("label", sa.String(32), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("evaluator", sa.String(64), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Guardrail Configs  ───────────────────────────
    op.create_table(
        "guardrail_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rule_type", sa.Enum("cost_limit", "loop_detection", "latency_budget", "quality_gate", "token_limit", name="rule_type"), nullable=False),
        sa.Column("threshold", sa.Float, nullable=False),
        sa.Column("action", sa.Enum("alert", "block", "kill", name="guardrail_action"), server_default="alert"),
        sa.Column("enabled", sa.Boolean, server_default="true"),
        sa.Column("config", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Alerts ───────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("guardrail_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guardrail_configs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_type", sa.String(64), nullable=False, index=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("severity", sa.Enum("info", "warning", "critical", name="alert_severity"), server_default="warning"),
        sa.Column("is_resolved", sa.Boolean, server_default="false"),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("guardrail_configs")
    op.drop_table("evaluations")
    op.drop_table("cost_records")
    op.drop_table("spans")
    op.drop_table("runs")
    op.drop_table("organizations")

    # Drop enum types
    for name in ["alert_severity", "guardrail_action", "rule_type", "span_kind", "run_status"]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
