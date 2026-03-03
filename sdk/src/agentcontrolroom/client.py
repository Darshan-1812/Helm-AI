"""
HTTP Client — ships trace data to the Agent Control Room backend.
Supports batching and async flush.
"""

import json
import threading
import time
import logging
from typing import Optional
from datetime import datetime, timezone

import httpx

from agentcontrolroom.spans import RunData

logger = logging.getLogger("agentcontrolroom")


class ACRClient:
    """
    HTTP client for Agent Control Room.

    Usage:
        client = ACRClient(
            api_key="acr-dev-xxxx",
            endpoint="http://localhost:8000",
        )

        # Ship a complete run
        client.send_run(run_data)

        # Or use auto-flush with batching
        client.queue_run(run_data)
        client.flush()  # or let background thread flush
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str = "http://localhost:8000",
        batch_size: int = 10,
        flush_interval: float = 5.0,
        timeout: float = 30.0,
        auto_flush: bool = True,
    ):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.timeout = timeout

        self._queue: list[RunData] = []
        self._lock = threading.Lock()
        self._client = httpx.Client(
            base_url=self.endpoint,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        # Background flush thread
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None
        if auto_flush:
            self._start_flush_thread()

    def send_run(self, run: RunData) -> dict:
        """Send a complete run synchronously to the backend."""
        try:
            payload = run.to_dict()
            response = self._client.post(
                "/api/v1/ingest/traces",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            logger.info(
                f"Trace sent: run_id={result.get('run_id')}, "
                f"spans={result.get('spans_ingested')}"
            )
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send trace: {e.response.status_code} {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to send trace: {e}")
            raise

    def queue_run(self, run: RunData):
        """Queue a run for batch sending."""
        with self._lock:
            self._queue.append(run)
            if len(self._queue) >= self.batch_size:
                self._flush_batch()

    def flush(self):
        """Flush all queued runs."""
        with self._lock:
            self._flush_batch()

    def _flush_batch(self):
        """Send all queued runs (called under lock)."""
        if not self._queue:
            return

        batch = list(self._queue)
        self._queue.clear()

        for run in batch:
            try:
                self.send_run(run)
            except Exception as e:
                logger.error(f"Failed to flush run {run.run_id}: {e}")

    def _start_flush_thread(self):
        """Start background thread for periodic flushing."""
        self._running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop, daemon=True, name="acr-flush"
        )
        self._flush_thread.start()

    def _flush_loop(self):
        """Background flush loop."""
        while self._running:
            time.sleep(self.flush_interval)
            try:
                self.flush()
            except Exception as e:
                logger.error(f"Background flush error: {e}")

    def close(self):
        """Flush remaining data and close the client."""
        self._running = False
        self.flush()
        self._client.close()

    def health_check(self) -> dict:
        """Check if the backend is healthy."""
        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
