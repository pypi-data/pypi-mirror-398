"""This example demonstrates custom masking with nested traces.

Shows how custom masking functions work across multi-level trace hierarchies,
such as a customer service agent handling support tickets.

This example uses custom masking functions instead of Beacon Guardrails.
"""

import re

from lumenova_beacon import BeaconClient
from lumenova_beacon.masking import compose, create_field_masker


# Create a comprehensive custom masking function
def custom_pii_masker(value):
    """Custom masker for common PII patterns."""
    if not isinstance(value, str):
        return value

    # Mask emails
    result = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '<EMAIL>', value)
    # Mask phone numbers
    result = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '<PHONE>', result)
    # Mask SSNs
    result = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '<SSN>', result)
    # Mask credit cards
    result = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '<CARD>', result)
    # Mask ticket IDs
    result = re.sub(r'\bTICKET-\d{6}\b', '<TICKET_ID>', result)
    # Mask account numbers
    result = re.sub(r'\bACC-\d{8}\b', '<ACCOUNT>', result)

    return result


field_masker = create_field_masker(
    field_names=['password', 'api_key', 'token', 'secret', 'ssn', 'card_number'],
    replacement='***MASKED***',
    case_sensitive=False,
)

# Compose the maskers
masking_fn = compose(custom_pii_masker, field_masker)

client = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=masking_fn,
)


# === Customer Support Agent with Nested Operations ===

with client.trace('support_agent_handle_ticket') as agent_span:
    # Level 1: Main support ticket
    ticket_data = {
        'ticket_id': 'TICKET-123456',
        'customer': {
            'name': 'Jane Doe',
            'email': 'jane.doe@customer.com',
            'phone': '555-987-6543',
            'account': 'ACC-98765432',
        },
        'issue': 'Unable to access my account after password reset',
        'priority': 'high',
    }
    agent_span.set_input(ticket_data)

    # Level 2: Verify customer identity
    with client.trace('verify_customer_identity') as verify_span:
        verify_data = {
            'account_number': ticket_data['customer']['account'],
            'email': ticket_data['customer']['email'],
            'phone': ticket_data['customer']['phone'],
        }
        verify_span.set_input(verify_data)

        # Level 3: Check account database
        with client.trace('query_customer_db') as db_span:
            db_span.set_input(
                {
                    'query': 'SELECT * FROM customers WHERE account = ?',
                    'account': verify_data['account_number'],
                }
            )
            customer_record = {
                'account': 'ACC-98765432',
                'email': 'jane.doe@customer.com',
                'phone': '555-987-6543',
                'verified': True,
            }
            db_span.set_output(customer_record)

        # Level 3: Validate security questions
        with client.trace('validate_security') as security_span:
            security_span.set_input(
                {
                    'account': verify_data['account_number'],
                    'answers_provided': True,
                }
            )
            security_span.set_output({'passed': True, 'score': 100})

        verify_span.set_output({'identity_verified': True})

    # Level 2: Diagnose issue
    with client.trace('diagnose_account_issue') as diagnose_span:
        diagnose_span.set_input(
            {
                'account': ticket_data['customer']['account'],
                'issue_description': ticket_data['issue'],
            }
        )

        # Level 3: Check login history
        with client.trace('check_login_history') as login_span:
            login_span.set_input({'account': ticket_data['customer']['account']})
            login_history = {
                'last_successful_login': '2024-03-14 10:30:00',
                'failed_attempts': 5,
                'last_ip': '192.168.1.100',
            }
            login_span.set_output(login_history)

        # Level 3: Check password reset status
        with client.trace('check_password_reset') as reset_span:
            reset_span.set_input({'account': ticket_data['customer']['account']})
            reset_status = {
                'reset_requested': True,
                'reset_token_expired': True,
                'reason': 'Token expired after 24 hours',
            }
            reset_span.set_output(reset_status)

        diagnosis = {
            'root_cause': 'Password reset token expired',
            'solution': 'Generate new reset token',
        }
        diagnose_span.set_output(diagnosis)

    # Level 2: Apply fix
    with client.trace('apply_fix') as fix_span:
        fix_span.set_input(
            {
                'account': ticket_data['customer']['account'],
                'solution': 'Generate new password reset token',
            }
        )

        # Level 3: Generate new reset token
        with client.trace('generate_reset_token') as token_span:
            token_span.set_input({'account': ticket_data['customer']['account']})
            new_token = {
                'token': 'RESET_TOKEN_abc123def456',
                'expires_in': '24 hours',
            }
            token_span.set_output(new_token)

        # Level 3: Send reset email
        with client.trace('send_reset_email') as email_span:
            email_data = {
                'to': ticket_data['customer']['email'],
                'subject': 'Password Reset Link',
                'token': new_token['token'],
            }
            email_span.set_input(email_data)
            email_span.set_output({'sent': True, 'message_id': 'MSG_789'})

        fix_span.set_output({'fix_applied': True, 'token_sent': True})

    # Level 2: Update ticket and notify customer
    with client.trace('update_ticket') as update_span:
        update_data = {
            'ticket_id': ticket_data['ticket_id'],
            'status': 'resolved',
            'resolution': 'New password reset link sent to jane.doe@customer.com',
        }
        update_span.set_input(update_data)

        # Level 3: Log resolution to database
        with client.trace('log_resolution') as log_span:
            log_span.set_input(
                {
                    'ticket_id': update_data['ticket_id'],
                    'resolution': update_data['resolution'],
                    'resolved_by': 'support_agent_ai',
                }
            )
            log_span.set_output({'logged': True})

        # Level 3: Send confirmation to customer
        with client.trace('send_confirmation') as confirm_span:
            confirm_data = {
                'to': ticket_data['customer']['email'],
                'ticket_id': ticket_data['ticket_id'],
                'message': f'Your ticket {ticket_data["ticket_id"]} has been resolved',
            }
            confirm_span.set_input(confirm_data)
            confirm_span.set_output({'sent': True})

        update_span.set_output({'ticket_updated': True})

    # Final agent response
    agent_response = {
        'ticket_id': ticket_data['ticket_id'],
        'status': 'resolved',
        'customer_email': ticket_data['customer']['email'],
        'customer_phone': ticket_data['customer']['phone'],
        'account': ticket_data['customer']['account'],
        'resolution_time_minutes': 8,
    }
    agent_span.set_output(agent_response)

print('✓ Support Agent with nested traces (3 levels deep)')
print('  All sensitive data masked across all trace levels:')
print("    - Emails: 'jane.doe@customer.com' → '<EMAIL>'")
print("    - Phones: '555-987-6543' → '<PHONE>'")
print("    - Accounts: 'ACC-98765432' → '<ACCOUNT>'")
print("    - Tickets: 'TICKET-123456' → '<TICKET_ID>'")
print('    - Tokens: Masked via field_names')
print()
print('Trace hierarchy:')
print('  support_agent_handle_ticket (L1)')
print('  ├── verify_customer_identity (L2)')
print('  │   ├── query_customer_db (L3)')
print('  │   └── validate_security (L3)')
print('  ├── diagnose_account_issue (L2)')
print('  │   ├── check_login_history (L3)')
print('  │   └── check_password_reset (L3)')
print('  ├── apply_fix (L2)')
print('  │   ├── generate_reset_token (L3)')
print('  │   └── send_reset_email (L3)')
print('  └── update_ticket (L2)')
print('      ├── log_resolution (L3)')
print('      └── send_confirmation (L3)')
