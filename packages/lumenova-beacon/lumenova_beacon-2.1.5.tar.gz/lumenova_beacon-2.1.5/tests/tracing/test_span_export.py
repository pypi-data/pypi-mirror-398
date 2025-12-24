"""Tests for span OTLP export functionality."""

import pytest
from unittest.mock import MagicMock, patch

from lumenova_beacon.tracing.span import Span, _BeaconReadableSpan, _iso8601_to_nanoseconds, _convert_attributes_for_otlp
from lumenova_beacon.types import SpanKind, SpanType, StatusCode


class TestIso8601ToNanoseconds:
    """Test _iso8601_to_nanoseconds helper function."""

    def test_none_returns_zero(self):
        """Test that None input returns 0."""
        assert _iso8601_to_nanoseconds(None) == 0

    def test_empty_string_returns_zero(self):
        """Test that empty string returns 0."""
        assert _iso8601_to_nanoseconds("") == 0

    def test_z_suffix_timestamp(self):
        """Test timestamp with Z suffix."""
        result = _iso8601_to_nanoseconds("2024-01-15T10:30:00Z")
        # Should be non-zero
        assert result > 0

    def test_timezone_offset_timestamp(self):
        """Test timestamp with timezone offset."""
        result = _iso8601_to_nanoseconds("2024-01-15T10:30:00+00:00")
        assert result > 0

    def test_microseconds_preserved(self):
        """Test that microseconds are preserved."""
        result1 = _iso8601_to_nanoseconds("2024-01-15T10:30:00.000000Z")
        result2 = _iso8601_to_nanoseconds("2024-01-15T10:30:00.500000Z")
        # 0.5 seconds = 500 million nanoseconds
        assert abs(result2 - result1 - 500_000_000) < 1000


class TestConvertAttributesForOtlp:
    """Test _convert_attributes_for_otlp helper function."""

    def test_string_preserved(self):
        """Test that strings are preserved."""
        result = _convert_attributes_for_otlp({"key": "value"})
        assert result == {"key": "value"}

    def test_int_preserved(self):
        """Test that integers are preserved."""
        result = _convert_attributes_for_otlp({"key": 42})
        assert result == {"key": 42}

    def test_float_preserved(self):
        """Test that floats are preserved."""
        result = _convert_attributes_for_otlp({"key": 3.14})
        assert result == {"key": 3.14}

    def test_bool_preserved(self):
        """Test that booleans are preserved."""
        result = _convert_attributes_for_otlp({"key": True})
        assert result == {"key": True}

    def test_dict_converted_to_json(self):
        """Test that dicts are converted to JSON strings."""
        result = _convert_attributes_for_otlp({"key": {"nested": "value"}})
        assert result == {"key": '{"nested": "value"}'}

    def test_list_items_converted(self):
        """Test that list items are properly converted."""
        result = _convert_attributes_for_otlp({"key": [1, "two", {"three": 3}]})
        assert result["key"][0] == 1
        assert result["key"][1] == "two"
        assert '{"three": 3}' in result["key"][2]

    def test_none_skipped(self):
        """Test that None values are skipped."""
        result = _convert_attributes_for_otlp({"key": None, "other": "value"})
        assert "key" not in result
        assert result["other"] == "value"


