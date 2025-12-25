"""Async HTTP transport layer for Artanis SDK."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional

import aiohttp


logger = logging.getLogger(__name__)


class Transport:
    """
    Non-blocking HTTP transport for sending traces and feedback.

    Uses a background thread pool to send HTTP requests asynchronously
    without blocking the main application thread.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        enabled: bool = True,
        debug: bool = False,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Initialize transport layer.

        Args:
            base_url: Base URL for Artanis API
            api_key: API key for authentication
            enabled: Whether tracing is enabled
            debug: Enable debug logging
            on_error: Optional callback for errors
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.enabled = enabled
        self.debug = debug
        self.on_error = on_error

        # Thread pool for async execution
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="artanis-")

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "artanis-python/0.1.0",
        }

    def _log_error(self, error: Exception, context: str = "") -> None:
        """Log error if debug enabled, call error callback if provided."""
        if self.debug:
            logger.warning(f"Artanis error ({context}): {error}")

        if self.on_error:
            try:
                self.on_error(error)
            except Exception as e:
                if self.debug:
                    logger.error(f"Error in on_error callback: {e}")

    async def _send_async(self, endpoint: str, data: Dict[str, Any]) -> None:
        """
        Send data to API asynchronously.

        Args:
            endpoint: API endpoint (e.g., "/v1/traces")
            data: Data to send as JSON
        """
        if not self.enabled:
            return

        url = f"{self.base_url}{endpoint}"

        try:
            # Create session within async context to avoid event loop conflicts
            timeout = aiohttp.ClientTimeout(total=10, connect=2)
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_headers(),
            ) as session:
                async with session.post(url, json=data) as response:
                    # Log non-2xx responses if debug enabled
                    if self.debug and response.status >= 300:
                        text = await response.text()
                        logger.warning(
                            f"Artanis API returned {response.status}: {text[:200]}"
                        )

                    # Don't raise on errors - fail silently
                    if response.status == 401:
                        raise Exception("Invalid API key")
                    elif response.status == 413:
                        raise Exception("Payload too large")
                    elif response.status == 429:
                        raise Exception("Rate limit exceeded")

        except Exception as e:
            self._log_error(e, f"POST {endpoint}")

    def _send_in_thread(self, endpoint: str, data: Dict[str, Any]) -> None:
        """
        Execute async send in a background thread.

        This method creates a new event loop in the background thread
        and runs the async send operation.
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._send_async(endpoint, data))
            finally:
                loop.close()
        except Exception as e:
            self._log_error(e, f"thread executor")

    def send(self, endpoint: str, data: Dict[str, Any]) -> None:
        """
        Send data to API in a non-blocking way.

        This is the main public method. It immediately returns after
        submitting the send task to the background thread pool.

        Args:
            endpoint: API endpoint (e.g., "/v1/traces")
            data: Data to send as JSON
        """
        if not self.enabled:
            return

        # Submit to thread pool and return immediately (fire-and-forget)
        self._executor.submit(self._send_in_thread, endpoint, data)

    def close(self) -> None:
        """
        Close transport and cleanup resources.

        Note: In normal usage, this doesn't need to be called as the
        SDK is designed for long-lived processes. However, it's useful
        for testing and explicit cleanup.
        """
        # Shutdown thread pool
        self._executor.shutdown(wait=False)

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            self.close()
        except Exception:
            pass  # Fail silently on cleanup
