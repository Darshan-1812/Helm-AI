"""
Cost Service — business logic for cost aggregation and spike detection.
"""

import uuid as uuid_mod
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.cost import CostRecord
from app.schemas.cost import CostSummary, CostByAgent, CostByModel, CostSpike


async def get_summary(
    db: AsyncSession, org_id: uuid_mod.UUID, days: int = 30
) -> CostSummary:
    """Get aggregated cost summary for a time window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.coalesce(func.sum(Run.total_cost), 0.0).label("total_cost"),
            func.coalesce(func.sum(Run.total_tokens), 0).label("total_tokens"),
            func.count(Run.id).label("total_runs"),
        ).where(Run.org_id == org_id, Run.started_at >= cutoff)
    )
    row = result.one()
    total_runs = row.total_runs or 0

    return CostSummary(
        total_cost=float(row.total_cost),
        total_tokens=int(row.total_tokens),
        total_runs=total_runs,
        avg_cost_per_run=float(row.total_cost) / max(total_runs, 1),
        period_start=cutoff,
        period_end=datetime.now(timezone.utc),
    )


async def get_by_agent(
    db: AsyncSession, org_id: uuid_mod.UUID, days: int = 30
) -> list[CostByAgent]:
    """Cost breakdown grouped by agent name."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            Run.agent_name,
            func.sum(Run.total_cost).label("total_cost"),
            func.sum(Run.total_tokens).label("total_tokens"),
            func.count(Run.id).label("run_count"),
        )
        .where(Run.org_id == org_id, Run.started_at >= cutoff)
        .group_by(Run.agent_name)
        .order_by(desc("total_cost"))
    )
    return [
        CostByAgent(
            agent_name=r.agent_name,
            total_cost=float(r.total_cost or 0),
            total_tokens=int(r.total_tokens or 0),
            run_count=r.run_count,
            avg_cost_per_run=float(r.total_cost or 0) / max(r.run_count, 1),
        )
        for r in result.all()
    ]


async def get_by_model(
    db: AsyncSession, org_id: uuid_mod.UUID, days: int = 30
) -> list[CostByModel]:
    """Cost breakdown grouped by LLM model."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            CostRecord.model,
            func.sum(CostRecord.cost_total).label("total_cost"),
            func.sum(CostRecord.tokens_total).label("total_tokens"),
            func.count(CostRecord.id).label("call_count"),
        )
        .where(CostRecord.org_id == org_id, CostRecord.recorded_at >= cutoff)
        .group_by(CostRecord.model)
        .order_by(desc("total_cost"))
    )
    return [
        CostByModel(
            model=r.model,
            total_cost=float(r.total_cost or 0),
            total_tokens=int(r.total_tokens or 0),
            call_count=r.call_count,
        )
        for r in result.all()
    ]


async def detect_spikes(
    db: AsyncSession, org_id: uuid_mod.UUID, days: int = 30, multiplier: float = 3.0
) -> list[CostSpike]:
    """Find runs costing > multiplier × average (cost spikes)."""
    summary = await get_summary(db, org_id, days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    threshold = max(summary.avg_cost_per_run * multiplier, 0.01)

    result = await db.execute(
        select(Run)
        .where(Run.org_id == org_id, Run.started_at >= cutoff, Run.total_cost > threshold)
        .order_by(desc(Run.total_cost))
        .limit(20)
    )
    return [
        CostSpike(
            run_id=r.id,
            agent_name=r.agent_name,
            cost=r.total_cost,
            avg_cost=summary.avg_cost_per_run,
            deviation=(r.total_cost - summary.avg_cost_per_run) / max(summary.avg_cost_per_run, 0.001),
            occurred_at=r.started_at,
        )
        for r in result.scalars().all()
    ]
