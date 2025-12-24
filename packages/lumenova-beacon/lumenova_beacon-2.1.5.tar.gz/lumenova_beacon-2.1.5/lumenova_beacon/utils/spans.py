"""Span utility functions for convenient span creation and management."""

from __future__ import annotations

from lumenova_beacon.tracing.span import Span
from lumenova_beacon.types import SpanKind, SpanType, Attributes


def create_and_start_span(
    name: str,
    *,
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_id: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    span_type: SpanType = SpanType.SPAN,
    attributes: Attributes | None = None,
    session_id: str | None = None,
) -> Span:
    """Create and immediately start a span.

    This utility function combines span creation and starting in one call,
    reducing boilerplate for the common pattern of creating a span and
    immediately starting it.

    This is particularly useful in decorators and callback handlers where
    you want to create and start a span as part of a single operation.

    Args:
        name: Name of the span
        trace_id: Trace ID (generated if not provided)
        span_id: Span ID (generated if not provided)
        parent_id: Parent span ID (None for root spans)
        kind: Type of span (default: INTERNAL)
        span_type: Type of span (default: SPAN)
        attributes: Custom attributes for the span
        session_id: Session ID (optional, stored in attributes)

    Returns:
        Started Span instance ready to be used

    Example:
        >>> span = create_and_start_span(
        ...     "api_call",
        ...     kind=SpanKind.CLIENT,
        ... )
        >>> # Span is already started, use it and end when done
        >>> span.set_output(response)
        >>> span.end()
    """
    span = Span(
        name=name,
        trace_id=trace_id,
        span_id=span_id,
        parent_id=parent_id,
        kind=kind,
        span_type=span_type,
        attributes=attributes,
        session_id=session_id,
    )
    span.start()
    return span
