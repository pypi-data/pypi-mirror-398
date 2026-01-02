"""Data handling enforcement and redaction rules."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


logger = logging.getLogger(__name__)


class DataHandlingViolation(Exception):
    def __init__(
        self,
        *,
        event_type: str,
        policy_name: str,
        message: str,
        timestamp: str,
        data_classification: str,
        rule_names: List[str],
        model: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.event_type = event_type
        self.policy_name = policy_name
        self.message = message
        self.timestamp = timestamp
        self.data_classification = data_classification
        self.rule_names = rule_names
        self.model = model

    def __str__(self) -> str:
        return (
            f"DataHandlingViolation(policy={self.policy_name}, event={self.event_type}, "
            f"message={self.message})"
        )


@dataclass
class RedactionRule:
    name: str
    pattern: re.Pattern
    replace: str
    classifications: Optional[Set[str]]
    apply_to: Optional[Set[str]]

    def applies(self, classification: str, target: str) -> bool:
        if self.classifications and classification not in self.classifications:
            return False
        if self.apply_to and target not in self.apply_to:
            return False
        return True


class DataHandlingEngine:
    def __init__(self, config: Dict[str, Any]):
        self.enabled = bool(config.get("enabled", False))
        self.mode = config.get("mode", "redact")
        self.default_apply_to = set(
            config.get(
                "apply_to",
                [
                    "request",
                    "response",
                    "tool_args",
                    "tool_result",
                    "agent_input",
                    "agent_output",
                    "custom",
                ],
            )
        )
        self.rules = self._load_rules(config.get("rules", []))

    def should_block(self) -> bool:
        return self.enabled and self.mode == "block" and bool(self.rules)

    def inspect(self, target: str, payload: Any, classification: str) -> Set[str]:
        if not self.enabled or not self.rules:
            return set()
        rules = self._rules_for(target, classification)
        if not rules:
            return set()
        matches: Set[str] = set()
        self._scan_value(payload, rules, matches)
        return matches

    def sanitize_payload(
        self, target: str, payload: Any, classification: str
    ) -> Tuple[Any, Set[str]]:
        if not self.enabled or self.mode == "allow" or not self.rules:
            return payload, set()
        rules = self._rules_for(target, classification)
        if not rules:
            return payload, set()
        applied: Set[str] = set()
        redacted = self._redact_value(payload, rules, applied)
        return redacted, applied

    def apply_to_event_body(
        self, event_type: str, body: Dict[str, Any], classification: str
    ) -> Dict[str, Any]:
        if not self.enabled or self.mode == "allow" or not self.rules:
            return body

        applied_rules: Set[str] = set(body.get("redaction", {}).get("rules", []))
        if event_type == "llm_call":
            body["request"], applied = self.sanitize_payload(
                "request", body.get("request"), classification
            )
            applied_rules.update(applied)
            body["response"], applied = self.sanitize_payload(
                "response", body.get("response"), classification
            )
            applied_rules.update(applied)
        elif event_type == "tool_call":
            body["arguments"], applied = self.sanitize_payload(
                "tool_args", body.get("arguments"), classification
            )
            applied_rules.update(applied)
            body["result"], applied = self.sanitize_payload(
                "tool_result", body.get("result"), classification
            )
            applied_rules.update(applied)
        elif event_type == "agent_step":
            body["input"], applied = self.sanitize_payload(
                "agent_input", body.get("input"), classification
            )
            applied_rules.update(applied)
            body["output"], applied = self.sanitize_payload(
                "agent_output", body.get("output"), classification
            )
            applied_rules.update(applied)
        else:
            body, applied = self.sanitize_payload("custom", body, classification)
            applied_rules.update(applied)

        if applied_rules:
            body["redaction"] = {
                "applied": True,
                "rules": sorted(applied_rules),
                "mode": self.mode,
            }
        return body

    def _load_rules(self, rules: Iterable[Dict[str, Any]]) -> List[RedactionRule]:
        loaded: List[RedactionRule] = []
        for rule in rules:
            pattern = rule.get("pattern")
            if not pattern:
                continue
            replace = rule.get("replace", "[REDACTED]")
            classifications = rule.get("classifications")
            apply_to = rule.get("apply_to")
            rule_apply_to = set(apply_to) if apply_to else set(self.default_apply_to)
            rule_classifications = set(classifications) if classifications else None
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                logger.warning(
                    "Skipping invalid redaction rule '%s' pattern '%s': %s",
                    rule.get("name", pattern),
                    pattern,
                    exc,
                )
                continue
            loaded.append(
                RedactionRule(
                    name=rule.get("name", pattern),
                    pattern=compiled,
                    replace=replace,
                    classifications=rule_classifications,
                    apply_to=rule_apply_to,
                )
            )
        return loaded

    def _rules_for(self, target: str, classification: str) -> List[RedactionRule]:
        return [rule for rule in self.rules if rule.applies(classification, target)]

    def _scan_value(self, value: Any, rules: List[RedactionRule], matches: Set[str]) -> None:
        if isinstance(value, str):
            for rule in rules:
                if rule.pattern.search(value):
                    matches.add(rule.name)
            return
        if isinstance(value, dict):
            for item in value.values():
                self._scan_value(item, rules, matches)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                self._scan_value(item, rules, matches)

    def _redact_value(
        self, value: Any, rules: List[RedactionRule], applied: Set[str]
    ) -> Any:
        if isinstance(value, str):
            redacted = value
            for rule in rules:
                if rule.pattern.search(redacted):
                    redacted = rule.pattern.sub(rule.replace, redacted)
                    applied.add(rule.name)
            return redacted
        if isinstance(value, dict):
            return {key: self._redact_value(val, rules, applied) for key, val in value.items()}
        if isinstance(value, list):
            return [self._redact_value(item, rules, applied) for item in value]
        if isinstance(value, tuple):
            return tuple(self._redact_value(item, rules, applied) for item in value)
        if isinstance(value, set):
            return {self._redact_value(item, rules, applied) for item in value}
        return value


def build_data_violation(
    *,
    event_type: str,
    classification: str,
    rule_names: Iterable[str],
    model: Optional[str] = None,
) -> DataHandlingViolation:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    rules = sorted(set(rule_names))
    message = f"Sensitive data matched rules: {', '.join(rules)}"
    return DataHandlingViolation(
        event_type=event_type,
        policy_name="data_handling.block",
        message=message,
        timestamp=timestamp,
        data_classification=classification,
        rule_names=rules,
        model=model,
    )
