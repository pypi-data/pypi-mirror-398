"""Example: Basic usage of manual span creation.

This example demonstrates:
- Using context managers for automatic span lifecycle management
- Setting span input, output, and metadata
- Automatic span timing and error capture
"""
import dotenv
from lumenova_beacon import BeaconClient

dotenv.load_dotenv()

# Create client (configure with endpoint/api_key or use environment variables)
client = BeaconClient()


# === Example 1: Basic Span with Input and Output ===

with client.trace("database_query") as span:
    span.set_input({"query": "SELECT * FROM users WHERE id = ?", "params": [123]})

    # Simulate database query
    result = {"id": 123, "name": "John Doe", "email": "john@example.com"}

    span.set_output(result)
    span.set_metadata("rows_returned", 1)
    span.set_metadata("database", "users_db")

print(f"Query result: {result['name']}")


# === Example 2: Another Span (Separate Trace) ===

with client.trace("special_operation") as span:
    span.set_input({"action": "special task", "priority": "high"})

    # Simulate work
    operation_result = {"status": "completed", "duration_ms": 150}

    span.set_output(operation_result)
    span.set_metadata("operation_type", "maintenance")

print(f"Operation status: {operation_result['status']}")
