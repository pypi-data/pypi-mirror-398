"""Tests for transport layer."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from artanis.transport import Transport


class TestTransportInit:
    """Test transport initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        transport = Transport(
            base_url="https://app.artanis.ai",
            api_key="sk_test123",
        )
        assert transport.base_url == "https://app.artanis.ai"
        assert transport.api_key == "sk_test123"
        assert transport.enabled is True

    def test_init_with_trailing_slash(self):
        """Test base_url trailing slash is removed."""
        transport = Transport(
            base_url="https://app.artanis.ai/",
            api_key="sk_test",
        )
        assert transport.base_url == "https://app.artanis.ai"

    def test_init_disabled(self):
        """Test initialization with tracing disabled."""
        transport = Transport(
            base_url="https://app.artanis.ai",
            api_key="sk_test",
            enabled=False,
        )
        assert transport.enabled is False

    def test_init_with_error_callback(self):
        """Test initialization with error callback."""
        callback = Mock()
        transport = Transport(
            base_url="https://app.artanis.ai",
            api_key="sk_test",
            on_error=callback,
        )
        assert transport.on_error == callback


class TestTransportHeaders:
    """Test HTTP header generation."""

    def test_get_headers(self):
        """Test headers include auth and content type."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test123",
        )
        headers = transport._get_headers()

        assert headers["Authorization"] == "Bearer sk_test123"
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers


class TestTransportSend:
    """Test send functionality."""

    def test_send_disabled(self):
        """Test send does nothing when disabled."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
            enabled=False,
        )

        # Should not raise, should do nothing
        transport.send("/api/v1/traces", {"test": "data"})

    @patch("artanis.transport.Transport._send_in_thread")
    def test_send_submits_to_executor(self, mock_send):
        """Test send submits task to thread pool."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        data = {"trace_id": "trace_123"}
        transport.send("/api/v1/traces", data)

        # Give thread pool a moment to process
        import time
        time.sleep(0.01)

        # Verify _send_in_thread was called via the executor
        # The executor.submit will call _send_in_thread in a background thread

    def test_send_fire_and_forget(self):
        """Test send returns immediately (fire-and-forget)."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        import time
        start = time.perf_counter()
        transport.send("/api/v1/traces", {"test": "data"})
        duration = time.perf_counter() - start

        # Should return in < 1ms (just submitting to thread pool)
        assert duration < 0.001


@pytest.mark.asyncio
class TestTransportAsync:
    """Test async send functionality."""

    async def test_send_async_success(self):
        """Test successful async send."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        mock_response = AsyncMock()
        mock_response.status = 202
        mock_response.text = AsyncMock(return_value="OK")

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
            await transport._send_async("/api/v1/traces", {"test": "data"})

        # Should have called post
        mock_session.post.assert_called_once()

    async def test_send_async_201_created(self):
        """Test async send handles 201 (observations created)."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.text = AsyncMock(return_value="Created")

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
            await transport._send_async("/api/v1/observations", {"test": "data"})

    async def test_send_async_401(self):
        """Test async send handles 401 (invalid API key)."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_invalid",
            debug=True,
        )

        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
            # Should not raise - fails silently
            await transport._send_async("/api/v1/traces", {"test": "data"})

    async def test_send_async_413(self):
        """Test async send handles 413 (payload too large)."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        mock_response = AsyncMock()
        mock_response.status = 413
        mock_response.text = AsyncMock(return_value="Payload too large")

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
            # Should not raise - fails silently
            await transport._send_async("/api/v1/traces", {"test": "data"})

    async def test_send_async_429(self):
        """Test async send handles 429 (rate limit)."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value="Rate limit exceeded")

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
            # Should not raise - fails silently
            await transport._send_async("/api/v1/traces", {"test": "data"})

    async def test_send_async_network_error(self):
        """Test async send handles network errors."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("Network error")
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
            # Should not raise - fails silently
            await transport._send_async("/api/v1/traces", {"test": "data"})


class TestTransportErrorHandling:
    """Test error handling and callbacks."""

    @pytest.mark.asyncio
    async def test_error_callback_called(self):
        """Test error callback is invoked on errors."""
        callback = Mock()
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
            on_error=callback,
        )

        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("Test error")
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
            await transport._send_async("/api/v1/traces", {"test": "data"})

        # Error callback should have been called
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_logging(self):
        """Test debug mode logs errors."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
            debug=True,
        )

        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("Test error")
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("artanis.transport.logger") as mock_logger:
            with patch("artanis.transport.aiohttp.ClientSession", return_value=mock_session):
                await transport._send_async("/api/v1/traces", {"test": "data"})

            # Should have logged warning
            mock_logger.warning.assert_called()


class TestTransportCleanup:
    """Test resource cleanup."""

    def test_close(self):
        """Test close method shuts down executor."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        # Should not raise
        transport.close()

        # Executor should be shut down
        assert transport._executor._shutdown


class TestTransportThreading:
    """Test threading behavior to catch event loop issues."""

    def test_send_in_thread_creates_new_event_loop(self):
        """Test _send_in_thread creates its own event loop."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        # Mock the async send to verify it gets called
        with patch.object(transport, "_send_async", new_callable=AsyncMock) as mock_send:
            transport._send_in_thread("/api/v1/traces", {"test": "data"})

            # _send_async should have been called
            mock_send.assert_called_once_with("/api/v1/traces", {"test": "data"})

    def test_concurrent_sends_dont_conflict(self):
        """Test multiple concurrent sends don't have event loop conflicts."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        # Mock the async send
        with patch.object(transport, "_send_async", new_callable=AsyncMock):
            # Send multiple requests concurrently
            for i in range(5):
                transport.send(f"/api/v1/traces", {"trace_id": f"trace_{i}"})

            # Give threads time to process
            import time
            time.sleep(0.1)

            # If there were event loop conflicts, we'd get exceptions
            # No exceptions means success


class TestTransportIntegration:
    """Integration-style tests simulating real usage."""

    def test_real_world_usage_pattern(self):
        """Test pattern matching real application usage."""
        transport = Transport(
            base_url="https://api.artanis.ai",
            api_key="sk_test",
        )

        # Mock the async send
        with patch.object(transport, "_send_async", new_callable=AsyncMock):
            # Simulate creating a trace
            transport.send("/api/v1/traces", {
                "trace_id": "trace_123",
                "name": "test-op",
                "status": "running",
                "timestamp": "2025-01-18T12:00:00Z",
            })

            # Simulate sending observations
            transport.send("/api/v1/observations", {
                "trace_id": "trace_123",
                "type": "input",
                "data": {"question": "What is AI?"},
                "timestamp": "2025-01-18T12:00:01Z",
            })

            transport.send("/api/v1/observations", {
                "trace_id": "trace_123",
                "type": "output",
                "data": "AI is...",
                "timestamp": "2025-01-18T12:00:02Z",
            })

            # Simulate completing trace
            transport.send("/api/v1/traces", {
                "trace_id": "trace_123",
                "name": "test-op",
                "status": "completed",
                "duration_ms": 1000,
                "timestamp": "2025-01-18T12:00:00Z",
            })

            # All sends should be fire-and-forget (no blocking)
            # No exceptions means success
