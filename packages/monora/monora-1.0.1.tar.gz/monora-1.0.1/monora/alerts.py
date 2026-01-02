"""Violation alert dispatching."""
from __future__ import annotations

import queue
import random
import sys
import threading
import time
from typing import Any, Dict, Optional

try:
    import requests
except ImportError as exc:  # pragma: no cover - optional dependency
    requests = None
    _requests_import_error = exc
else:
    _requests_import_error = None


class AlertError(Exception):
    """Alert dispatch failure."""


def build_violation_payload(
    *,
    violation: Any,
    trace_id: Optional[str],
    span_id: Optional[str],
    parent_span_id: Optional[str],
    service_name: Optional[str],
    environment: Optional[str],
) -> Dict[str, Any]:
    payload = {
        "event_type": "policy_violation",
        "policy_event_type": getattr(violation, "event_type", None),
        "model": getattr(violation, "model", None),
        "policy_name": getattr(violation, "policy_name", None),
        "message": getattr(violation, "message", None),
        "timestamp": getattr(violation, "timestamp", None),
        "data_classification": getattr(violation, "data_classification", None),
        "rule_names": getattr(violation, "rule_names", None),
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "service_name": service_name,
        "environment": environment,
    }
    return payload


class ViolationWebhookDispatcher:
    def __init__(
        self,
        endpoint: str,
        headers: Dict[str, str],
        *,
        timeout_sec: float = 5.0,
        retry_attempts: int = 3,
        backoff_base_sec: float = 0.5,
        queue_size: int = 200,
        failure_mode: str = "warn",
        queue_full_mode: str = "warn",
    ) -> None:
        if requests is None:
            raise AlertError(
                "requests is required for violation_webhook alerts. Install monora[https]."
            ) from _requests_import_error
        self.endpoint = endpoint
        self.headers = headers
        self.timeout = timeout_sec
        self.retries = retry_attempts
        self.backoff_base_sec = backoff_base_sec
        self.queue = queue.Queue(maxsize=queue_size)
        self.failure_mode = failure_mode
        self.queue_full_mode = queue_full_mode
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._fatal_error: Optional[Exception] = None

    def start(self) -> None:
        self._thread.start()

    def send(self, payload: Dict[str, Any]) -> None:
        if self._fatal_error and self.failure_mode == "raise":
            raise AlertError("Violation webhook dispatcher failed") from self._fatal_error
        try:
            self.queue.put_nowait(payload)
        except queue.Full:
            self._handle_queue_full()

    def flush(self) -> None:
        while True:
            try:
                payload = self.queue.get_nowait()
            except queue.Empty:
                break
            self._send_payload(payload)

    def close(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2.0)
        self.flush()

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                payload = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self._send_payload(payload)

    def _send_payload(self, payload: Dict[str, Any]) -> None:
        for attempt in range(self.retries):
            try:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return
            except requests.RequestException as exc:
                if attempt == self.retries - 1:
                    self._handle_failure(exc)
                    return
                backoff = self.backoff_base_sec * (2**attempt) + random.uniform(0, 0.1)
                time.sleep(backoff)

    def _handle_queue_full(self) -> None:
        message = "Monora violation webhook queue full; dropping alert"
        if self.queue_full_mode == "raise":
            raise AlertError(message)
        if self.queue_full_mode == "warn":
            print(message, file=sys.stderr)

    def _handle_failure(self, exc: Exception) -> None:
        if self.failure_mode == "raise":
            self._fatal_error = exc
            return
        if self.failure_mode == "warn":
            print(f"Monora violation webhook failed: {exc}", file=sys.stderr)


def expand_headers(headers: Dict[str, Any]) -> Dict[str, str]:
    expanded: Dict[str, str] = {}
    for key, value in headers.items():
        expanded[key] = _expand_env(str(value))
    return expanded


def _expand_env(value: str) -> str:
    if "${" not in value:
        return value
    result = value
    for part in value.split("${"):
        if "}" not in part:
            continue
        env_key = part.split("}")[0]
        env_val = os.getenv(env_key, "")
        result = result.replace(f"${{{env_key}}}", env_val)
    return result


import os  # keep at end for minimal import side-effects
