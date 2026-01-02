"""Interactive setup wizard for Monora configuration."""
from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

import click

from monora.config import DEFAULT_CONFIG

try:  # Optional YAML support
    import yaml
except Exception:  # pragma: no cover - optional import
    yaml = None


def build_config(answers: Dict[str, Any]) -> Dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    defaults = config.setdefault("defaults", {})
    defaults["service_name"] = answers["service_name"]
    defaults["environment"] = answers["environment"]

    sinks = []
    if answers.get("stdout_sink"):
        sinks.append({"type": "stdout", "format": "json"})
    if answers.get("file_sink"):
        sinks.append(
            {
                "type": "file",
                "path": answers["file_path"],
                "rotation": "daily",
                "max_size_mb": 100,
                "batch_size": 100,
                "flush_interval_sec": 5.0,
            }
        )
    if answers.get("https_sink"):
        headers = {}
        if answers.get("https_auth_header"):
            headers["Authorization"] = answers["https_auth_header"]
        sinks.append(
            {
                "type": "https",
                "endpoint": answers["https_endpoint"],
                "headers": headers,
                "batch_size": 50,
                "timeout_sec": 10.0,
                "retry_attempts": 3,
                "backoff_base_sec": 0.5,
            }
        )
    if not sinks:
        sinks.append({"type": "stdout", "format": "json"})
    config["sinks"] = sinks

    policies = config.setdefault("policies", {})
    policies["model_allowlist"] = answers.get("allowlist", [])
    policies["model_denylist"] = answers.get("denylist", [])
    policies["enforce"] = bool(answers.get("enable_policies"))

    instrumentation = config.setdefault("instrumentation", {})
    instrumentation["enabled"] = bool(answers.get("enable_instrumentation", False))
    if answers.get("instrumentation_purpose"):
        instrumentation["default_purpose"] = answers["instrumentation_purpose"]

    data_handling = config.setdefault("data_handling", {})
    if answers.get("enable_data_handling"):
        data_handling["enabled"] = True
        data_handling["mode"] = answers.get("data_handling_mode", "redact")
        data_handling["rules"] = [
            {
                "name": "email",
                "pattern": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                "replace": "[REDACTED_EMAIL]",
                "classifications": ["confidential", "secret"],
                "apply_to": ["request", "response"],
            }
        ]
    else:
        data_handling["enabled"] = False
        data_handling["rules"] = []

    alerts = config.setdefault("alerts", {})
    alerts["violation_webhook"] = answers.get("violation_webhook")
    if answers.get("alerts_auth_header"):
        alerts["headers"] = {"Authorization": answers["alerts_auth_header"]}

    error_handling = config.setdefault("error_handling", {})
    error_handling["queue_full_mode"] = answers.get("queue_full_mode", "warn")

    buffering = config.setdefault("buffering", {})
    timeout = answers.get("queue_full_timeout_sec")
    if timeout is not None:
        buffering["queue_full_timeout_sec"] = timeout

    return config


def render_config(config: Dict[str, Any], fmt: str) -> Tuple[str, str]:
    fmt = fmt.lower()
    if fmt == "yaml":
        if yaml is None:
            return json.dumps(config, indent=2), "json"
        return (
            yaml.safe_dump(config, sort_keys=False, default_flow_style=False),
            "yaml",
        )
    if fmt == "json":
        return json.dumps(config, indent=2), "json"
    return json.dumps(config, indent=2), "json"


