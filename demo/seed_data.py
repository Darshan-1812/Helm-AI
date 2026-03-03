"""
Seed Data Script — populates the database directly via API.

Usage:
    python demo/seed_data.py

Generates a comprehensive set of demo data including:
- Multiple agent types with varying configurations
- Success and failure scenarios
- Cost variations across models
- Multiple tool call patterns
"""

import os
import sys
import random
from datetime import datetime, timezone, timedelta

# Add SDK to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "src"))

from agentcontrolroom import ACRClient
from agentcontrolroom.spans import SpanData, RunData, SpanKind
from agentcontrolroom.cost import CostCalculator

API_KEY = os.getenv("ACR_API_KEY", "")
ENDPOINT = os.getenv("ACR_ENDPOINT", "http://localhost:8000")


AGENTS = [
    {"name": "research-agent", "models": ["gpt-4o", "gpt-4"], "tools": ["web-search", "wiki-lookup", "arxiv-search"]},
    {"name": "code-assistant", "models": ["gpt-4o-mini", "gpt-4o"], "tools": ["code-execute", "file-reader", "linter"]},
    {"name": "data-analyst", "models": ["claude-3.5-sonnet", "gemini-1.5-pro"], "tools": ["sql-query", "chart-gen", "csv-parser"]},
    {"name": "support-bot", "models": ["gpt-3.5-turbo", "gpt-4o-mini"], "tools": ["kb-search", "ticket-create"]},
    {"name": "content-writer", "models": ["claude-3.5-sonnet", "gpt-4o"], "tools": ["web-search", "plagiarism-check", "seo-analyzer"]},
]

QUERIES = [
    "Explain quantum computing fundamentals",
    "Write a REST API in Python",
    "Analyze Q4 revenue trends",
    "How do I reset my password?",
    "Create a blog post about AI trends",
    "Debug this React component",
    "Compare AWS vs GCP pricing",
    "Summarize this research paper",
    "Generate a marketing strategy",
    "Optimize database queries",
    "Build a machine learning pipeline",
    "Design a microservices architecture",
    "Review security vulnerabilities",
    "Create unit tests for auth module",
    "Analyze customer feedback sentiment",
]


def create_run(calc: CostCalculator, agent_config: dict, query: str, success: bool = True) -> RunData:
    """Create a realistic agent run."""
    model = random.choice(agent_config["models"])
    run_start = datetime.now(timezone.utc) - timedelta(
        hours=random.randint(0, 72),
        minutes=random.randint(0, 59),
    )

    run = RunData(agent_name=agent_config["name"], input_text=query, started_at=run_start)
    current_time = run_start

    # Root agent span
    agent_span = SpanData(
        name=agent_config["name"],
        span_kind=SpanKind.AGENT,
        run_id=run.run_id,
        input_data=query,
        started_at=run_start,
    )

    # LLM reasoning
    pt, ct = random.randint(200, 2000), random.randint(50, 1000)
    lat = random.uniform(500, 6000)
    llm = SpanData(
        name="reasoning", span_kind=SpanKind.LLM, run_id=run.run_id,
        parent_span_id=agent_span.span_id, model=model,
        input_data=f"System: You are helpful.\nUser: {query}",
        output_data=f"I'll help with '{query}'.",
        tokens_prompt=pt, tokens_completion=ct, tokens_total=pt + ct,
        cost=calc.calculate(model, pt, ct), latency_ms=lat, started_at=current_time,
    )
    llm.ended_at = current_time + timedelta(milliseconds=lat)
    current_time = llm.ended_at
    run.add_span(llm)

    # Tool calls
    num_tools = random.randint(1, min(3, len(agent_config["tools"])))
    tools = random.sample(agent_config["tools"], num_tools)
    for i, tool_name in enumerate(tools):
        t_lat = random.uniform(100, 3000)
        tool = SpanData(
            name=tool_name, span_kind=SpanKind.TOOL, run_id=run.run_id,
            parent_span_id=agent_span.span_id,
            input_data=f"Using {tool_name} for: {query}",
            output_data=f"Result from {tool_name}",
            latency_ms=t_lat, started_at=current_time,
        )
        tool.ended_at = current_time + timedelta(milliseconds=t_lat)
        current_time = tool.ended_at
        if not success and i == len(tools) - 1:
            tool.error = f"ConnectionError: {tool_name} service unavailable"
            tool.error_type = "ConnectionError"
        run.add_span(tool)

    # Final synthesis
    sp, sc = random.randint(500, 3000), random.randint(200, 1500)
    s_lat = random.uniform(1000, 10000)
    synth = SpanData(
        name="synthesis", span_kind=SpanKind.LLM, run_id=run.run_id,
        parent_span_id=agent_span.span_id, model=model,
        input_data="Synthesize results...",
        output_data=f"Based on research about '{query}'...",
        tokens_prompt=sp, tokens_completion=sc, tokens_total=sp + sc,
        cost=calc.calculate(model, sp, sc), latency_ms=s_lat, started_at=current_time,
    )
    synth.ended_at = current_time + timedelta(milliseconds=s_lat)
    current_time = synth.ended_at
    run.add_span(synth)

    # Finish
    agent_span.output_data = f"Completed: {query}"
    agent_span.ended_at = current_time
    agent_span.latency_ms = (agent_span.ended_at - agent_span.started_at).total_seconds() * 1000
    run.add_span(agent_span)
    run.finish(output=f"Answer for '{query}'..." if success else None, status="completed" if success else "failed")
    run.ended_at = current_time
    return run


def main():
    print("=" * 60)
    print("  Agent Control Room — Seed Data Generator")
    print("=" * 60)

    if not API_KEY:
        print("\n⚠️  Set ACR_API_KEY environment variable first.")
        return

    client = ACRClient(api_key=API_KEY, endpoint=ENDPOINT, auto_flush=False)
    calc = CostCalculator()

    try:
        health = client.health_check()
        print(f"\n✅ Backend: {health.get('status')} (v{health.get('version')})")
    except Exception as e:
        print(f"\n❌ Backend unreachable: {e}")
        return

    total_runs = 30
    print(f"\n📊 Generating {total_runs} seed runs...\n")

    for i in range(total_runs):
        agent_config = random.choice(AGENTS)
        query = random.choice(QUERIES)
        success = random.random() > 0.15  # 85% success rate

        run = create_run(calc, agent_config, query, success)
        try:
            client.send_run(run)
            icon = "✅" if success else "❌"
            cost = sum(s.cost or 0 for s in run.spans)
            print(f"  {icon} [{i+1:2d}/{total_runs}] {agent_config['name']:20s} | ${cost:.4f} | {query[:40]}")
        except Exception as e:
            print(f"  ❌ [{i+1:2d}] Failed: {e}")

    print(f"\n{'=' * 60}")
    print(f"  Seeded {total_runs} runs. Open http://localhost:3000")
    print(f"{'=' * 60}")
    client.close()


if __name__ == "__main__":
    main()
