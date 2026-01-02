"""Diagnostics commands for Monora configuration."""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
from numbers import Real
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import click

from monora.config import load_config


ALLOWED_QUEUE_MODES = {"warn", "raise", "block"}
ALLOWED_SINK_FAILURE_MODES = {"warn", "raise", "silent"}
ALLOWED_ROTATION = {"none", "daily", "size"}
ALLOWED_DATA_HANDLING = {"redact", "block", "allow"}


def validate_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    sinks = config.get("sinks", [])
    if not sinks:
        errors.append("No sinks configured.")
    for idx, sink in enumerate(sinks or []):
        sink_type = str(sink.get("type", "")).lower()
        prefix = f"sinks[{idx}]"
        if sink_type == "stdout":
            continue
        if sink_type == "file":
            path = sink.get("path")
            if not path:
                errors.append(f"{prefix}: file sink requires 'path'.")
            rotation = sink.get("rotation", "none")
            if rotation not in ALLOWED_ROTATION:
                errors.append(f"{prefix}: invalid rotation '{rotation}'.")
            if rotation == "size" and not sink.get("max_size_mb"):
                warnings.append(f"{prefix}: rotation=size without max_size_mb.")
            continue
        if sink_type == "https":
            endpoint = sink.get("endpoint")
            if not endpoint:
                errors.append(f"{prefix}: https sink requires 'endpoint'.")
            else:
                parsed = urlparse(str(endpoint))
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    errors.append(f"{prefix}: invalid https endpoint '{endpoint}'.")
            continue
        if sink_type:
            errors.append(f"{prefix}: unknown sink type '{sink_type}'.")
        else:
            errors.append(f"{prefix}: sink type missing.")

    buffering = config.get("buffering", {})
    queue_size = buffering.get("queue_size", 0)
    batch_size = buffering.get("batch_size", 0)
    flush_interval = buffering.get("flush_interval_sec", 0)
    if not isinstance(queue_size, int):
        errors.append("buffering.queue_size must be a positive integer.")
    elif queue_size <= 0:
        errors.append("buffering.queue_size must be a positive integer.")
    if not isinstance(batch_size, int):
        errors.append("buffering.batch_size must be a positive integer.")
    elif batch_size <= 0:
        errors.append("buffering.batch_size must be a positive integer.")
    if isinstance(queue_size, int) and isinstance(batch_size, int) and batch_size > queue_size:
        warnings.append("buffering.batch_size exceeds queue_size.")
    if flush_interval is not None:
        if not isinstance(flush_interval, Real):
            errors.append("buffering.flush_interval_sec must be a number.")
        elif flush_interval < 0:
            errors.append("buffering.flush_interval_sec must be >= 0.")
    queue_full_timeout = buffering.get("queue_full_timeout_sec")
    if queue_full_timeout is not None:
        if not isinstance(queue_full_timeout, Real):
            errors.append("buffering.queue_full_timeout_sec must be a number.")
        elif queue_full_timeout <= 0:
            errors.append("buffering.queue_full_timeout_sec must be > 0 when set.")

    error_handling = config.get("error_handling", {})
    queue_full_mode = error_handling.get("queue_full_mode", "warn")
    if queue_full_mode not in ALLOWED_QUEUE_MODES:
        errors.append("error_handling.queue_full_mode must be warn|raise|block.")
    sink_failure_mode = error_handling.get("sink_failure_mode", "warn")
    if sink_failure_mode not in ALLOWED_SINK_FAILURE_MODES:
        errors.append("error_handling.sink_failure_mode must be warn|raise|silent.")

    data_handling = config.get("data_handling", {})
    if data_handling.get("enabled"):
        mode = data_handling.get("mode", "redact")
        if mode not in ALLOWED_DATA_HANDLING:
            errors.append("data_handling.mode must be redact|block|allow.")
        rules = data_handling.get("rules", [])
        if not rules:
            warnings.append("data_handling enabled but rules list is empty.")
        for idx, rule in enumerate(rules or []):
            pattern = rule.get("pattern")
            if not pattern:
                warnings.append(f"data_handling.rules[{idx}] missing pattern.")
                continue
            try:
                re.compile(pattern)
            except re.error as exc:
                errors.append(f"data_handling.rules[{idx}] invalid pattern: {exc}")

    instrumentation = config.get("instrumentation", {})
    if instrumentation.get("enabled") and not instrumentation.get("targets"):
        warnings.append("instrumentation.enabled true but no targets configured.")

    return {"errors": errors, "warnings": warnings}


