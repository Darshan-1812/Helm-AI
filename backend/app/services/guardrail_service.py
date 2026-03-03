"""
Guardrail Service — business logic for checking runs against rules and creating alerts.
"""

import uuid as uuid_mod
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardrail import GuardrailConfig, Alert, RuleType, AlertSeverity
from app.models.run import Run

logger = logging.getLogger(__name__)


async def check_run_against_rules(
    db: AsyncSession, org_id: uuid_mod.UUID, run_id: uuid_mod.UUID
) -> list[Alert]:
    """
    Evaluate a completed run against all enabled guardrail rules.
    Creates Alert records for any violations.
    """
    # Fetch run
    result = await db.execute(select(Run).where(Run.id == run_id, Run.org_id == org_id))
    run = result.scalar_one_or_none()
    if not run:
        return []

    # Fetch enabled rules
    rules_result = await db.execute(
        select(GuardrailConfig).where(
            GuardrailConfig.org_id == org_id,
            GuardrailConfig.enabled == True,
        )
    )
    rules = rules_result.scalars().all()

    alerts_created = []

    for rule in rules:
        violation = _check_rule(run, rule)
        if violation:
            alert = await create_alert(
                db=db,
                org_id=org_id,
                run_id=run_id,
                guardrail_id=rule.id,
                alert_type=rule.rule_type.value,
                message=violation,
                severity=_severity_for_action(rule.action.value),
            )
            alerts_created.append(alert)
            logger.warning(f"Guardrail '{rule.name}' fired for run={run_id}: {violation}")

    return alerts_created


def _check_rule(run: Run, rule: GuardrailConfig) -> str | None:
    """Check a single rule against a run. Returns violation message or None."""
    if rule.rule_type == RuleType.COST_LIMIT:
        if (run.total_cost or 0) > rule.threshold:
            return (
                f"Cost ${run.total_cost:.4f} exceeds limit ${rule.threshold:.4f} "
                f"for agent '{run.agent_name}'"
            )

    elif rule.rule_type == RuleType.LOOP_DETECTION:
        if (run.total_spans or 0) > rule.threshold:
            return (
                f"Span count {run.total_spans} exceeds loop threshold {int(rule.threshold)} "
                f"for agent '{run.agent_name}'"
            )

    elif rule.rule_type == RuleType.LATENCY_BUDGET:
        if (run.latency_ms or 0) > rule.threshold:
            return (
                f"Latency {run.latency_ms:.0f}ms exceeds budget {rule.threshold:.0f}ms "
                f"for agent '{run.agent_name}'"
            )

    elif rule.rule_type == RuleType.TOKEN_LIMIT:
        if (run.total_tokens or 0) > rule.threshold:
            return (
                f"Token count {run.total_tokens} exceeds limit {int(rule.threshold)} "
                f"for agent '{run.agent_name}'"
            )

    return None


def _severity_for_action(action: str) -> AlertSeverity:
    """Map guardrail action to alert severity."""
    mapping = {
        "alert": AlertSeverity.WARNING,
        "block": AlertSeverity.CRITICAL,
        "kill": AlertSeverity.CRITICAL,
    }
    return mapping.get(action, AlertSeverity.WARNING)


async def create_alert(
    db: AsyncSession,
    org_id: uuid_mod.UUID,
    run_id: uuid_mod.UUID | None,
    guardrail_id: uuid_mod.UUID | None,
    alert_type: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.WARNING,
    details: dict | None = None,
) -> Alert:
    """Create and persist an alert."""
    alert = Alert(
        org_id=org_id,
        run_id=run_id,
        guardrail_id=guardrail_id,
        alert_type=alert_type,
        message=message,
        severity=severity,
        details=details or {},
    )
    db.add(alert)
    await db.flush()
    return alert
