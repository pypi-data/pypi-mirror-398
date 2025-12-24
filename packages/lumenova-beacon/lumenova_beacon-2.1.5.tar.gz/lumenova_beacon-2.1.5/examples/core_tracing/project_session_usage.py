"""This example demonstrates configuring session_id at different levels.

Configuration can be set via explicit parameters, client initialization, or environment
variables. Child spans automatically inherit values from their parents.
"""

import os
import dotenv
from lumenova_beacon import BeaconClient, trace

dotenv.load_dotenv()

# === Approach 1: Client-level Defaults ===

client = BeaconClient(
    session_id="user-session-abc123"
)

with client.trace("process_payment") as span:
    span.set_input({"amount": 99.99, "currency": "USD"})
    span.set_output({"transaction_id": "txn-12345", "status": "success"})


# === Approach 2: Span-level Specification ===

client2 = BeaconClient()

with client2.trace(
    "analytics_event",
    session_id="analytics-session-xyz"
) as span:
    span.set_input({"event": "page_view", "page": "/dashboard"})
    span.set_output({"recorded": True})

# Override client defaults for specific spans
with client.trace("special_operation", session_id="override-session") as span:
    span.set_input({"task": "special"})
    span.set_output({"result": "completed"})


# === Approach 3: Decorator-level Specification ===

@trace(session_id="service-session-123")
def service_a_operation(data: str) -> dict:
    """Function with configuration set at decorator level."""
    return {"processed": data, "service": "A"}


@trace()
def service_b_helper(value: int) -> int:
    """Helper function that inherits from parent."""
    return value * 2


@trace(session_id="service-b-session")
def service_b_operation(value: int) -> dict:
    """Function with nested call that inherits configuration."""
    result = service_b_helper(value)
    return {"processed": result, "service": "B"}


result_a = service_a_operation("test data")
result_b = service_b_operation(42)


# === Approach 4: Nested Inheritance ===

@trace()
def step_1(data: str) -> str:
    """First step - inherits from parent."""
    return f"step1: {data}"


@trace()
def step_2(data: str) -> str:
    """Second step - inherits from parent."""
    return f"step2: {data}"


@trace(session_id="workflow-session-789")
def multi_step_workflow(input_data: str) -> dict:
    """Multi-step workflow where all nested calls inherit configuration."""
    result_1 = step_1(input_data)
    result_2 = step_2(result_1)

    return {
        "input": input_data,
        "step_1_result": result_1,
        "step_2_result": result_2,
        "status": "completed"
    }


result = multi_step_workflow("test-data")
