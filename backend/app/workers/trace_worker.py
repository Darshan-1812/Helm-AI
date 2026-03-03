"""
Trace Worker — processes ingested spans asynchronously via Dramatiq.
"""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
import os
import json
import logging

logger = logging.getLogger(__name__)

# ── Configure Dramatiq Broker ────────────────────────
broker_url = os.getenv("DRAMATIQ_BROKER_URL", "redis://redis:6379/1")
broker = RedisBroker(url=broker_url)
dramatiq.set_broker(broker)


@dramatiq.actor(max_retries=3, min_backoff=1000, max_backoff=30000)
def process_trace(run_id: str, org_id: str, trace_data: str):
    """
    Process trace data asynchronously.
    Handles post-ingestion tasks:
    - Cost calculation refinement
    - Guardrail evaluation
    - Alert generation
    """
    logger.info(f"Processing trace for run_id={run_id}, org_id={org_id}")

    try:
        data = json.loads(trace_data)

        # ── Cost calculation ─────────────────────────
        # Refine cost calculations with detailed pricing
        _calculate_detailed_costs(run_id, data)

        # ── Guardrail checks ────────────────────────
        _check_guardrails(run_id, org_id, data)

        logger.info(f"Trace processing completed for run_id={run_id}")

    except Exception as e:
        logger.error(f"Trace processing failed for run_id={run_id}: {e}")
        raise


def _calculate_detailed_costs(run_id: str, data: dict):
    """
    Calculate detailed prompt/completion cost split using model pricing.
    """
    MODEL_PRICING = {
        # model: (cost_per_1k_prompt_tokens, cost_per_1k_completion_tokens)
        "gpt-4": (0.03, 0.06),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4o": (0.005, 0.015),
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-3.5-turbo": (0.0005, 0.0015),
        "claude-3-opus": (0.015, 0.075),
        "claude-3-sonnet": (0.003, 0.015),
        "claude-3-haiku": (0.00025, 0.00125),
        "claude-3.5-sonnet": (0.003, 0.015),
        "gemini-pro": (0.00025, 0.0005),
        "gemini-1.5-pro": (0.00125, 0.005),
        "gemini-1.5-flash": (0.000075, 0.0003),
    }

    spans = data.get("spans", [])
    for span in spans:
        model = span.get("model", "")
        if model and model in MODEL_PRICING:
            prompt_rate, completion_rate = MODEL_PRICING[model]
            prompt_tokens = span.get("tokens_prompt", 0) or 0
            completion_tokens = span.get("tokens_completion", 0) or 0

            span["cost_prompt"] = (prompt_tokens / 1000) * prompt_rate
            span["cost_completion"] = (completion_tokens / 1000) * completion_rate
            span["cost_total"] = span["cost_prompt"] + span["cost_completion"]

    logger.info(f"Detailed costs calculated for {len(spans)} spans in run={run_id}")


def _check_guardrails(run_id: str, org_id: str, data: dict):
    """
    Run guardrail checks on the processed trace.
    Generates alerts for violations.
    """
    total_cost = sum(s.get("cost", 0) or 0 for s in data.get("spans", []))
    span_count = len(data.get("spans", []))

    # ── Loop detection (too many spans = possible infinite loop)
    if span_count > 100:
        logger.warning(f"Possible loop detected in run={run_id}: {span_count} spans")

    # ── Cost spike check
    if total_cost > 1.0:  # > $1 per run
        logger.warning(f"High cost run={run_id}: ${total_cost:.4f}")

    logger.info(f"Guardrail checks completed for run={run_id}")
