"""Tests for SDK cost calculator."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agentcontrolroom.cost import CostCalculator


class TestCostCalculator:
    """Tests for CostCalculator pricing logic."""

    def setup_method(self):
        self.calc = CostCalculator()

    def test_gpt4o_pricing(self):
        """GPT-4o should use correct input/output rates."""
        cost = self.calc.calculate("gpt-4o", prompt_tokens=1000, completion_tokens=500)
        # GPT-4o: $5/M input, $15/M output
        expected = (1000 / 1_000_000 * 5.0) + (500 / 1_000_000 * 15.0)
        assert abs(cost - expected) < 0.0001

    def test_gpt4o_mini_pricing(self):
        """GPT-4o-mini should be significantly cheaper than GPT-4o."""
        cost_4o = self.calc.calculate("gpt-4o", 1000, 500)
        cost_mini = self.calc.calculate("gpt-4o-mini", 1000, 500)
        assert cost_mini < cost_4o

    def test_unknown_model_returns_zero(self):
        """Unknown models should return 0.0 cost."""
        cost = self.calc.calculate("totally-unknown-model", 1000, 500)
        assert cost == 0.0

    def test_zero_tokens(self):
        """Zero tokens = zero cost."""
        cost = self.calc.calculate("gpt-4o", 0, 0)
        assert cost == 0.0

    def test_claude_pricing(self):
        """Claude models should have valid pricing."""
        cost = self.calc.calculate("claude-3.5-sonnet", 1000, 500)
        assert cost > 0.0

    def test_gemini_pricing(self):
        """Gemini models should have valid pricing."""
        cost = self.calc.calculate("gemini-1.5-pro", 1000, 500)
        assert cost > 0.0

    def test_all_models_have_pricing(self):
        """Every model in the pricing table should return a non-zero cost."""
        for model in self.calc.MODEL_PRICING:
            cost = self.calc.calculate(model, 100, 100)
            assert cost > 0.0, f"Model {model} returned zero cost"

    def test_prompt_only(self):
        """Should handle prompt-only calls (no completion)."""
        cost = self.calc.calculate("gpt-4o", 1000, 0)
        assert cost > 0.0

    def test_completion_only(self):
        """Should handle completion-only (no prompt)."""
        cost = self.calc.calculate("gpt-4o", 0, 500)
        assert cost > 0.0
