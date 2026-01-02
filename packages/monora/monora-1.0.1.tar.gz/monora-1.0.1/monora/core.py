"""Core SDK functionality and global state management."""
import sys
import threading
import queue
import time
import atexit
from typing import Dict, List, Optional, Callable
from pathlib import Path

from .config import load_config
from .sinks import Sink, SinkError, StdoutSink, FileSink, HttpSink
from .events import EventBuilder
from .policy import PolicyEngine, PolicyViolation
from .hasher import Hasher


class MonoraSDK:
    """Global SDK state and configuration."""

    def __init__(self):
        self.initialized = False
        self.config: Dict = {}
        self.sinks: List[Sink] = []
        self.event_builder: Optional[EventBuilder] = None
        self.policy_engine: Optional[PolicyEngine] = None
        self.hasher: Optional[Hasher] = None
        self.violation_handler: Optional[Callable[[PolicyViolation], None]] = None

        # Background worker for non-blocking event emission
        self.event_queue: queue.Queue = queue.Queue(maxsize=10000)
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_flag = threading.Event()

        # Fallback file sink for when primary sinks fail
        self.fallback_sink: Optional[FileSink] = None

    def init(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict] = None,
        env_prefix: str = "MONORA_",
        fail_fast: bool = False,
    ) -> None:
        """Initialize the Monora SDK.

        Args:
            config_path: Path to YAML/JSON config file
            config_dict: Direct config dictionary
            env_prefix: Environment variable prefix
            fail_fast: Raise on sink initialization errors vs warn
        """
        if self.initialized:
            print("WARNING: Monora already initialized", file=sys.stderr)
            return

        # Load configuration
        self.config = load_config(
            config_path=config_path,
            config_dict=config_dict,
            env_prefix=env_prefix,
        )

        # Initialize components
        self.event_builder = EventBuilder(self.config)
        self.policy_engine = PolicyEngine(self.config.get("policies", {}))
        self.hasher = Hasher(self.config.get("immutability", {}))

        # Initialize sinks
        self._init_sinks(fail_fast)

        # Setup fallback file sink
        self._init_fallback_sink()

        # Start background worker
        self._start_worker()

        # Register cleanup on exit
        atexit.register(self.shutdown)

        self.initialized = True

    def _init_sinks(self, fail_fast: bool) -> None:
        """Initialize configured sinks."""
        sink_configs = self.config.get("sinks", [])

        for sink_config in sink_configs:
            try:
                sink = self._create_sink(sink_config)
                self.sinks.append(sink)
            except Exception as e:
                error_msg = f"Failed to initialize sink {sink_config.get('type')}: {e}"
                if fail_fast:
                    raise RuntimeError(error_msg) from e
                else:
                    print(f"WARNING: {error_msg}", file=sys.stderr)

        # Ensure at least one sink
        if not self.sinks:
            print("WARNING: No sinks configured, adding stdout sink", file=sys.stderr)
            self.sinks.append(StdoutSink())

    def _create_sink(self, config: Dict) -> Sink:
        """Create a sink from configuration."""
        sink_type = config.get("type", "stdout")

        if sink_type == "stdout":
            return StdoutSink(format=config.get("format", "json"))

        elif sink_type == "file":
            return FileSink(
                path=config["path"],
                batch_size=config.get("batch_size", 100),
                flush_interval_sec=config.get("flush_interval_sec", 5.0),
                rotation=config.get("rotation", "none"),
                max_size_mb=config.get("max_size_mb", 100),
            )

        elif sink_type == "https":
            # Expand environment variables in headers
            headers = config.get("headers", {})
            expanded_headers = {
                k: self._expand_env_vars(v) for k, v in headers.items()
            }

            return HttpSink(
                endpoint=config["endpoint"],
                headers=expanded_headers,
                batch_size=config.get("batch_size", 50),
                timeout_sec=config.get("timeout_sec", 10.0),
                retry_attempts=config.get("retry_attempts", 3),
            )

        else:
            raise ValueError(f"Unknown sink type: {sink_type}")

    def _expand_env_vars(self, value: str) -> str:
        """Expand ${VAR} syntax in strings."""
        import re
        import os

        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, "")

        return re.sub(r"\$\{(\w+)\}", replace, value)

    def _init_fallback_sink(self) -> None:
        """Initialize fallback file sink for when primary sinks fail."""
        try:
            fallback_path = Path.home() / ".monora" / "fallback.jsonl"
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            self.fallback_sink = FileSink(str(fallback_path), batch_size=10)
        except Exception as e:
            print(f"WARNING: Failed to create fallback sink: {e}", file=sys.stderr)

    def _start_worker(self) -> None:
        """Start background worker thread for non-blocking event emission."""

        def worker():
            while not self.shutdown_flag.is_set():
                try:
                    # Get event with timeout to allow shutdown check
                    event = self.event_queue.get(timeout=0.5)
                    self._emit_to_sinks(event)
                    self.event_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"WARNING: Worker thread error: {e}", file=sys.stderr)

        self.worker_thread = threading.Thread(
            target=worker, daemon=False, name="monora-event-worker"
        )
        self.worker_thread.start()

    def emit_event(self, event: Dict) -> None:
        """Emit an event through the background worker (non-blocking).

        Args:
            event: Event dictionary
        """
        if not self.initialized:
            print("WARNING: Monora not initialized, dropping event", file=sys.stderr)
            return

        try:
            # Non-blocking put with timeout
            self.event_queue.put(event, timeout=0.1)
        except queue.Full:
            print("WARNING: Event queue full, dropping event", file=sys.stderr)
            # Try fallback sink
            if self.fallback_sink:
                try:
                    self.fallback_sink.emit([event])
                except Exception:
                    pass

    def _emit_to_sinks(self, event: Dict) -> None:
        """Emit event to all sinks with error handling."""
        failure_mode = self.config.get("error_handling", {}).get(
            "sink_failure_mode", "warn"
        )

        for sink in self.sinks:
            try:
                sink.emit([event])
            except SinkError as e:
                if failure_mode == "raise":
                    raise
                elif failure_mode == "warn":
                    print(f"WARNING: Sink error: {e}", file=sys.stderr)
                    # Try fallback
                    if self.fallback_sink:
                        try:
                            self.fallback_sink.emit([event])
                        except Exception:
                            pass
                # "silent" mode: do nothing

    def shutdown(self) -> None:
        """Shutdown SDK and cleanup resources."""
        if not self.initialized:
            return

        # Signal worker to stop
        self.shutdown_flag.set()

        # Wait for queue to drain (with timeout)
        try:
            self.event_queue.join()
        except Exception:
            pass

        # Wait for worker thread
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)

        # Flush and close all sinks
        for sink in self.sinks:
            try:
                sink.flush()
                sink.close()
            except Exception as e:
                print(f"WARNING: Error closing sink: {e}", file=sys.stderr)

        # Close fallback sink
        if self.fallback_sink:
            try:
                self.fallback_sink.close()
            except Exception:
                pass

        self.initialized = False


# Global SDK instance
_sdk = MonoraSDK()


def get_sdk() -> MonoraSDK:
    """Get the global SDK instance."""
    return _sdk
