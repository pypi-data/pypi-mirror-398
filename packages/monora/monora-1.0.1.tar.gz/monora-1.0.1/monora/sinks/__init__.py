"""Sink factory."""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

from .base import Sink, SinkError
from .file import FileSink
from .https import HttpSink
from .stdout import StdoutSink


def build_sinks(configs: List[Dict[str, Any]], *, fail_fast: bool = False) -> List[Sink]:
    sinks: List[Sink] = []
    for config in configs:
        sink_type = (config.get("type") or "").lower()
        try:
            if sink_type == "stdout":
                sinks.append(StdoutSink(format=config.get("format", "json")))
            elif sink_type == "file":
                sinks.append(
                    FileSink(
                        config["path"],
                        batch_size=config.get("batch_size", 100),
                        flush_interval_sec=config.get("flush_interval_sec", 5.0),
                        rotation=config.get("rotation", "none"),
                        max_size_mb=config.get("max_size_mb"),
                    )
                )
            elif sink_type == "https":
                headers = _expand_headers(config.get("headers", {}))
                sinks.append(
                    HttpSink(
                        config["endpoint"],
                        headers,
                        batch_size=config.get("batch_size", 50),
                        timeout_sec=config.get("timeout_sec", 10.0),
                        retry_attempts=config.get("retry_attempts", 3),
                        backoff_base_sec=config.get("backoff_base_sec", 0.5),
                    )
                )
            else:
                raise ValueError(f"Unknown sink type: {sink_type}")
        except Exception as exc:
            if fail_fast:
                raise
            print(f"Monora: failed to init sink {sink_type}: {exc}", file=sys.stderr)
    return sinks


def _expand_headers(headers: Dict[str, Any]) -> Dict[str, str]:
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


__all__ = [
    "Sink",
    "SinkError",
    "StdoutSink",
    "FileSink",
    "HttpSink",
    "build_sinks",
]
