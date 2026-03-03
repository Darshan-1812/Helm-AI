"""
Cost schemas — request/response models for cost intelligence.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CostSummary(BaseModel):
    """Aggregated cost summary."""

    total_cost: float
    total_tokens: int
    total_runs: int
    avg_cost_per_run: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class CostByAgent(BaseModel):
    """Cost breakdown by agent name."""

    agent_name: str
    total_cost: float
    total_tokens: int
    run_count: int
    avg_cost_per_run: float


class CostByModel(BaseModel):
    """Cost breakdown by LLM model."""

    model: str
    total_cost: float
    total_tokens: int
    call_count: int


class CostSpike(BaseModel):
    """Detected cost anomaly."""

    run_id: UUID
    agent_name: str
    cost: float
    avg_cost: float
    deviation: float  # how many std devs above mean
    occurred_at: datetime


class CostSummaryResponse(BaseModel):
    """Full cost intelligence response."""

    summary: CostSummary
    by_agent: list[CostByAgent]
    by_model: list[CostByModel]
    spikes: list[CostSpike]
