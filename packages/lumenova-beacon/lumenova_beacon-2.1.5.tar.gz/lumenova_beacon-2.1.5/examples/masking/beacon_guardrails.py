"""This example demonstrates automatic PII masking using Beacon Guardrails.

Beacon Guardrails provides server-side PII detection and masking powered by Presidio.
This is the RECOMMENDED approach for sensitive data masking in production.

Requirements:
    - Beacon Guardrails service running (or access to Beacon cloud)
    - Set BEACON_ENDPOINT and BEACON_API_KEY environment variables
"""

from lumenova_beacon import BeaconClient
from lumenova_beacon.masking import (
    MaskingMode,
    PIIType,
    create_beacon_masking_function,
)


# === Example 1: Basic Setup with Endpoint Inheritance ===
# The masking function automatically inherits endpoint and API key from BeaconClient
# Guardrails endpoint is derived as {client.endpoint}/guardrails

masking_fn = create_beacon_masking_function(
    pii_types=[PIIType.PERSON, PIIType.EMAIL_ADDRESS, PIIType.PHONE_NUMBER],
    mode=MaskingMode.TAG,
)

client = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=masking_fn,
)

with client.trace('send_email') as span:
    span.set_input(
        {
            'to': 'john.doe@example.com',
            'from': 'support@company.com',
            'body': 'Hello John Doe, your account has been updated.',
        }
    )
    span.set_output({'status': 'sent', 'message_id': 'MSG123'})

print('✓ Example 1: Basic masking with TAG mode')
print('  Emails and names are masked as <EMAIL_ADDRESS> and <PERSON>')
print()


# === Example 2: REDACT Mode (Complete Obfuscation) ===
redact_masking = create_beacon_masking_function(
    pii_types=[PIIType.US_SSN, PIIType.CREDIT_CARD],
    mode=MaskingMode.REDACT,
)

client2 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=redact_masking,
)

with client2.trace('process_payment') as span:
    span.set_input(
        {
            'ssn': '123-45-6789',
            'card': '4532-1234-5678-9012',
            'amount': 99.99,
        }
    )
    span.set_output({'transaction_id': 'TXN456', 'status': 'approved'})

print('✓ Example 2: REDACT mode')
print('  SSN and credit card numbers replaced with ***')
print()


# === Example 3: PARTIALLY_REDACT Mode (Preserve Structure) ===
partial_masking = create_beacon_masking_function(
    pii_types=[PIIType.EMAIL_ADDRESS, PIIType.PERSON],
    mode=MaskingMode.PARTIALLY_REDACT,
)

client3 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=partial_masking,
)

with client3.trace('user_signup') as span:
    span.set_input(
        {
            'name': 'Jane Smith',
            'email': 'jane.smith@company.com',
        }
    )
    span.set_output({'user_id': 'USR789'})

print('✓ Example 3: PARTIALLY_REDACT mode')
print("  'Jane Smith' → 'J*** S****' (preserves first letter and structure)")
print("  'jane.smith@company.com' → 'j***.*@c******.c**'")
print()


# === Example 4: Custom Regex Patterns ===
custom_masking = create_beacon_masking_function(
    pii_types=[PIIType.EMAIL_ADDRESS],
    custom_patterns=[
        r'\b[A-Z]{2}\d{6}\b',  # Custom ID like "AB123456"
        r'\bAPI[_-]?KEY[_-]?[a-zA-Z0-9]{16,}\b',  # API keys
    ],
    mode=MaskingMode.TAG,
)

client4 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=custom_masking,
)

with client4.trace('api_integration') as span:
    span.set_input(
        {
            'user_id': 'AB123456',
            'api_key': 'API_KEY_abc123xyz789secret',
            'email': 'admin@internal.com',
        }
    )
    span.set_output({'status': 'connected'})

print('✓ Example 4: Custom regex patterns')
print('  Custom patterns masked along with standard PII types')
print()


# === Example 5: Explicit Guardrails Endpoint (Advanced) ===
# Use when guardrails service is at a different location than Beacon API

explicit_masking = create_beacon_masking_function(
    guardrails_endpoint='https://guardrails.custom-domain.ai/v1',
    api_key='different-guardrails-api-key',
    pii_types=[PIIType.PERSON],
    mode=MaskingMode.TAG,
)

client5 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='beacon-api-key',
    masking_function=explicit_masking,
)

with client5.trace('cross_service_call') as span:
    span.set_input({'operator': 'Alice Johnson'})
    span.set_output({'status': 'completed'})

print('✓ Example 5: Explicit guardrails endpoint')
print('  Useful when Beacon and Guardrails are separate services')
print()


# Summary
print('=' * 60)
print('Masking Modes:')
print('  TAG: Replace with labels like <PERSON>, <EMAIL_ADDRESS>')
print('  REDACT: Replace with asterisks ***')
print('  PARTIALLY_REDACT: Show first character, preserve structure')
print()
print('Supported PII Types (Presidio-based):')
print('  PERSON, EMAIL_ADDRESS, PHONE_NUMBER, US_SSN, CREDIT_CARD,')
print('  IP_ADDRESS, LOCATION, US_PASSPORT, and more')
print()
print('Setup:')
print('  - Default: Inherits endpoint/api_key from BeaconClient (recommended)')
print('  - Advanced: Specify separate guardrails_endpoint and api_key')
