"""Signed attestation bundle helpers."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class AttestationError(RuntimeError):
    """Raised when attestation signing fails."""


@dataclass
class SignatureResult:
    signature: str
    signature_type: str
    key_id: Optional[str] = None
    fingerprint: Optional[str] = None


def serialize_report(report: Dict[str, Any]) -> bytes:
    return json.dumps(report, indent=2, ensure_ascii=True).encode("utf-8")


def compute_sha256(payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def sign_report_gpg(
    report_bytes: bytes,
    *,
    key_id: Optional[str] = None,
    gpg_home: Optional[str] = None,
) -> SignatureResult:
    gpg_bin = shutil.which("gpg")
    if not gpg_bin:
        raise AttestationError("gpg not found on PATH")

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = f"{tmpdir}/report.json"
        sig_path = f"{tmpdir}/report.json.asc"
        with open(report_path, "wb") as handle:
            handle.write(report_bytes)

        cmd = [gpg_bin, "--armor", "--detach-sign", "--output", sig_path]
        if gpg_home:
            cmd.extend(["--homedir", gpg_home])
        if key_id:
            cmd.extend(["--local-user", key_id])
        cmd.append(report_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AttestationError(result.stderr.strip() or "gpg signing failed")

        with open(sig_path, "r", encoding="utf-8") as handle:
            signature = handle.read()

    fingerprint = _gpg_fingerprint(key_id, gpg_home)
    return SignatureResult(
        signature=signature,
        signature_type="gpg",
        key_id=key_id,
        fingerprint=fingerprint,
    )


def build_attestation_bundle(
    report: Dict[str, Any],
    report_bytes: bytes,
    signature: SignatureResult,
) -> Dict[str, Any]:
    return {
        "bundle_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_sha256": compute_sha256(report_bytes),
        "report_json": report_bytes.decode("utf-8"),
        "signature": {
            "type": signature.signature_type,
            "value": signature.signature,
            "key_id": signature.key_id,
            "fingerprint": signature.fingerprint,
            "signed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _gpg_fingerprint(key_id: Optional[str], gpg_home: Optional[str]) -> Optional[str]:
    if not key_id:
        return None
    gpg_bin = shutil.which("gpg")
    if not gpg_bin:
        return None

    cmd = [gpg_bin, "--with-colons", "--fingerprint", key_id]
    if gpg_home:
        cmd.extend(["--homedir", gpg_home])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if not line.startswith("fpr:"):
            continue
        parts = line.split(":")
        for part in reversed(parts):
            if part:
                return part
    return None
