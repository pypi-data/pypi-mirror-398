"""Integration-specific masking implementations.

This package contains integrations with external masking services:

- beacon_guardrails: Integration with Beacon API's built-in guardrail functionality
  for automatic PII detection and redaction.
"""

from lumenova_beacon.masking.integrations.beacon_guardrails import (
    BeaconGuardrailsClient,
    create_beacon_masking_function,
)


__all__ = [
    'BeaconGuardrailsClient',
    'create_beacon_masking_function',
]
