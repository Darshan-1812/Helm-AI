"""Tests for SDK tracer decorators and context managers."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agentcontrolroom.tracer import Tracer
from agentcontrolroom.spans import SpanKind


class TestTracer:
    """Tests for Tracer decorator-based tracing."""

    def setup_method(self):
        self.tracer = Tracer(auto_send=False)

    def test_tracer_init(self):
        assert self.tracer is not None
        assert self.tracer._auto_send is False

    def test_agent_decorator(self):
        """@trace.agent should capture function execution."""
        @self.tracer.agent("test-agent")
        def my_agent(query):
            return f"result: {query}"

        result = my_agent("hello")
        assert result == "result: hello"

    def test_tool_decorator(self):
        """@trace.tool should capture tool calls."""
        @self.tracer.tool("search")
        def my_tool(query):
            return f"found: {query}"

        result = my_tool("test")
        assert result == "found: test"

    def test_llm_call_decorator(self):
        """@trace.llm_call should capture LLM calls."""
        @self.tracer.llm_call("gpt-4o")
        def my_llm(prompt):
            return "AI response"

        result = my_llm("tell me a joke")
        assert result == "AI response"

    def test_nested_decorators(self):
        """Nested decorated functions should work correctly."""
        @self.tracer.agent("outer-agent")
        def outer():
            return inner()

        @self.tracer.tool("inner-tool")
        def inner():
            return "inner result"

        result = outer()
        assert result == "inner result"

    def test_decorator_preserves_exceptions(self):
        """Decorated function should re-raise exceptions."""
        @self.tracer.tool("failing-tool")
        def failing():
            raise ValueError("test error")

        try:
            failing()
            assert False, "Should have raised"
        except ValueError as e:
            assert str(e) == "test error"

    def test_context_manager(self):
        """Context manager style tracing should work."""
        with self.tracer.span("custom-op", kind="tool") as span:
            span.set_input("input data")
            span.set_output("output data")

    def test_multiple_calls(self):
        """Multiple calls to the same decorated function should each trace."""
        @self.tracer.tool("counter")
        def count(n):
            return n * 2

        results = [count(i) for i in range(5)]
        assert results == [0, 2, 4, 6, 8]