def doctor_checks(
    config: Dict[str, Any],
    *,
    check_network: bool = True,
) -> Dict[str, List[str]]:
    results = validate_config(config)
    errors = list(results["errors"])
    warnings = list(results["warnings"])

    requests_available = _check_requests()
    sinks = config.get("sinks", [])
    for idx, sink in enumerate(sinks or []):
        sink_type = str(sink.get("type", "")).lower()
        prefix = f"sinks[{idx}]"
        if sink_type == "file":
            path = sink.get("path")
            if path and not _check_file_writable(path):
                errors.append(f"{prefix}: cannot write to {path}.")
        if sink_type == "https":
            if not requests_available:
                errors.append(f"{prefix}: requests not installed (monora[https]).")
            endpoint = sink.get("endpoint")
            if check_network and endpoint:
                _network_check(endpoint, warnings, f"{prefix}: ")

    fallback_path = config.get("error_handling", {}).get("fallback_path")
    if fallback_path and not _check_file_writable(fallback_path):
        warnings.append(f"fallback_path not writable: {fallback_path}.")

    alerts = config.get("alerts", {})
    webhook = alerts.get("violation_webhook")
    if webhook:
        if not requests_available:
            errors.append("alerts.violation_webhook requires requests (monora[https]).")
        if check_network:
            _network_check(webhook, warnings, "alerts: ")

    if not _check_gpg():
        warnings.append("gpg not found; signed attestations will be unavailable.")

    return {"errors": errors, "warnings": warnings}


def _check_requests() -> bool:
    try:
        import requests  # noqa: F401
    except Exception:
        return False
    return True


def _check_file_writable(path: str) -> bool:
    try:
        parent = os.path.dirname(path) or "."
        os.makedirs(parent, exist_ok=True)
        with open(path, "a", encoding="utf-8"):
            pass
        return True
    except Exception:
        return False


def _network_check(endpoint: str, warnings: List[str], prefix: str) -> None:
    parsed = urlparse(str(endpoint))
    host = parsed.hostname
    if not host:
        warnings.append(f"{prefix}unable to parse host from {endpoint}.")
        return
    port = parsed.port
    if not port:
        port = 443 if parsed.scheme == "https" else 80
    try:
        with socket.create_connection((host, port), timeout=3.0):
            return
    except Exception as exc:
        warnings.append(f"{prefix}network check failed for {endpoint}: {exc}")


def _check_gpg() -> bool:
    return shutil.which("gpg") is not None


def _emit_results(results: Dict[str, List[str]], *, as_json: bool) -> int:
    errors = results.get("errors", [])
    warnings = results.get("warnings", [])
    if as_json:
        click.echo(json.dumps(results, indent=2))
    else:
        if not errors and not warnings:
            click.echo("OK: no issues found.")
        if errors:
            click.echo("Errors:")
            for item in errors:
                click.echo(f"  - {item}")
        if warnings:
            click.echo("Warnings:")
            for item in warnings:
                click.echo(f"  - {item}")
    return 1 if errors else 0


@click.command(name="validate")
@click.option("--config", "config_path", default="monora.yml", show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def validate_command(config_path: str, as_json: bool) -> None:
    """Validate Monora configuration."""
    config = load_config(config_path=config_path)
    results = validate_config(config)
    exit_code = _emit_results(results, as_json=as_json)
    if exit_code:
        raise SystemExit(exit_code)


@click.command(name="doctor")
@click.option("--config", "config_path", default="monora.yml", show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
@click.option("--no-network", is_flag=True, help="Skip network checks")
def doctor_command(config_path: str, as_json: bool, no_network: bool) -> None:
    """Run runtime diagnostics for Monora configuration."""
    config = load_config(config_path=config_path)
    results = doctor_checks(config, check_network=not no_network)
    exit_code = _emit_results(results, as_json=as_json)
    if exit_code:
        raise SystemExit(exit_code)
