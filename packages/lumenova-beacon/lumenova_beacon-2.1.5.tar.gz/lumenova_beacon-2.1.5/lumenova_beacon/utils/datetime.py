"""Datetime utility functions for Lumenova Beacon SDK."""

from __future__ import annotations

from datetime import datetime


def parse_iso_datetime(iso_string: str | None) -> datetime | None:
    """Parse ISO datetime string, handling Z suffix.

    The API returns datetime strings in ISO format with 'Z' suffix
    (e.g., "2024-01-01T00:00:00Z"). Python's fromisoformat doesn't
    handle 'Z', so we need to replace it with '+00:00'.

    Args:
        iso_string: ISO datetime string with optional Z suffix, or None

    Returns:
        Parsed datetime object or None if input is None

    Examples:
        >>> parse_iso_datetime("2024-01-01T00:00:00Z")
        datetime.datetime(2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

        >>> parse_iso_datetime("2024-01-01T00:00:00+00:00")
        datetime.datetime(2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

        >>> parse_iso_datetime(None)
        None
    """
    if not iso_string:
        return None
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))