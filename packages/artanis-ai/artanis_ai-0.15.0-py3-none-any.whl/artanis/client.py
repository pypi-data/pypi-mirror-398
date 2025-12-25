"""Main Artanis client class."""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Union

from artanis.trace import Trace
from artanis.transport import Transport
from artanis.types import Rating

logger = logging.getLogger(__name__)


class Artanis:
    """
    Main Artanis SDK client.

    Provides methods for creating traces and recording feedback for
    AI application observability.

    Example:
        from artanis import Artanis

        artanis = Artanis(api_key="sk_...")

        # Create a trace
        trace = artanis.trace("answer-question")
        trace.input(question="What is AI?")
        trace.output("AI stands for Artificial Intelligence")

        # Record feedback
        artanis.feedback(trace.id, rating="positive")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://app.artanis.ai",
        enabled: bool = True,
        debug: bool = False,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Initialize Artanis client.

        Args:
            api_key: Your Artanis API key (or set ARTANIS_API_KEY env var)
            base_url: Base URL for Artanis API (default: https://app.artanis.ai)
            enabled: Enable/disable all tracing (default: True)
            debug: Enable debug logging (default: False)
            on_error: Optional callback for error handling

        Raises:
            ValueError: If api_key is not provided and ARTANIS_API_KEY is not set

        Example:
            # From environment variable
            artanis = Artanis()

            # Explicit API key
            artanis = Artanis(api_key="sk_...")

            # Custom configuration
            artanis = Artanis(
                api_key="sk_...",
                base_url="https://custom.api.com",
                enabled=True,
                debug=False,
                on_error=lambda e: logger.warning(f"Artanis: {e}")
            )

            # Disable for testing
            artanis = Artanis(enabled=False)
        """
        # Read from environment if not provided
        self._api_key = api_key or os.environ.get("ARTANIS_API_KEY")

        if not self._api_key and enabled:
            raise ValueError(
                "Artanis API key is required. "
                "Provide api_key parameter or set ARTANIS_API_KEY environment variable."
            )

        # Read other settings from environment (with provided values as defaults)
        self._base_url = os.environ.get("ARTANIS_BASE_URL", base_url)
        self._enabled = os.environ.get("ARTANIS_ENABLED", str(enabled)).lower() in (
            "true",
            "1",
            "yes",
        )
        self._debug = os.environ.get("ARTANIS_DEBUG", str(debug)).lower() in (
            "true",
            "1",
            "yes",
        )

        # Configure logging if debug enabled
        if self._debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

        # Initialize transport
        self._transport = Transport(
            base_url=self._base_url,
            api_key=self._api_key or "",  # Empty string if disabled
            enabled=self._enabled,
            debug=self._debug,
            on_error=on_error,
        )

    def trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Trace:
        """
        Create a new trace for an operation.

        Args:
            name: Name of the operation (e.g., "answer-question", "classify-ticket")
            metadata: Optional metadata for filtering/searching (e.g., user_id, session_id)

        Returns:
            Trace instance for recording inputs, outputs, and state

        Example:
            # Basic usage
            trace = artanis.trace("answer-question")
            trace.input(question="What is AI?")
            trace.output("AI stands for Artificial Intelligence")

            # With metadata
            trace = artanis.trace(
                "answer-question",
                metadata={"user_id": "user-123", "session_id": "session-456"}
            )

            # With state for replay
            trace = artanis.trace("rag-query")
            trace.state("documents", [{"id": "doc1", "score": 0.95}])
            trace.input(query="...", model="gpt-4")
            trace.output(response)

            # Context manager usage
            with artanis.trace("operation") as trace:
                trace.input(data=...)
                result = perform_operation()
                trace.output(result)
        """
        return Trace(name=name, transport=self._transport, metadata=metadata)

    def feedback(
        self,
        trace_id: str,
        rating: Rating,
        comment: Optional[str] = None,
        correction: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record feedback for a trace.

        Args:
            trace_id: ID of the trace to provide feedback for
            rating: Rating as "positive", "negative", or numeric (0.0-1.0)
            comment: Optional comment or note
            correction: Optional correction data (e.g., {"answer": "correct value"})

        Example:
            # Binary feedback
            artanis.feedback(trace.id, rating="positive")
            artanis.feedback(trace.id, rating="negative", comment="Wrong answer")

            # Numeric rating
            artanis.feedback(trace.id, rating=0.85)

            # With correction
            artanis.feedback(
                trace.id,
                rating="negative",
                correction={"answer": "The correct answer is..."}
            )
        """
        payload = {
            "trace_id": trace_id,
            "rating": rating,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        }

        if comment is not None:
            payload["comment"] = comment

        if correction is not None:
            payload["correction"] = correction

        # Send feedback asynchronously
        self._transport.send("/api/v1/feedback", payload)

    def close(self) -> None:
        """
        Close the client and cleanup resources.

        This is typically not needed in normal usage as the SDK is designed
        for long-lived processes. However, it can be useful in testing or
        for explicit cleanup.

        Example:
            artanis = Artanis()
            try:
                # Use SDK...
                pass
            finally:
                artanis.close()
        """
        self._transport.close()

    def __enter__(self) -> "Artanis":
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Cleanup on context exit."""
        self.close()
