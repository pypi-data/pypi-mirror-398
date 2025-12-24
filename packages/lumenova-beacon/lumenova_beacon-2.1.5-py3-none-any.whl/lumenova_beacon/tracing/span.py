"""Span class for creating and managing spans."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from lumenova_beacon.types import Attributes, SpanType, SpanKind, StatusCode
from lumenova_beacon.utils import (
    generate_span_id,
    generate_trace_id,
    get_current_timestamp,
)

if TYPE_CHECKING:
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import ReadableSpan


class Span:
    """Represents a single span in a trace.

    A span tracks a unit of work with timing, status, and custom attributes.
    Spans can be nested to form a trace hierarchy.
    """

    def __init__(
        self,
        name: str,
        *,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_id: str | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        span_type: SpanType = SpanType.SPAN,
        attributes: Attributes | None = None,
        session_id: str | None = None,
    ):
        """Initialize a new span.

        Args:
            name: Name of the span
            trace_id: Trace ID (generated if not provided)
            span_id: Span ID (generated if not provided)
            parent_id: Parent span ID (None for root spans)
            kind: Type of span (default: INTERNAL)
            span_type: Type of span (default: SPAN)
            attributes: Custom attributes for the span
            session_id: Session ID (optional, stored in attributes)
        """
        self.name = name
        self.trace_id = trace_id or generate_trace_id()
        self.span_id = span_id or generate_span_id()
        self.parent_id = parent_id
        self.kind = kind
        self.span_type = span_type
        self.trace_state: list[str] = []

        self.start_time: str | None = None
        self.end_time: str | None = None
        self.status_code = StatusCode.UNSET
        self.status_description: str | None = None

        # Initialize attributes with span.type
        self.attributes: Attributes = attributes or {}
        self.attributes["span.type"] = span_type.value

        # Add session_id to attributes if provided
        if session_id is not None:
            self.attributes["session_id"] = session_id

    @property
    def session_id(self) -> str | None:
        """Get the session_id from attributes if it exists."""
        return self.attributes.get("session_id")

    def start(self) -> "Span":
        """Start the span by recording the start time.

        Returns:
            Self for method chaining
        """
        self.start_time = get_current_timestamp()
        return self

    def end(self, *, status_code: StatusCode | None = None) -> "Span":
        """End the span by recording the end time.

        Args:
            status_code: Optional status code to set (default: keeps current status)

        Returns:
            Self for method chaining
        """
        self.end_time = get_current_timestamp()
        if status_code is not None:
            self.status_code = status_code
        return self

    def set_status(self, status_code: StatusCode, description: str | None = None) -> "Span":
        """Set the span's status code and optional description.

        Args:
            status_code: Status code to set
            description: Optional description (typically for ERROR status)

        Returns:
            Self for method chaining
        """
        self.status_code = status_code
        self.status_description = description
        return self

    def set_attribute(self, key: str, value: Any) -> "Span":
        """Set a custom attribute on the span.

        Args:
            key: Attribute key
            value: Attribute value (primitives preserved, complex types JSON-serialized)

        Returns:
            Self for method chaining
        """
        if isinstance(value, (str, bool, int, float)):
            self.attributes[key] = value
        else:
            self.attributes[key] = json.dumps(value, default=str)
        return self

    def set_attributes(self, attributes: Attributes) -> "Span":
        """Set multiple attributes at once.

        Args:
            attributes: Dictionary of attributes to set

        Returns:
            Self for method chaining
        """
        for key, value in attributes.items():
            self.set_attribute(key, value)
        return self

    def set_input(self, input_data: Any) -> "Span":
        """Set the span.input attribute.

        Args:
            input_data: Input data (will be JSON-serialized)

        Returns:
            Self for method chaining
        """
        return self.set_attribute("span.input", input_data)

    def set_output(self, output_data: Any) -> "Span":
        """Set the span.output attribute.

        Args:
            output_data: Output data (will be JSON-serialized)

        Returns:
            Self for method chaining
        """
        return self.set_attribute("span.output", output_data)

    def set_metadata(self, key: str, value: Any) -> "Span":
        """Set a metadata attribute with the span.metadata prefix.

        Args:
            key: Metadata key (without the prefix)
            value: Metadata value

        Returns:
            Self for method chaining
        """
        return self.set_attribute(f"span.metadata.{key}", value)

    def record_exception(self, exc: BaseException) -> "Span":
        """Record an exception in the span and set status to ERROR.

        Args:
            exc: The exception to record

        Returns:
            Self for method chaining
        """
        # Record exception details
        exc_type = type(exc).__name__
        exc_message = str(exc)

        self.status_code = StatusCode.ERROR
        self.status_description = exc_message

        self.set_attribute("exception.type", exc_type)
        self.set_attribute("exception.message", exc_message)

        return self

    def __enter__(self) -> "Span":
        """Context manager entry: start the span."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit: end the span and record any exception."""
        if exc_val is not None:
            self.record_exception(exc_val)
        self.end()

    def to_dict(self) -> dict[str, Any]:
        """Convert the span to a dictionary representation.

        Returns:
            Dictionary with all span data in OpenTelemetry format
        """
        # Build status dictionary
        status_dict = {"status_code": self.status_code.value}
        if self.status_description:
            status_dict["description"] = self.status_description

        result = {
            "name": self.name,
            "context": {
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "trace_state": self.trace_state,
            },
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": status_dict,
            "attributes": self.attributes,
        }

        # Only include parent_id if it's not None
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id

        return result

    def to_otel_span(self, resource: "Resource | None" = None) -> "ReadableSpan":
        """Convert this span to an OpenTelemetry ReadableSpan for OTLP export.

        This method converts the Beacon SDK span to an OpenTelemetry-compatible
        format that can be exported via OTLPSpanExporter.

        Args:
            resource: Optional OpenTelemetry Resource. If not provided, a default
                resource with service.name="beacon-sdk" will be used.

        Returns:
            A ReadableSpan compatible with OTLPSpanExporter.

        Raises:
            ImportError: If OpenTelemetry SDK is not installed.
        """
        from opentelemetry.trace import SpanContext, TraceFlags
        from opentelemetry.trace import SpanKind as OTelSpanKind
        from opentelemetry.trace.status import Status, StatusCode as OTelStatusCode
        from opentelemetry.sdk.resources import Resource as OTelResource

        # Convert trace_id: hex string (32 chars) → 128-bit int
        trace_id_int = int(self.trace_id, 16)

        # Convert span_id: hex string (16 chars) → 64-bit int
        span_id_int = int(self.span_id, 16)

        # Convert parent_id if present
        parent_span_id_int = int(self.parent_id, 16) if self.parent_id else 0

        # Create SpanContext
        span_context = SpanContext(
            trace_id=trace_id_int,
            span_id=span_id_int,
            is_remote=False,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
        )

        # Create parent SpanContext if parent exists
        parent = None
        if self.parent_id:
            parent = SpanContext(
                trace_id=trace_id_int,
                span_id=parent_span_id_int,
                is_remote=False,
                trace_flags=TraceFlags(TraceFlags.SAMPLED),
            )

        # Convert SpanKind
        kind_mapping = {
            SpanKind.INTERNAL: OTelSpanKind.INTERNAL,
            SpanKind.SERVER: OTelSpanKind.SERVER,
            SpanKind.CLIENT: OTelSpanKind.CLIENT,
            SpanKind.PRODUCER: OTelSpanKind.PRODUCER,
            SpanKind.CONSUMER: OTelSpanKind.CONSUMER,
        }
        otel_kind = kind_mapping.get(self.kind, OTelSpanKind.INTERNAL)

        # Convert timestamps: ISO 8601 → nanoseconds
        start_time_ns = _iso8601_to_nanoseconds(self.start_time)
        end_time_ns = _iso8601_to_nanoseconds(self.end_time)

        # Convert status
        status_mapping = {
            StatusCode.UNSET: OTelStatusCode.UNSET,
            StatusCode.OK: OTelStatusCode.OK,
            StatusCode.ERROR: OTelStatusCode.ERROR,
        }
        otel_status_code = status_mapping.get(self.status_code, OTelStatusCode.UNSET)
        status = Status(otel_status_code, self.status_description)

        # Convert attributes - ensure all values are OTLP-compatible
        otel_attributes = _convert_attributes_for_otlp(self.attributes)

        # Use default resource if none provided
        if resource is None:
            resource = OTelResource.create({"service.name": "beacon-sdk"})

        return _BeaconReadableSpan(
            name=self.name,
            context=span_context,
            parent=parent,
            kind=otel_kind,
            start_time=start_time_ns,
            end_time=end_time_ns,
            status=status,
            attributes=otel_attributes,
            resource=resource,
        )


