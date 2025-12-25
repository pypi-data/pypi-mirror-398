"""Tests for Artanis client."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from artanis import Artanis
from artanis.trace import Trace


class TestArtanisInit:
    """Test Artanis client initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = Artanis(api_key="sk_test123")
        assert client._api_key == "sk_test123"
        assert client._enabled is True

    def test_init_from_env(self, monkeypatch):
        """Test initialization from environment variable."""
        monkeypatch.setenv("ARTANIS_API_KEY", "sk_env123")
        client = Artanis()
        assert client._api_key == "sk_env123"

    def test_init_missing_api_key(self, monkeypatch):
        """Test that missing API key raises ValueError when enabled."""
        monkeypatch.delenv("ARTANIS_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key is required"):
            Artanis()

    def test_init_disabled_no_key_required(self, monkeypatch):
        """Test that disabled client doesn't require API key."""
        monkeypatch.delenv("ARTANIS_API_KEY", raising=False)
        client = Artanis(enabled=False)
        assert client._enabled is False

    def test_init_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = Artanis(api_key="sk_test", base_url="https://custom.api.com")
        assert client._base_url == "https://custom.api.com"

    def test_init_with_debug(self):
        """Test initialization with debug enabled."""
        client = Artanis(api_key="sk_test", debug=True)
        assert client._debug is True

    def test_init_with_error_callback(self):
        """Test initialization with error callback."""
        callback = Mock()
        client = Artanis(api_key="sk_test", on_error=callback)
        assert client._transport.on_error == callback

    def test_env_enabled_false(self, monkeypatch):
        """Test ARTANIS_ENABLED=false disables client."""
        monkeypatch.setenv("ARTANIS_API_KEY", "sk_test")
        monkeypatch.setenv("ARTANIS_ENABLED", "false")
        client = Artanis()
        assert client._enabled is False


class TestArtanisTrace:
    """Test trace creation."""

    def test_trace_basic(self):
        """Test basic trace creation."""
        client = Artanis(api_key="sk_test")
        trace = client.trace("test-operation")

        assert isinstance(trace, Trace)
        assert trace._name == "test-operation"
        assert trace.id.startswith("trace_")

    def test_trace_with_metadata(self):
        """Test trace creation with metadata."""
        client = Artanis(api_key="sk_test")
        metadata = {"user_id": "user-123", "session_id": "session-456"}
        trace = client.trace("test-operation", metadata=metadata)

        assert trace._metadata == metadata

    def test_trace_unique_ids(self):
        """Test that each trace gets a unique ID."""
        client = Artanis(api_key="sk_test")
        trace1 = client.trace("op1")
        trace2 = client.trace("op2")

        assert trace1.id != trace2.id


class TestArtanisFeedback:
    """Test feedback recording."""

    @patch("artanis.client.Transport.send")
    def test_feedback_positive(self, mock_send):
        """Test recording positive feedback."""
        client = Artanis(api_key="sk_test")
        client.feedback("trace_123", rating="positive")

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert call_args[0] == "/api/v1/feedback"
        assert call_args[1]["trace_id"] == "trace_123"
        assert call_args[1]["rating"] == "positive"

    @patch("artanis.client.Transport.send")
    def test_feedback_negative(self, mock_send):
        """Test recording negative feedback."""
        client = Artanis(api_key="sk_test")
        client.feedback("trace_123", rating="negative")

        call_args = mock_send.call_args[0]
        assert call_args[1]["rating"] == "negative"

    @patch("artanis.client.Transport.send")
    def test_feedback_numeric(self, mock_send):
        """Test recording numeric feedback."""
        client = Artanis(api_key="sk_test")
        client.feedback("trace_123", rating=0.85)

        call_args = mock_send.call_args[0]
        assert call_args[1]["rating"] == 0.85

    @patch("artanis.client.Transport.send")
    def test_feedback_with_comment(self, mock_send):
        """Test feedback with comment."""
        client = Artanis(api_key="sk_test")
        client.feedback("trace_123", rating="negative", comment="Wrong answer")

        call_args = mock_send.call_args[0]
        assert call_args[1]["comment"] == "Wrong answer"

    @patch("artanis.client.Transport.send")
    def test_feedback_with_correction(self, mock_send):
        """Test feedback with correction."""
        client = Artanis(api_key="sk_test")
        correction = {"answer": "The correct answer is 42"}
        client.feedback("trace_123", rating="negative", correction=correction)

        call_args = mock_send.call_args[0]
        assert call_args[1]["correction"] == correction


class TestArtanisContextManager:
    """Test context manager support."""

    def test_context_manager(self):
        """Test Artanis can be used as context manager."""
        with Artanis(api_key="sk_test") as client:
            assert isinstance(client, Artanis)
            trace = client.trace("test")
            assert isinstance(trace, Trace)

    @patch("artanis.client.Transport.close")
    def test_context_manager_cleanup(self, mock_close):
        """Test context manager calls close on exit."""
        with Artanis(api_key="sk_test") as client:
            pass

        mock_close.assert_called_once()
