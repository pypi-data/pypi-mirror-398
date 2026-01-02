"""Runtime state and event dispatching."""
from __future__ import annotations

import atexit
import asyncio
import inspect
import queue
import sys
import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from .alerts import (
    AlertError,
    ViolationWebhookDispatcher,
    build_violation_payload,
    expand_headers,
)
from .config import load_config
from .data_handling import DataHandlingEngine
from .events import EventBuilder
from .hasher import Hasher
from .policy import PolicyEngine, PolicyViolation
from .context import get_current_span
from .registry import ModelRegistry
from .sinks import build_sinks
from .sinks.base import Sink, SinkError
from .sinks.file import FileSink


@dataclass
class MonoraState:
    config: dict
    event_builder: EventBuilder
    policy_engine: PolicyEngine
    hasher: Hasher
    dispatcher: "EventDispatcher"
    registry: ModelRegistry
    violation_handler: Optional[Callable[[Exception], None]] = None
    violation_dispatcher: Optional[ViolationWebhookDispatcher] = None
    data_handler: Optional[DataHandlingEngine] = None


class EventDispatcher:
    def __init__(self, sinks: List[Sink], config: dict):
        self.sinks = sinks
        buffering = config.get("buffering", {})
        error_handling = config.get("error_handling", {})
        self.queue = queue.Queue(maxsize=buffering.get("queue_size", 1000))
        self.batch_size = buffering.get("batch_size", 50)
        self.flush_interval = buffering.get("flush_interval_sec", 1.0)
        self.queue_full_timeout = buffering.get("queue_full_timeout_sec")
        self.sink_failure_mode = error_handling.get("sink_failure_mode", "warn")
        self.queue_full_mode = error_handling.get("queue_full_mode", "warn")
        self.fallback_path = error_handling.get("fallback_path")
        self._fallback_sink: Optional[FileSink] = None
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._fatal_error: Optional[Exception] = None
        self._flush_lock = threading.Lock()

    def start(self) -> None:
        self._thread.start()

    def emit(self, event: dict) -> None:
        if self._fatal_error and self.sink_failure_mode == "raise":
            raise SinkError("Monora dispatcher is in failed state") from self._fatal_error
        if self.queue_full_mode == "block":
            try:
                if self.queue_full_timeout is None:
                    self.queue.put(event)
                else:
                    self.queue.put(event, timeout=self.queue_full_timeout)
                return
            except queue.Full:
                self._handle_queue_full([event])
                return
        try:
            self.queue.put_nowait(event)
        except queue.Full:
            self._handle_queue_full([event])

    def flush(self) -> None:
        with self._flush_lock:
            events = self._drain_queue()
            if events:
                self._emit_to_sinks(events)
            for sink in self.sinks:
                try:
                    sink.flush()
                except Exception as exc:
                    self._handle_sink_error(sink, [], exc)

    def close(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2.0)
        self.flush()
        for sink in self.sinks:
            try:
                sink.close()
            except Exception as exc:
                self._handle_sink_error(sink, [], exc)
        if self._fallback_sink:
            self._fallback_sink.close()

    def _worker(self) -> None:
        batch: List[dict] = []
        last_flush = time.monotonic()
        while not self._stop_event.is_set():
            timeout = max(0.1, self.flush_interval)
            try:
                event = self.queue.get(timeout=timeout)
            except queue.Empty:
                event = None
            if event is not None:
                batch.append(event)
            now = time.monotonic()
            if batch and (len(batch) >= self.batch_size or now - last_flush >= self.flush_interval):
                self._emit_to_sinks(batch)
                batch = []
                last_flush = now
        if batch:
            self._emit_to_sinks(batch)
        remaining = self._drain_queue()
        if remaining:
            self._emit_to_sinks(remaining)

    def _drain_queue(self) -> List[dict]:
        drained: List[dict] = []
        while True:
            try:
                drained.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return drained

    def _emit_to_sinks(self, events: Iterable[dict]) -> None:
        events_list = list(events)
        if not events_list:
            return
        for sink in self.sinks:
            try:
                sink.emit(events_list)
            except Exception as exc:
                self._handle_sink_error(sink, events_list, exc)

    def _handle_queue_full(self, events: List[dict]) -> None:
        message = "Monora queue full; dropping events"
        if self.queue_full_mode == "raise":
            raise SinkError(message)
        if self.queue_full_mode == "warn":
            print(message, file=sys.stderr)
        self._emit_to_fallback(events)

    def _handle_sink_error(self, sink: Sink, events: Iterable[dict], exc: Exception) -> None:
        message = f"Monora sink failure ({sink.__class__.__name__}): {exc}"
        if self.sink_failure_mode == "raise":
            self._fatal_error = exc
        elif self.sink_failure_mode == "warn":
            print(message, file=sys.stderr)
        self._emit_to_fallback(list(events))

    def _emit_to_fallback(self, events: List[dict]) -> None:
        if not self.fallback_path or not events:
            return
        if self._fallback_sink is None:
            try:
                self._fallback_sink = FileSink(
                    self.fallback_path, batch_size=1, flush_interval_sec=0.0
                )
            except Exception as exc:
                print(f"Monora fallback sink init failed: {exc}", file=sys.stderr)
                return
        try:
            self._fallback_sink.emit(events)
            self._fallback_sink.flush()
        except Exception as exc:
            print(f"Monora fallback sink emit failed: {exc}", file=sys.stderr)


_state: Optional[MonoraState] = None
_state_lock = threading.Lock()


