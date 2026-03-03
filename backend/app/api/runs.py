"""
Runs API — list, filter, and retrieve agent runs with full trace detail.
"""

import uuid as uuid_mod
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.api.auth import get_org_id
from app.models.run import Run, RunStatus
from app.models.span import Span
from app.schemas.trace import RunResponse, RunDetailResponse, RunListResponse, SpanResponse

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("", response_model=RunListResponse)
async def list_runs(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    agent_name: Optional[str] = Query(None),
    min_cost: Optional[float] = Query(None),
    max_cost: Optional[float] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    """List runs with filtering, pagination, and sorting."""

    query = select(Run).where(Run.org_id == org_id)

    # ── Filters ──────────────────────────────────────
    if status:
        query = query.where(Run.status == RunStatus(status))
    if agent_name:
        query = query.where(Run.agent_name.ilike(f"%{agent_name}%"))
    if min_cost is not None:
        query = query.where(Run.total_cost >= min_cost)
    if max_cost is not None:
        query = query.where(Run.total_cost <= max_cost)
    if date_from:
        query = query.where(Run.started_at >= date_from)
    if date_to:
        query = query.where(Run.started_at <= date_to)

    # ── Count total ──────────────────────────────────
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # ── Sort ─────────────────────────────────────────
    sort_column = getattr(Run, sort_by, Run.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # ── Paginate ─────────────────────────────────────
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    runs = result.scalars().all()

    return RunListResponse(
        runs=[RunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run(
    run_id: uuid_mod.UUID,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single run with all its spans (trace timeline)."""

    result = await db.execute(
        select(Run)
        .where(Run.id == run_id, Run.org_id == org_id)
        .options(selectinload(Run.spans))
    )
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    # Sort spans by started_at for timeline view
    sorted_spans = sorted(run.spans, key=lambda s: s.started_at or datetime.min)

    run_data = RunDetailResponse.model_validate(run)
    run_data.spans = [SpanResponse.model_validate(s) for s in sorted_spans]

    return run_data


@router.delete("/{run_id}")
async def delete_run(
    run_id: uuid_mod.UUID,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a run and all its associated data."""

    result = await db.execute(
        select(Run).where(Run.id == run_id, Run.org_id == org_id)
    )
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    await db.delete(run)
    return {"message": "Run deleted successfully"}
