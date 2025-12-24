"""Configuration utility functions for Beacon SDK."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar('T')


def resolve_config_value(
    explicit: T | None,
    from_parent: T | None,
    from_client: T | None,
) -> T | None:
    """Resolve a configuration value through a cascade of sources.

    Uses the priority order (first non-None wins):
    1. Explicit value (highest priority)
    2. Parent/context value
    3. Client default (lowest priority)

    This pattern is used throughout Beacon for resolving configuration like
    session_id, where values can come from multiple sources:
    - Explicit parameters to a method
    - Parent span or context
    - Client-level defaults
    - Environment variables (handled elsewhere)

    Args:
        explicit: Explicitly provided value (e.g., method parameter)
        from_parent: Value from parent context (e.g., parent span)
        from_client: Value from client configuration

    Returns:
        The first non-None value from the cascade, or None if all are None

    Example:
        >>> session_id = resolve_config_value(
        ...     explicit=None,  # Not provided by caller
        ...     from_parent=parent_span.session_id,
        ...     from_client=client.config.session_id,
        ... )
    """
    if explicit is not None:
        return explicit
    if from_parent is not None:
        return from_parent
    return from_client
