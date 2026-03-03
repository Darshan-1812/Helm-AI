"""
Demo Agent — demonstrates SDK instrumentation with mock LLM/tool calls.

This agent generates realistic trace data for demo purposes.
Run it to populate the dashboard with sample data.

Usage:
    python demo/demo_agent.py
"""

import os
import sys
import time
import uuid
import random
from datetime import datetime, timezone, timedelta

# Add SDK to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "src"))

from agentcontrolroom import trace, ACRClient
from agentcontrolroom.spans import SpanData, RunData, SpanKind
from agentcontrolroom.cost import CostCalculator

# ── Configuration ────────────────────────────────────
API_KEY = os.getenv("ACR_API_KEY", "")
ENDPOINT = os.getenv("ACR_ENDPOINT", "http://localhost:8000")


def create_demo_run(
    agent_name: str,
    query: str,
    model: str = "gpt-4o",
    num_tool_calls: int = 2,
    success: bool = True,
) -> RunData:
    """Create a realistic demo run with spans."""
    calc = CostCalculator()
    run_start = datetime.now(timezone.utc) - timedelta(seconds=random.randint(10, 120))

    run = RunData(
        agent_name=agent_name,
        input_text=query,
        started_at=run_start,
    )

    # ── Root agent span ──────────────────────────────
    agent_span = SpanData(
        name=agent_name,
        span_kind=SpanKind.AGENT,
        run_id=run.run_id,
        input_data=query,
        started_at=run_start,
    )

    current_time = run_start

    # ── LLM reasoning span ──────────────────────────
    prompt_tokens = random.randint(200, 1500)
    completion_tokens = random.randint(50, 800)
    llm_latency = random.uniform(500, 5000)

    llm_span = SpanData(
        name="reasoning",
        span_kind=SpanKind.LLM,
        run_id=run.run_id,
        parent_span_id=agent_span.span_id,
        model=model,
        input_data=f"System: You are a helpful assistant.\nUser: {query}",
        output_data=f"I'll help you with '{query}'. Let me search for relevant information.",
        tokens_prompt=prompt_tokens,
        tokens_completion=completion_tokens,
        tokens_total=prompt_tokens + completion_tokens,
        cost=calc.calculate(model, prompt_tokens, completion_tokens),
        latency_ms=llm_latency,
        started_at=current_time,
    )
    llm_span.ended_at = current_time + timedelta(milliseconds=llm_latency)
    current_time = llm_span.ended_at

    run.add_span(llm_span)

    # ── Tool call spans ──────────────────────────────
    tools = [
        ("web-search", "Searching the web for: " + query),
        ("calculator", "Calculating result for: " + query),
        ("database-lookup", "Looking up records for: " + query),
        ("api-call", "Calling external API for: " + query),
        ("file-reader", "Reading document for: " + query),
    ]

    for i in range(min(num_tool_calls, len(tools))):
        tool_name, tool_input = tools[i]
        tool_latency = random.uniform(100, 2000)

        tool_span = SpanData(
            name=tool_name,
            span_kind=SpanKind.TOOL,
            run_id=run.run_id,
            parent_span_id=agent_span.span_id,
            input_data=tool_input,
            output_data=f"Result from {tool_name}: [mock data for '{query}']",
            latency_ms=tool_latency,
            started_at=current_time,
        )
        tool_span.ended_at = current_time + timedelta(milliseconds=tool_latency)
        current_time = tool_span.ended_at

        # Occasionally add errors
        if not success and i == num_tool_calls - 1:
            tool_span.error = f"ConnectionError: Failed to reach {tool_name} service"
            tool_span.error_type = "ConnectionError"

        run.add_span(tool_span)

    # ── Final LLM synthesis ──────────────────────────
    synth_prompt = random.randint(500, 2000)
    synth_completion = random.randint(200, 1000)
    synth_latency = random.uniform(1000, 8000)

    synth_span = SpanData(
        name="synthesis",
        span_kind=SpanKind.LLM,
        run_id=run.run_id,
        parent_span_id=agent_span.span_id,
        model=model,
        input_data="Synthesize the following results into a comprehensive answer...",
        output_data=f"Based on my research, here's what I found about '{query}'...",
        tokens_prompt=synth_prompt,
        tokens_completion=synth_completion,
        tokens_total=synth_prompt + synth_completion,
        cost=calc.calculate(model, synth_prompt, synth_completion),
        latency_ms=synth_latency,
        started_at=current_time,
    )
    synth_span.ended_at = current_time + timedelta(milliseconds=synth_latency)
    current_time = synth_span.ended_at

    run.add_span(synth_span)

    # ── Finish agent span and run ────────────────────
    agent_span.output_data = f"Completed research on '{query}'"
    agent_span.ended_at = current_time
    agent_span.latency_ms = (agent_span.ended_at - agent_span.started_at).total_seconds() * 1000
    run.add_span(agent_span)

    status = "completed" if success else "failed"
    run.finish(
        output=f"Here's my analysis of '{query}'..." if success else None,
        status=status,
    )
    run.ended_at = current_time

    return run


def main():
    """Generate demo runs and send to backend."""
    print("=" * 60)
    print("  Agent Control Room — Demo Agent")
    print("=" * 60)

    if not API_KEY:
        print("\n⚠️  No API key set. Set ACR_API_KEY environment variable.")
        print("   Run the backend first and check the console for the default API key.")
        print("   Then: set ACR_API_KEY=acr-dev-xxxxx")
        return

    client = ACRClient(api_key=API_KEY, endpoint=ENDPOINT, auto_flush=False)

    # Check backend health
    try:
        health = client.health_check()
        print(f"\n✅ Backend: {health.get('status')} (v{health.get('version')})")
    except Exception as e:
        print(f"\n❌ Backend unreachable: {e}")
        return

    # ── Generate demo runs ───────────────────────────
    demo_scenarios = [
        ("research-agent", "What are the latest trends in AI?", "gpt-4o", 3, True),
        ("research-agent", "Explain quantum computing", "gpt-4o", 2, True),
        ("code-assistant", "Write a Python web scraper", "gpt-4o-mini", 2, True),
        ("code-assistant", "Debug this React component", "gpt-4o-mini", 1, True),
        ("data-analyst", "Analyze Q4 sales trends", "claude-3.5-sonnet", 3, True),
        ("data-analyst", "Generate revenue forecast", "claude-3.5-sonnet", 2, True),
        ("support-bot", "How do I reset my password?", "gpt-3.5-turbo", 1, True),
        ("support-bot", "My order is delayed", "gpt-3.5-turbo", 2, False),  # Failed run
        ("research-agent", "Compare AWS vs GCP vs Azure", "gpt-4", 4, True),  # Expensive run
        ("code-assistant", "Refactor the authentication module", "gpt-4o", 3, True),
    ]

    print(f"\n📊 Generating {len(demo_scenarios)} demo runs...\n")

    for agent, query, model, tools, success in demo_scenarios:
        run = create_demo_run(agent, query, model, tools, success)
        try:
            result = client.send_run(run)
            status_icon = "✅" if success else "❌"
            total_cost = sum(s.cost or 0 for s in run.spans)
            print(
                f"  {status_icon} {agent:20s} | {model:20s} | "
                f"${total_cost:.4f} | {len(run.spans)} spans | {query[:40]}"
            )
        except Exception as e:
            print(f"  ❌ Failed to send: {e}")

    print(f"\n{'=' * 60}")
    print(f"  Demo complete! Open http://localhost:3000 to see the dashboard.")
    print(f"{'=' * 60}")
    client.close()


if __name__ == "__main__":
    main()
