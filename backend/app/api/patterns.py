"""
Patterns API — failure pattern detection endpoints.
"""

import uuid as uuid_mod

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_org_id
from app.services.pattern_service import detect_patterns

router = APIRouter(prefix="/patterns", tags=["Pattern Detection"])


@router.get("/detect")
async def get_detected_patterns(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=90),
):
    """
    Detect failure patterns across recent agent runs.

    Returns patterns sorted by severity:
    - repeated_error: Same error type occurring frequently
    - latency_increase: Agent latency trending upward
    - cost_creep: Average cost per run increasing
    - high_failure_rate: Agent failing > 30% of runs
    """
    patterns = await detect_patterns(db, org_id, days)
    return {
        "patterns": [p.to_dict() for p in patterns],
        "total": len(patterns),
        "period_days": days,
    }
