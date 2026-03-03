"""
Evaluation Worker — structured quality evaluation on agent traces via Dramatiq.

Supports pluggable evaluators:
- Built-in heuristic evaluators (production-ready)
- Ragas integration (optional, for RAG evaluations)
- DeepEval integration (optional, for general LLM evaluations)
"""

import dramatiq
import json
import logging
import uuid as uuid_mod
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ── Model Pricing for cost-based evaluation ───────────
MODEL_PRICING = {
    "gpt-4": (0.03, 0.06),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-sonnet": (0.003, 0.015),
    "claude-3.5-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "gemini-pro": (0.00025, 0.0005),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-1.5-flash": (0.000075, 0.0003),
}


# ═══════════════════════════════════════════════════════
# Evaluator Registry — pluggable evaluation framework
# ═══════════════════════════════════════════════════════

class BaseEvaluator:
    """Base class for all evaluators."""

    name: str = "base"

    def evaluate(self, run_data: dict) -> dict:
        """
        Evaluate a run and return results.

        Returns:
            {
                "score": float (0.0 - 1.0),
                "label": "pass" | "fail" | "warning",
                "reason": str,
                "details": dict,
            }
        """
        raise NotImplementedError


class HallucinationEvaluator(BaseEvaluator):
    """
    Heuristic hallucination detection.
    Checks for:
    - Output length vs input length ratio (overly long outputs may hallucinate)
    - Presence of hedging phrases
    - Consistency signals
    """

    name = "hallucination"

    def evaluate(self, run_data: dict) -> dict:
        spans = run_data.get("spans", [])
        llm_spans = [s for s in spans if s.get("span_kind") == "llm"]

        if not llm_spans:
            return {"score": 1.0, "label": "pass", "reason": "No LLM spans to evaluate", "details": {}}

        scores = []
        for span in llm_spans:
            input_text = span.get("input_data", "") or ""
            output_text = span.get("output_data", "") or ""

            # Heuristic: If output is much longer than input, may be hallucinating
            input_len = len(input_text)
            output_len = len(output_text)
            ratio = output_len / max(input_len, 1)

            score = 1.0
            if ratio > 10:
                score -= 0.3  # Very long output relative to input
            if ratio > 20:
                score -= 0.2

            # Check for hedging phrases (good sign — less hallucination)
            hedging = ["I'm not sure", "I don't know", "might be", "possibly", "approximately"]
            if any(h.lower() in output_text.lower() for h in hedging):
                score = min(score + 0.1, 1.0)

            # Check for confident false-claim signals
            overconfident = ["definitely", "absolutely certain", "100%", "guaranteed"]
            if any(o.lower() in output_text.lower() for o in overconfident):
                score -= 0.1

            scores.append(max(0.0, min(1.0, score)))

        avg_score = sum(scores) / len(scores)
        label = "pass" if avg_score >= 0.7 else ("warning" if avg_score >= 0.4 else "fail")

        return {
            "score": round(avg_score, 4),
            "label": label,
            "reason": f"Evaluated {len(llm_spans)} LLM spans. Avg hallucination score: {avg_score:.2f}",
            "details": {"span_scores": scores, "num_llm_spans": len(llm_spans)},
        }


class FaithfulnessEvaluator(BaseEvaluator):
    """
    Checks if the output stays faithful to the input context.
    Uses text overlap and reference signals.
    """

    name = "faithfulness"

    def evaluate(self, run_data: dict) -> dict:
        input_text = run_data.get("input_text", "") or ""
        output_text = run_data.get("output_text", "") or ""

        if not output_text:
            return {"score": 0.5, "label": "warning", "reason": "No output to evaluate", "details": {}}

        # Keyword overlap between input and output
        input_words = set(input_text.lower().split())
        output_words = set(output_text.lower().split())

        if not input_words:
            return {"score": 0.7, "label": "pass", "reason": "No input context to compare", "details": {}}

        overlap = len(input_words & output_words) / len(input_words)
        score = min(0.5 + overlap * 0.5, 1.0)

        # Check for tool results being referenced in output
        spans = run_data.get("spans", [])
        tool_spans = [s for s in spans if s.get("span_kind") == "tool"]
        if tool_spans:
            tool_outputs = " ".join(s.get("output_data", "") or "" for s in tool_spans)
            tool_words = set(tool_outputs.lower().split())
            if tool_words:
                tool_overlap = len(tool_words & output_words) / max(len(tool_words), 1)
                score = min(score + tool_overlap * 0.2, 1.0)

        label = "pass" if score >= 0.7 else ("warning" if score >= 0.4 else "fail")
        return {
            "score": round(score, 4),
            "label": label,
            "reason": f"Input-output keyword overlap: {overlap:.2f}",
            "details": {"keyword_overlap": overlap, "tool_count": len(tool_spans)},
        }