class TestSpanToOtelSpan:
    """Test Span.to_otel_span() method."""

    def test_basic_conversion(self):
        """Test basic span conversion to OTel format."""
        span = Span(
            name="test_span",
            trace_id="0" * 32,
            span_id="0" * 16,
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"
        span.status_code = StatusCode.OK

        otel_span = span.to_otel_span()

        assert otel_span.name == "test_span"
        assert otel_span.start_time > 0
        assert otel_span.end_time > otel_span.start_time

    def test_parent_conversion(self):
        """Test that parent span context is properly set."""
        span = Span(
            name="child_span",
            trace_id="a" * 32,
            span_id="b" * 16,
            parent_id="c" * 16,
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"

        otel_span = span.to_otel_span()

        assert otel_span.parent is not None

    def test_no_parent_when_none(self):
        """Test that parent is None when no parent_id."""
        span = Span(
            name="root_span",
            trace_id="a" * 32,
            span_id="b" * 16,
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"

        otel_span = span.to_otel_span()

        assert otel_span.parent is None

    def test_kind_mapping(self):
        """Test that span kind is properly mapped."""
        from opentelemetry.trace import SpanKind as OTelSpanKind

        span = Span(
            name="client_span",
            kind=SpanKind.CLIENT,
            span_type=SpanType.GENERATION,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"

        otel_span = span.to_otel_span()

        assert otel_span.kind == OTelSpanKind.CLIENT

    def test_status_mapping(self):
        """Test that status is properly mapped."""
        from opentelemetry.trace.status import StatusCode as OTelStatusCode

        span = Span(
            name="error_span",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"
        span.status_code = StatusCode.ERROR
        span.status_description = "Test error"

        otel_span = span.to_otel_span()

        assert otel_span.status.status_code == OTelStatusCode.ERROR
        assert otel_span.status.description == "Test error"

    def test_attributes_converted(self):
        """Test that attributes are properly converted."""
        span = Span(
            name="test_span",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"
        span.set_attribute("string_attr", "value")
        span.set_attribute("int_attr", 42)

        otel_span = span.to_otel_span()

        assert "span.type" in otel_span.attributes

    def test_custom_resource(self):
        """Test that custom resource is used when provided."""
        from opentelemetry.sdk.resources import Resource

        custom_resource = Resource.create({"service.name": "custom-service"})

        span = Span(
            name="test_span",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"

        otel_span = span.to_otel_span(resource=custom_resource)

        assert otel_span.resource == custom_resource


class TestBeaconReadableSpan:
    """Test _BeaconReadableSpan class."""

    def test_all_properties_accessible(self):
        """Test that all required properties are accessible."""
        from opentelemetry.trace import SpanContext, TraceFlags
        from opentelemetry.trace import SpanKind as OTelSpanKind
        from opentelemetry.trace.status import Status, StatusCode as OTelStatusCode
        from opentelemetry.sdk.resources import Resource

        context = SpanContext(
            trace_id=1,
            span_id=1,
            is_remote=False,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
        )
        status = Status(OTelStatusCode.OK)
        resource = Resource.create({})

        readable_span = _BeaconReadableSpan(
            name="test",
            context=context,
            parent=None,
            kind=OTelSpanKind.INTERNAL,
            start_time=1000000000,
            end_time=2000000000,
            status=status,
            attributes={"key": "value"},
            resource=resource,
        )

        # Test all properties are accessible
        assert readable_span.name == "test"
        assert readable_span.context == context
        assert readable_span.get_span_context() == context
        assert readable_span.parent is None
        assert readable_span.kind == OTelSpanKind.INTERNAL
        assert readable_span.start_time == 1000000000
        assert readable_span.end_time == 2000000000
        assert readable_span.status == status
        assert readable_span.attributes == {"key": "value"}
        assert readable_span.resource == resource
        assert readable_span.events == ()
        assert readable_span.links == ()
        assert readable_span.instrumentation_scope is None


class TestClientExportSpan:
    """Test BeaconClient.export_span() method."""

    def test_export_span_with_provider(self):
        """Test export_span when TracerProvider is configured."""
        from lumenova_beacon import BeaconClient
        from opentelemetry.sdk.trace import TracerProvider

        # Create client with auto_instrument disabled (we'll mock the provider)
        with patch.dict("os.environ", {"BEACON_ENDPOINT": "https://test.com"}):
            client = BeaconClient(auto_instrument_opentelemetry=False)

        # Create a span
        span = Span(
            name="test_span",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"

        # Mock the tracer provider
        mock_processor = MagicMock()
        mock_provider = MagicMock(spec=TracerProvider)
        mock_provider._active_span_processor = mock_processor

        with patch("opentelemetry.trace.get_tracer_provider", return_value=mock_provider):
            result = client.export_span(span)

        # The mock should have been called
        assert mock_processor.on_end.called

    def test_export_span_without_provider(self):
        """Test export_span when no TracerProvider is configured."""
        from lumenova_beacon import BeaconClient

        with patch.dict("os.environ", {"BEACON_ENDPOINT": "https://test.com"}):
            client = BeaconClient(auto_instrument_opentelemetry=False)

        span = Span(
            name="test_span",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span.start_time = "2024-01-15T10:30:00Z"
        span.end_time = "2024-01-15T10:30:01Z"

        # Mock to return a non-SDK provider (no spec=TracerProvider)
        with patch("opentelemetry.trace.get_tracer_provider", return_value=MagicMock()):
            result = client.export_span(span)

        # Should return False when no proper provider
        assert result is False


class TestClientExportSpans:
    """Test BeaconClient.export_spans() method."""

    def test_export_spans_counts_successes(self):
        """Test that export_spans returns count of successful exports."""
        from lumenova_beacon import BeaconClient

        with patch.dict("os.environ", {"BEACON_ENDPOINT": "https://test.com"}):
            client = BeaconClient(auto_instrument_opentelemetry=False)

        # Create multiple spans
        spans = []
        for i in range(3):
            span = Span(
                name=f"test_span_{i}",
                kind=SpanKind.INTERNAL,
                span_type=SpanType.SPAN,
            )
            span.start_time = "2024-01-15T10:30:00Z"
            span.end_time = "2024-01-15T10:30:01Z"
            spans.append(span)

        # Mock export_span to return True
        with patch.object(client, "export_span", return_value=True):
            result = client.export_spans(spans)

        assert result == 3

    def test_export_spans_handles_failures(self):
        """Test that export_spans handles partial failures."""
        from lumenova_beacon import BeaconClient

        with patch.dict("os.environ", {"BEACON_ENDPOINT": "https://test.com"}):
            client = BeaconClient(auto_instrument_opentelemetry=False)

        spans = []
        for i in range(3):
            span = Span(
                name=f"test_span_{i}",
                kind=SpanKind.INTERNAL,
                span_type=SpanType.SPAN,
            )
            span.start_time = "2024-01-15T10:30:00Z"
            span.end_time = "2024-01-15T10:30:01Z"
            spans.append(span)

        # Mock export_span to alternate success/failure
        with patch.object(client, "export_span", side_effect=[True, False, True]):
            result = client.export_spans(spans)

        assert result == 2


class TestClientFlush:
    """Test BeaconClient.flush() method."""

    def test_flush_with_provider(self):
        """Test flush when TracerProvider is configured."""
        from lumenova_beacon import BeaconClient
        from opentelemetry.sdk.trace import TracerProvider

        with patch.dict("os.environ", {"BEACON_ENDPOINT": "https://test.com"}):
            client = BeaconClient(auto_instrument_opentelemetry=False)

        mock_provider = MagicMock(spec=TracerProvider)
        mock_provider.force_flush.return_value = True

        with patch("opentelemetry.trace.get_tracer_provider", return_value=mock_provider):
            result = client.flush()

        # Should call force_flush
        mock_provider.force_flush.assert_called_once_with(30000)

    def test_flush_without_provider(self):
        """Test flush when no TracerProvider is configured."""
        from lumenova_beacon import BeaconClient

        with patch.dict("os.environ", {"BEACON_ENDPOINT": "https://test.com"}):
            client = BeaconClient(auto_instrument_opentelemetry=False)

        # Mock to return a non-SDK provider (no spec=TracerProvider)
        with patch("opentelemetry.trace.get_tracer_provider", return_value=MagicMock()):
            result = client.flush()

        # Should return True (nothing to flush)
        assert result is True
