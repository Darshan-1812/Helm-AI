"""
Cost Intelligence API — delegates to cost_service.
"""

import uuid as uuid_mod

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_org_id
from app.schemas.cost import (
    CostSummaryResponse,
    CostByAgent,
    CostByModel,
)
from app.services import cost_service

router = APIRouter(prefix="/costs", tags=["Cost Intelligence"])


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Get full cost intelligence: summary, by-agent, by-model, and spikes."""
    summary = await cost_service.get_summary(db, org_id, days)
    by_agent = await cost_service.get_by_agent(db, org_id, days)
    by_model = await cost_service.get_by_model(db, org_id, days)
    spikes = await cost_service.detect_spikes(db, org_id, days)

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
    return await cost_service.get_by_agent(db, org_id, days)


@router.get("/by-model", response_model=list[CostByModel])
async def get_cost_by_model(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Get cost breakdown by LLM model."""
    return await cost_service.get_by_model(db, org_id, days)
