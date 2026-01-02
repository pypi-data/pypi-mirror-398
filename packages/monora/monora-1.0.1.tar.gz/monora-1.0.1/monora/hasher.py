"""Immutable hash chaining for events."""
from __future__ import annotations

import hashlib
import json
import sys
from typing import Optional, Tuple

from .context import get_current_context


class Hasher:
    def __init__(self, config: dict):
        self.enabled = bool(config.get("enabled", True))
        self.scope = config.get("scope", "per_trace")
        self.algorithm = config.get("hash_algorithm", "sha256")
        self.global_chain: list[str] = []

    def hash_event(self, event: dict) -> Tuple[Optional[str], Optional[str]]:
        if not self.enabled:
            return None, None

        prev_hash = self._get_prev_hash()
        event_copy = {k: v for k, v in event.items() if k not in {"event_hash", "prev_hash"}}
        try:
            canonical = json.dumps(event_copy, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            print(f"Monora: failed to serialize event for hashing: {exc}", file=sys.stderr)
            return prev_hash, None

        hasher = hashlib.new(self.algorithm)
        if prev_hash:
            hasher.update(prev_hash.encode("utf-8"))
        hasher.update(canonical.encode("utf-8"))
        event_hash = f"{self.algorithm}:{hasher.hexdigest()}"

        self._append_hash(event_hash)
        return prev_hash, event_hash

    def _get_prev_hash(self) -> Optional[str]:
        if self.scope == "global":
            return self.global_chain[-1] if self.global_chain else None
        ctx = get_current_context()
        return ctx.hash_chain[-1] if ctx and ctx.hash_chain else None

    def _append_hash(self, event_hash: str) -> None:
        if self.scope == "global":
            self.global_chain.append(event_hash)
            return
        ctx = get_current_context()
        if ctx is not None:
            ctx.hash_chain.append(event_hash)
