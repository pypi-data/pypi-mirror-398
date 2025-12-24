"""Core masking engine for recursive data traversal and redaction.

This module provides the main engine that applies masking functions to any data structure,
including nested dictionaries, lists, and JSON-stringified values.
"""

import json
import re

from typing import Any

from lumenova_beacon.masking.types import MaskingFunction


# Fields that should never be masked (technical identifiers)
SKIP_MASKING_FIELDS = {
    # IDs and identifiers
    'id',
    'span_id',
    'trace_id',
    'parent_id',
    'session_id',
    'user_id',
    'trace_state',
    # Timestamps
    'timestamp',
    'start_time',
    'end_time',
    'created_at',
    'updated_at',
    # Technical fields
    'status_code',
    'status',
    'kind',
    'type',
    'span_type',
    'version',
    # Model and span metadata
    'span.model.name',
    'span.model.parameters',
    'span.type',
    'name',
    # Cost details (nested fields)
    'span.cost_details',
    'input',
    'output',
    'cache_creation',
    'cache_read',
    'total',
    # Usage details (nested fields)
    'span.usage_details',
    'completion_tokens',
    'prompt_tokens',
    'total_tokens',
    # Prompt-specific technical fields
    'prompt.id',
    'prompt.name',
    'prompt.version',
    'prompt.type',
    'prompt.labels',
    'prompt.tags',
}

# Pattern to detect UUID-like strings (don't mask these)
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE
)


def _should_skip_field(key: str) -> bool:
    """Check if a field should be skipped from masking.

    Args:
        key: The field key to check

    Returns:
        True if the field should not be masked
    """
    # Skip exact matches
    if key in SKIP_MASKING_FIELDS:
        return True

    # Skip any field ending with _id
    if key.endswith('_id'):
        return True

    # Skip any field ending with .id (nested IDs like prompt.id)
    if key.endswith('.id'):
        return True

    return False


def _is_uuid(value: str) -> bool:
    """Check if a string looks like a UUID.

    Args:
        value: String to check

    Returns:
        True if the string matches UUID pattern
    """
    return bool(UUID_PATTERN.match(value))


def apply_masking(data: Any, masking_fn: MaskingFunction) -> Any:
    """Apply a masking function to data with recursive deep traversal.

    This function processes the data structure recursively, applying the masking function
    to all values. It handles:
    - Primitive types (strings, numbers, booleans, None)
    - Nested dictionaries
    - Lists and arrays
    - JSON-stringified values (parses, masks, and re-serializes)

    Args:
        data: The data to mask. Can be any JSON-serializable structure.
        masking_fn: A function that takes any value and returns the masked version.

    Returns:
        The masked data with the same structure as the input.

    Example:
        >>> def mask_emails(value):
        ...     if isinstance(value, str) and "@" in value:
        ...         return "<EMAIL>"
        ...     return value
        >>> data = {"user": "john@example.com", "count": 5}
        >>> apply_masking(data, mask_emails)
        {'user': '<EMAIL>', 'count': 5}
    """
    return _traverse_recursive(data, masking_fn)


def _traverse_recursive(obj: Any, masking_fn: MaskingFunction) -> Any:
    """Recursively traverse and mask data structures.

    Args:
        obj: The object to traverse and mask.
        masking_fn: The masking function to apply.

    Returns:
        The masked object.
    """
    if obj is None:
        return None

    if isinstance(obj, dict):
        return _mask_dict(obj, masking_fn)
    elif isinstance(obj, list):
        return _mask_list(obj, masking_fn)
    elif isinstance(obj, str):
        return _mask_string(obj, masking_fn)
    elif isinstance(obj, (int, float, bool)):
        # Apply masking function to primitives as well
        # (some masking functions may want to redact specific numbers, etc.)
        return masking_fn(obj)
    else:
        # For unknown types, apply the masking function directly
        return masking_fn(obj)


def _mask_dict(obj: dict[str, Any], masking_fn: MaskingFunction) -> dict[str, Any]:
    """Mask all values in a dictionary recursively.

    Args:
        obj: The dictionary to mask.
        masking_fn: The masking function to apply.

    Returns:
        A new dictionary with masked values.
    """
    result = {}
    for key, value in obj.items():
        # Skip masking for technical identifier fields
        if _should_skip_field(key):
            result[key] = value
        else:
            # Recursively mask each value
            result[key] = _traverse_recursive(value, masking_fn)
    return result


def _mask_list(obj: list[Any], masking_fn: MaskingFunction) -> list[Any]:
    """Mask all items in a list recursively.

    Args:
        obj: The list to mask.
        masking_fn: The masking function to apply.

    Returns:
        A new list with masked items.
    """
    return [_traverse_recursive(item, masking_fn) for item in obj]


def _mask_string(obj: str, masking_fn: MaskingFunction) -> str:
    """Mask a string value, handling JSON-encoded strings.

    If the string is valid JSON (representing a dict or list), it will be parsed,
    recursively masked, and re-serialized. Otherwise, the masking function is
    applied directly to the string.

    UUIDs are automatically detected and skipped from masking to prevent false positives.

    Args:
        obj: The string to mask.
        masking_fn: The masking function to apply.

    Returns:
        The masked string.
    """
    # Skip masking for UUIDs (they can trigger false PII detections)
    if _is_uuid(obj):
        return obj

    # First, try to parse as JSON if it looks like a JSON object or array
    if obj.startswith(('{', '[')):
        try:
            parsed = json.loads(obj)
            # If it's a dict or list, recursively mask it
            if isinstance(parsed, (dict, list)):
                masked = _traverse_recursive(parsed, masking_fn)
                return json.dumps(masked, default=str)
        except (json.JSONDecodeError, ValueError):
            # Not valid JSON, treat as regular string
            pass

    # Apply masking function to the string itself
    result = masking_fn(obj)
    # Ensure we return a string
    if isinstance(result, str):
        return result
    else:
        return str(result)


__all__ = [
    'apply_masking',
]
