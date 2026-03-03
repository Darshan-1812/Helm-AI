"""
CrewAI Auto-Instrumentation (Stub)

TODO: Full implementation will monkey-patch CrewAI's:
- Agent.execute_task
- Crew.kickoff
- Task.execute

For now, provides a callback-based approach.
"""

import logging
from typing import Any

logger = logging.getLogger("agentcontrolroom.instruments.crewai")


class ACRCrewCallback:
    """
    CrewAI callback handler for Agent Control Room.

    Usage:
        from agentcontrolroom.instruments.crewai import ACRCrewCallback

        callback = ACRCrewCallback(tracer=trace)

        # Pass callback to CrewAI agents
        agent = Agent(
            role="researcher",
            callbacks=[callback],
        )
    """

    def __init__(self, tracer=None):
        self._tracer = tracer
        logger.info("ACR CrewAI instrumentation initialized")

    def on_agent_start(self, agent_name: str, task: str, **kwargs):
        logger.debug(f"CrewAI agent started: {agent_name}, task: {task[:50]}")

    def on_agent_end(self, agent_name: str, result: Any, **kwargs):
        logger.debug(f"CrewAI agent ended: {agent_name}")

    def on_task_start(self, task_name: str, agent_name: str, **kwargs):
        logger.debug(f"CrewAI task started: {task_name} (agent: {agent_name})")

    def on_task_end(self, task_name: str, result: Any, **kwargs):
        logger.debug(f"CrewAI task ended: {task_name}")

    def on_crew_start(self, crew_name: str, tasks: list, **kwargs):
        logger.debug(f"CrewAI crew started: {crew_name}, {len(tasks)} tasks")

    def on_crew_end(self, crew_name: str, result: Any, **kwargs):
        logger.debug(f"CrewAI crew ended: {crew_name}")

    def on_tool_use(self, tool_name: str, input_data: str, **kwargs):
        logger.debug(f"CrewAI tool used: {tool_name}")

    def on_error(self, error: Exception, context: str = "", **kwargs):
        logger.error(f"CrewAI error in {context}: {error}")
