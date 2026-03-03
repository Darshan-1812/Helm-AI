"""Tests for SDK span data models."""

import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agentcontrolroom.spans import SpanData, RunData, SpanKind


class TestSpanData:
    """Tests for SpanData model."""

    def test_create_span(self):
        span = SpanData(name="test-span", span_kind=SpanKind.TOOL, run_id="run-1")
        assert span.name == "test-span"
        assert span.span_kind == SpanKind.TOOL
        assert span.span_id is not None
        assert span.error is None

    def test_span_with_llm_data(self):
        span = SpanData(
            name="gpt-call",
            span_kind=SpanKind.LLM,
            run_id="run-1",
            model="gpt-4o",
            tokens_prompt=100,
            tokens_completion=50,
            tokens_total=150,
            cost=0.0125,
        )
        assert span.model == "gpt-4o"
        assert span.tokens_total == 150
        assert span.cost == 0.0125

    def test_span_with_error(self):
        span = SpanData(
            name="failing-tool",
            span_kind=SpanKind.TOOL,
            run_id="run-1",
            error="ConnectionError: timeout",
            error_type="ConnectionError",
        )
        assert span.error is not None
        assert span.error_type == "ConnectionError"

    def test_span_serialization(self):
        span = SpanData(
            name="test",
            span_kind=SpanKind.AGENT,
            run_id="run-1",
            input_data="hello",
            output_data="world",
        )
        data = span.to_dict()
        assert data["name"] == "test"
        assert data["span_kind"] == "agent"
        assert data["input_data"] == "hello"

    def test_span_kind_values(self):
        """All span kinds should be valid."""
        for kind in SpanKind:
            span = SpanData(name=f"test-{kind.value}", span_kind=kind, run_id="r")
            assert span.span_kind == kind


class TestRunData:
    """Tests for RunData model."""

    def test_create_run(self):
        run = RunData(agent_name="test-agent")
        assert run.agent_name == "test-agent"
        assert run.run_id is not None
        assert run.spans == []
        assert run.status == "running"

    def test_add_span(self):
        run = RunData(agent_name="test-agent")
        span = SpanData(name="s1", span_kind=SpanKind.TOOL, run_id=run.run_id)
        run.add_span(span)
        assert len(run.spans) == 1

    def test_finish_run(self):
        run = RunData(agent_name="test-agent")
        run.finish(output="done", status="completed")
        assert run.status == "completed"
        assert run.output == "done"
        assert run.ended_at is not None

    def test_run_serialization(self):
        run = RunData(agent_name="test-agent", input_text="query")
        span = SpanData(name="s1", span_kind=SpanKind.LLM, run_id=run.run_id)
        run.add_span(span)
        data = run.to_dict()
        assert data["agent_name"] == "test-agent"
        assert len(data["spans"]) == 1

    def test_run_total_cost(self):
        run = RunData(agent_name="test-agent")
        run.add_span(SpanData(name="s1", span_kind=SpanKind.LLM, run_id=run.run_id, cost=0.01))
        run.add_span(SpanData(name="s2", span_kind=SpanKind.LLM, run_id=run.run_id, cost=0.02))
        total = sum(s.cost or 0 for s in run.spans)
        assert abs(total - 0.03) < 0.0001
