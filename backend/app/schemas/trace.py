"""
Trace ingestion schemas — request/response models for span ingestion.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SpanIngest(BaseModel):
    """A single span to ingest from the SDK."""

    span_id: Optional[UUID] = None
    parent_span_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    name: str
    span_kind: str  # agent, llm, tool, retriever, chain, embedding, reranker
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    model: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tokens_total: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    attributes: Optional[dict] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class TraceIngestRequest(BaseModel):
    """Batch of spans to ingest."""

    agent_name: str
    run_id: Optional[UUID] = None
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    status: Optional[str] = "completed"
    metadata: Optional[dict] = Field(default_factory=dict)
    tags: Optional[list] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    spans: list[SpanIngest] = Field(default_factory=list)


class TraceIngestResponse(BaseModel):
    """Response after successful ingestion."""

    run_id: UUID
    spans_ingested: int
    message: str = "Trace ingested successfully"


class SpanResponse(BaseModel):
    """Span data in API responses."""

    id: UUID
    run_id: UUID
    parent_span_id: Optional[UUID] = None
    name: str
    span_kind: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    model: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tokens_total: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    attributes: Optional[dict] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RunResponse(BaseModel):
    """Run data in API responses."""

    id: UUID
    org_id: UUID
    agent_name: str
    status: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    error_message: Optional[str] = None
    total_tokens: int = 0
    total_cost: float = 0.0
    total_spans: int = 0
    latency_ms: Optional[float] = None
    metadata: Optional[dict] = Field(default=None, alias="metadata_")
    tags: Optional[list] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class RunDetailResponse(RunResponse):
    """Full run detail including spans."""

    spans: list[SpanResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class RunListResponse(BaseModel):
    """Paginated run list."""

    runs: list[RunResponse]
    total: int
    page: int
    page_size: int
