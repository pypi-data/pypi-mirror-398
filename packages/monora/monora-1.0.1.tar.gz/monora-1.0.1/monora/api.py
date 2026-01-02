"""Public API helpers."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .runtime import emit_event, ensure_state


def log_event(
    event_type: str,
    data: Dict[str, Any],
    *,
    data_classification: Optional[str] = None,
    purpose: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """Log a custom event."""
    state = ensure_state()
    event = state.event_builder.build(
        event_type,
        data,
        data_classification=data_classification,
        purpose=purpose,
        reason=reason,
    )
    emit_event(event)
