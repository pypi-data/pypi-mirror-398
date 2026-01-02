"""Provider/model registry and resolution."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .policy import compile_patterns


logger = logging.getLogger(__name__)


PatternList = List[Tuple[str, Any]]


@dataclass
class ProviderEntry:
    name: str
    patterns: PatternList
    version_range: Optional[str] = None
    deprecated: bool = False
    deprecation_message: Optional[str] = None


@dataclass
class RegistryHistoryEntry:
    version: str
    date: Optional[str] = None
    changes: List[str] = field(default_factory=list)


class ModelRegistry:
    def __init__(self, config: Dict[str, Any]):
        self.version = config.get("version") or "1.0.0"
        self.history = self._load_history(config.get("history", []))
        self.default_provider = config.get("default_provider", "unknown")
        self.allow_unknown = bool(config.get("allow_unknown", True))
        self.providers: List[ProviderEntry] = []
        self._models: Dict[str, Dict[str, Any]] = {}
        self._alias_to_canonical: Dict[str, str] = {}
        for entry in config.get("providers", []):
            name = entry.get("name")
            patterns = compile_patterns(entry.get("model_patterns", []))
            if not name or not patterns:
                continue
            self.providers.append(
                ProviderEntry(
                    name=name,
                    patterns=patterns,
                    version_range=entry.get("version_range"),
                    deprecated=bool(entry.get("deprecated", False)),
                    deprecation_message=entry.get("deprecation_message"),
                )
            )

        registry_path = config.get("registry_path")
        registry_data = (
            self._load_custom_registry(registry_path)
            if registry_path
            else self._load_default_registry()
        )
        self._load_models(registry_data.get("models", {}))
        self._load_models(config.get("models", {}))

    def resolve(self, model: Optional[str]) -> tuple[str, bool]:
        provider, matched, _ = self.resolve_entry(model)
        return provider, matched

    def resolve_entry(self, model: Optional[str]) -> tuple[str, bool, Optional[ProviderEntry]]:
        if not model:
            return self.default_provider, False, None
        model = self._canonicalize_model(model)
        for provider in self.providers:
            for _, pattern in provider.patterns:
                if pattern.match(model):
                    return provider.name, True, provider
        return self.default_provider, False, None

    @staticmethod
    def _load_history(raw: Any) -> List[RegistryHistoryEntry]:
        history: List[RegistryHistoryEntry] = []
        if not isinstance(raw, list):
            return history
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            version = entry.get("version")
            if not version:
                continue
            changes = entry.get("changes") or []
            if not isinstance(changes, list):
                changes = [str(changes)]
            history.append(
                RegistryHistoryEntry(
                    version=version,
                    date=entry.get("date"),
                    changes=[str(item) for item in changes],
                )
            )
        return history

    @staticmethod
    def _load_default_registry() -> Dict[str, Any]:
        path = Path(__file__).with_name("registry_data.json")
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError as exc:
            logger.error("Default registry file not found at %s: %s", path, exc)
            return {}
        except json.JSONDecodeError as exc:
            logger.error("Default registry JSON malformed at %s: %s", path, exc)
            return {}

    @staticmethod
    def _load_custom_registry(path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as exc:
            logger.error("Failed to load registry file at %s: %s", path, exc)
            raise RuntimeError(f"Failed to load registry file '{path}': {exc}") from exc

    def _load_models(self, models: Any) -> None:
        if not isinstance(models, dict):
            return
        for model_id, entry in models.items():
            if not isinstance(entry, dict):
                continue
            self._models[model_id] = entry
            aliases = entry.get("aliases") or []
            if not isinstance(aliases, (list, tuple, set)):
                continue
            for alias in aliases:
                if not alias:
                    continue
                alias_key = alias.lower()
                existing = self._alias_to_canonical.get(alias_key)
                if existing and existing != model_id:
                    message = (
                        f"Alias '{alias}' already mapped to model '{existing}', "
                        f"cannot assign to '{model_id}'"
                    )
                    logger.error(message)
                    raise ValueError(message)
                self._alias_to_canonical[alias_key] = model_id

    def _canonicalize_model(self, model: str) -> str:
        if not model:
            return model
        return self._alias_to_canonical.get(model.lower(), model)
