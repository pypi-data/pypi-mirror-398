"""Sink interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class SinkError(Exception):
    """Sink failure."""


class Sink(ABC):
    @abstractmethod
    def emit(self, events: Iterable[dict]) -> None:
        """Emit one or more events."""

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered events."""

    @abstractmethod
    def close(self) -> None:
        """Cleanup resources."""
