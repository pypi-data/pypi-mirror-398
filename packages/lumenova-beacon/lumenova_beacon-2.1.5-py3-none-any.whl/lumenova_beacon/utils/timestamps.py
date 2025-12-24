"""Timestamp utility functions for Lumenova Beacon SDK."""

from datetime import datetime, timezone


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format with 'Z' suffix.

    Returns:
        Current UTC timestamp in ISO format with 'Z' suffix

    Examples:
        >>> import re
        >>> timestamp = get_current_timestamp()
        >>> bool(re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', timestamp))
        True
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")