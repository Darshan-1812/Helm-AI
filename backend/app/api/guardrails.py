"""
Guardrails API — configure and manage guardrail rules.
"""

import uuid as uuid_mod
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_org_id
from app.models.guardrail import GuardrailConfig, Alert, RuleType, GuardrailAction, AlertSeverity
from app.schemas.evaluation import GuardrailConfigRequest, GuardrailConfigResponse, AlertResponse

router = APIRouter(prefix="/guardrails", tags=["Guardrails"])


# ── Guardrail Configs ────────────────────────────────

@router.get("/configs", response_model=list[GuardrailConfigResponse])
async def list_guardrails(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """List all guardrail configurations for the organization."""
    result = await db.execute(
        select(GuardrailConfig)
        .where(GuardrailConfig.org_id == org_id)
        .order_by(desc(GuardrailConfig.created_at))
    )
    configs = result.scalars().all()
    return [GuardrailConfigResponse.model_validate(c) for c in configs]


@router.post("/configs", response_model=GuardrailConfigResponse)
async def create_guardrail(
    payload: GuardrailConfigRequest,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new guardrail rule."""
    config = GuardrailConfig(
        org_id=org_id,
        name=payload.name,
        rule_type=RuleType(payload.rule_type),
        threshold=payload.threshold,
        action=GuardrailAction(payload.action),
        enabled=payload.enabled,
        config=payload.config,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return GuardrailConfigResponse.model_validate(config)


@router.put("/configs/{config_id}", response_model=GuardrailConfigResponse)
async def update_guardrail(
    config_id: uuid_mod.UUID,
    payload: GuardrailConfigRequest,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing guardrail rule."""
    result = await db.execute(
        select(GuardrailConfig)
        .where(GuardrailConfig.id == config_id, GuardrailConfig.org_id == org_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Guardrail config not found")

    config.name = payload.name
    config.rule_type = RuleType(payload.rule_type)
    config.threshold = payload.threshold
    config.action = GuardrailAction(payload.action)
    config.enabled = payload.enabled
    config.config = payload.config

    await db.flush()
    await db.refresh(config)
    return GuardrailConfigResponse.model_validate(config)


@router.delete("/configs/{config_id}")
async def delete_guardrail(
    config_id: uuid_mod.UUID,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a guardrail rule."""
    result = await db.execute(
        select(GuardrailConfig)
        .where(GuardrailConfig.id == config_id, GuardrailConfig.org_id == org_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Guardrail config not found")

    await db.delete(config)
    return {"message": "Guardrail deleted successfully"}


# ── Alerts ───────────────────────────────────────────

@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    resolved: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List alerts with optional filtering."""
    query = select(Alert).where(Alert.org_id == org_id)

    if resolved is not None:
        query = query.where(Alert.is_resolved == resolved)
    if severity:
        query = query.where(Alert.severity == AlertSeverity(severity))

    query = query.order_by(desc(Alert.created_at)).limit(limit)

    result = await db.execute(query)
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: uuid_mod.UUID,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as resolved."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.org_id == org_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    return {"message": "Alert resolved"}
