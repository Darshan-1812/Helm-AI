"""
Span data model — OTel-aligned with custom AI semantic conventions.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass, field


class SpanKind(str, Enum):
    """OpenTelemetry-aligned span kinds for AI agent operations."""
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    RETRIEVER = "retriever"
    CHAIN = "chain"
    EMBEDDING = "embedding"
    RERANKER = "reranker"


@dataclass
class SpanData:
    """
    Represents a single span — one operation in an agent execution.

    Aligned with OpenTelemetry semantic conventions for AI:
    - ai.model          → LLM model name
    - ai.tokens.prompt  → prompt token count
    - ai.tokens.completion → completion token count
    - ai.cost           → calculated cost in USD
    - ai.tool.name      → tool/function name
    """

    name: str
    span_kind: SpanKind
    span_id: uuid.UUID = field(default_factory=uuid.uuid4)
    parent_span_id: Optional[uuid.UUID] = None
    run_id: Optional[uuid.UUID] = None

    # I/O
    input_data: Optional[str] = None
    output_data: Optional[str] = None

    # LLM-specific
    model: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tokens_total: Optional[int] = None
    cost: Optional[float] = None

    # Performance
    latency_ms: Optional[float] = None

    # Error
    error: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    attributes: dict = field(default_factory=dict)

    # Timestamps
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    def finish(self):
        """Mark the span as finished and calculate latency."""
        self.ended_at = datetime.now(timezone.utc)
        delta = self.ended_at - self.started_at
        self.latency_ms = delta.total_seconds() * 1000

        # Calculate total tokens
        if self.tokens_prompt is not None or self.tokens_completion is not None:
            self.tokens_total = (self.tokens_prompt or 0) + (self.tokens_completion or 0)

    def set_error(self, error: Exception):
        """Record an error on this span."""
        self.error = str(error)
        self.error_type = type(error).__name__

    def to_dict(self) -> dict:
        """Serialize to dictionary for API submission."""
        return {
            "span_id": str(self.span_id),
            "parent_span_id": str(self.parent_span_id) if self.parent_span_id else None,
            "run_id": str(self.run_id) if self.run_id else None,
            "name": self.name,
            "span_kind": self.span_kind.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "model": self.model,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "tokens_total": self.tokens_total,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "error_type": self.error_type,
            "attributes": self.attributes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


@dataclass
class RunData:
    """Represents a complete agent run with all its spans."""

    agent_name: str
    run_id: uuid.UUID = field(default_factory=uuid.uuid4)
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    status: str = "completed"
    metadata: dict = field(default_factory=dict)
    tags: list = field(default_factory=list)
    spans: list[SpanData] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    def add_span(self, span: SpanData):
        """Add a span to this run."""
        span.run_id = self.run_id
        self.spans.append(span)

    def finish(self, output: Optional[str] = None, status: str = "completed"):
        """Mark the run as finished."""
        self.ended_at = datetime.now(timezone.utc)
        self.output_text = output
        self.status = status

    def to_dict(self) -> dict:
        """Serialize to dictionary for API submission."""
        return {
            "agent_name": self.agent_name,
            "run_id": str(self.run_id),
            "input_text": self.input_text,
            "output_text": self.output_text,
            "status": self.status,
            "metadata": self.metadata,
            "tags": self.tags,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "spans": [s.to_dict() for s in self.spans],
        }
