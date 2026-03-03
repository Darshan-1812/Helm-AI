"""
Token-to-cost calculator with pricing tables for popular LLM models.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing per 1K tokens for a model."""
    prompt_cost_per_1k: float
    completion_cost_per_1k: float


# ── Pricing Table (cost per 1K tokens in USD) ───────
MODEL_PRICING: dict[str, ModelPricing] = {
    # OpenAI
    "gpt-4": ModelPricing(0.03, 0.06),
    "gpt-4-turbo": ModelPricing(0.01, 0.03),
    "gpt-4-turbo-preview": ModelPricing(0.01, 0.03),
    "gpt-4o": ModelPricing(0.005, 0.015),
    "gpt-4o-mini": ModelPricing(0.00015, 0.0006),
    "gpt-3.5-turbo": ModelPricing(0.0005, 0.0015),
    "gpt-3.5-turbo-16k": ModelPricing(0.003, 0.004),
    # Anthropic
    "claude-3-opus": ModelPricing(0.015, 0.075),
    "claude-3-opus-20240229": ModelPricing(0.015, 0.075),
    "claude-3-sonnet": ModelPricing(0.003, 0.015),
    "claude-3-sonnet-20240229": ModelPricing(0.003, 0.015),
    "claude-3-haiku": ModelPricing(0.00025, 0.00125),
    "claude-3-haiku-20240307": ModelPricing(0.00025, 0.00125),
    "claude-3.5-sonnet": ModelPricing(0.003, 0.015),
    "claude-3.5-sonnet-20240620": ModelPricing(0.003, 0.015),
    "claude-3.5-haiku": ModelPricing(0.001, 0.005),
    # Google
    "gemini-pro": ModelPricing(0.00025, 0.0005),
    "gemini-1.5-pro": ModelPricing(0.00125, 0.005),
    "gemini-1.5-flash": ModelPricing(0.000075, 0.0003),
    "gemini-2.0-flash": ModelPricing(0.0001, 0.0004),
    # Meta (via API providers)
    "llama-3-70b": ModelPricing(0.00059, 0.00079),
    "llama-3-8b": ModelPricing(0.00005, 0.00008),
    "llama-3.1-405b": ModelPricing(0.003, 0.003),
    # Mistral
    "mistral-large": ModelPricing(0.004, 0.012),
    "mistral-medium": ModelPricing(0.0027, 0.0081),
    "mistral-small": ModelPricing(0.001, 0.003),
    "mixtral-8x7b": ModelPricing(0.0007, 0.0007),
}


class CostCalculator:
    """
    Calculate the cost of LLM calls based on model and token usage.

    Usage:
        calc = CostCalculator()
        cost = calc.calculate("gpt-4o", prompt_tokens=500, completion_tokens=200)
        print(f"Cost: ${cost:.6f}")

        # Add custom model pricing
        calc.add_model("my-model", 0.001, 0.002)
    """

    def __init__(self):
        self._pricing = dict(MODEL_PRICING)

    def add_model(
        self,
        model_name: str,
        prompt_cost_per_1k: float,
        completion_cost_per_1k: float,
    ):
        """Add or update pricing for a model."""
        self._pricing[model_name] = ModelPricing(
            prompt_cost_per_1k, completion_cost_per_1k
        )

    def calculate(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> Optional[float]:
        """
        Calculate cost in USD for a given model and token usage.
        Returns None if model pricing is not found.
        """
        pricing = self._pricing.get(model)
        if pricing is None:
            # Try partial match (e.g., "gpt-4o-2024-05-13" → "gpt-4o")
            for key, val in self._pricing.items():
                if model.startswith(key):
                    pricing = val
                    break

        if pricing is None:
            return None

        prompt_cost = (prompt_tokens / 1000) * pricing.prompt_cost_per_1k
        completion_cost = (completion_tokens / 1000) * pricing.completion_cost_per_1k
        return prompt_cost + completion_cost

    def get_pricing(self, model: str) -> Optional[ModelPricing]:
        """Get pricing info for a model."""
        return self._pricing.get(model)

    @property
    def supported_models(self) -> list[str]:
        """List all models with known pricing."""
        return sorted(self._pricing.keys())