class CorrectnessEvaluator(BaseEvaluator):
    """
    Basic correctness heuristics.
    Checks for error-free completion and reasonable output length.
    """

    name = "correctness"

    def evaluate(self, run_data: dict) -> dict:
        status = run_data.get("status", "completed")
        output_text = run_data.get("output_text", "") or ""
        spans = run_data.get("spans", [])
        error_spans = [s for s in spans if s.get("error")]

        score = 1.0
        reasons = []

        # Failed run = low correctness
        if status == "failed":
            score -= 0.5
            reasons.append("Run failed")

        # Errors in spans
        if error_spans:
            penalty = min(len(error_spans) * 0.15, 0.4)
            score -= penalty
            reasons.append(f"{len(error_spans)} span(s) had errors")

        # Too short output = potentially incomplete
        if len(output_text) < 20 and status == "completed":
            score -= 0.2
            reasons.append("Output is very short")

        # No output at all
        if not output_text and status == "completed":
            score -= 0.3
            reasons.append("No output produced")

        score = max(0.0, min(1.0, score))
        label = "pass" if score >= 0.7 else ("warning" if score >= 0.4 else "fail")

        return {
            "score": round(score, 4),
            "label": label,
            "reason": "; ".join(reasons) if reasons else "All checks passed",
            "details": {"error_count": len(error_spans), "output_length": len(output_text)},
        }


class RelevanceEvaluator(BaseEvaluator):
    """
    Checks if the output is relevant to the input query.
    Uses keyword matching and topic consistency.
    """

    name = "relevance"

    def evaluate(self, run_data: dict) -> dict:
        input_text = run_data.get("input_text", "") or ""
        output_text = run_data.get("output_text", "") or ""

        if not input_text or not output_text:
            return {"score": 0.5, "label": "warning", "reason": "Missing input or output", "details": {}}

        # Word-level relevance
        input_words = set(w.lower() for w in input_text.split() if len(w) > 3)
        output_words = set(w.lower() for w in output_text.split() if len(w) > 3)

        if not input_words:
            return {"score": 0.7, "label": "pass", "reason": "Input too short for analysis", "details": {}}

        overlap = len(input_words & output_words)
        relevance_ratio = overlap / len(input_words)
        score = min(0.4 + relevance_ratio * 0.6, 1.0)

        label = "pass" if score >= 0.7 else ("warning" if score >= 0.4 else "fail")
        return {
            "score": round(score, 4),
            "label": label,
            "reason": f"Topic relevance: {relevance_ratio:.2f} ({overlap}/{len(input_words)} keywords)",
            "details": {"relevance_ratio": relevance_ratio, "matched_keywords": overlap},
        }


# ── Evaluator Registry ──────────────────────────────
EVALUATORS: dict[str, BaseEvaluator] = {
    "hallucination": HallucinationEvaluator(),
    "faithfulness": FaithfulnessEvaluator(),
    "correctness": CorrectnessEvaluator(),
    "relevance": RelevanceEvaluator(),
}


# ═══════════════════════════════════════════════════════
# Dramatiq Actor — async evaluation pipeline
# ═══════════════════════════════════════════════════════

@dramatiq.actor(max_retries=2, min_backoff=2000, max_backoff=60000)
def evaluate_run(run_id: str, org_id: str, eval_types: str):
    """
    Run quality evaluations on an agent run.

    Args:
        run_id: UUID of the run to evaluate
        org_id: Organization UUID
        eval_types: JSON-encoded list of eval types to run
    """
    logger.info(f"Evaluating run_id={run_id}, types={eval_types}")

    try:
        types = json.loads(eval_types) if isinstance(eval_types, str) else eval_types

        # For now, build run_data from the args
        # In production: fetch run + spans from DB
        run_data = _fetch_run_data(run_id, org_id)

        results = {}
        for eval_type in types:
            evaluator = EVALUATORS.get(eval_type)
            if evaluator:
                result = evaluator.evaluate(run_data)
                results[eval_type] = result
                logger.info(f"  {eval_type}: {result['score']:.3f} ({result['label']})")

                # Save to DB
                _save_evaluation(run_id, org_id, eval_type, result)
            else:
                logger.warning(f"  Unknown eval type: {eval_type}")

        # Check quality gates and generate alerts
        _check_quality_gates(run_id, org_id, results)

        logger.info(f"Evaluation completed for run_id={run_id}")
        return results

    except Exception as e:
        logger.error(f"Evaluation failed for run_id={run_id}: {e}")
        raise


def _fetch_run_data(run_id: str, org_id: str) -> dict:
    """
    Fetch run data from DB for evaluation.
    TODO: Replace with actual DB query using async session.
    """
    # Placeholder — in production, query Run + Spans from PostgreSQL
    return {
        "run_id": run_id,
        "org_id": org_id,
        "status": "completed",
        "input_text": "",
        "output_text": "",
        "spans": [],
    }


def _save_evaluation(run_id: str, org_id: str, eval_type: str, result: dict):
    """
    Save evaluation result to DB.
    TODO: Replace with actual DB insert using sync session.
    """
    logger.info(
        f"Saving evaluation: run={run_id}, type={eval_type}, "
        f"score={result['score']}, label={result['label']}"
    )


def _check_quality_gates(run_id: str, org_id: str, results: dict):
    """Check if any evaluation falls below quality gate thresholds."""
    for eval_type, result in results.items():
        if result["score"] < 0.4:
            logger.warning(
                f"Quality gate FAILED: run={run_id}, type={eval_type}, "
                f"score={result['score']}"
            )
            # TODO: Send alert via alert_worker
