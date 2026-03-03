"""
Trace ingestion API — receives spans from the SDK.
"""

import uuid as uuid_mod
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_org_id
from app.models.run import Run, RunStatus
from app.models.span import Span, SpanKind
from app.models.cost import CostRecord
from app.schemas.trace import TraceIngestRequest, TraceIngestResponse

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/traces", response_model=TraceIngestResponse)
async def ingest_traces(
    payload: TraceIngestRequest,
    org_id: uuid_mod.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a complete agent run with all its spans.
    Called by the SDK after an agent execution completes.
    """
    try:
        # ── Create or update the Run ─────────────────
        run_id = payload.run_id or uuid_mod.uuid4()

        # Calculate aggregated metrics from spans
        total_tokens = sum(s.tokens_total or 0 for s in payload.spans)
        total_cost = sum(s.cost or 0.0 for s in payload.spans)

        # Calculate latency
        latency_ms = None
        if payload.started_at and payload.ended_at:
            delta = payload.ended_at - payload.started_at
            latency_ms = delta.total_seconds() * 1000

        run = Run(
            id=run_id,
            org_id=org_id,
            agent_name=payload.agent_name,
            status=RunStatus(payload.status) if payload.status else RunStatus.COMPLETED,
            input_text=payload.input_text,
            output_text=payload.output_text,
            total_tokens=total_tokens,
            total_cost=total_cost,
            total_spans=len(payload.spans),
            latency_ms=latency_ms,
            metadata_=payload.metadata,
            tags=payload.tags,
            started_at=payload.started_at or datetime.now(timezone.utc),
            ended_at=payload.ended_at,
        )
        db.add(run)

        # ── Create Spans ─────────────────────────────
        for span_data in payload.spans:
            span_id = span_data.span_id or uuid_mod.uuid4()

            # Validate span_kind
            try:
                span_kind = SpanKind(span_data.span_kind)
            except ValueError:
                span_kind = SpanKind.CHAIN

            span = Span(
                id=span_id,
                run_id=run_id,
                org_id=org_id,
                parent_span_id=span_data.parent_span_id,
                name=span_data.name,
                span_kind=span_kind,
                input_data=span_data.input_data,
                output_data=span_data.output_data,
                model=span_data.model,
                tokens_prompt=span_data.tokens_prompt,
                tokens_completion=span_data.tokens_completion,
                tokens_total=span_data.tokens_total,
                cost=span_data.cost,
                latency_ms=span_data.latency_ms,
                error=span_data.error,
                error_type=span_data.error_type,
                attributes=span_data.attributes,
                started_at=span_data.started_at or datetime.now(timezone.utc),
                ended_at=span_data.ended_at,
            )
            db.add(span)

            # ── Create cost record for LLM spans ─────
            if span_data.model and span_data.cost:
                cost_record = CostRecord(
                    org_id=org_id,
                    run_id=run_id,
                    span_id=span_id,
                    model=span_data.model,
                    tokens_prompt=span_data.tokens_prompt or 0,
                    tokens_completion=span_data.tokens_completion or 0,
                    tokens_total=span_data.tokens_total or 0,
                    cost_prompt=0.0,  # Detailed cost split calculated later
                    cost_completion=0.0,
                    cost_total=span_data.cost,
                )
                db.add(cost_record)

        await db.flush()

        return TraceIngestResponse(
            run_id=run_id,
            spans_ingested=len(payload.spans),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
