"""
Client-side Guardrails — enforce reliability constraints at the SDK level.
"""

import logging
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("agentcontrolroom")


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation."""
    rule: str
    message: str
    value: float
    threshold: float
    action: str  # "alert", "block", "kill"


class Guardrails:
    """
    Client-side guardrails for AI agents.

    Usage:
        guardrails = Guardrails()
        guardrails.set_cost_limit(max_cost=5.0, action="kill")
        guardrails.set_latency_budget(max_ms=30000, action="alert")
        guardrails.set_loop_detection(max_iterations=50, action="block")

        # Check during execution
        guardrails.check_cost(current_cost=3.5)
        guardrails.check_latency(elapsed_ms=25000)
        guardrails.check_loop(iteration_count=10)
    """

    def __init__(self):
        self._cost_limit: Optional[float] = None
        self._cost_action: str = "alert"

        self._latency_budget_ms: Optional[float] = None
        self._latency_action: str = "alert"

        self._max_iterations: Optional[int] = None
        self._loop_action: str = "block"

        self._quality_gate: Optional[float] = None
        self._quality_action: str = "alert"

        self._violations: list[GuardrailViolation] = []
        self._on_violation: Optional[Callable[[GuardrailViolation], None]] = None

    def set_cost_limit(self, max_cost: float, action: str = "kill"):
        """Set maximum cost for a single run."""
        self._cost_limit = max_cost
        self._cost_action = action

    def set_latency_budget(self, max_ms: float, action: str = "alert"):
        """Set maximum latency budget for a run."""
        self._latency_budget_ms = max_ms
        self._latency_action = action

    def set_loop_detection(self, max_iterations: int, action: str = "block"):
        """Set maximum iteration count before loop is detected."""
        self._max_iterations = max_iterations
        self._loop_action = action

    def set_quality_gate(self, min_score: float, action: str = "alert"):
        """Set minimum quality score threshold."""
        self._quality_gate = min_score
        self._quality_action = action

    def on_violation(self, callback: Callable[[GuardrailViolation], None]):
        """Register a callback for guardrail violations."""
        self._on_violation = callback

    def check_cost(self, current_cost: float) -> Optional[GuardrailViolation]:
        """Check if current cost exceeds the limit."""
        if self._cost_limit and current_cost > self._cost_limit:
            violation = GuardrailViolation(
                rule="cost_limit",
                message=f"Cost ${current_cost:.4f} exceeds limit ${self._cost_limit:.4f}",
                value=current_cost,
                threshold=self._cost_limit,
                action=self._cost_action,
            )
            self._handle_violation(violation)
            return violation
        return None

    def check_latency(self, elapsed_ms: float) -> Optional[GuardrailViolation]:
        """Check if latency exceeds budget."""
        if self._latency_budget_ms and elapsed_ms > self._latency_budget_ms:
            violation = GuardrailViolation(
                rule="latency_budget",
                message=f"Latency {elapsed_ms:.0f}ms exceeds budget {self._latency_budget_ms:.0f}ms",
                value=elapsed_ms,
                threshold=self._latency_budget_ms,
                action=self._latency_action,
            )
            self._handle_violation(violation)
            return violation
        return None

    def check_loop(self, iteration_count: int) -> Optional[GuardrailViolation]:
        """Check for infinite loop (too many iterations)."""
        if self._max_iterations and iteration_count > self._max_iterations:
            violation = GuardrailViolation(
                rule="loop_detection",
                message=f"Loop detected: {iteration_count} iterations exceeds max {self._max_iterations}",
                value=float(iteration_count),
                threshold=float(self._max_iterations),
                action=self._loop_action,
            )
            self._handle_violation(violation)
            return violation
        return None

    def check_quality(self, score: float) -> Optional[GuardrailViolation]:
        """Check if quality score meets the gate threshold."""
        if self._quality_gate and score < self._quality_gate:
            violation = GuardrailViolation(
                rule="quality_gate",
                message=f"Quality score {score:.3f} below threshold {self._quality_gate:.3f}",
                value=score,
                threshold=self._quality_gate,
                action=self._quality_action,
            )
            self._handle_violation(violation)
            return violation
        return None

    def _handle_violation(self, violation: GuardrailViolation):
        """Handle a guardrail violation."""
        self._violations.append(violation)
        logger.warning(f"Guardrail violation: {violation.message} [action={violation.action}]")

        if self._on_violation:
            self._on_violation(violation)

        if violation.action == "kill":
            raise RuntimeError(f"Guardrail KILL: {violation.message}")
        elif violation.action == "block":
            raise RuntimeError(f"Guardrail BLOCK: {violation.message}")

    @property
    def violations(self) -> list[GuardrailViolation]:
        """Get all recorded violations."""
        return list(self._violations)

    def clear_violations(self):
        """Clear recorded violations."""
        self._violations.clear()