def _iso8601_to_nanoseconds(iso_string: str | None) -> int:
    """Convert ISO 8601 timestamp to nanoseconds since epoch.

    Args:
        iso_string: ISO 8601 formatted string (e.g., "2024-10-15T14:30:45.123456Z")

    Returns:
        Nanoseconds since Unix epoch, or 0 if iso_string is None/empty.
    """
    if not iso_string:
        return 0

    # Handle 'Z' suffix
    if iso_string.endswith("Z"):
        iso_string = iso_string[:-1] + "+00:00"

    dt = datetime.fromisoformat(iso_string)
    # Ensure timezone aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to nanoseconds
    timestamp_s = dt.timestamp()
    return int(timestamp_s * 1_000_000_000)


def _convert_attributes_for_otlp(attributes: dict[str, Any]) -> dict[str, Any]:
    """Convert Beacon attributes to OTLP-compatible format.

    OTLP only supports: str, bool, int, float, and sequences of these types.

    Args:
        attributes: Beacon span attributes dictionary.

    Returns:
        Dictionary with OTLP-compatible attribute values.
    """
    result = {}
    for key, value in attributes.items():
        if isinstance(value, (str, bool, int, float)):
            result[key] = value
        elif isinstance(value, (list, tuple)):
            # Convert list items
            result[key] = [
                v if isinstance(v, (str, bool, int, float)) else json.dumps(v)
                for v in value
            ]
        elif isinstance(value, dict):
            # Convert dict to JSON string
            result[key] = json.dumps(value)
        elif value is None:
            # Skip None values
            continue
        else:
            # Convert other types to string
            result[key] = str(value)
    return result


