"""Security review report generation."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from monora.config import load_config
from monora.registry import ModelRegistry
from monora.verify import verify_chain, detect_sequence_gaps, detect_tampering

logger = logging.getLogger(__name__)


def generate_security_report(
    events: List[Dict[str, Any]],
    config_path: Optional[str] = None,
    config_dict: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Generate a comprehensive security review report.

    Args:
        events: List of event dictionaries from logs
        config_path: Optional path to config file
        config_dict: Optional config dictionary

    Returns:
        Dictionary containing comprehensive security review report
    """
    # Load configuration
    if config_path or config_dict:
        config = load_config(config_path=config_path, config_dict=config_dict)
    else:
        config = {}

    # Build report sections
    report = {
        "report_metadata": _build_report_metadata(events),
        "configuration_snapshot": _build_config_snapshot(config),
        "chain_integrity": _verify_chain_integrity(events),
        "completeness": _build_completeness(events),
        "compliance_summary": _build_compliance_summary(events, config),
        "risk_assessment": _assess_risks(events, config),
        "operational_metrics": _build_operational_metrics(events, config),
        "attestation": _build_attestation(),
    }

    return report


def _build_report_metadata(events: List[Dict]) -> Dict:
    """Build report metadata section."""
    timestamps = [
        datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        for e in events
        if "timestamp" in e
    ]

    start = min(timestamps) if timestamps else None
    end = max(timestamps) if timestamps else None
    duration_days = (end - start).days if (start and end) else 0

    return {
        "report_type": "security_review",
        "format_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "monora-cli/1.0.0",
        "report_id": f"sreport_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "report_period": {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "duration_days": duration_days,
        },
        "event_source": {
            "total_events": len(events),
            "hash_verified": all("event_hash" in e for e in events),
        },
    }


def _build_config_snapshot(config: Dict) -> Dict:
    """Capture configuration snapshot."""
    config_json = json.dumps(config, sort_keys=True, separators=(",", ":"))
    config_hash = hashlib.sha256(config_json.encode()).hexdigest()

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "config_hash": f"sha256:{config_hash}",
        "policies": config.get("policies", {}),
        "immutability": config.get("immutability", {}),
        "defaults": config.get("defaults", {}),
        "registry": config.get("registry", {}),
    }


def _verify_chain_integrity(events: List[Dict]) -> Dict:
    """Verify hash chain integrity."""
    is_valid, error = verify_chain(events)
    tampered = detect_tampering(events)

    traces = {e.get("trace_id") for e in events if e.get("trace_id")}

    return {
        "verification_status": "verified" if is_valid else "failed",
        "verification_algorithm": "sha256",
        "total_events_verified": len(events),
        "events_with_invalid_hash": len(tampered),
        "chain_breaks_detected": sum(
            1 for t in tampered if "chain break" in t.get("reason", "").lower()
        ),
        "traces_verified": len(traces),
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "tampering_detected": len(tampered) > 0,
        "tampered_events": tampered[:10],  # First 10 for brevity
    }


def _build_completeness(events: List[Dict]) -> Dict:
    """Build audit completeness summary based on event_sequence."""
    gaps = detect_sequence_gaps(events)
    missing = sum(len(g.get("missing_sequences", [])) for g in gaps)
    duplicates = sum(len(g.get("duplicate_sequences", [])) for g in gaps)
    return {
        "traces_checked": len({e.get("trace_id") for e in events if e.get("trace_id")}),
        "traces_with_gaps": len(gaps),
        "missing_events": missing,
        "duplicate_sequences": duplicates,
        "gaps": gaps[:10],
    }


def _build_compliance_summary(events: List[Dict], config: Dict) -> Dict:
    """Build compliance summary section."""
    from monora.cli.report import _build_report

    # Reuse existing report builder
    base_report = _build_report(events, policies=config.get("policies"))

    violations = base_report.get("violations", [])
    compliance = base_report.get("model_compliance", {})

    # Calculate violation rate
    timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
    if timestamps:
        start = min(
            datetime.fromisoformat(t.replace("Z", "+00:00")) for t in timestamps
        )
        end = max(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in timestamps)
        days = (end - start).days or 1
        violations_per_day = len(violations) / days
    else:
        violations_per_day = 0.0

    # Allowlist coverage
    allowed = compliance.get("allowed_models_used", [])
    forbidden = compliance.get("forbidden_models_blocked", [])
    unknown = compliance.get("unknown_models_used", [])
    total_models = len(allowed) + len(unknown)
    coverage_pct = (len(allowed) / total_models * 100) if total_models > 0 else 100.0

    return {
        "policy_violations": {
            "total_violations": len(violations),
            "by_policy": _count_by_policy(violations),
            "unique_models_blocked": list({v.get("model") for v in violations}),
            "violations_per_day": round(violations_per_day, 2),
        },
        "model_compliance": {
            **compliance,
            "allowlist_coverage_pct": round(coverage_pct, 1),
        },
        "classification_compliance": _build_classification_compliance(events),
    }


