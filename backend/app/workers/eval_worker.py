"""
Evaluation Worker — runs quality evaluation on agent traces via Dramatiq.
"""

import dramatiq
import json
import logging
import random

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=2, min_backoff=2000, max_backoff=60000)
def evaluate_run(run_id: str, org_id: str, eval_types: str):
    """
    Run quality evaluation on an agent run.

    In production, this integrates with:
    - Ragas (for RAG-specific evaluations)
    - DeepEval (for general LLM evaluations)

    For MVP, generates mock evaluation scores.
    """
    logger.info(f"Evaluating run_id={run_id}, types={eval_types}")

    try:
        types = json.loads(eval_types) if isinstance(eval_types, str) else eval_types

        results = {}
        for eval_type in types:
            score = _evaluate(eval_type, run_id)
            results[eval_type] = score
            logger.info(f"  {eval_type}: {score:.3f}")

        logger.info(f"Evaluation completed for run_id={run_id}: {results}")
        return results

    except Exception as e:
        logger.error(f"Evaluation failed for run_id={run_id}: {e}")
        raise


def _evaluate(eval_type: str, run_id: str) -> float:
    """
    Evaluate a specific quality dimension.

    TODO: Replace with actual Ragas/DeepEval integration:

    from ragas.metrics import faithfulness, hallucination
    from ragas import evaluate

    result = evaluate(
        dataset,
        metrics=[faithfulness, hallucination],
    )

    For MVP, returns mock scores.
    """
    # Mock evaluation scores for demo
    # In production, this calls Ragas/DeepEval
    mock_scores = {
        "hallucination": random.uniform(0.7, 1.0),   # higher = less hallucination
        "faithfulness": random.uniform(0.6, 1.0),
        "correctness": random.uniform(0.5, 1.0),
        "relevance": random.uniform(0.7, 1.0),
        "toxicity": random.uniform(0.9, 1.0),        # higher = less toxic
    }
    return mock_scores.get(eval_type, random.uniform(0.5, 1.0))
