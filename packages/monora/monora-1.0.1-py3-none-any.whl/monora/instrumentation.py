"""Auto-instrumentation helpers for supported SDKs."""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from .decorators import llm_call


class InstrumentationError(RuntimeError):
    """Raised when auto-instrumentation fails in fail-fast mode."""


def auto_instrument(config: Dict[str, Any], *, fail_fast: bool = False) -> Dict[str, Any]:
    """Apply optional auto-instrumentation for supported SDKs.

    Returns a report with patched methods and any warnings.
    """
    settings = config.get("instrumentation", {})
    if not settings.get("enabled", False):
        return {"enabled": False, "patched": {}, "errors": []}

    targets = settings.get("targets") or ["openai", "anthropic"]
    purpose = settings.get("default_purpose") or config.get("defaults", {}).get(
        "purpose", "general"
    )
    data_classification = settings.get("data_classification")
    reason = settings.get("reason")
    effective_fail_fast = fail_fast or settings.get("fail_fast", False)

    report = {"enabled": True, "patched": {}, "errors": []}

    for target in targets:
        if target == "openai":
            patched, errors = _instrument_openai(
                purpose, reason, data_classification
            )
        elif target == "anthropic":
            patched, errors = _instrument_anthropic(
                purpose, reason, data_classification
            )
        else:
            patched, errors = [], [f"Unknown instrumentation target '{target}'"]

        report["patched"][target] = patched
        report["errors"].extend(errors)

    if report["errors"]:
        for error in report["errors"]:
            print(f"Monora instrumentation: {error}", file=sys.stderr)

    if effective_fail_fast:
        no_patches = all(not items for items in report["patched"].values())
        if no_patches or report["errors"]:
            raise InstrumentationError(
                "Monora instrumentation failed; no supported SDK methods patched"
            )

    return report


def _instrument_openai(
    purpose: str,
    reason: Optional[str],
    data_classification: Optional[str],
) -> Tuple[List[str], List[str]]:
    if not _module_available("openai"):
        return [], ["OpenAI SDK not installed; skipping auto-instrumentation"]

    decorator = llm_call(
        model=None,
        data_classification=data_classification,
        purpose=purpose,
        reason=reason,
    )

    targets = [
        ("openai.resources.chat.completions", "Completions", "create"),
        ("openai.resources.completions", "Completions", "create"),
    ]
    if _target_available("openai.resources.responses", "Responses"):
        targets.append(("openai.resources.responses", "Responses", "create"))
    return _patch_targets(targets, decorator)


def _instrument_anthropic(
    purpose: str,
    reason: Optional[str],
    data_classification: Optional[str],
) -> Tuple[List[str], List[str]]:
    if not _module_available("anthropic"):
        return [], ["Anthropic SDK not installed; skipping auto-instrumentation"]

    decorator = llm_call(
        model=None,
        data_classification=data_classification,
        purpose=purpose,
        reason=reason,
    )
    targets = [("anthropic.resources.messages", "Messages", "create")]
    if _target_available("anthropic.resources.completions", "Completions"):
        targets.append(("anthropic.resources.completions", "Completions", "create"))
    return _patch_targets(targets, decorator)


def _patch_targets(
    targets: List[Tuple[str, str, str]],
    decorator: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> Tuple[List[str], List[str]]:
    patched = []
    errors = []
    for module_path, class_name, method_name in targets:
        ok, error = _patch_method(module_path, class_name, method_name, decorator)
        if ok:
            patched.append(f"{module_path}.{class_name}.{method_name}")
        elif error:
            errors.append(error)
    return patched, errors


def _patch_method(
    module_path: str,
    class_name: str,
    method_name: str,
    decorator: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> Tuple[bool, Optional[str]]:
    try:
        module = importlib.import_module(module_path)
    except Exception:
        return False, f"Module '{module_path}' not available"

    cls = getattr(module, class_name, None)
    if cls is None:
        return False, f"Class '{class_name}' not found in {module_path}"

    method = getattr(cls, method_name, None)
    if method is None:
        return False, f"Method '{class_name}.{method_name}' not found in {module_path}"

    func, rewrap = _unwrap_method(method)
    if getattr(func, "__monora_wrapped__", False):
        return True, None
    if not callable(func):
        return False, f"Method '{class_name}.{method_name}' is not callable"
    if inspect.iscoroutinefunction(func):
        return (
            False,
            f"Async method '{module_path}.{class_name}.{method_name}' not supported",
        )

    wrapped = decorator(func)
    setattr(wrapped, "__monora_wrapped__", True)
    if rewrap:
        wrapped = rewrap(wrapped)
    setattr(cls, method_name, wrapped)
    return True, None


def _unwrap_method(method: Any) -> Tuple[Callable[..., Any], Optional[Callable[..., Any]]]:
    if isinstance(method, staticmethod):
        return method.__func__, staticmethod
    if isinstance(method, classmethod):
        return method.__func__, classmethod
    return method, None


def _module_available(name: str) -> bool:
    if name in sys.modules:
        return True
    spec = importlib.util.find_spec(name)
    return spec is not None


def _target_available(module_path: str, class_name: str) -> bool:
    if not _module_available(module_path):
        return False
    try:
        module = importlib.import_module(module_path)
    except Exception:
        return False
    return getattr(module, class_name, None) is not None