def _count_by_policy(violations: List[Dict]) -> Dict[str, int]:
    """Count violations by policy."""
    counts = {}
    for v in violations:
        policy = v.get("policy", "unknown")
        counts[policy] = counts.get(policy, 0) + 1
    return counts


def _build_classification_compliance(events: List[Dict]) -> Dict:
    """Build classification compliance breakdown."""
    by_classification = {}
    for event in events:
        classification = event.get("data_classification", "unknown")
        if classification not in by_classification:
            by_classification[classification] = {"total_events": 0, "violations": 0}

        by_classification[classification]["total_events"] += 1

        # Count violations
        body = event.get("body", {})
        if body.get("status") == "policy_violation":
            by_classification[classification]["violations"] += 1

    return by_classification


def _assess_risks(events: List[Dict], config: Dict) -> Dict:
    """Assess security risks."""
    from monora.cli.report import _build_report

    report = _build_report(events, policies=config.get("policies"))

    violations = report.get("violations", [])
    unknown_models = report.get("model_compliance", {}).get("unknown_models_used", [])
    tampered = detect_tampering(events)
    gaps = detect_sequence_gaps(events)

    risk_factors = []
    total_score = 0

    # Violations risk
    if len(violations) > 10:
        severity = "high"
        score = 3
    elif len(violations) > 0:
        severity = "low"
        score = 1
    else:
        severity = "none"
        score = 0

    risk_factors.append(
        {
            "factor": "policy_violations",
            "severity": severity,
            "score": score,
            "details": f"{len(violations)} violations detected",
        }
    )
    total_score += score

    # Unknown models risk
    if len(unknown_models) > 5:
        severity = "high"
        score = 3
    elif len(unknown_models) > 0:
        severity = "medium"
        score = 2
    else:
        severity = "none"
        score = 0

    risk_factors.append(
        {
            "factor": "unknown_models",
            "severity": severity,
            "score": score,
            "details": f"{len(unknown_models)} unknown models used",
        }
    )
    total_score += score

    # Chain integrity risk
    if len(tampered) > 0:
        severity = "critical"
        score = 5
    else:
        severity = "none"
        score = 0

    risk_factors.append(
        {
            "factor": "chain_integrity",
            "severity": severity,
            "score": score,
            "details": "Tampering detected" if tampered else "All events verified",
        }
    )
    total_score += score

    # Completeness risk
    if len(gaps) > 0:
        severity = "medium"
        score = 2
    else:
        severity = "none"
        score = 0

    risk_factors.append(
        {
            "factor": "completeness",
            "severity": severity,
            "score": score,
            "details": f"{len(gaps)} traces with sequence gaps",
        }
    )
    total_score += score

    # Overall risk level
    if total_score >= 5:
        risk_level = "high"
    elif total_score >= 2:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "overall_risk_level": risk_level,
        "risk_factors": risk_factors,
        "total_risk_score": total_score,
    }


def _build_operational_metrics(events: List[Dict], config: Dict) -> Dict:
    """Build operational metrics section."""
    from monora.cli.report import _build_report

    report = _build_report(events)

    # Get model usage
    by_model = report.get("by_model", {})
    token_usage = report.get("token_usage", {})

    # Build provider aggregation with registry defaults
    registry = ModelRegistry(config.get("registry", {}))
    by_provider = {}
    for model, count in by_model.items():
        provider = None
        resolution_error = None
        try:
            resolved = registry.resolve(model)
        except Exception as exc:
            resolved = None
            resolution_error = exc
        if resolved:
            provider, _ = resolved
        if not provider:
            if resolution_error:
                logger.warning(
                    "Model registry resolution failed for '%s': %s", model, resolution_error
                )
            else:
                logger.warning(
                    "Model registry missing provider for '%s'; using 'unknown'", model
                )
            provider = "unknown"
        if isinstance(provider, str) and provider:
            by_provider[provider] = by_provider.get(provider, 0) + count

    return {
        "total_traces": report.get("traces", 0),
        "total_llm_calls": sum(by_model.values()),
        "by_provider": by_provider,
        "by_model": by_model,
        "token_usage": token_usage,
        "errors": {
            "total_errors": len(report.get("errors", [])),
            "by_type": _count_errors_by_type(report.get("errors", [])),
        },
    }


def _count_errors_by_type(errors: List[Dict]) -> Dict[str, int]:
    """Count errors by type."""
    counts = {}
    for error in errors:
        error_type = error.get("error", "unknown")
        if isinstance(error_type, dict):
            error_type = error_type.get("type", "unknown")
        counts[error_type] = counts.get(error_type, 0) + 1
    return counts


def _build_attestation() -> Dict:
    """Build attestation section."""
    return {
        "attestation_type": "hash_verification",
        "attester": "monora-cli",
        "attestation_timestamp": datetime.now(timezone.utc).isoformat(),
        "verified_by": None,
        "approval_status": "pending_review",
        "notes": [],
    }
