"""
Trace Service — business logic for trace ingestion and retrieval.
"""

import uuid as uuid_mod
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.models.span import Span, SpanKind
from app.models.cost import CostRecord


async def ingest_run(
    db: AsyncSession,
    org_id: uuid_mod.UUID,
    payload: "TraceIngestRequest",
) -> tuple[uuid_mod.UUID, int]:
    """
    Ingest a full agent run with spans and cost records.

    Returns:
        (run_id, spans_ingested)
    """
    run_id = payload.run_id or uuid_mod.uuid4()

    # ── Aggregate metrics from spans ─────────────────
    total_tokens = sum(s.tokens_total or 0 for s in payload.spans)
    total_cost = sum(s.cost or 0.0 for s in payload.spans)
    latency_ms = None
    if payload.started_at and payload.ended_at:
        latency_ms = (payload.ended_at - payload.started_at).total_seconds() * 1000

    # ── Create Run ───────────────────────────────────
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

    # ── Create Spans + Cost Records ──────────────────
    # Sort spans: parents before children to satisfy FK constraint
    sorted_spans = _topo_sort_spans(payload.spans)

    for span_data in sorted_spans:
        span_id = span_data.span_id or uuid_mod.uuid4()

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

        if span_data.model and span_data.cost:
            cost_record = CostRecord(
                org_id=org_id,
                run_id=run_id,
                span_id=span_id,
                model=span_data.model,
                tokens_prompt=span_data.tokens_prompt or 0,
                tokens_completion=span_data.tokens_completion or 0,
                tokens_total=span_data.tokens_total or 0,
                cost_prompt=0.0,
                cost_completion=0.0,
                cost_total=span_data.cost,
            )
            db.add(cost_record)

    await db.flush()
    return run_id, len(payload.spans)


def _topo_sort_spans(spans: list) -> list:
    """
    Topologically sort spans so parents are always before children.
    Roots (no parent_span_id) come first, then their children, etc.
    """
    span_ids = {str(s.span_id) for s in spans if s.span_id}
    roots = []
    children = []

    for span in spans:
        parent_id = str(span.parent_span_id) if span.parent_span_id else None
        if parent_id is None or parent_id not in span_ids:
            roots.append(span)
        else:
            children.append(span)

    # Build result: roots first, then children in dependency order
    result = list(roots)
    inserted_ids = {str(s.span_id) for s in roots if s.span_id}

    remaining = list(children)
    max_iterations = len(remaining) + 1
    for _ in range(max_iterations):
        if not remaining:
            break
        next_remaining = []
        for span in remaining:
            parent_id = str(span.parent_span_id) if span.parent_span_id else None
            if parent_id in inserted_ids:
                result.append(span)
                if span.span_id:
                    inserted_ids.add(str(span.span_id))
            else:
                next_remaining.append(span)
        remaining = next_remaining

    # Any remaining spans (shouldn't happen, but safety)
    result.extend(remaining)
    return result
