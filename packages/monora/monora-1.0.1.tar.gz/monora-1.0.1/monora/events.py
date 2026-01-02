"""Event envelope builder and helpers."""
from __future__ import annotations

from typing import Dict, Optional

from ._internal import (
    EnvironmentEnricher,
    HostEnricher,
    ProcessEnricher,
    ServiceNameEnricher,
    TimestampEnricher,
    generate_ulid,
)
from .context import get_current_span, next_event_sequence


class EventBuilder:
    def __init__(self, config: Dict):
        self.defaults = config.get("defaults", {})
        self.enrichers = [
            TimestampEnricher(),
            ServiceNameEnricher(config),
            EnvironmentEnricher(config),
            HostEnricher(),
            ProcessEnricher(),
        ]

    def build(
        self,
        event_type: str,
        body: Dict,
        data_classification: Optional[str] = None,
        purpose: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict:
        span = get_current_span()
        event = {
            "schema_version": "1.0.0",
            "event_id": generate_ulid("evt"),
            "event_type": event_type,
            "trace_id": span.trace_id if span else generate_ulid("trc"),
            "span_id": span.span_id if span else generate_ulid("spn"),
            "parent_span_id": span.parent_span_id if span else None,
            "data_classification": data_classification
            or self.defaults.get("data_classification", "internal"),
            "purpose": purpose or self.defaults.get("purpose", "general"),
            "reason": reason,
            "body": body,
        }
        sequence = next_event_sequence()
        if sequence is not None:
            event["event_sequence"] = sequence
        for enricher in self.enrichers:
            enricher.enrich(event)
        return event
