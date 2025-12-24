"""Type definitions for the masking module.

This module provides enums, type aliases, and data structures for sensitive data redaction.
"""

from enum import Enum
from typing import Any, Callable


# Type alias for masking functions
MaskingFunction = Callable[[Any], Any]
"""A function that takes any data and returns masked data."""


class MaskingMode(str, Enum):
    """Masking modes supported by Beacon Guardrails API.

    - TAG: Replace sensitive data with category labels (e.g., "John Doe" -> "<PERSON>")
    - REDACT: Replace with asterisks (e.g., "John Doe" -> "**** ***")
    - PARTIALLY_REDACT: Show first character of each segment while preserving special characters
        Examples:
        - "John Doe" -> "J*** D**" (preserves space)
        - "john.doe@example.com" -> "j***.*@e******.c**" (preserves @ and dots)
        - "123-45-6789" -> "1**-4*-6***" (preserves hyphens)
    """

    TAG = 'TAG'
    REDACT = 'REDACT'
    PARTIALLY_REDACT = 'PARTIALLY_REDACT'


class PIIType(str, Enum):
    """PII (Personally Identifiable Information) types supported by Beacon Guardrails API.

    These types are based on Presidio's supported entities:
    https://microsoft.github.io/presidio/supported_entities/
    """

    CREDIT_CARD = 'CREDIT_CARD'
    """Credit card numbers"""

    CRYPTO = 'CRYPTO'
    """Cryptocurrency addresses"""

    DATE_TIME = 'DATE_TIME'
    """Date and time expressions"""

    EMAIL_ADDRESS = 'EMAIL_ADDRESS'
    """Email addresses (e.g., "user@example.com")"""

    IBAN_CODE = 'IBAN_CODE'
    """International Bank Account Numbers"""

    IP_ADDRESS = 'IP_ADDRESS'
    """IP addresses (IPv4 and IPv6)"""

    NRP = 'NRP'
    """National Registration/Identification Number"""

    LOCATION = 'LOCATION'
    """Physical locations and addresses"""

    PERSON = 'PERSON'
    """Person names (e.g., "John Doe")"""

    PHONE_NUMBER = 'PHONE_NUMBER'
    """Phone numbers (e.g., "555-123-4567")"""

    MEDICAL_LICENSE = 'MEDICAL_LICENSE'
    """Medical license numbers"""

    URL = 'URL'
    """URLs and web addresses"""

    US_BANK_NUMBER = 'US_BANK_NUMBER'
    """US bank account numbers"""

    US_DRIVER_LICENSE = 'US_DRIVER_LICENSE'
    """US driver's license numbers"""

    US_ITIN = 'US_ITIN'
    """US Individual Taxpayer Identification Numbers"""

    US_PASSPORT = 'US_PASSPORT'
    """US passport numbers"""

    US_SSN = 'US_SSN'
    """US Social Security Numbers (e.g., "123-45-6789")"""


# Convenience list of all PII types
ALL_PII_TYPES = list(PIIType)
"""List of all available PII types for comprehensive masking."""


__all__ = [
    'MaskingFunction',
    'MaskingMode',
    'PIIType',
    'ALL_PII_TYPES',
]
