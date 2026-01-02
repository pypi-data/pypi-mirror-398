"""Configuration loading and normalization."""
from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict, Optional

try:
    import yaml
except Exception:  # pragma: no cover - optional import
    yaml = None


DEFAULT_CONFIG: Dict[str, Any] = {
    "defaults": {
        "data_classification": "internal",
        "purpose": "general",
        "service_name": None,
        "environment": "dev",
    },
    "sinks": [
        {"type": "stdout", "format": "json"},
    ],
    "immutability": {
        "enabled": True,
        "scope": "per_trace",
        "hash_algorithm": "sha256",
    },
    "registry": {
        "version": "1.0.0",
        "history": [],
        "default_provider": "unknown",
        "allow_unknown": True,
        "providers": [
            {"name": "openai", "model_patterns": ["gpt-*", "o1-*"]},
            {"name": "anthropic", "model_patterns": ["claude-*"]},
            {"name": "deepseek", "model_patterns": ["deepseek:*", "deepseek*"]},
        ],
    },
    "instrumentation": {
        "enabled": False,
        "targets": ["openai", "anthropic"],
        "default_purpose": None,
        "data_classification": None,
        "reason": None,
        "fail_fast": False,
    },
    "data_handling": {
        "enabled": False,
        "mode": "redact",
        "apply_to": [
            "request",
            "response",
            "tool_args",
            "tool_result",
            "agent_input",
            "agent_output",
            "custom",
        ],
        "rules": [],
    },
    "policies": {
        "model_allowlist": [],
        "model_denylist": [],
        "classification_max_models": {},
        "enforce": True,
    },
    "alerts": {
        "violation_webhook": None,
        "headers": {},
        "timeout_sec": 5.0,
        "retry_attempts": 3,
        "backoff_base_sec": 0.5,
        "queue_size": 200,
    },
    "error_handling": {
        "sink_failure_mode": "warn",
        "log_user_exceptions": True,
        "queue_full_mode": "warn",
        "fallback_path": "./monora_fallback.jsonl",
    },
    "buffering": {
        "queue_size": 1000,
        "batch_size": 50,
        "flush_interval_sec": 1.0,
        "queue_full_timeout_sec": None,
    },
}


def load_config(
    *,
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    env_prefix: str = "MONORA_",
) -> Dict[str, Any]:
    """Load config with precedence: dict > file > env > defaults."""
    config = deepcopy(DEFAULT_CONFIG)

    env_config = _config_from_env(env_prefix)
    _merge_dicts(config, env_config)

    if config_path:
        file_config = _load_config_file(config_path)
        _merge_dicts(config, file_config)

    if config_dict:
        _merge_dicts(config, config_dict)

    # Expand environment variables in string values
    _expand_env_vars(config)

    return config


def _load_config_file(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(config_path)
    with open(config_path, "r", encoding="utf-8") as handle:
        raw = handle.read()
    if config_path.endswith(".json"):
        return json.loads(raw) if raw.strip() else {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to load YAML config files")
    return yaml.safe_load(raw) or {}


def _config_from_env(prefix: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = _env_key_to_path(key[len(prefix) :])
        if not path:
            continue
        _set_path_value(result, path, _parse_env_value(value))
    return result


def _env_key_to_path(key: str) -> list[Any]:
    parts = [part for part in key.split("_") if part]
    if not parts:
        return []

    if len(parts) >= 2 and parts[0].upper() == "DATA" and parts[1].upper() == "HANDLING":
        root = "data_handling"
        rest = parts[2:]
    elif len(parts) >= 2 and parts[0].upper() == "ERROR" and parts[1].upper() == "HANDLING":
        root = "error_handling"
        rest = parts[2:]
    else:
        root = parts[0].lower()
        rest = parts[1:]

    if root == "policies" and rest[:3] == ["CLASSIFICATION", "MAX", "MODELS"]:
        if len(rest) < 5:
            return []
        classification = rest[3].lower()
        tail = rest[4:]
        return ["policies", "classification_max_models", classification, "_".join(tail).lower()]

    path: list[Any] = [root]
    buffer: list[str] = []
    for part in rest:
        if part.isdigit():
            if buffer:
                path.append("_".join(buffer).lower())
                buffer = []
            path.append(int(part))
        else:
            buffer.append(part)
    if buffer:
        path.append("_".join(buffer).lower())
    return path


def _set_path_value(target: Dict[str, Any], path: list[Any], value: Any) -> None:
    cursor: Any = target
    for idx, segment in enumerate(path):
        is_last = idx == len(path) - 1
        if isinstance(segment, int):
            if not isinstance(cursor, list):
                cursor_path = path[: idx]
                container = []
                if cursor_path:
                    _assign_container(target, cursor_path, container)
                cursor = container
            while len(cursor) <= segment:
                cursor.append({})
            if is_last:
                cursor[segment] = value
            else:
                if not isinstance(cursor[segment], (dict, list)):
                    cursor[segment] = {}
                cursor = cursor[segment]
        else:
            if is_last:
                cursor[segment] = value
            else:
                if segment not in cursor or not isinstance(cursor[segment], (dict, list)):
                    cursor[segment] = {}
                cursor = cursor[segment]


def _assign_container(target: Dict[str, Any], path: list[Any], container: Any) -> None:
    cursor: Any = target
    for segment in path[:-1]:
        if isinstance(segment, int):
            while len(cursor) <= segment:
                cursor.append({})
            cursor = cursor[segment]
        else:
            cursor = cursor.setdefault(segment, {})
    last = path[-1]
    if isinstance(last, int):
        while len(cursor) <= last:
            cursor.append({})
        cursor[last] = container
    else:
        cursor[last] = container


def _parse_env_value(value: str) -> Any:
    raw = value.strip()
    if not raw:
        return ""
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if raw.startswith("[") or raw.startswith("{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    if "," in raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    for key, value in (override or {}).items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_dicts(base[key], value)
        elif key in base and isinstance(base[key], list) and isinstance(value, list):
            for idx, item in enumerate(value):
                if idx < len(base[key]) and isinstance(base[key][idx], dict) and isinstance(item, dict):
                    _merge_dicts(base[key][idx], item)
                else:
                    if idx >= len(base[key]):
                        base[key].append(item)
                    else:
                        base[key][idx] = item
        else:
            base[key] = value


def _expand_env_vars(obj: Any) -> None:
    """Expand environment variables in config strings.

    Supports ${VAR_NAME} and $VAR_NAME syntax.
    Modifies the object in-place.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                obj[key] = os.path.expandvars(value)
            elif isinstance(value, (dict, list)):
                _expand_env_vars(value)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            if isinstance(item, str):
                obj[idx] = os.path.expandvars(item)
            elif isinstance(item, (dict, list)):
                _expand_env_vars(item)
