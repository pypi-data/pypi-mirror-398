"""Tests for Span class."""

import json
from unittest.mock import patch

import pytest

from lumenova_beacon.tracing.span import Span
from lumenova_beacon.types import SpanKind, SpanType, StatusCode


class TestSpanInitialization:
    """Test Span initialization."""

    def test_init_with_minimal_params(self):
        """Test span initialization with minimal parameters."""
        span = Span(name="test_operation")

        assert span.name == "test_operation"
        assert span.kind == SpanKind.INTERNAL
        assert span.span_type == SpanType.SPAN
        assert span.status_code == StatusCode.UNSET
        assert span.status_description is None
        assert span.start_time is None
        assert span.end_time is None
        assert span.parent_id is None
        assert span.trace_id is not None  # Auto-generated
        assert span.span_id is not None  # Auto-generated
        assert span.trace_state == []
        assert span.session_id is None

    def test_init_with_all_params(self):
        """Test span initialization with all parameters."""
        span = Span(
            name="test_operation",
            trace_id="trace-123",
            span_id="span-456",
            parent_id="parent-789",
            kind=SpanKind.CLIENT,
            span_type=SpanType.GENERATION,
            attributes={"key": "value"},
            session_id="test-session",
        )

        assert span.name == "test_operation"
        assert span.trace_id == "trace-123"
        assert span.span_id == "span-456"
        assert span.parent_id == "parent-789"
        assert span.kind == SpanKind.CLIENT
        assert span.span_type == SpanType.GENERATION
        assert span.attributes["key"] == "value"
        assert span.session_id == "test-session"

    def test_init_adds_span_type_to_attributes(self):
        """Test that span.type is added to attributes."""
        span = Span(name="test", span_type=SpanType.GENERATION)

        assert "span.type" in span.attributes
        assert span.attributes["span.type"] == SpanType.GENERATION.value

    def test_init_adds_session_id_to_attributes(self):
        """Test that session_id is added to attributes when provided."""
        span = Span(name="test", session_id="test-session")

        assert "session_id" in span.attributes
        assert span.attributes["session_id"] == "test-session"

    def test_init_without_session_id(self):
        """Test that session_id is not in attributes when not provided."""
        span = Span(name="test")

        # session_id property should return None
        assert span.session_id is None

    def test_init_generates_unique_ids(self):
        """Test that each span gets unique IDs."""
        span1 = Span(name="span1")
        span2 = Span(name="span2")

        assert span1.span_id != span2.span_id
        assert span1.trace_id != span2.trace_id


class TestSpanLifecycle:
    """Test Span lifecycle methods."""

    def test_start_sets_start_time(self):
        """Test that start() sets the start time."""
        span = Span(name="test")

        assert span.start_time is None

        span.start()

        assert span.start_time is not None
        assert isinstance(span.start_time, str)

    def test_start_returns_self(self):
        """Test that start() returns self for chaining."""
        span = Span(name="test")

        result = span.start()

        assert result is span

    def test_end_sets_end_time(self):
        """Test that end() sets the end time."""
        span = Span(name="test")
        span.start()

        assert span.end_time is None

        span.end()

        assert span.end_time is not None
        assert isinstance(span.end_time, str)

    def test_end_with_status_code(self):
        """Test that end() can set status code."""
        span = Span(name="test")
        span.start()

        span.end(status_code=StatusCode.OK)

        assert span.status_code == StatusCode.OK

    def test_end_returns_self(self):
        """Test that end() returns self for chaining."""
        span = Span(name="test")

        result = span.end()

        assert result is span

    def test_set_status(self):
        """Test setting span status."""
        span = Span(name="test")

        span.set_status(StatusCode.ERROR, "Something went wrong")

        assert span.status_code == StatusCode.ERROR
        assert span.status_description == "Something went wrong"

    def test_set_status_without_description(self):
        """Test setting status without description."""
        span = Span(name="test")

        span.set_status(StatusCode.OK)

        assert span.status_code == StatusCode.OK
        assert span.status_description is None

    def test_set_status_returns_self(self):
        """Test that set_status() returns self for chaining."""
        span = Span(name="test")

        result = span.set_status(StatusCode.OK)

        assert result is span


