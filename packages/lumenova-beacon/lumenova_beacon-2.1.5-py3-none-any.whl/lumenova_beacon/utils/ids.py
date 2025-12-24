"""ID generation utility functions for Lumenova Beacon SDK."""

import secrets


def generate_span_id() -> str:
    """Generate a random 16-character hex span ID.

    Returns:
        A 16-character hexadecimal string suitable for use as a span ID

    Examples:
        >>> span_id = generate_span_id()
        >>> len(span_id)
        16
        >>> all(c in '0123456789abcdef' for c in span_id)
        True
    """
    return secrets.token_hex(8)


def generate_trace_id() -> str:
    """Generate a random 32-character hex trace ID.

    Returns:
        A 32-character hexadecimal string suitable for use as a trace ID

    Examples:
        >>> trace_id = generate_trace_id()
        >>> len(trace_id)
        32
        >>> all(c in '0123456789abcdef' for c in trace_id)
        True
    """
    return secrets.token_hex(16)