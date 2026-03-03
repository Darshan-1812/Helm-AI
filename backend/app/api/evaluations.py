"""
Evaluations API — quality scoring and evaluation results.
"""

import uuid as uuid_mod
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_org_id
from app.models.evaluation import Evaluation, EvalType
from app.models.run import Run
from app.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationSummary,
    EvaluationListResponse,
)

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.get("", response_model=EvaluationListResponse)
async def list_evaluations(
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    run_id: Optional[uuid_mod.UUID] = Query(None),
    eval_type: Optional[str] = Query(None),
):
    """List evaluations with filtering."""
    query = select(Evaluation).where(Evaluation.org_id == org_id)

    if run_id:
        query = query.where(Evaluation.run_id == run_id)
    if eval_type:
        query = query.where(Evaluation.eval_type == EvalType(eval_type))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(desc(Evaluation.evaluated_at)).offset(offset).limit(page_size)

    result = await db.execute(query)
    evaluations = result.scalars().all()

    return EvaluationListResponse(
        evaluations=[EvaluationResponse.model_validate(e) for e in evaluations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary/{run_id}", response_model=EvaluationSummary)
async def get_evaluation_summary(
    run_id: uuid_mod.UUID,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated evaluation scores for a run."""
    # Get run
    run_result = await db.execute(
        select(Run).where(Run.id == run_id, Run.org_id == org_id)
    )
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Get average scores by type
    scores = {}
    for eval_type in ["hallucination", "faithfulness", "correctness", "relevance"]:
        result = await db.execute(
            select(func.avg(Evaluation.score))
            .where(
                Evaluation.run_id == run_id,
                Evaluation.org_id == org_id,
                Evaluation.eval_type == EvalType(eval_type),
            )
        )
        avg_score = result.scalar()
        scores[f"avg_{eval_type}"] = float(avg_score) if avg_score else None

    # Count total evaluations
    count_result = await db.execute(
        select(func.count(Evaluation.id))
        .where(Evaluation.run_id == run_id, Evaluation.org_id == org_id)
    )
    total = count_result.scalar() or 0

    return EvaluationSummary(
        run_id=run_id,
        agent_name=run.agent_name,
        total_evaluations=total,
        **scores,
    )


@router.post("/run", response_model=dict)
async def trigger_evaluation(
    payload: EvaluationRequest,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger evaluation on a run (placeholder — triggers Dramatiq worker in production)."""
    # Verify run exists
    run_result = await db.execute(
        select(Run).where(Run.id == payload.run_id, Run.org_id == org_id)
    )
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # In production, this dispatches to Dramatiq worker:
    # eval_worker.evaluate_run.send(str(payload.run_id), str(org_id), payload.eval_types)

    return {
        "message": "Evaluation triggered",
        "run_id": str(payload.run_id),
        "eval_types": payload.eval_types,
        "status": "queued",
    }