class TestSpanAttributes:
    """Test Span attribute management."""

    def test_set_attribute_string(self):
        """Test setting a string attribute."""
        span = Span(name="test")

        span.set_attribute("key", "value")

        assert span.attributes["key"] == "value"

    def test_set_attribute_non_string(self):
        """Test setting a primitive attribute (preserved as-is)."""
        span = Span(name="test")

        span.set_attribute("count", 42)
        span.set_attribute("ratio", 3.14)
        span.set_attribute("enabled", True)

        # Primitives (int, float, bool) are preserved
        assert span.attributes["count"] == 42
        assert span.attributes["ratio"] == 3.14
        assert span.attributes["enabled"] is True

    def test_set_attribute_dict(self):
        """Test setting a dictionary attribute."""
        span = Span(name="test")

        span.set_attribute("data", {"key": "value"})

        # Should be JSON-serialized
        assert isinstance(span.attributes["data"], str)
        assert json.loads(span.attributes["data"]) == {"key": "value"}

    def test_set_attribute_list(self):
        """Test setting a list attribute."""
        span = Span(name="test")

        span.set_attribute("tags", ["tag1", "tag2"])

        # Should be JSON-serialized
        assert isinstance(span.attributes["tags"], str)
        assert json.loads(span.attributes["tags"]) == ["tag1", "tag2"]

    def test_set_attribute_returns_self(self):
        """Test that set_attribute() returns self for chaining."""
        span = Span(name="test")

        result = span.set_attribute("key", "value")

        assert result is span

    def test_set_attributes_multiple(self):
        """Test setting multiple attributes at once."""
        span = Span(name="test")

        span.set_attributes({"key1": "value1", "key2": "value2"})

        assert span.attributes["key1"] == "value1"
        assert span.attributes["key2"] == "value2"

    def test_set_attributes_returns_self(self):
        """Test that set_attributes() returns self for chaining."""
        span = Span(name="test")

        result = span.set_attributes({"key": "value"})

        assert result is span

    def test_set_input(self):
        """Test setting span input."""
        span = Span(name="test")

        span.set_input({"query": "test question"})

        assert "span.input" in span.attributes
        assert json.loads(span.attributes["span.input"]) == {"query": "test question"}

    def test_set_input_returns_self(self):
        """Test that set_input() returns self for chaining."""
        span = Span(name="test")

        result = span.set_input("test")

        assert result is span

    def test_set_output(self):
        """Test setting span output."""
        span = Span(name="test")

        span.set_output({"answer": "test answer"})

        assert "span.output" in span.attributes
        assert json.loads(span.attributes["span.output"]) == {"answer": "test answer"}

    def test_set_output_returns_self(self):
        """Test that set_output() returns self for chaining."""
        span = Span(name="test")

        result = span.set_output("test")

        assert result is span

    def test_set_metadata(self):
        """Test setting metadata with prefix."""
        span = Span(name="test")

        span.set_metadata("user_id", "user-123")

        assert "span.metadata.user_id" in span.attributes
        assert span.attributes["span.metadata.user_id"] == "user-123"

    def test_set_metadata_returns_self(self):
        """Test that set_metadata() returns self for chaining."""
        span = Span(name="test")

        result = span.set_metadata("key", "value")

        assert result is span


class TestSpanExceptionHandling:
    """Test Span exception recording."""

    def test_record_exception(self):
        """Test recording an exception."""
        span = Span(name="test")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            span.record_exception(e)

        assert span.status_code == StatusCode.ERROR
        assert span.status_description == "Test error"
        assert span.attributes["exception.type"] == "ValueError"
        assert span.attributes["exception.message"] == "Test error"

    def test_record_exception_returns_self(self):
        """Test that record_exception() returns self for chaining."""
        span = Span(name="test")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = span.record_exception(e)

        assert result is span

    def test_record_different_exception_types(self):
        """Test recording different exception types."""
        span = Span(name="test")

        try:
            raise RuntimeError("Runtime error")
        except RuntimeError as e:
            span.record_exception(e)

        assert span.attributes["exception.type"] == "RuntimeError"
        assert span.attributes["exception.message"] == "Runtime error"


