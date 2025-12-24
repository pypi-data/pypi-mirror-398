"""Sensitive data masking module for Beacon SDK.

This module provides tools for redacting sensitive information from telemetry data
before it is transmitted to the Beacon server. It supports:

- Custom masking functions with full flexibility
- Beacon API Guardrails integration for automated PII detection
- Utility functions for common masking patterns

Usage:
    # Custom masking function
    from lumenova_beacon import BeaconClient

    def my_masker(value):
        if isinstance(value, str) and "@" in value:
            return "<EMAIL>"
        return value

    client = BeaconClient(
        endpoint="...",
        masking_function=my_masker
    )

    # Beacon Guardrails (recommended)
    from lumenova_beacon import BeaconClient
    from lumenova_beacon.masking import (
        create_beacon_masking_function,
        MaskingMode,
        PIIType
    )

    masking_fn = create_beacon_masking_function(
        pii_types=[PIIType.PERSON, PIIType.EMAIL_ADDRESS],
        mode=MaskingMode.TAG
    )

    client = BeaconClient(
        endpoint="...",
        masking_function=masking_fn
    )
"""

from lumenova_beacon.masking.engine import apply_masking
from lumenova_beacon.masking.integrations.beacon_guardrails import create_beacon_masking_function
from lumenova_beacon.masking.types import ALL_PII_TYPES, MaskingFunction, MaskingMode, PIIType
from lumenova_beacon.masking.utils import (
    compose,
    create_field_masker,
    create_regex_masker,
    create_string_pattern_masker,
)


__all__ = [
    # Core engine
    'apply_masking',
    # Types
    'MaskingFunction',
    'MaskingMode',
    'PIIType',
    'ALL_PII_TYPES',
    # Utilities
    'compose',
    'create_regex_masker',
    'create_field_masker',
    'create_string_pattern_masker',
    'create_beacon_masking_function',
]