class _BeaconReadableSpan:
    """A ReadableSpan implementation for OTLP export.

    This class implements the minimum interface required by OTLPSpanExporter
    to export Beacon SDK spans via OpenTelemetry.
    """

    def __init__(
        self,
        name: str,
        context: "SpanContext",
        parent: "SpanContext | None",
        kind: "OTelSpanKind",
        start_time: int,
        end_time: int,
        status: "Status",
        attributes: dict[str, Any],
        resource: "Resource",
    ):
        """Initialize the ReadableSpan.

        Args:
            name: Span name
            context: SpanContext with trace_id and span_id
            parent: Parent SpanContext or None
            kind: OpenTelemetry SpanKind
            start_time: Start time in nanoseconds since epoch
            end_time: End time in nanoseconds since epoch
            status: Span status
            attributes: Span attributes
            resource: OpenTelemetry Resource
        """
        self._name = name
        self._context = context
        self._parent = parent
        self._kind = kind
        self._start_time = start_time
        self._end_time = end_time
        self._status = status
        self._attributes = attributes
        self._resource = resource
        self._events = ()
        self._links = ()
        self._instrumentation_scope = None

    @property
    def name(self) -> str:
        """Return the span name."""
        return self._name

    @property
    def context(self) -> "SpanContext":
        """Return the span context."""
        return self._context

    def get_span_context(self) -> "SpanContext":
        """Return the span context (required by exporter)."""
        return self._context

    @property
    def parent(self) -> "SpanContext | None":
        """Return the parent span context."""
        return self._parent

    @property
    def kind(self) -> "OTelSpanKind":
        """Return the span kind."""
        return self._kind

    @property
    def start_time(self) -> int:
        """Return the start time in nanoseconds."""
        return self._start_time

    @property
    def end_time(self) -> int:
        """Return the end time in nanoseconds."""
        return self._end_time

    @property
    def status(self) -> "Status":
        """Return the span status."""
        return self._status

    @property
    def attributes(self) -> dict[str, Any]:
        """Return the span attributes."""
        return self._attributes

    @property
    def resource(self) -> "Resource":
        """Return the resource."""
        return self._resource

    @property
    def events(self) -> tuple:
        """Return span events (empty for Beacon spans)."""
        return self._events

    @property
    def links(self) -> tuple:
        """Return span links (empty for Beacon spans)."""
        return self._links

    @property
    def instrumentation_scope(self):
        """Return the instrumentation scope."""
        return self._instrumentation_scope

    @property
    def dropped_attributes(self) -> int:
        """Return count of dropped attributes (always 0 for Beacon spans)."""
        return 0

    @property
    def dropped_events(self) -> int:
        """Return count of dropped events (always 0 for Beacon spans)."""
        return 0

    @property
    def dropped_links(self) -> int:
        """Return count of dropped links (always 0 for Beacon spans)."""
        return 0
