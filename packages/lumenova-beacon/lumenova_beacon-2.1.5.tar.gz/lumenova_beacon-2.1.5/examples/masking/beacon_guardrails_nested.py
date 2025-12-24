"""This example demonstrates Beacon Guardrails masking with nested traces.

Shows how PII masking works across multi-level trace hierarchies, such as
AI agents that perform multiple tool calls and sub-operations.

Requirements:
    - Beacon Guardrails service running (or access to Beacon cloud)
    - Set BEACON_ENDPOINT and BEACON_API_KEY environment variables
"""

from lumenova_beacon import BeaconClient
from lumenova_beacon.masking import (
    ALL_PII_TYPES,
    MaskingMode,
    create_beacon_masking_function,
)


# Alternative imports if you want to specify individual PII types:
# from lumenova_beacon.masking import PIIType

# Create masking function with comprehensive PII detection
# Use ALL_PII_TYPES to mask all supported PII types, or specify individual types
masking_fn = create_beacon_masking_function(
    pii_types=ALL_PII_TYPES,  # Mask all PII types
    mode=MaskingMode.TAG,
)

# Alternative: specify only the PII types you need
# masking_fn = create_beacon_masking_function(
#     pii_types=[
#         PIIType.PERSON,
#         PIIType.EMAIL_ADDRESS,
#         PIIType.PHONE_NUMBER,
#         PIIType.CREDIT_CARD,
#         PIIType.US_SSN,
#         PIIType.LOCATION,
#     ],
#     mode=MaskingMode.TAG,
# )

client = BeaconClient(
    endpoint='https://api.beacon.ai',
    api_key='your-api-key',
    masking_function=masking_fn,
)


# === Simulated AI Agent with Nested Operations ===

with client.trace('ai_agent_process_request') as agent_span:
    # Level 1: Main agent request
    user_request = {
        'user_id': 'user_12345',
        'query': 'Book a flight for John Smith from New York to San Francisco',
        'contact': {
            'email': 'john.smith@email.com',
            'phone': '555-123-4567',
        },
    }
    agent_span.set_input(user_request)

    # Level 2: Extract entities from user request
    with client.trace('extract_entities') as extract_span:
        extract_span.set_input({'text': user_request['query']})

        entities = {
            'passenger_name': 'John Smith',
            'origin': 'New York',
            'destination': 'San Francisco',
        }
        extract_span.set_output(entities)

    # Level 2: Search for flights
    with client.trace('search_flights') as search_span:
        search_criteria = {
            'origin': entities['origin'],
            'destination': entities['destination'],
            'passenger': entities['passenger_name'],
        }
        search_span.set_input(search_criteria)

        # Level 3: Query flight database
        with client.trace('query_flight_db') as db_span:
            db_span.set_input(
                {
                    'query': 'SELECT * FROM flights WHERE origin = ? AND destination = ?',
                    'params': [entities['origin'], entities['destination']],
                }
            )
            db_span.set_output({'results_count': 12})

        # Level 3: Filter by preferences
        with client.trace('filter_preferences') as filter_span:
            filter_span.set_input(
                {
                    'flights_count': 12,
                    'user_preferences': {'max_price': 500, 'direct_only': True},
                }
            )
            filter_span.set_output({'filtered_count': 5})

        search_results = {
            'flights_found': 5,
            'best_option': {
                'flight_number': 'AA123',
                'price': 450.00,
                'departure': '2024-03-15 08:00',
            },
        }
        search_span.set_output(search_results)

    # Level 2: Process payment
    with client.trace('process_payment') as payment_span:
        payment_info = {
            'passenger': 'John Smith',
            'email': 'john.smith@email.com',
            'card_number': '4532-1234-5678-9012',
            'billing_address': '123 Main St, New York, NY 10001',
            'amount': 450.00,
        }
        payment_span.set_input(payment_info)

        # Level 3: Validate payment method
        with client.trace('validate_payment') as validate_span:
            validate_span.set_input(
                {
                    'card_number': payment_info['card_number'],
                    'amount': payment_info['amount'],
                }
            )
            validate_span.set_output({'valid': True, 'fraud_score': 0.05})

        # Level 3: Charge card
        with client.trace('charge_card') as charge_span:
            charge_span.set_input(
                {
                    'card_number': payment_info['card_number'],
                    'amount': payment_info['amount'],
                }
            )
            charge_span.set_output(
                {
                    'transaction_id': 'TXN_ABC123',
                    'status': 'approved',
                }
            )

        payment_span.set_output(
            {
                'transaction_id': 'TXN_ABC123',
                'status': 'success',
            }
        )

    # Level 2: Send confirmation
    with client.trace('send_confirmation') as confirm_span:
        confirmation_data = {
            'recipient': 'john.smith@email.com',
            'passenger_name': 'John Smith',
            'flight': 'AA123',
            'booking_reference': 'BOOK789',
            'contact_phone': '555-123-4567',
        }
        confirm_span.set_input(confirmation_data)

        # Level 3: Generate email
        with client.trace('generate_email') as email_span:
            email_span.set_input(
                {
                    'template': 'flight_confirmation',
                    'data': confirmation_data,
                }
            )
            email_content = {
                'subject': 'Flight Confirmation - AA123',
                'body': f'Dear {confirmation_data["passenger_name"]}, your flight is confirmed...',
            }
            email_span.set_output(email_content)

        # Level 3: Send via email service
        with client.trace('email_service_send') as send_span:
            send_span.set_input(
                {
                    'to': confirmation_data['recipient'],
                    'subject': email_content['subject'],
                    'body': email_content['body'],
                }
            )
            send_span.set_output({'message_id': 'MSG_XYZ456', 'status': 'sent'})

        confirm_span.set_output({'confirmation_sent': True})

    # Final agent response
    agent_response = {
        'status': 'success',
        'message': f'Flight booked for {entities["passenger_name"]}',
        'booking_reference': 'BOOK789',
        'passenger_email': user_request['contact']['email'],
        'passenger_phone': user_request['contact']['phone'],
    }
    agent_span.set_output(agent_response)

print('✓ AI Agent with nested traces (3 levels deep)')
print('  All PII masked across all trace levels using ALL_PII_TYPES')
print('  Detected and masked PII:')
print("    - Names: 'John Smith' → '<PERSON>'")
print("    - Emails: 'john.smith@email.com' → '<EMAIL_ADDRESS>'")
print("    - Phones: '555-123-4567' → '<PHONE_NUMBER>'")
print("    - Cards: '4532-1234-5678-9012' → '<CREDIT_CARD>'")
print("    - Locations: 'New York', 'San Francisco' → '<LOCATION>'")
print()
print('Trace hierarchy:')
print('  ai_agent_process_request (L1)')
print('  ├── extract_entities (L2)')
print('  ├── search_flights (L2)')
print('  │   ├── query_flight_db (L3)')
print('  │   └── filter_preferences (L3)')
print('  ├── process_payment (L2)')
print('  │   ├── validate_payment (L3)')
print('  │   └── charge_card (L3)')
print('  └── send_confirmation (L2)')
print('      ├── generate_email (L3)')
print('      └── email_service_send (L3)')
