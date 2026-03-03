"""
Pattern Detection Service — identifies failure patterns across agent runs.

Detects:
- Repeated errors (same error_type/agent)
- Increasing latency trends
- Cost creep over time
- Stuck agents (high span counts)
"""

import uuid as uuid_mod
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.models.span import Span

logger = logging.getLogger(__name__)


class Pattern:
    """Represents a detected failure pattern."""

    def __init__(
        self,
        pattern_type: str,
        severity: str,
        title: str,
        description: str,
        agent_name: str | None = None,
        affected_runs: int = 0,
        details: dict | None = None,
    ):
        self.pattern_type = pattern_type
        self.severity = severity
        self.title = title
        self.description = description
        self.agent_name = agent_name
        self.affected_runs = affected_runs
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "agent_name": self.agent_name,
            "affected_runs": self.affected_runs,
            "details": self.details,
        }


async def detect_patterns(
    db: AsyncSession,
    org_id: uuid_mod.UUID,
    days: int = 7,
) -> list[Pattern]:
    """
    Detect failure patterns across recent runs.
    Returns a list of Pattern objects sorted by severity.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    patterns: list[Pattern] = []

    # ── 1. Repeated Errors ───────────────────────────
    error_patterns = await _detect_repeated_errors(db, org_id, cutoff)
    patterns.extend(error_patterns)

    # ── 2. Latency Trends ────────────────────────────
    latency_patterns = await _detect_latency_trends(db, org_id, cutoff)
    patterns.extend(latency_patterns)

    # ── 3. Cost Creep ────────────────────────────────
    cost_patterns = await _detect_cost_creep(db, org_id, cutoff)
    patterns.extend(cost_patterns)

    # ── 4. Failure Rate Spikes ───────────────────────
    failure_patterns = await _detect_failure_spikes(db, org_id, cutoff)
    patterns.extend(failure_patterns)

    # Sort by severity: critical > warning > info
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    patterns.sort(key=lambda p: severity_order.get(p.severity, 9))

    return patterns


async def _detect_repeated_errors(
    db: AsyncSession, org_id: uuid_mod.UUID, cutoff: datetime
) -> list[Pattern]:
    """Find error types that occur repeatedly in the same agent."""
    result = await db.execute(
        select(
            Span.error_type,
            Run.agent_name,
            func.count(Span.id).label("error_count"),
        )
        .join(Run, Span.run_id == Run.id)
        .where(
            Span.org_id == org_id,
            Span.error.isnot(None),
            Span.error_type.isnot(None),
            Run.started_at >= cutoff,
        )
        .group_by(Span.error_type, Run.agent_name)
        .having(func.count(Span.id) >= 3)
        .order_by(desc("error_count"))
        .limit(10)
    )

    patterns = []
    for row in result.all():
        severity = "critical" if row.error_count >= 10 else "warning"
        patterns.append(
            Pattern(
                pattern_type="repeated_error",
                severity=severity,
                title=f"Repeated {row.error_type} errors",
                description=(
                    f"Agent '{row.agent_name}' has encountered {row.error_count} "
                    f"'{row.error_type}' errors in the last {(datetime.now(timezone.utc) - cutoff).days} days"
                ),
                agent_name=row.agent_name,
                affected_runs=row.error_count,
                details={"error_type": row.error_type, "count": row.error_count},
            )
        )
    return patterns


async def _detect_latency_trends(
    db: AsyncSession, org_id: uuid_mod.UUID, cutoff: datetime
) -> list[Pattern]:
    """Detect agents with increasing average latency."""
    midpoint = cutoff + (datetime.now(timezone.utc) - cutoff) / 2

    # First half average
    first_half = await db.execute(
        select(
            Run.agent_name,
            func.avg(Run.latency_ms).label("avg_latency"),
            func.count(Run.id).label("run_count"),
        )
        .where(Run.org_id == org_id, Run.started_at >= cutoff, Run.started_at < midpoint, Run.latency_ms.isnot(None))
        .group_by(Run.agent_name)
        .having(func.count(Run.id) >= 3)
    )
    first_data = {r.agent_name: (float(r.avg_latency), r.run_count) for r in first_half.all()}

    # Second half average
    second_half = await db.execute(
        select(
            Run.agent_name,
            func.avg(Run.latency_ms).label("avg_latency"),
            func.count(Run.id).label("run_count"),
        )
        .where(Run.org_id == org_id, Run.started_at >= midpoint, Run.latency_ms.isnot(None))
        .group_by(Run.agent_name)
        .having(func.count(Run.id) >= 3)
    )

    patterns = []
    for row in second_half.all():
        agent = row.agent_name
        if agent in first_data:
            old_avg, _ = first_data[agent]
            new_avg = float(row.avg_latency)
            if old_avg > 0 and new_avg > old_avg * 1.5:  # 50%+ increase
                increase_pct = ((new_avg - old_avg) / old_avg) * 100
                severity = "critical" if increase_pct > 100 else "warning"
                patterns.append(
                    Pattern(
                        pattern_type="latency_increase",
                        severity=severity,
                        title=f"Latency increase for {agent}",
                        description=(
                            f"Average latency increased {increase_pct:.0f}% "
                            f"({old_avg:.0f}ms → {new_avg:.0f}ms)"
                        ),
                        agent_name=agent,
                        details={
                            "old_avg_ms": old_avg,
                            "new_avg_ms": new_avg,
                            "increase_pct": increase_pct,
                        },
                    )
                )
    return patterns


async def _detect_cost_creep(
    db: AsyncSession, org_id: uuid_mod.UUID, cutoff: datetime
) -> list[Pattern]:
    """Detect agents with steadily increasing costs per run."""
    midpoint = cutoff + (datetime.now(timezone.utc) - cutoff) / 2

    first_half = await db.execute(
        select(
            Run.agent_name,
            func.avg(Run.total_cost).label("avg_cost"),
        )
        .where(Run.org_id == org_id, Run.started_at >= cutoff, Run.started_at < midpoint)
        .group_by(Run.agent_name)
        .having(func.count(Run.id) >= 3)
    )
    first_data = {r.agent_name: float(r.avg_cost) for r in first_half.all()}

    second_half = await db.execute(
        select(
            Run.agent_name,
            func.avg(Run.total_cost).label("avg_cost"),
        )
        .where(Run.org_id == org_id, Run.started_at >= midpoint)
        .group_by(Run.agent_name)
        .having(func.count(Run.id) >= 3)
    )

    patterns = []
    for row in second_half.all():
        agent = row.agent_name
        if agent in first_data:
            old_avg = first_data[agent]
            new_avg = float(row.avg_cost)
            if old_avg > 0 and new_avg > old_avg * 1.3:  # 30%+ increase
                increase_pct = ((new_avg - old_avg) / old_avg) * 100
                patterns.append(
                    Pattern(
                        pattern_type="cost_creep",
                        severity="warning",
                        title=f"Cost creep for {agent}",
                        description=(
                            f"Average cost per run increased {increase_pct:.0f}% "
                            f"(${old_avg:.4f} → ${new_avg:.4f})"
                        ),
                        agent_name=agent,
                        details={
                            "old_avg_cost": old_avg,
                            "new_avg_cost": new_avg,
                            "increase_pct": increase_pct,
                        },
                    )
                )
    return patterns


async def _detect_failure_spikes(
    db: AsyncSession, org_id: uuid_mod.UUID, cutoff: datetime
) -> list[Pattern]:
    """Detect agents with high failure rates."""
    result = await db.execute(
        select(
            Run.agent_name,
            func.count(Run.id).label("total"),
            func.sum(
                func.cast(Run.status == RunStatus.FAILED, type_=func.count(Run.id).type)
            ).label("failed"),
        )
        .where(Run.org_id == org_id, Run.started_at >= cutoff)
        .group_by(Run.agent_name)
        .having(func.count(Run.id) >= 5)
    )

    patterns = []
    for row in result.all():
        total = row.total
        failed = row.failed or 0
        if total > 0:
            failure_rate = failed / total
            if failure_rate >= 0.3:  # 30%+ failure rate
                severity = "critical" if failure_rate >= 0.5 else "warning"
                patterns.append(
                    Pattern(
                        pattern_type="high_failure_rate",
                        severity=severity,
                        title=f"High failure rate for {row.agent_name}",
                        description=(
                            f"{failed}/{total} runs failed ({failure_rate:.0%} failure rate)"
                        ),
                        agent_name=row.agent_name,
                        affected_runs=failed,
                        details={
                            "total_runs": total,
                            "failed_runs": failed,
                            "failure_rate": failure_rate,
                        },
                    )
                )
    return patterns
