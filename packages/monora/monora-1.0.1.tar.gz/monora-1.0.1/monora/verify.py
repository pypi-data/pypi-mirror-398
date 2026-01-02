"""Hash chain verification utilities."""
from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional, Tuple


class ChainVerificationError(Exception):
    """Raised when hash chain verification fails."""

    pass


def verify_event_hash(event: Dict) -> bool:
    """Verify that an event's hash matches its contents.

    Args:
        event: Event dictionary with event_hash field

    Returns:
        True if hash is valid, False otherwise
    """
    if "event_hash" not in event:
        return False

    event_hash = event["event_hash"]
    if not event_hash or ":" not in event_hash:
        return False

    algorithm, expected_hash = event_hash.split(":", 1)

    # Recreate canonical JSON
    event_copy = {k: v for k, v in event.items() if k not in {"event_hash", "prev_hash"}}
    canonical = json.dumps(event_copy, sort_keys=True, separators=(",", ":"))

    # Compute hash with prev_hash if present
    hasher = hashlib.new(algorithm)
    if event.get("prev_hash"):
        hasher.update(event["prev_hash"].encode("utf-8"))
    hasher.update(canonical.encode("utf-8"))

    computed_hash = hasher.hexdigest()
    return computed_hash == expected_hash


def verify_chain(events: List[Dict]) -> Tuple[bool, Optional[str]]:
    """Verify the integrity of a hash chain.

    Args:
        events: List of events in chronological order

    Returns:
        Tuple of (is_valid, error_message)
        is_valid is True if chain is valid, False otherwise
        error_message is None if valid, or description of error
    """
    if not events:
        return True, None

    # Verify first event has no prev_hash
    first = events[0]
    if first.get("prev_hash") is not None:
        return False, f"First event {first.get('event_id')} has prev_hash (should be None)"

    # Verify each event's hash
    for i, event in enumerate(events):
        if not verify_event_hash(event):
            return (
                False,
                f"Event {event.get('event_id')} at index {i} has invalid hash",
            )

    # Verify chain linkage
    for i in range(1, len(events)):
        prev_event = events[i - 1]
        curr_event = events[i]

        expected_prev = prev_event.get("event_hash")
        actual_prev = curr_event.get("prev_hash")

        if expected_prev != actual_prev:
            return (
                False,
                f"Chain break at index {i}: event {curr_event.get('event_id')} "
                f"prev_hash={actual_prev} but previous event hash={expected_prev}",
            )

    return True, None


def verify_trace_chain(events: List[Dict], trace_id: str) -> Tuple[bool, Optional[str]]:
    """Verify hash chain for events in a specific trace.

    Args:
        events: List of all events
        trace_id: Trace ID to filter by

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Filter events for this trace
    trace_events = [e for e in events if e.get("trace_id") == trace_id]

    if not trace_events:
        return True, None

    # Sort by timestamp to ensure chronological order
    trace_events.sort(key=lambda e: e.get("timestamp", ""))

    return verify_chain(trace_events)


def detect_tampering(events: List[Dict]) -> List[Dict]:
    """Detect potentially tampered events in a chain.

    Args:
        events: List of events

    Returns:
        List of events that appear to be tampered with
    """
    tampered = []

    for event in events:
        if not verify_event_hash(event):
            tampered.append(
                {
                    "event_id": event.get("event_id"),
                    "timestamp": event.get("timestamp"),
                    "reason": "Invalid event hash",
                }
            )

    # Check chain linkage
    for i in range(1, len(events)):
        prev_hash = events[i - 1].get("event_hash")
        curr_prev = events[i].get("prev_hash")

        if prev_hash != curr_prev:
            tampered.append(
                {
                    "event_id": events[i].get("event_id"),
                    "timestamp": events[i].get("timestamp"),
                    "reason": f"Chain break: expected prev_hash={prev_hash}, got={curr_prev}",
                }
            )

    return tampered


def detect_sequence_gaps(events: List[Dict]) -> List[Dict]:
    """Detect gaps in per-trace event sequence numbers."""
    traces: Dict[str, List[int]] = {}
    for event in events:
        trace_id = event.get("trace_id")
        seq = event.get("event_sequence")
        if not trace_id or not isinstance(seq, int):
            continue
        traces.setdefault(trace_id, []).append(seq)

    gaps = []
    for trace_id, seqs in traces.items():
        if not seqs:
            continue
        seqs_sorted = sorted(seqs)
        expected_max = seqs_sorted[-1]
        expected = set(range(1, expected_max + 1))
        observed = set(seqs_sorted)
        missing = sorted(expected - observed)
        duplicates = _find_duplicates(seqs_sorted)
        if missing or duplicates:
            gaps.append(
                {
                    "trace_id": trace_id,
                    "expected_count": expected_max,
                    "observed_count": len(seqs_sorted),
                    "missing_sequences": missing,
                    "duplicate_sequences": duplicates,
                }
            )
    return gaps


def _find_duplicates(values: List[int]) -> List[int]:
    duplicates = []
    seen = set()
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates
