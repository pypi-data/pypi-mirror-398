"""Decorators for automatic span creation and tracing."""

from __future__ import annotations

import functools
import inspect
from typing import  Any, Callable, TypeVar, cast, overload

from lumenova_beacon.tracing.span import Span
from lumenova_beacon.tracing.trace import TraceContext
from lumenova_beacon.types import SpanType, SpanKind

F = TypeVar("F", bound=Callable[..., Any])


def _prepare_span(
    client: 'BeaconClient',
    span_name: str,
    kind: SpanKind,
    span_type: SpanType,
    capture_args: bool,
    args: tuple,
    kwargs: dict,
    func: Callable,
    session_id: str | None = None,
) -> Span:
    """Prepare a span for tracing with optional input capture.

    Args:
        client: The BeaconClient instance
        span_name: Name for the span
        kind: Type of span
        span_type: Type of span
        capture_args: Whether to capture input arguments
        args: Positional arguments to capture
        kwargs: Keyword arguments to capture
        func: The function being traced
        session_id: Session ID (optional, inherits from parent or client default)

    Returns:
        Configured Span instance
    """
    span = client.create_span(
        name=span_name,
        kind=kind,
        span_type=span_type,
        session_id=session_id,
    )

    # Set function name attribute
    span.set_attribute("code.function", func.__name__)

    # Check if it's a method (qualname contains '.')
    # For methods: __qualname__ = "ClassName.method_name"
    # For functions: __qualname__ = "function_name"
    if '.' in func.__qualname__:
        # Extract class name from qualname (everything before the last dot)
        class_name = func.__qualname__.rsplit('.', 1)[0]
        span.set_attribute("code.namespace", class_name)

    # Capture input arguments
    if capture_args:
        input_data = {"args": args, "kwargs": kwargs}
        span.set_input(input_data)

    return span


def _capture_output_if_needed(span: Span, result: Any, capture_result: bool) -> None:
    """Capture function output to span if requested.

    Args:
        span: The span to update
        result: The function result to capture
        capture_result: Whether to capture the result
    """
    if capture_result:
        span.set_output(result)


# Type overloads for proper type hints in both usage patterns
@overload
def trace(_func: F) -> F:
    """Overload for @trace without parentheses."""
    ...


@overload
def trace(
    _func: None = None,
    *,
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    span_type: SpanType = SpanType.FUNCTION,
    capture_args: bool = True,
    capture_result: bool = True,
    session_id: str | None = None,
) -> Callable[[F], F]:
    """Overload for @trace() with parentheses."""
    ...


def trace(
    _func: Callable | None = None,
    *,
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    span_type: SpanType = SpanType.FUNCTION,
    capture_args: bool = True,
    capture_result: bool = True,
    session_id: str | None = None,
) -> Callable[[F], F] | F:
    """Decorator to automatically trace function calls.

    This decorator supports both usage patterns:
    - Without parentheses: @trace
    - With parentheses: @trace() or @trace(name="custom")

    Usage:
        # Without parentheses (uses all defaults)
        @trace
        def my_function(arg1, arg2):
            return arg1 + arg2

        # With empty parentheses (uses all defaults)
        @trace()
        def my_function(arg1, arg2):
            return arg1 + arg2

        # With parameters
        @trace(name="custom_name", kind=SpanKind.CLIENT)
        def api_call():
            pass

        # With session_id
        @trace(session_id="session-123")
        def process_data():
            pass

    Args:
        _func: The function being decorated (when used without parentheses)
        name: Custom span name (defaults to function name)
        kind: Type of span (default: INTERNAL)
        span_type: Type of span (default: FUNCTION)
        capture_args: Capture function arguments as input (default: True)
        capture_result: Capture function result as output (default: True)
        session_id: Session ID (optional, inherits from parent or client default)

    Returns:
        Decorated function or decorator function
    """

    def decorator(func: F) -> F:
        span_name = name or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            from lumenova_beacon.core.client import get_client
            client = get_client()
            if not client:
                # No client configured, just run the function
                return func(*args, **kwargs)

            span = _prepare_span(
                client, span_name, kind, span_type, capture_args, args, kwargs, func,
                session_id
            )

            # Execute function with span context
            # TraceContext handles starting, ending, exception recording, and sending
            with TraceContext(span, client=client):
                result = func(*args, **kwargs)
                _capture_output_if_needed(span, result, capture_result)
                return result

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            from lumenova_beacon.core.client import get_client
            client = get_client()
            if not client:
                # No client configured, just run the function
                return await func(*args, **kwargs)

            span = _prepare_span(
                client, span_name, kind, span_type, capture_args, args, kwargs, func,
                session_id
            )

            # Execute function with async span context
            # TraceContext handles starting, ending, exception recording, and sending
            async with TraceContext(span, client=client):
                result = await func(*args, **kwargs)
                _capture_output_if_needed(span, result, capture_result)
                return result

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    # Detect how the decorator is being used
    if _func is None:
        # Called with parentheses: @trace() or @trace(name="foo")
        # Return the decorator to be applied
        return decorator
    else:
        # Called without parentheses: @trace
        # Apply the decorator immediately
        return decorator(cast(F, _func))
