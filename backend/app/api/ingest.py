"""
Trace ingestion API — receives spans from the SDK.
Uses trace_service for business logic.
"""

import uuid as uuid_mod

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_org_id
from app.schemas.trace import TraceIngestRequest, TraceIngestResponse
from app.services.trace_service import ingest_run

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
        run_id, spans_ingested = await ingest_run(db, org_id, payload)

        return TraceIngestResponse(
            run_id=run_id,
            spans_ingested=spans_ingested,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
