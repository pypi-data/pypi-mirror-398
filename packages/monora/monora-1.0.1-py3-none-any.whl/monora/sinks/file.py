"""File sink with JSON-lines output and optional rotation."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .base import Sink, SinkError


class FileSink(Sink):
    def __init__(
        self,
        path: str,
        *,
        batch_size: int = 100,
        flush_interval_sec: float = 5.0,
        rotation: str = "none",
        max_size_mb: Optional[int] = None,
    ):
        self.path = Path(path)
        self.batch_size = batch_size
        self.flush_interval_sec = flush_interval_sec
        self.rotation = rotation
        self.max_size_mb = max_size_mb
        self.buffer: List[dict] = []
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._current_date = self._today()

        if self.flush_interval_sec and self.flush_interval_sec > 0:
            self._thread = threading.Thread(target=self._flush_loop, daemon=True)
            self._thread.start()

    def emit(self, events: Iterable[dict]) -> None:
        with self.lock:
            self.buffer.extend(events)
            if len(self.buffer) >= self.batch_size:
                self._flush_internal()

    def flush(self) -> None:
        with self.lock:
            self._flush_internal()

    def close(self) -> None:
        if self._thread:
            self._stop_event.set()
            self._thread.join(timeout=1.0)
        self.flush()

    def _flush_loop(self) -> None:
        while not self._stop_event.wait(self.flush_interval_sec):
            self.flush()

    def _flush_internal(self) -> None:
        if not self.buffer:
            return
        try:
            self._ensure_path()
            with self.path.open("a", encoding="utf-8") as handle:
                for event in self.buffer:
                    handle.write(json.dumps(event) + "\n")
            self.buffer.clear()
        except Exception as exc:
            raise SinkError(f"File sink failed: {exc}") from exc

    def _ensure_path(self) -> None:
        if self.rotation == "daily":
            today = self._today()
            if today != self._current_date:
                self._current_date = today
            self.path = self._daily_path(today)
        elif self.rotation == "size" and self.max_size_mb:
            max_bytes = self.max_size_mb * 1024 * 1024
            if self.path.exists() and self.path.stat().st_size >= max_bytes:
                self._rotate_file()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _rotate_file(self) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        rotated = self.path.with_name(f"{self.path.stem}.{timestamp}{self.path.suffix}")
        try:
            os.rename(self.path, rotated)
        except OSError as exc:
            raise SinkError(f"Failed to rotate file: {exc}") from exc

    def _daily_path(self, date: str) -> Path:
        if self.path.suffix:
            return self.path.with_name(f"{self.path.stem}.{date}{self.path.suffix}")
        return self.path.with_name(f"{self.path.name}.{date}")

    def _today(self) -> str:
        return datetime.utcnow().strftime("%Y%m%d")
