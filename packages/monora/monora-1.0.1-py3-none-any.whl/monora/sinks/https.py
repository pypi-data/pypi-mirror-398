"""HTTP sink."""
from __future__ import annotations

import random
import threading
import time
from typing import Dict, Iterable, List

try:
    import requests
except ImportError as exc:  # pragma: no cover - optional dependency
    requests = None
    _requests_import_error = exc
else:
    _requests_import_error = None

from .base import Sink, SinkError


class HttpSink(Sink):
    def __init__(
        self,
        endpoint: str,
        headers: Dict[str, str],
        *,
        batch_size: int = 50,
        timeout_sec: float = 10.0,
        retry_attempts: int = 3,
        backoff_base_sec: float = 0.5,
    ):
        if requests is None:
            raise SinkError(
                "requests is required for HttpSink. Install with monora[https]."
            ) from _requests_import_error
        self.endpoint = endpoint
        self.headers = headers
        self.batch_size = batch_size
        self.timeout = timeout_sec
        self.retries = retry_attempts
        self.backoff_base_sec = backoff_base_sec
        self.buffer: List[dict] = []
        self.lock = threading.Lock()

    def emit(self, events: Iterable[dict]) -> None:
        with self.lock:
            self.buffer.extend(events)
            if len(self.buffer) >= self.batch_size:
                self._flush_internal()

    def flush(self) -> None:
        with self.lock:
            self._flush_internal()

    def close(self) -> None:
        self.flush()

    def _flush_internal(self) -> None:
        if not self.buffer:
            return
        payload = {"events": self.buffer}
        for attempt in range(self.retries):
            try:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                self.buffer.clear()
                return
            except requests.RequestException as exc:
                if attempt == self.retries - 1:
                    raise SinkError(
                        f"HTTP sink failed after {self.retries} attempts"
                    ) from exc
                backoff = self.backoff_base_sec * (2**attempt) + random.uniform(0, 0.1)
                time.sleep(backoff)
