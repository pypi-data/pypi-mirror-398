"""Policy engine for model allow/deny enforcement."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class PolicyViolation(Exception):
    event_type: str
    model: str
    policy_name: str
    message: str
    timestamp: str


PatternList = List[tuple[str, re.Pattern]]


class PolicyEngine:
    def __init__(self, config: Dict):
        self.allowlist = compile_patterns(config.get("model_allowlist", []))
        self.denylist = compile_patterns(config.get("model_denylist", []))
        self.enforce = bool(config.get("enforce", True))
        self.classification_rules = self._compile_classification_rules(
            config.get("classification_max_models", {})
        )

    def _compile_classification_rules(self, rules: Dict) -> Dict[str, Dict[str, PatternList]]:
        compiled: Dict[str, Dict[str, PatternList]] = {}
        for classification, entry in rules.items():
            compiled[classification] = {
                "allowed": compile_patterns(entry.get("allowed", [])),
                "denied": compile_patterns(entry.get("denied", [])),
            }
        return compiled

    def check_model(self, model: Optional[str], data_classification: str) -> Optional[PolicyViolation]:
        if not model:
            return None

        violation = self._check_model(model, data_classification)
        if violation and self.enforce:
            raise violation
        return violation

    def _check_model(self, model: str, data_classification: str) -> Optional[PolicyViolation]:
        if _matches_any(self.denylist, model):
            return self._violation(model, "model_denylist", "Model matches denylist pattern")

        if self.allowlist and not _matches_any(self.allowlist, model):
            return self._violation(model, "model_allowlist", "Model not in allowlist")

        classification = self.classification_rules.get(data_classification)
        if classification:
            denied = classification.get("denied", [])
            if denied and _matches_any(denied, model):
                return self._violation(
                    model,
                    "classification_max_models.denied",
                    f"Model denied for classification '{data_classification}'",
                )

            allowed = classification.get("allowed", [])
            if allowed and not _matches_any(allowed, model):
                return self._violation(
                    model,
                    "classification_max_models.allowed",
                    f"Model not allowed for classification '{data_classification}'",
                )

        return None

    def get_allowed_patterns(self) -> List[str]:
        """Return list of allowed model patterns from allowlist.

        Returns:
            List of pattern strings (e.g., ["gpt-4*", "claude-3-*"])
            Empty list if no allowlist configured
        """
        return [pattern for pattern, _ in self.allowlist]

    def get_denied_patterns(self) -> List[str]:
        """Return list of denied model patterns from denylist.

        Returns:
            List of pattern strings (e.g., ["deepseek:*", "*alpha*"])
            Empty list if no denylist configured
        """
        return [pattern for pattern, _ in self.denylist]

    def is_model_allowed(self, model: str, classification: str = "internal") -> bool:
        """Check if model would be allowed without raising exception.

        Args:
            model: Model identifier to check
            classification: Data classification level (default: "internal")

        Returns:
            True if model passes all policy checks, False otherwise

        Note:
            This method never raises PolicyViolation, even when enforce=True.
            Use check_model() for enforcement with exceptions.
        """
        if not model:
            return True  # Match check_model() behavior for None/empty

        violation = self._check_model(model, classification)
        return violation is None

    def get_classification_rules(self) -> Dict[str, Dict[str, List[str]]]:
        """Get all classification-specific model restrictions.

        Returns:
            Dict mapping classification to {"allowed": [...], "denied": [...]}
            Example: {"secret": {"allowed": ["claude-3-opus*"], "denied": []}}
            Empty dict if no classification rules configured
        """
        result = {}
        for classification, rules in self.classification_rules.items():
            result[classification] = {
                "allowed": [p for p, _ in rules.get("allowed", [])],
                "denied": [p for p, _ in rules.get("denied", [])]
            }
        return result

    def get_matching_patterns(self, model: str) -> Dict[str, List[str]]:
        """Find all patterns that match the given model.

        Args:
            model: Model identifier to check against all patterns

        Returns:
            Dict with keys "allowed" and "denied", each containing list of matching patterns
            Example: {"allowed": ["gpt-4*"], "denied": []}
        """
        if not model:
            return {"allowed": [], "denied": []}

        allowed_matches = [
            pattern_str
            for pattern_str, pattern_re in self.allowlist
            if pattern_re.match(model)
        ]

        denied_matches = [
            pattern_str
            for pattern_str, pattern_re in self.denylist
            if pattern_re.match(model)
        ]

        return {"allowed": allowed_matches, "denied": denied_matches}

    def is_enforcement_enabled(self) -> bool:
        """Check if policy enforcement mode is enabled.

        Returns:
            True if violations raise exceptions, False if they only warn
        """
        return self.enforce

    def _violation(self, model: str, policy_name: str, message: str) -> PolicyViolation:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        return PolicyViolation(
            event_type="llm_call",
            model=model,
            policy_name=policy_name,
            message=message,
            timestamp=timestamp,
        )


def compile_patterns(patterns: List[str]) -> PatternList:
    return [(pattern, re.compile(fnmatch.translate(pattern))) for pattern in patterns]


def _matches_any(patterns: PatternList, model: str) -> bool:
    """Check if model matches any of the compiled patterns."""
    for raw, pattern in patterns:
        if pattern.match(model):
            return True
    return False