class TestSpanContextManager:
    """Test Span as context manager."""

    def test_context_manager_starts_span(self):
        """Test that context manager starts the span."""
        span = Span(name="test")

        with span:
            assert span.start_time is not None

    def test_context_manager_ends_span(self):
        """Test that context manager ends the span."""
        span = Span(name="test")

        with span:
            pass

        assert span.end_time is not None

    def test_context_manager_returns_span(self):
        """Test that context manager returns the span."""
        span = Span(name="test")

        with span as s:
            assert s is span

    def test_context_manager_records_exception(self):
        """Test that context manager records exceptions."""
        span = Span(name="test")

        try:
            with span:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert span.status_code == StatusCode.ERROR
        assert span.status_description == "Test error"
        assert span.attributes["exception.type"] == "ValueError"

    def test_context_manager_propagates_exception(self):
        """Test that context manager propagates exceptions."""
        span = Span(name="test")

        with pytest.raises(ValueError):
            with span:
                raise ValueError("Test error")


class TestSpanSerialization:
    """Test Span serialization to dictionary."""

    def test_to_dict_basic(self):
        """Test basic span serialization."""
        span = Span(
            name="test_operation",
            trace_id="trace-123",
            span_id="span-456",
            kind=SpanKind.INTERNAL,
        )
        span.start()
        span.end()

        data = span.to_dict()

        assert data["name"] == "test_operation"
        assert data["context"]["trace_id"] == "trace-123"
        assert data["context"]["span_id"] == "span-456"
        assert data["kind"] == SpanKind.INTERNAL.value
        assert data["start_time"] is not None
        assert data["end_time"] is not None
        assert data["status"]["status_code"] == StatusCode.UNSET.value

    def test_to_dict_with_parent(self):
        """Test serialization with parent ID."""
        span = Span(
            name="test",
            trace_id="trace-123",
            span_id="span-456",
            parent_id="parent-789",
        )

        data = span.to_dict()

        assert data["parent_id"] == "parent-789"

    def test_to_dict_without_parent(self):
        """Test serialization without parent ID."""
        span = Span(name="test")

        data = span.to_dict()

        assert "parent_id" not in data

    def test_to_dict_with_status_description(self):
        """Test serialization with status description."""
        span = Span(name="test")
        span.set_status(StatusCode.ERROR, "Something went wrong")

        data = span.to_dict()

        assert data["status"]["status_code"] == StatusCode.ERROR.value
        assert data["status"]["description"] == "Something went wrong"

    def test_to_dict_without_status_description(self):
        """Test serialization without status description."""
        span = Span(name="test")

        data = span.to_dict()

        assert "description" not in data["status"]

    def test_to_dict_includes_attributes(self):
        """Test that serialization includes attributes."""
        span = Span(name="test")
        span.set_attribute("key", "value")

        data = span.to_dict()

        assert data["attributes"]["key"] == "value"

    def test_to_dict_includes_trace_state(self):
        """Test that serialization includes trace state."""
        span = Span(name="test")

        data = span.to_dict()

        assert "trace_state" in data["context"]
        assert data["context"]["trace_state"] == []


class TestSpanMethodChaining:
    """Test Span method chaining."""

    def test_chaining_methods(self):
        """Test that methods can be chained together."""
        span = (
            Span(name="test")
            .start()
            .set_attribute("key", "value")
            .set_input({"query": "test"})
            .set_output({"result": "success"})
            .set_metadata("user", "test-user")
            .set_status(StatusCode.OK)
            .end()
        )

        assert span.start_time is not None
        assert span.end_time is not None
        assert span.attributes["key"] == "value"
        assert "span.input" in span.attributes
        assert "span.output" in span.attributes
        assert "span.metadata.user" in span.attributes
        assert span.status_code == StatusCode.OK


class TestSpanEdgeCases:
    """Test Span edge cases."""

    def test_session_id_property_with_value(self):
        """Test session_id property when session_id is set."""
        span = Span(name="test", session_id="test-session")

        assert span.session_id == "test-session"

    def test_session_id_property_without_value(self):
        """Test session_id property when session_id is not set."""
        span = Span(name="test")

        assert span.session_id is None

    def test_multiple_start_calls(self):
        """Test that calling start() multiple times updates start_time."""
        span = Span(name="test")

        span.start()
        first_start = span.start_time

        # Wait a tiny bit and start again
        import time
        time.sleep(0.001)

        span.start()
        second_start = span.start_time

        # Second start should be different (later)
        assert second_start != first_start

    def test_end_before_start(self):
        """Test that span can be ended before starting."""
        span = Span(name="test")

        span.end()

        assert span.end_time is not None
        assert span.start_time is None

    def test_set_attribute_with_none_value(self):
        """Test setting attribute with None value."""
        span = Span(name="test")

        span.set_attribute("key", None)

        # None should be JSON-serialized
        assert span.attributes["key"] == "null"
