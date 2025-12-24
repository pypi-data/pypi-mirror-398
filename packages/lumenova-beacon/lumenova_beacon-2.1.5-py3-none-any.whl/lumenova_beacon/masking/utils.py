"""Utility functions for creating custom masking functions.

This module provides helper functions for common masking patterns, including:
- Composing multiple masking functions
- Regex-based masking
- Field name-based masking
"""

import re

from typing import Any

from lumenova_beacon.masking.types import MaskingFunction


def compose(*masking_fns: MaskingFunction) -> MaskingFunction:
    """Compose multiple masking functions into a single function.

    The functions are applied in order, with each function receiving the output
    of the previous one.

    Args:
        *masking_fns: Variable number of masking functions to compose.

    Returns:
        A single masking function that applies all provided functions in sequence.

    Example:
        >>> def mask_emails(value):
        ...     if isinstance(value, str) and "@" in value:
        ...         return "<EMAIL>"
        ...     return value
        >>> def mask_phones(value):
        ...     if isinstance(value, str) and re.match(r'\\d{3}-\\d{3}-\\d{4}', value):
        ...         return "<PHONE>"
        ...     return value
        >>> combined = compose(mask_emails, mask_phones)
        >>> combined("user@example.com")
        '<EMAIL>'
    """

    def composed_fn(value: Any) -> Any:
        result = value
        for fn in masking_fns:
            result = fn(result)
        return result

    return composed_fn


def create_regex_masker(
    patterns: list[str], replacement: str = '***REDACTED***'
) -> MaskingFunction:
    """Create a masking function that replaces text matching regex patterns.

    Args:
        patterns: List of regex patterns to match.
        replacement: The string to replace matches with.

    Returns:
        A masking function that replaces matches with the replacement string.

    Example:
        >>> masker = create_regex_masker([r'\\b\\d{3}-\\d{2}-\\d{4}\\b'], '<SSN>')
        >>> masker("My SSN is 123-45-6789")
        'My SSN is <SSN>'
    """
    compiled_patterns = [re.compile(pattern) for pattern in patterns]

    def regex_masker(value: Any) -> Any:
        if not isinstance(value, str):
            return value

        result = value
        for pattern in compiled_patterns:
            result = pattern.sub(replacement, result)
        return result

    return regex_masker


def create_field_masker(
    field_names: list[str], replacement: str = '***REDACTED***', case_sensitive: bool = False
) -> MaskingFunction:
    """Create a masking function that redacts specific dictionary field values.

    This function is designed to be used with the masking engine. It checks if
    the current value is a dictionary and masks values for specified field names.

    Note: This masker should be applied to dictionary objects, not individual values.
    It's most effective when used as a pre-processor before the recursive traversal.

    Args:
        field_names: List of field names whose values should be masked.
        replacement: The string to replace field values with.
        case_sensitive: Whether field name matching should be case-sensitive.

    Returns:
        A masking function that masks values for specified fields.

    Example:
        >>> masker = create_field_masker(['password', 'api_key', 'secret'])
        >>> masker({'password': 'secret123', 'username': 'john'})
        {'password': '***REDACTED***', 'username': 'john'}
    """
    if case_sensitive:
        field_set = set(field_names)
    else:
        field_set = {name.lower() for name in field_names}

    def field_masker(value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        result = {}
        for key, val in value.items():
            check_key = key if case_sensitive else key.lower()
            if check_key in field_set:
                result[key] = replacement
            else:
                result[key] = val
        return result

    return field_masker


def create_string_pattern_masker(
    patterns: list[str], replacement: str = '***REDACTED***'
) -> MaskingFunction:
    """Create a masking function that replaces entire strings matching patterns.

    Unlike create_regex_masker which does partial replacement within strings,
    this function replaces the entire string if any pattern matches.

    Args:
        patterns: List of regex patterns to match.
        replacement: The string to replace the entire value with.

    Returns:
        A masking function that replaces matching strings entirely.

    Example:
        >>> masker = create_string_pattern_masker([r'.*password.*'], '<SENSITIVE>')
        >>> masker("my_password_123")
        '<SENSITIVE>'
    """
    compiled_patterns = [re.compile(pattern) for pattern in patterns]

    def string_masker(value: Any) -> Any:
        if not isinstance(value, str):
            return value

        for pattern in compiled_patterns:
            if pattern.match(value):
                return replacement
        return value

    return string_masker


__all__ = [
    'compose',
    'create_regex_masker',
    'create_field_masker',
    'create_string_pattern_masker',
]
