"""Trace context management using contextvars for thread-safe tracking."""

from __future__ import annotations

import logging
from contextvars import ContextVar

from lumenova_beacon.tracing.span import Span
from lumenova_beacon.types import StatusCode

logger = logging.getLogger(__name__)


# Context variables for tracking current trace and span
_current_trace_id: ContextVar[str | None] = ContextVar(
    "current_trace_id", default=None
)
_current_span: ContextVar[Span | None] = ContextVar("current_span", default=None)

# Context variable for pending prompt metadata (used when compile() is called
# before a LangChain LLM span is created)
_pending_prompt: ContextVar[dict | None] = ContextVar("pending_prompt", default=None)


def get_current_trace_id() -> str | None:
    """Get the current trace ID from context.

    Returns:
        Current trace ID or None if no trace is active
    """
    return _current_trace_id.get()


def get_current_span() -> Span | None:
    """Get the current span from context.

    Returns:
        Current span or None if no span is active
    """
    return _current_span.get()


def set_current_trace_id(trace_id: str) -> None:
    """Set the current trace ID in context.

    Args:
        trace_id: Trace ID to set
    """
    _current_trace_id.set(trace_id)


def set_current_span(span: Span) -> None:
    """Set the current span in context.

    Args:
        span: Span to set as current
    """
    _current_span.set(span)
    _current_trace_id.set(span.trace_id)


def clear_context() -> None:
    """Clear the current trace context."""
    _current_trace_id.set(None)
    _current_span.set(None)


def set_pending_prompt(prompt_info: dict) -> None:
    """Set pending prompt metadata to be picked up by the next LLM span.

    This is used when compile() is called and the prompt metadata needs to
    flow to a LangChain LLM span that will be created later.

    Args:
        prompt_info: Dictionary with prompt metadata (id, name, version, labels, tags)
    """
    _pending_prompt.set(prompt_info)


def get_pending_prompt() -> dict | None:
    """Get the pending prompt metadata.

    Returns:
        Dictionary with prompt metadata or None if no pending prompt
    """
    return _pending_prompt.get()


def clear_pending_prompt() -> None:
    """Clear the pending prompt metadata."""
    _pending_prompt.set(None)


class TraceContext:
    """Context manager for managing trace context with automatic cleanup.

    Supports both sync and async contexts:
    - Use `with TraceContext(...)` for synchronous code
    - Use `async with TraceContext(...)` for asynchronous code
    """

    def __init__(self, span: Span, client: "BeaconClient | None" = None):
        """Initialize the trace context.

        Args:
            span: The span to set as active
            client: The BeaconClient to use for sending the span (optional)
        """
        self.span = span
        self.client = client
        self.previous_span: Span | None = None
        self.previous_trace_id: str | None = None

    def _enter_context(self) -> Span:
        """Common logic for entering the trace context.

        Returns:
            The span that was set as active
        """
        self.previous_span = get_current_span()
        self.previous_trace_id = get_current_trace_id()
        set_current_span(self.span)

        # Start span if not already started
        if self.span.start_time is None:
            self.span.start()

        return self.span

    def _exit_context(self, exc_val: BaseException | None) -> None:
        """Common logic for exiting the trace context.

        Args:
            exc_val: Exception that occurred, if any
        """
        # End the span and record any exception
        if exc_val is not None:
            self.span.record_exception(exc_val)
        else:
            # Set OK status on successful completion if still UNSET
            if self.span.status_code == StatusCode.UNSET:
                self.span.set_status(StatusCode.OK)

        # Only end if not already ended
        if self.span.end_time is None:
            self.span.end()

        # Export the span via OpenTelemetry
        self._export_span()

        # Restore previous context
        self._restore_context()

    def _export_span(self) -> None:
        """Export the span via OpenTelemetry's configured exporter.

        This method converts the Beacon span to an OpenTelemetry ReadableSpan
        and sends it through the configured TracerProvider's span processors.
        """
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider

            provider = trace.get_tracer_provider()
            if not isinstance(provider, TracerProvider):
                # No SDK TracerProvider configured, skip export
                return

            # Convert Beacon span to OTel ReadableSpan
            otel_span = self.span.to_otel_span()

            # Send through all span processors
            # Access the active span processor which wraps all added processors
            if hasattr(provider, '_active_span_processor'):
                provider._active_span_processor.on_end(otel_span)
        except ImportError:
            # OpenTelemetry not installed, skip export
            pass
        except Exception as e:
            logger.debug(f"Failed to export span via OpenTelemetry: {e}")

    def __enter__(self) -> Span:
        """Enter the sync trace context, saving previous context."""
        return self._enter_context()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the sync trace context, restoring previous context."""
        self._exit_context(exc_val)
        # Note: Spans are sent via OpenTelemetry's BatchSpanProcessor and OTLPSpanExporter

    async def __aenter__(self) -> Span:
        """Enter the async trace context, saving previous context."""
        return self._enter_context()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async trace context, restoring previous context."""
        self._exit_context(exc_val)
        # Note: Spans are sent via OpenTelemetry's BatchSpanProcessor and OTLPSpanExporter

    def _restore_context(self) -> None:
        """Restore the previous trace context."""
        if self.previous_span is not None:
            set_current_span(self.previous_span)
        elif self.previous_trace_id is not None:
            # Restore trace_id only - also clear the current span
            _current_span.set(None)
            set_current_trace_id(self.previous_trace_id)
        else:
            clear_context()
