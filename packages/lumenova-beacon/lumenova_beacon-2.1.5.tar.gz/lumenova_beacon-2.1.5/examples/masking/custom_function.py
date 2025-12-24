"""This example demonstrates custom masking functions for client-side data redaction.

Use custom masking functions when you need full control over the masking logic
or when not using Beacon Guardrails service.
"""

import re

from lumenova_beacon import BeaconClient
from lumenova_beacon.masking import compose, create_field_masker, create_regex_masker


# === Example 1: Simple Custom Function ===
def simple_email_masker(value):
    """Mask email addresses in strings."""
    if isinstance(value, str):
        return re.sub(r'\S+@\S+\.\S+', '<EMAIL>', value)
    return value


client1 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=simple_email_masker,
)

with client1.trace('send_notification') as span:
    span.set_input({'message': 'Contact support@example.com for help'})
    span.set_output({'sent': True})

print('✓ Example 1: Simple custom function')
print("  'support@example.com' → '<EMAIL>'")
print()


# === Example 2: Regex Pattern Masker ===
regex_masker = create_regex_masker(
    patterns=[
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b4\d{3}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b',  # Visa cards
        r'\bsk-[a-zA-Z0-9]{32,}\b',  # OpenAI API keys
    ],
    replacement='<REDACTED>',
)

client2 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=regex_masker,
)

with client2.trace('verify_identity') as span:
    span.set_input(
        {
            'ssn': '123-45-6789',
            'card': '4532 1234 5678 9012',
        }
    )
    span.set_output({'verified': True})

print('✓ Example 2: Regex pattern masker')
print('  Multiple patterns masked with single function')
print()


# === Example 3: Field Name Masker ===
field_masker = create_field_masker(
    field_names=['password', 'api_key', 'secret', 'token'],
    replacement='***REDACTED***',
    case_sensitive=False,  # Matches 'Password', 'API_KEY', etc.
)

client3 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=field_masker,
)

with client3.trace('user_login') as span:
    span.set_input(
        {
            'username': 'alice',
            'password': 'secret123',
        }
    )
    span.set_output(
        {
            'session_token': 'abc123xyz',
            'user_id': 'USR42',
        }
    )

print('✓ Example 3: Field name masker')
print('  Sensitive field values replaced based on key names')
print()


# === Example 4: Composed Masking ===
# Combine multiple maskers into one

email_masker = create_regex_masker(
    patterns=[r'\S+@\S+\.\S+'],
    replacement='<EMAIL>',
)

phone_masker = create_regex_masker(
    patterns=[r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'],
    replacement='<PHONE>',
)

key_masker = create_field_masker(
    field_names=['api_key'],
    replacement='***',
)

combined_masker = compose(email_masker, phone_masker, key_masker)

client4 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=combined_masker,
)

with client4.trace('contact_form') as span:
    span.set_input(
        {
            'email': 'user@company.com',
            'phone': '555-123-4567',
            'api_key': 'secret_key_123',
            'message': 'Please call me',
        }
    )
    span.set_output({'status': 'submitted'})

print('✓ Example 4: Composed masking')
print('  Emails, phones, and API keys all masked')
print()


# === Example 5: Advanced Custom Masker ===
def advanced_masker(value):
    """Advanced masker with recursion and custom logic."""
    if isinstance(value, str):
        # Mask emails
        result = re.sub(r'\S+@\S+\.\S+', '<EMAIL>', value)
        # Mask IP addresses
        result = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', result)
        # Mask bearer tokens
        result = re.sub(r'Bearer\s+[a-zA-Z0-9._-]+', 'Bearer <TOKEN>', result)
        return result

    if isinstance(value, dict):
        # Redact sensitive keys
        masked = {}
        for key, val in value.items():
            if any(kw in key.lower() for kw in ['password', 'secret', 'key', 'auth']):
                masked[key] = '***'
            else:
                masked[key] = advanced_masker(val)
        return masked

    if isinstance(value, list):
        return [advanced_masker(item) for item in value]

    return value


client5 = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=advanced_masker,
)

with client5.trace('api_call') as span:
    span.set_input(
        {
            'url': '/users',
            'headers': {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI',
                'X-Forwarded-For': '192.168.1.100',
            },
            'data': {
                'email': 'admin@company.com',
                'api_key': 'sk-secret123',
            },
        }
    )
    span.set_output({'status': 200})

print('✓ Example 5: Advanced custom masker')
print('  Recursive processing with custom logic')
print()


# Summary
print('=' * 60)
print('Custom Masking Approaches:')
print('  1. Simple function: Quick regex-based masking')
print('  2. create_regex_masker(): Mask multiple patterns')
print('  3. create_field_masker(): Mask by dictionary keys')
print('  4. compose(): Combine multiple maskers')
print('  5. Advanced custom: Full control with recursion')
print()
print('When to use custom masking:')
print('  - Not using Beacon Guardrails service')
print('  - Need specific masking logic')
print('  - Client-side only requirements')
