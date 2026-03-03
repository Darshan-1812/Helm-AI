"""
LangChain Auto-Instrumentation (Stub)

TODO: Full implementation will monkey-patch LangChain's:
- BaseLLM.invoke / ainvoke
- BaseTool.run / arun
- BaseRetriever.get_relevant_documents

For now, provides a callback handler approach.
"""

from typing import Any, Optional
import logging

logger = logging.getLogger("agentcontrolroom.instruments.langchain")


class ACRCallbackHandler:
    """
    LangChain callback handler for Agent Control Room.

    Usage:
        from agentcontrolroom.instruments.langchain import ACRCallbackHandler
        from langchain_openai import ChatOpenAI

        handler = ACRCallbackHandler(tracer=trace)
        llm = ChatOpenAI(callbacks=[handler])
    """

    def __init__(self, tracer=None):
        self._tracer = tracer
        logger.info("ACR LangChain instrumentation initialized")

    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs):
        logger.debug(f"LLM started: {serialized.get('name', 'unknown')}")

    def on_llm_end(self, response: Any, **kwargs):
        logger.debug("LLM ended")

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        logger.debug(f"Tool started: {serialized.get('name', 'unknown')}")

    def on_tool_end(self, output: str, **kwargs):
        logger.debug("Tool ended")

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs):
        logger.debug(f"Chain started: {serialized.get('name', 'unknown')}")

    def on_chain_end(self, outputs: dict, **kwargs):
        logger.debug("Chain ended")

    def on_llm_error(self, error: Exception, **kwargs):
        logger.error(f"LLM error: {error}")

    def on_tool_error(self, error: Exception, **kwargs):
        logger.error(f"Tool error: {error}")
