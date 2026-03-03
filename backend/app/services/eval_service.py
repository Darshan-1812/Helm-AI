"""
Evaluation Service — business logic for quality scoring.
"""

import uuid as uuid_mod
from datetime import datetime, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.span import Span


async def list_evaluations(
    db: AsyncSession,
    org_id: uuid_mod.UUID,
    run_id: uuid_mod.UUID | None = None,
    eval_type: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list, int]:
    """
    List evaluations with optional filtering.
    Returns (evaluations, total_count).
    """
    query = select(Evaluation).where(Evaluation.org_id == org_id)
    count_query = select(func.count(Evaluation.id)).where(Evaluation.org_id == org_id)

    if run_id:
        query = query.where(Evaluation.run_id == run_id)
        count_query = count_query.where(Evaluation.run_id == run_id)
    if eval_type:
        query = query.where(Evaluation.eval_type == eval_type)
        count_query = count_query.where(Evaluation.eval_type == eval_type)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(desc(Evaluation.evaluated_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all(), total


async def get_run_summary(
    db: AsyncSession, org_id: uuid_mod.UUID, run_id: uuid_mod.UUID
) -> dict:
    """Get average scores per eval_type for a run."""
    result = await db.execute(
        select(
            Evaluation.eval_type,
            func.avg(Evaluation.score).label("avg_score"),
            func.count(Evaluation.id).label("count"),
        )
        .where(Evaluation.org_id == org_id, Evaluation.run_id == run_id)
        .group_by(Evaluation.eval_type)
    )
    return {
        r.eval_type: {"avg_score": round(float(r.avg_score), 4), "count": r.count}
        for r in result.all()
    }


async def save_evaluation(
    db: AsyncSession,
    org_id: uuid_mod.UUID,
    run_id: uuid_mod.UUID,
    eval_type: str,
    score: float,
    evaluator: str = "system",
    label: str | None = None,
    reason: str | None = None,
    span_id: uuid_mod.UUID | None = None,
    details: dict | None = None,
) -> Evaluation:
    """Save a single evaluation result."""
    evaluation = Evaluation(
        org_id=org_id,
        run_id=run_id,
        span_id=span_id,
        eval_type=eval_type,
        score=score,
        label=label or ("pass" if score >= 0.7 else "fail"),
        reason=reason,
        evaluator=evaluator,
        details=details or {},
    )
    db.add(evaluation)
    await db.flush()
    return evaluation