def init(
    *,
    config_path: Optional[str] = None,
    config_dict: Optional[dict] = None,
    env_prefix: str = "MONORA_",
    fail_fast: bool = False,
) -> None:
    global _state
    with _state_lock:
        if _state is not None:
            _state.dispatcher.close()
            _state = None
        _init_locked(
            config_path=config_path,
            config_dict=config_dict,
            env_prefix=env_prefix,
            fail_fast=fail_fast,
        )


def _init_locked(
    *,
    config_path: Optional[str] = None,
    config_dict: Optional[dict] = None,
    env_prefix: str = "MONORA_",
    fail_fast: bool = False,
) -> None:
    global _state
    config = load_config(
        config_path=config_path, config_dict=config_dict, env_prefix=env_prefix
    )
    sinks = build_sinks(config.get("sinks", []), fail_fast=fail_fast)
    if not sinks:
        sinks = build_sinks([{"type": "stdout"}], fail_fast=True)

    dispatcher = EventDispatcher(sinks, config)

    registry = ModelRegistry(config.get("registry", {}))

    state = MonoraState(
        config=config,
        event_builder=EventBuilder(config),
        policy_engine=PolicyEngine(config.get("policies", {})),
        hasher=Hasher(config.get("immutability", {})),
        dispatcher=dispatcher,
        registry=registry,
    )
    state.data_handler = DataHandlingEngine(config.get("data_handling", {}))
    try:
        _init_violation_dispatcher(state, fail_fast=fail_fast)
        _auto_instrument(config, fail_fast=fail_fast)
    except Exception:
        _close_sinks(sinks)
        if state.violation_dispatcher:
            state.violation_dispatcher.close()
        raise
    dispatcher.start()
    _state = state
    atexit.register(shutdown)


def _close_sinks(sinks: List[Sink]) -> None:
    for sink in sinks:
        try:
            result = sink.close()
            if inspect.isawaitable(result):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    asyncio.run(result)
                else:
                    loop.create_task(result)
        except Exception as exc:
            print(f"Monora: failed to close sink: {exc}", file=sys.stderr)


def ensure_state() -> MonoraState:
    global _state
    if _state is None:
        with _state_lock:
            if _state is None:
                _init_locked()
    return _state  # type: ignore[return-value]


def shutdown() -> None:
    global _state
    with _state_lock:
        if _state is None:
            return
        _state.dispatcher.close()
        if _state.violation_dispatcher:
            _state.violation_dispatcher.close()
        _state = None


def set_violation_handler(handler: Callable[[Exception], None]) -> None:
    state = ensure_state()
    state.violation_handler = handler


def emit_event(event: dict) -> None:
    state = ensure_state()
    if state.data_handler:
        classification = event.get("data_classification") or state.config.get("defaults", {}).get(
            "data_classification", "internal"
        )
        event["body"] = state.data_handler.apply_to_event_body(
            event.get("event_type", "custom"), event.get("body", {}), classification
        )
    prev_hash, event_hash = state.hasher.hash_event(event)
    event["prev_hash"] = prev_hash
    event["event_hash"] = event_hash
    state.dispatcher.emit(event)


def notify_violation(violation: PolicyViolation) -> None:
    state = ensure_state()
    if state.violation_handler:
        try:
            state.violation_handler(violation)
        except Exception as exc:
            print(f"Monora violation handler error: {exc}", file=sys.stderr)
    if state.violation_dispatcher:
        span = get_current_span()
        payload = build_violation_payload(
            violation=violation,
            trace_id=span.trace_id if span else None,
            span_id=span.span_id if span else None,
            parent_span_id=span.parent_span_id if span else None,
            service_name=state.config.get("defaults", {}).get("service_name"),
            environment=state.config.get("defaults", {}).get("environment"),
        )
        try:
            state.violation_dispatcher.send(payload)
        except Exception as exc:
            print(f"Monora violation webhook error: {exc}", file=sys.stderr)


def _init_violation_dispatcher(state: MonoraState, *, fail_fast: bool) -> None:
    alerts_config = state.config.get("alerts", {})
    endpoint = alerts_config.get("violation_webhook")
    if not endpoint:
        return
    error_handling = state.config.get("error_handling", {})
    try:
        dispatcher = ViolationWebhookDispatcher(
            endpoint,
            expand_headers(alerts_config.get("headers", {})),
            timeout_sec=alerts_config.get("timeout_sec", 5.0),
            retry_attempts=alerts_config.get("retry_attempts", 3),
            backoff_base_sec=alerts_config.get("backoff_base_sec", 0.5),
            queue_size=alerts_config.get("queue_size", 200),
            failure_mode=error_handling.get("sink_failure_mode", "warn"),
            queue_full_mode=error_handling.get("queue_full_mode", "warn"),
        )
        dispatcher.start()
        state.violation_dispatcher = dispatcher
    except AlertError as exc:
        if fail_fast:
            raise
        print(f"Monora: failed to init violation webhook: {exc}", file=sys.stderr)


def _auto_instrument(config: dict, *, fail_fast: bool) -> None:
    try:
        from .instrumentation import InstrumentationError, auto_instrument
    except Exception as exc:
        if fail_fast:
            raise
        print(f"Monora: failed to load instrumentation: {exc}", file=sys.stderr)
        return

    try:
        auto_instrument(config, fail_fast=fail_fast)
    except InstrumentationError as exc:
        if fail_fast:
            raise
        print(f"Monora: auto-instrumentation failed: {exc}", file=sys.stderr)
