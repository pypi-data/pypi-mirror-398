"""Tests for Trace class."""

import time
import pytest
from unittest.mock import Mock, call

from artanis.trace import Trace, generate_trace_id, generate_observation_id


class TestTraceId:
    """Test trace ID generation."""

    def test_generate_trace_id_format(self):
        """Test trace ID has correct format."""
        trace_id = generate_trace_id()
        assert trace_id.startswith("trace_")
        assert len(trace_id) > 10

    def test_generate_trace_id_unique(self):
        """Test trace IDs are unique."""
        ids = [generate_trace_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestObservationId:
    """Test observation ID generation."""

    def test_generate_observation_id_format(self):
        """Test observation ID has correct format."""
        obs_id = generate_observation_id()
        assert obs_id.startswith("obs_")
        assert len(obs_id) > 10

    def test_generate_observation_id_unique(self):
        """Test observation IDs are unique."""
        ids = [generate_observation_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestTraceCreation:
    """Test trace creation and initialization."""

    def test_trace_sends_creation_on_init(self):
        """Test trace sends creation payload on initialization."""
        transport = Mock()
        trace = Trace("test-op", transport, metadata={"user_id": "user-123"})

        # Should send trace creation immediately
        transport.send.assert_called_once()

        call_args = transport.send.call_args[0]
        endpoint = call_args[0]
        payload = call_args[1]

        assert endpoint == "/api/v1/traces"
        assert payload["trace_id"] == trace.id
        assert payload["name"] == "test-op"
        assert payload["status"] == "running"
        assert payload["metadata"] == {"user_id": "user-123"}
        assert "timestamp" in payload

    def test_trace_creation_without_metadata(self):
        """Test trace creation without metadata."""
        transport = Mock()
        trace = Trace("test-op", transport)

        call_args = transport.send.call_args[0]
        payload = call_args[1]

        assert "metadata" not in payload


class TestTraceInput:
    """Test trace input observation."""

    def test_input_sends_observation_immediately(self):
        """Test input() sends observation immediately."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()  # Clear creation call

        trace.input(question="What is AI?", model="gpt-4")

        # Should send observation
        assert transport.send.call_count == 1
        call_args = transport.send.call_args[0]
        endpoint = call_args[0]
        payload = call_args[1]

        assert endpoint == "/api/v1/observations"
        assert payload["trace_id"] == trace.id
        assert payload["type"] == "input"
        assert payload["data"] == {"question": "What is AI?", "model": "gpt-4"}
        assert "timestamp" in payload

    def test_input_multiple_calls_send_multiple_observations(self):
        """Test multiple input() calls send separate observations."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        trace.input(question="What is AI?")
        trace.input(model="gpt-4")
        trace.input(temperature=0.7)

        # Should send 3 separate observations
        assert transport.send.call_count == 3

        # Check each observation
        calls = transport.send.call_args_list
        assert calls[0][0][0] == "/api/v1/observations"
        assert calls[0][0][1]["data"] == {"question": "What is AI?"}

        assert calls[1][0][0] == "/api/v1/observations"
        assert calls[1][0][1]["data"] == {"model": "gpt-4"}

        assert calls[2][0][0] == "/api/v1/observations"
        assert calls[2][0][1]["data"] == {"temperature": 0.7}

    def test_input_returns_self(self):
        """Test input() returns self for chaining."""
        transport = Mock()
        trace = Trace("test-op", transport)
        result = trace.input(test="value")
        assert result is trace


class TestTraceOutput:
    """Test trace output observation."""

    def test_output_sends_observation_and_completion(self):
        """Test output() sends observation and marks trace completed."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        trace.output("AI stands for Artificial Intelligence")

        # Should send observation + completion (2 calls)
        assert transport.send.call_count == 2

        # First call: output observation
        obs_call = transport.send.call_args_list[0][0]
        assert obs_call[0] == "/api/v1/observations"
        assert obs_call[1]["type"] == "output"
        assert obs_call[1]["data"] == "AI stands for Artificial Intelligence"

        # Second call: trace completion
        completion_call = transport.send.call_args_list[1][0]
        assert completion_call[0] == "/api/v1/traces"
        assert completion_call[1]["status"] == "completed"
        assert "duration_ms" in completion_call[1]

    def test_output_dict(self):
        """Test recording dict output."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        output = {"answer": "test", "confidence": 0.95}
        trace.output(output)

        obs_call = transport.send.call_args_list[0][0]
        assert obs_call[1]["data"] == output

    def test_output_returns_self(self):
        """Test output() returns self for chaining."""
        transport = Mock()
        trace = Trace("test-op", transport)
        result = trace.output("test")
        assert result is trace


class TestTraceState:
    """Test trace state observation."""

    def test_state_sends_observation_immediately(self):
        """Test state() sends observation immediately with key."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        trace.state("config", {"model": "gpt-4", "temperature": 0.7})

        # Should send observation
        assert transport.send.call_count == 1
        call_args = transport.send.call_args[0]
        endpoint = call_args[0]
        payload = call_args[1]

        assert endpoint == "/api/v1/observations"
        assert payload["trace_id"] == trace.id
        assert payload["type"] == "state"
        assert payload["data"] == {"model": "gpt-4", "temperature": 0.7}
        assert payload["key"] == "config"
        assert "timestamp" in payload

    def test_state_multiple_entries_send_separate_observations(self):
        """Test multiple state() calls send separate observations."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        trace.state("config", {"model": "gpt-4"})
        trace.state("documents", [{"id": "doc1"}])
        trace.state("chunks", [{"id": "chunk1"}])

        # Should send 3 separate observations
        assert transport.send.call_count == 3

        # Check each has correct key
        calls = transport.send.call_args_list
        assert calls[0][0][1]["key"] == "config"
        assert calls[1][0][1]["key"] == "documents"
        assert calls[2][0][1]["key"] == "chunks"

    def test_state_returns_self(self):
        """Test state() returns self for chaining."""
        transport = Mock()
        trace = Trace("test-op", transport)
        result = trace.state("test", "value")
        assert result is trace


class TestTraceCompletion:
    """Test trace completion."""

    def test_completion_includes_duration(self):
        """Test completion payload includes duration."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        # Simulate some work
        time.sleep(0.01)  # 10ms

        trace.output("result")

        # Check completion call (second call)
        completion_call = transport.send.call_args_list[1][0]
        payload = completion_call[1]

        # Duration should be >= 10ms (allowing for timing variance)
        assert payload["duration_ms"] >= 8

    def test_completion_includes_metadata(self):
        """Test completion includes metadata if provided."""
        transport = Mock()
        trace = Trace("test-op", transport, metadata={"user_id": "123"})
        transport.send.reset_mock()

        trace.output("result")

        completion_call = transport.send.call_args_list[1][0]
        payload = completion_call[1]
        assert payload["metadata"] == {"user_id": "123"}


class TestTraceContextManager:
    """Test trace context manager support."""

    def test_context_manager_basic(self):
        """Test trace can be used as context manager."""
        transport = Mock()

        with Trace("test-op", transport) as trace:
            transport.send.reset_mock()
            trace.input(data="test")

        # Should send input observation
        assert transport.send.call_count >= 1

    def test_context_manager_with_exception(self):
        """Test context manager handles exceptions gracefully."""
        transport = Mock()

        with pytest.raises(ValueError):
            with Trace("test-op", transport) as trace:
                trace.input(data="test")
                raise ValueError("Test error")

        # Should have sent trace creation and input observation
        # Note: We no longer track errors in the trace
        assert transport.send.call_count >= 2


class TestTraceChaining:
    """Test method chaining."""

    def test_method_chaining(self):
        """Test methods can be chained."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        # Chain all methods
        result = (
            trace.input(question="What is AI?")
            .state("config", {"model": "gpt-4"})
            .output("AI stands for Artificial Intelligence")
        )

        assert result is trace

        # Should send: input obs, state obs, output obs, completion
        assert transport.send.call_count == 4


class TestTraceTimestamps:
    """Test timestamp handling."""

    def test_timestamps_are_iso_format(self):
        """Test timestamps are in ISO 8601 format with Z suffix."""
        transport = Mock()
        trace = Trace("test-op", transport)

        call_args = transport.send.call_args[0]
        payload = call_args[1]
        timestamp = payload["timestamp"]

        # Should be ISO format with Z suffix
        assert timestamp.endswith("Z")
        assert "T" in timestamp

    def test_observation_timestamps_are_current(self):
        """Test observation timestamps are current."""
        transport = Mock()
        trace = Trace("test-op", transport)
        transport.send.reset_mock()

        trace.input(data="test")

        call_args = transport.send.call_args[0]
        payload = call_args[1]
        timestamp = payload["timestamp"]

        assert timestamp.endswith("Z")
        assert "T" in timestamp
