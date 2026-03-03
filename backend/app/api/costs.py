"""
Cost Intelligence API — aggregated cost analytics with spike detection.
"""

import uuid as uuid_mod
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_org_id
from app.models.run import Run
from app.models.cost import CostRecord
from app.schemas.cost import (
    CostSummary,
    CostByAgent,
    CostByModel,
    CostSpike,
    CostSummaryResponse,
)

router = APIRouter(prefix="/costs", tags=["Cost Intelligence"])


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Get full cost intelligence: summary, by-agent, by-model, and spikes."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # ── Summary ──────────────────────────────────────
    summary_result = await db.execute(
        select(
            func.coalesce(func.sum(Run.total_cost), 0.0).label("total_cost"),
            func.coalesce(func.sum(Run.total_tokens), 0).label("total_tokens"),
            func.count(Run.id).label("total_runs"),
        )
        .where(Run.org_id == org_id, Run.started_at >= cutoff)
    )
    row = summary_result.one()
    total_runs = row.total_runs or 0
    summary = CostSummary(
        total_cost=float(row.total_cost),
        total_tokens=int(row.total_tokens),
        total_runs=total_runs,
        avg_cost_per_run=float(row.total_cost) / max(total_runs, 1),
        period_start=cutoff,
        period_end=datetime.now(timezone.utc),
    )

    # ── By Agent ─────────────────────────────────────
    agent_result = await db.execute(
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
    by_agent = [
        CostByAgent(
            agent_name=r.agent_name,
            total_cost=float(r.total_cost or 0),
            total_tokens=int(r.total_tokens or 0),
            run_count=r.run_count,
            avg_cost_per_run=float(r.total_cost or 0) / max(r.run_count, 1),
        )
        for r in agent_result.all()
    ]

    # ── By Model ─────────────────────────────────────
    model_result = await db.execute(
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
    by_model = [
        CostByModel(
            model=r.model,
            total_cost=float(r.total_cost or 0),
            total_tokens=int(r.total_tokens or 0),
            call_count=r.call_count,
        )
        for r in model_result.all()
    ]

    # ── Spike Detection ──────────────────────────────
    # Runs that cost > 3x the average
    avg_cost = summary.avg_cost_per_run
    spike_threshold = max(avg_cost * 3, 0.01)  # at least $0.01

    spike_result = await db.execute(
        select(Run)
        .where(
            Run.org_id == org_id,
            Run.started_at >= cutoff,
            Run.total_cost > spike_threshold,
        )
        .order_by(desc(Run.total_cost))
        .limit(20)
    )
    spikes = [
        CostSpike(
            run_id=r.id,
            agent_name=r.agent_name,
            cost=r.total_cost,
            avg_cost=avg_cost,
            deviation=(r.total_cost - avg_cost) / max(avg_cost, 0.001),
            occurred_at=r.started_at,
        )
        for r in spike_result.scalars().all()
    ]

    return CostSummaryResponse(
        summary=summary,
        by_agent=by_agent,
        by_model=by_model,
        spikes=spikes,
    )


@router.get("/by-agent", response_model=list[CostByAgent])
async def get_cost_by_agent(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Get cost breakdown by agent name."""
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


@router.get("/by-model", response_model=list[CostByModel])
async def get_cost_by_model(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Get cost breakdown by LLM model."""
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
