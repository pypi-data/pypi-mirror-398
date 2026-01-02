"""Event enrichers that add metadata to events."""
from datetime import datetime, timezone
import socket
import os
from typing import Dict


class Enricher:
    """Base enricher interface."""

    def enrich(self, event: Dict) -> None:
        """Enrich the event dict in-place."""
        raise NotImplementedError


class TimestampEnricher(Enricher):
    """Add ISO 8601 UTC timestamp."""

    def enrich(self, event: Dict) -> None:
        event["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class ServiceNameEnricher(Enricher):
    """Add service name from config or process name."""

    def __init__(self, config: Dict):
        defaults = config.get("defaults", {})
        self.service_name = defaults.get("service_name") or self._get_process_name()

    def _get_process_name(self) -> str:
        """Get the process name from argv or fallback."""
        import sys

        if sys.argv:
            return os.path.basename(sys.argv[0]) or "unknown"
        return "unknown"

    def enrich(self, event: Dict) -> None:
        event["service_name"] = self.service_name


class EnvironmentEnricher(Enricher):
    """Add environment (dev/staging/production)."""

    def __init__(self, config: Dict):
        defaults = config.get("defaults", {})
        self.environment = defaults.get("environment", "dev")

    def enrich(self, event: Dict) -> None:
        event["environment"] = self.environment


class HostEnricher(Enricher):
    """Add hostname."""

    def __init__(self):
        try:
            self.host = socket.gethostname()
        except Exception:
            self.host = "unknown"

    def enrich(self, event: Dict) -> None:
        event["host"] = self.host


class ProcessEnricher(Enricher):
    """Add process ID."""

    def __init__(self):
        self.process_id = os.getpid()

    def enrich(self, event: Dict) -> None:
        event["process_id"] = self.process_id