def run_wizard(
    *,
    config_path: str,
    fmt: str,
    assume_yes: bool,
    force: bool,
) -> Tuple[Dict[str, Any], str]:
    if os.path.exists(config_path) and not force:
        if assume_yes:
            raise click.ClickException(
                f"{config_path} already exists. Use --force to overwrite."
            )
        overwrite = click.confirm(
            f"{config_path} already exists. Overwrite?", default=False
        )
        if not overwrite:
            raise click.ClickException("Aborted.")

    service_default = os.path.basename(os.getcwd()) or "monora-app"
    if assume_yes:
        answers = {
            "service_name": service_default,
            "environment": "dev",
            "stdout_sink": True,
            "file_sink": False,
            "https_sink": False,
            "enable_policies": False,
            "allowlist": [],
            "denylist": [],
            "enable_instrumentation": False,
            "instrumentation_purpose": "general",
            "enable_data_handling": False,
            "data_handling_mode": "redact",
            "violation_webhook": None,
            "alerts_auth_header": None,
            "queue_full_mode": "warn",
            "queue_full_timeout_sec": None,
        }
        return build_config(answers), fmt

    answers = {
        "service_name": click.prompt("Service name", default=service_default),
        "environment": click.prompt(
            "Environment",
            type=click.Choice(["dev", "staging", "production"]),
            default="dev",
        ),
    }

    answers["stdout_sink"] = click.confirm("Enable stdout sink?", default=True)
    answers["file_sink"] = click.confirm("Enable file sink?", default=True)
    if answers["file_sink"]:
        answers["file_path"] = click.prompt(
            "File sink path", default="./monora_events.jsonl"
        )
    answers["https_sink"] = click.confirm("Enable HTTPS sink?", default=False)
    if answers["https_sink"]:
        answers["https_endpoint"] = click.prompt("HTTPS endpoint URL")
        if click.confirm("Add Authorization header using MONORA_API_KEY?", default=False):
            answers["https_auth_header"] = "Bearer ${MONORA_API_KEY}"

    answers["enable_policies"] = click.confirm(
        "Configure model allowlist/denylist?", default=False
    )
    if answers["enable_policies"]:
        allowlist_raw = click.prompt(
            "Allowlist patterns (comma-separated)",
            default="gpt-4*,claude-3-*",
        )
        denylist_raw = click.prompt(
            "Denylist patterns (comma-separated)",
            default="deepseek:*",
        )
        answers["allowlist"] = _parse_list(allowlist_raw)
        answers["denylist"] = _parse_list(denylist_raw)
    else:
        answers["allowlist"] = []
        answers["denylist"] = []

    answers["enable_instrumentation"] = click.confirm(
        "Enable auto-instrumentation?", default=False
    )
    if answers["enable_instrumentation"]:
        answers["instrumentation_purpose"] = click.prompt(
            "Default purpose for instrumentation", default="general"
        )

    answers["enable_data_handling"] = click.confirm(
        "Enable data redaction rules?", default=False
    )
    if answers["enable_data_handling"]:
        answers["data_handling_mode"] = click.prompt(
            "Data handling mode",
            type=click.Choice(["redact", "block", "allow"]),
            default="redact",
        )

    answers["violation_webhook"] = click.prompt(
        "Violation webhook URL (blank to skip)", default="", show_default=False
    ).strip() or None
    if answers["violation_webhook"] and click.confirm(
        "Add Authorization header using MONORA_ALERTS_KEY?", default=False
    ):
        answers["alerts_auth_header"] = "Bearer ${MONORA_ALERTS_KEY}"

    answers["queue_full_mode"] = click.prompt(
        "Queue overflow mode",
        type=click.Choice(["warn", "raise", "block"]),
        default="warn",
    )
    if answers["queue_full_mode"] == "block":
        while True:
            timeout_raw = click.prompt(
                "Queue full timeout (seconds, blank for no timeout)",
                default="",
                show_default=False,
            ).strip()
            if not timeout_raw:
                answers["queue_full_timeout_sec"] = None
                break
            try:
                answers["queue_full_timeout_sec"] = float(timeout_raw)
                break
            except ValueError:
                click.echo("Please enter a valid number or leave blank.")

    return build_config(answers), fmt


def _parse_list(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


@click.command(name="init")
@click.option("--path", "config_path", default="monora.yml", show_default=True)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    show_default=True,
)
@click.option("--yes", "assume_yes", is_flag=True, help="Accept defaults without prompts")
@click.option("--force", is_flag=True, help="Overwrite existing config file")
def init_command(config_path: str, fmt: str, assume_yes: bool, force: bool) -> None:
    """Interactive configuration wizard."""
    config, requested_format = run_wizard(
        config_path=config_path,
        fmt=fmt,
        assume_yes=assume_yes,
        force=force,
    )
    output, rendered_format = render_config(config, requested_format)
    with open(config_path, "w", encoding="utf-8") as handle:
        handle.write(output)

    if requested_format == "yaml" and rendered_format != "yaml":
        click.echo("PyYAML not available; wrote JSON content instead.")

    click.echo(f"Monora config written to {config_path}")
    click.echo("Next steps:")
    click.echo("  1) monora init created your config")
    click.echo("  2) monora init is optional; update monora.yml as needed")
    click.echo("  3) monora init is done; run your app with monora.init(...)")
