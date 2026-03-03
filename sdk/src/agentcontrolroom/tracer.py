"""
Tracer — decorator-based tracing for AI agents and tools.

The core of the SDK. Provides `@trace.agent` and `@trace.tool` decorators
that capture full execution context automatically.
"""

import uuid
import functools
import threading
import logging
from typing import Optional, Callable, Any
from datetime import datetime, timezone
from contextlib import contextmanager

from agentcontrolroom.spans import SpanData, RunData, SpanKind
from agentcontrolroom.cost import CostCalculator
from agentcontrolroom.client import ACRClient

logger = logging.getLogger("agentcontrolroom")


class Tracer:
    """
    Main tracer class — captures agent execution traces.

    Usage:
        tracer = Tracer(
            api_key="acr-dev-xxxx",
            endpoint="http://localhost:8000",
            agent_name="my-agent",
        )

        @tracer.agent(name="research-agent")
        def research(query):
            ...

        @tracer.tool(name="web-search")
        def search(query):
            ...

        # Or manually:
        with tracer.start_run("my-agent") as run:
            with tracer.start_span("llm-call", SpanKind.LLM) as span:
                span.model = "gpt-4o"
                span.input_data = "Hello"
                result = llm.invoke("Hello")
                span.output_data = result
                span.tokens_prompt = 10
                span.tokens_completion = 50
    """

    def __init__(
        self,
        api_key: str = "",
        endpoint: str = "http://localhost:8000",
        auto_send: bool = True,
    ):
        self._client: Optional[ACRClient] = None
        self._api_key = api_key
        self._endpoint = endpoint
        self._auto_send = auto_send
        self._cost_calculator = CostCalculator()

        # Thread-local storage for current run/span context
        self._local = threading.local()

        if api_key:
            self._client = ACRClient(
                api_key=api_key,
                endpoint=endpoint,
            )

    @property
    def _current_run(self) -> Optional[RunData]:
        return getattr(self._local, "current_run", None)

    @_current_run.setter
    def _current_run(self, value):
        self._local.current_run = value

    @property
    def _current_span(self) -> Optional[SpanData]:
        return getattr(self._local, "current_span", None)

    @_current_span.setter
    def _current_span(self, value):
        self._local.current_span = value

    @property
    def _span_stack(self) -> list[SpanData]:
        if not hasattr(self._local, "span_stack"):
            self._local.span_stack = []
        return self._local.span_stack

    def configure(self, api_key: str, endpoint: str = "http://localhost:8000"):
        """Configure the tracer with API credentials."""
        self._api_key = api_key
        self._endpoint = endpoint
        self._client = ACRClient(api_key=api_key, endpoint=endpoint)

    # ── Decorators ───────────────────────────────────

    def agent(
        self,
        name: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ):
        """
        Decorator to trace an agent function.

        @trace.agent(name="research-agent")
        def research(query: str):
            ...
        """
        def decorator(func: Callable) -> Callable:
            agent_name = name or func.__name__

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Create a new run
                run = RunData(
                    agent_name=agent_name,
                    input_text=str(args[0]) if args else str(kwargs),
                    tags=tags or [],
                    metadata=metadata or {},
                )
                self._current_run = run

                # Create root agent span
                span = SpanData(
                    name=agent_name,
                    span_kind=SpanKind.AGENT,
                    run_id=run.run_id,
                    input_data=str(args[0]) if args else str(kwargs),
                )
                self._current_span = span
                self._span_stack.append(span)

                try:
                    result = func(*args, **kwargs)

                    # Finish span
                    span.output_data = str(result) if result else None
                    span.finish()

                    # Finish run
                    run.add_span(span)
                    run.finish(output=str(result) if result else None, status="completed")

                    # Auto-send
                    if self._auto_send and self._client:
                        try:
                            self._client.send_run(run)
                        except Exception as e:
                            logger.error(f"Failed to send trace: {e}")

                    return result

                except Exception as e:
                    span.set_error(e)
                    span.finish()
                    run.add_span(span)
                    run.finish(status="failed")

                    if self._auto_send and self._client:
                        try:
                            self._client.send_run(run)
                        except Exception as send_err:
                            logger.error(f"Failed to send error trace: {send_err}")

                    raise

                finally:
                    self._span_stack.pop() if self._span_stack else None
                    self._current_span = self._span_stack[-1] if self._span_stack else None
                    self._current_run = None

            return wrapper
        return decorator

    def tool(self, name: Optional[str] = None):
        """
        Decorator to trace a tool function.

        @trace.tool(name="web-search")
        def search(query: str):
            ...
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                parent_span = self._current_span
                parent_id = parent_span.span_id if parent_span else None
                run_id = self._current_run.run_id if self._current_run else None

                span = SpanData(
                    name=tool_name,
                    span_kind=SpanKind.TOOL,
                    parent_span_id=parent_id,
                    run_id=run_id,
                    input_data=str({"args": args, "kwargs": kwargs}),
                )
                self._current_span = span
                self._span_stack.append(span)

                try:
                    result = func(*args, **kwargs)
                    span.output_data = str(result) if result else None
                    span.finish()

                    # Add to current run
                    if self._current_run:
                        self._current_run.add_span(span)

                    return result

                except Exception as e:
                    span.set_error(e)
                    span.finish()
                    if self._current_run:
                        self._current_run.add_span(span)
                    raise

                finally:
                    self._span_stack.pop() if self._span_stack else None
                    self._current_span = self._span_stack[-1] if self._span_stack else None

            return wrapper
        return decorator

    def llm_call(
        self,
        name: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Decorator to trace an LLM call.

        @trace.llm_call(name="generate", model="gpt-4o")
        def generate(prompt: str):
            ...
        """
        def decorator(func: Callable) -> Callable:
            call_name = name or func.__name__

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                parent_span = self._current_span
                parent_id = parent_span.span_id if parent_span else None
                run_id = self._current_run.run_id if self._current_run else None

                span = SpanData(
                    name=call_name,
                    span_kind=SpanKind.LLM,
                    parent_span_id=parent_id,
                    run_id=run_id,
                    model=model,
                    input_data=str(args[0]) if args else str(kwargs),
                )
                self._current_span = span
                self._span_stack.append(span)

                try:
                    result = func(*args, **kwargs)

                    span.output_data = str(result) if result else None
                    span.finish()

                    # Calculate cost if we have token info
                    if model and span.tokens_prompt is not None:
                        cost = self._cost_calculator.calculate(
                            model,
                            span.tokens_prompt or 0,
                            span.tokens_completion or 0,
                        )
                        if cost is not None:
                            span.cost = cost

                    if self._current_run:
                        self._current_run.add_span(span)

                    return result

                except Exception as e:
                    span.set_error(e)
                    span.finish()
                    if self._current_run:
                        self._current_run.add_span(span)
                    raise

                finally:
                    self._span_stack.pop() if self._span_stack else None
                    self._current_span = self._span_stack[-1] if self._span_stack else None

            return wrapper
        return decorator

    # ── Context Managers ─────────────────────────────

    @contextmanager
    def start_run(self, agent_name: str, input_text: str = "", **kwargs):
        """
        Context manager to manually create a run.

        with tracer.start_run("my-agent") as run:
            ...
        """
        run = RunData(
            agent_name=agent_name,
            input_text=input_text,
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
        )
        self._current_run = run

        try:
            yield run
            run.finish(status="completed")
        except Exception as e:
            run.finish(status="failed")
            raise
        finally:
            if self._auto_send and self._client:
                try:
                    self._client.send_run(run)
                except Exception as e:
                    logger.error(f"Failed to send run: {e}")
            self._current_run = None

    @contextmanager
    def start_span(self, name: str, span_kind: SpanKind = SpanKind.CHAIN, **kwargs):
        """
        Context manager to manually create a span.

        with tracer.start_span("llm-call", SpanKind.LLM) as span:
            span.model = "gpt-4o"
            ...
        """
        parent_span = self._current_span
        parent_id = parent_span.span_id if parent_span else None
        run_id = self._current_run.run_id if self._current_run else None

        span = SpanData(
            name=name,
            span_kind=span_kind,
            parent_span_id=parent_id,
            run_id=run_id,
            model=kwargs.get("model"),
            input_data=kwargs.get("input_data"),
        )

        self._current_span = span
        self._span_stack.append(span)

        try:
            yield span
            span.finish()

            # Auto-calculate cost for LLM spans
            if span.model and span.tokens_prompt is not None:
                cost = self._cost_calculator.calculate(
                    span.model,
                    span.tokens_prompt or 0,
                    span.tokens_completion or 0,
                )
                if cost is not None:
                    span.cost = cost

        except Exception as e:
            span.set_error(e)
            span.finish()
            raise
        finally:
            if self._current_run:
                self._current_run.add_span(span)
            self._span_stack.pop() if self._span_stack else None
            self._current_span = self._span_stack[-1] if self._span_stack else None

    def close(self):
        """Close the tracer and flush remaining data."""
        if self._client:
            self._client.close()


# ── Global tracer singleton ──────────────────────────
trace = Tracer()
