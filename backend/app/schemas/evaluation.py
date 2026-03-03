"""
Evaluation schemas — request/response models for quality scoring.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    """Request to trigger evaluation on a run."""

    run_id: UUID
    eval_types: list[str] = Field(
        default=["hallucination", "faithfulness", "correctness", "relevance"]
    )


class EvaluationResponse(BaseModel):
    """Single evaluation result."""

    id: UUID
    run_id: UUID
    span_id: Optional[UUID] = None
    eval_type: str
    score: float
    label: Optional[str] = None
    reason: Optional[str] = None
    details: Optional[dict] = None
    evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EvaluationSummary(BaseModel):
    """Aggregated evaluation scores for a run."""

    run_id: UUID
    agent_name: str
    avg_hallucination: Optional[float] = None
    avg_faithfulness: Optional[float] = None
    avg_correctness: Optional[float] = None
    avg_relevance: Optional[float] = None
    total_evaluations: int


class EvaluationListResponse(BaseModel):
    """Paginated evaluation list."""

    evaluations: list[EvaluationResponse]
    total: int
    page: int
    page_size: int


class GuardrailConfigRequest(BaseModel):
    """Create or update a guardrail rule."""

    name: str
    rule_type: str  # cost_limit, loop_detection, latency_budget, quality_gate, token_limit
    threshold: float
    action: str = "alert"  # alert, block, kill
    enabled: bool = True
    config: Optional[dict] = Field(default_factory=dict)


class GuardrailConfigResponse(BaseModel):
    """Guardrail config in API responses."""

    id: UUID
    org_id: UUID
    name: str
    rule_type: str
    threshold: float
    action: str
    enabled: bool
    config: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Alert in API responses."""

    id: UUID
    org_id: UUID
    run_id: Optional[UUID] = None
    alert_type: str
    message: str
    severity: str
    is_resolved: bool
    details: Optional[dict] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
