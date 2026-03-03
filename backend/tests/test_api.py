"""
Backend integration test stubs.
These require a running PostgreSQL instance — designed for docker-compose test env.
"""

import pytest
import uuid
from datetime import datetime, timezone

# Mark all tests in this module as requiring async + db
pytestmark = [pytest.mark.asyncio]


class TestIngestEndpoint:
    """Tests for the trace ingestion API endpoint."""

    async def test_ingest_creates_run(self):
        """POST /api/v1/ingest/traces should create a run with spans."""
        # TODO: Set up test client with TestClient(app)
        # payload = {
        #     "agent_name": "test-agent",
        #     "status": "completed",
        #     "input_text": "test query",
        #     "spans": [
        #         {
        #             "name": "reasoning",
        #             "span_kind": "llm",
        #             "model": "gpt-4o",
        #             "tokens_prompt": 100,
        #             "tokens_completion": 50,
        #             "cost": 0.0125,
        #         }
        #     ],
        # }
        # response = await client.post("/api/v1/ingest/traces", json=payload)
        # assert response.status_code == 200
        # assert response.json()["spans_ingested"] == 1
        pass

    async def test_ingest_requires_api_key(self):
        """Ingestion should fail without X-API-Key header."""
        # TODO: Set up test client without API key
        # response = await client.post("/api/v1/ingest/traces", json={})
        # assert response.status_code == 401
        pass


class TestCostsEndpoint:
    """Tests for cost intelligence API endpoints."""

    async def test_cost_summary_returns_data(self):
        """GET /api/v1/costs/summary should return cost metrics."""
        # TODO: Seed test data, then query
        # response = await client.get("/api/v1/costs/summary?days=30")
        # assert response.status_code == 200
        # data = response.json()
        # assert "summary" in data
        # assert "by_agent" in data
        pass

    async def test_cost_by_agent(self):
        """GET /api/v1/costs/by-agent should group by agent name."""
        pass

    async def test_spike_detection(self):
        """Cost spikes should be detected for anomalous runs."""
        pass


class TestRunsEndpoint:
    """Tests for runs API endpoints."""

    async def test_list_runs(self):
        """GET /api/v1/runs should return paginated runs."""
        pass

    async def test_filter_runs_by_status(self):
        """Filtering by status should work."""
        pass

    async def test_get_run_detail(self):
        """GET /api/v1/runs/{id} should return run with spans."""
        pass


class TestGuardrailsEndpoint:
    """Tests for guardrails API endpoints."""

    async def test_create_guardrail(self):
        """POST /api/v1/guardrails/configs should create a rule."""
        pass

    async def test_list_alerts(self):
        """GET /api/v1/guardrails/alerts should return alerts."""
        pass
