"""Trace class for capturing application traces."""

import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from artanis.types import ObservationType

if TYPE_CHECKING:
    from artanis.transport import Transport


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return f"trace_{secrets.token_urlsafe(16)}"


def generate_observation_id() -> str:
    """Generate a unique observation ID."""
    return f"obs_{secrets.token_urlsafe(15)}"


class Trace:
    """
    Represents a single trace of an operation.

    Traces capture inputs, outputs, and state from AI application operations.
    Observations are sent immediately as they occur for crash resilience.
    All methods are thread-safe and can be called multiple times.
    """

    def __init__(
        self,
        name: str,
        transport: "Transport",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new trace.

        Args:
            name: Name of the operation being traced
            transport: Transport instance for sending data
            metadata: Optional metadata for filtering/searching
        """
        self.id = generate_trace_id()
        self._name = name
        self._transport = transport
        self._metadata = metadata or {}

        # Timing
        self._start_time = time.perf_counter()
        # Format timestamp as ISO 8601 with Z suffix (e.g., 2025-12-18T23:16:04.123Z)
        self._timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # Create trace in backend with status "running"
        self._send_trace_creation()

    def input(self, **kwargs: Any) -> "Trace":
        """
        Record input data for this trace.

        Each call sends an input observation immediately.

        Args:
            **kwargs: Input data as keyword arguments

        Returns:
            self (for method chaining)

        Example:
            trace.input(question="What is AI?", model="gpt-4")
            trace.input(temperature=0.7)  # Sends separate observation
        """
        self._send_observation("input", kwargs)
        return self

    def output(self, value: Any) -> "Trace":
        """
        Record the output/result of this operation.

        Sends an output observation and marks trace as completed.

        Args:
            value: The output value (any JSON-serializable type)

        Returns:
            self (for method chaining)

        Example:
            trace.output("AI stands for Artificial Intelligence")
            trace.output({"answer": "...", "confidence": 0.95})
        """
        # Send output observation
        self._send_observation("output", value)

        # Update trace status to completed
        self._send_trace_completion()
        return self

    def state(self, name: str, value: Any) -> "Trace":
        """
        Capture state for replay purposes.

        State represents context needed to exactly reproduce this operation,
        such as retrieved documents, configuration, or guidelines.
        Each call sends a state observation immediately.

        Args:
            name: Name of the state (e.g., "documents", "config", "chunks")
            value: State value (any JSON-serializable type)

        Returns:
            self (for method chaining)

        Example:
            trace.state("config", {"model": "gpt-4", "temperature": 0.7})
            trace.state("documents", [{"id": "doc1", "score": 0.95}])
        """
        self._send_observation("state", value, name)
        return self

    def _send_trace_creation(self) -> None:
        """Send trace creation to backend."""
        payload: Dict[str, Any] = {
            "trace_id": self.id,
            "name": self._name,
            "timestamp": self._timestamp,
            "status": "running",
        }

        if self._metadata:
            payload["metadata"] = self._metadata

        self._transport.send("/api/v1/traces", payload)

    def _send_observation(
        self, obs_type: ObservationType, data: Any, key: Optional[str] = None
    ) -> None:
        """Send observation to backend."""
        payload: Dict[str, Any] = {
            "trace_id": self.id,
            "type": obs_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        }

        if key:
            payload["key"] = key

        self._transport.send("/api/v1/observations", payload)

    def _send_trace_completion(self) -> None:
        """Send trace completion to backend."""
        duration_ms = int((time.perf_counter() - self._start_time) * 1000)

        payload: Dict[str, Any] = {
            "trace_id": self.id,
            "name": self._name,
            "timestamp": self._timestamp,
            "status": "completed",
            "duration_ms": duration_ms,
        }

        if self._metadata:
            payload["metadata"] = self._metadata

        self._transport.send("/api/v1/traces", payload)

    def __enter__(self) -> "Trace":
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Automatically send trace completion on context exit."""
        # Note: We no longer track errors in traces, so we just complete the trace
        pass
