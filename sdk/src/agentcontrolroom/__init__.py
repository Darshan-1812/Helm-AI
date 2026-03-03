"""
Agent Control Room SDK
======================

Reliability Layer for Autonomous AI Agents.

Usage:
    from agentcontrolroom import trace, ACRClient

    client = ACRClient(api_key="your-key", endpoint="http://localhost:8000")

    @trace.agent(name="my-agent")
    def my_agent(query: str):
        ...

    @trace.tool(name="web-search")
    def search(query: str):
        ...
"""

from agentcontrolroom.tracer import trace, Tracer
from agentcontrolroom.client import ACRClient
from agentcontrolroom.spans import SpanKind
from agentcontrolroom.cost import CostCalculator

__version__ = "0.1.0"

__all__ = [
    "trace",
    "Tracer",
    "ACRClient",
    "SpanKind",
    "CostCalculator",
]
