"""Stdout sink."""
from __future__ import annotations

import json
from typing import Iterable

from .base import Sink


class StdoutSink(Sink):
    def __init__(self, format: str = "json"):
        self.format = format

    def emit(self, events: Iterable[dict]) -> None:
        for event in events:
            if self.format == "pretty":
                print(json.dumps(event, indent=2))
            else:
                print(json.dumps(event))

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None
