"""
LlamaIndex Auto-Instrumentation (Stub)

TODO: Full implementation will monkey-patch LlamaIndex's:
- LLM.complete / acomplete
- LLM.chat / achat
- BaseRetriever.retrieve
- QueryEngine.query

For now, provides a callback handler approach.
"""

import logging
from typing import Any

logger = logging.getLogger("agentcontrolroom.instruments.llamaindex")


class ACRLlamaIndexCallback:
    """
    LlamaIndex callback handler for Agent Control Room.

    Usage:
        from agentcontrolroom.instruments.llamaindex import ACRLlamaIndexCallback
        from llama_index.core import Settings

        handler = ACRLlamaIndexCallback(tracer=trace)
        Settings.callback_manager.add_handler(handler)
    """

    def __init__(self, tracer=None):
        self._tracer = tracer
        logger.info("ACR LlamaIndex instrumentation initialized")

    def on_llm_start(self, model: str, messages: list, **kwargs):
        logger.debug(f"LlamaIndex LLM started: {model}")

    def on_llm_end(self, response: Any, **kwargs):
        logger.debug("LlamaIndex LLM ended")

    def on_retrieval_start(self, query: str, **kwargs):
        logger.debug(f"LlamaIndex retrieval started: {query[:50]}")

    def on_retrieval_end(self, nodes: list, **kwargs):
        logger.debug(f"LlamaIndex retrieval ended: {len(nodes)} nodes")

    def on_query_start(self, query: str, **kwargs):
        logger.debug(f"LlamaIndex query started: {query[:50]}")

    def on_query_end(self, response: Any, **kwargs):
        logger.debug("LlamaIndex query ended")

    def on_embedding_start(self, texts: list, **kwargs):
        logger.debug(f"LlamaIndex embedding: {len(texts)} texts")

    def on_embedding_end(self, embeddings: list, **kwargs):
        logger.debug(f"LlamaIndex embedding done: {len(embeddings)} vectors")

    def on_reranking_start(self, query: str, nodes: list, **kwargs):
        logger.debug(f"LlamaIndex reranking: {len(nodes)} nodes")

    def on_reranking_end(self, nodes: list, **kwargs):
        logger.debug(f"LlamaIndex reranking done: {len(nodes)} nodes")

    def on_error(self, error: Exception, context: str = "", **kwargs):
        logger.error(f"LlamaIndex error in {context}: {error}")
