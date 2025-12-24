"""This example demonstrates automatic FastAPI tracing using OpenTelemetry FastAPIInstrumentor.

Creating a BeaconClient automatically sets up OpenTelemetry integration. After calling
FastAPIInstrumentor.instrument_app(app), all endpoint requests are automatically traced.

Requirements:
    pip install lumenova-beacon[opentelemetry,examples]
"""

import os
import dotenv
from opentelemetry import trace
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from lumenova_beacon.core.client import BeaconClient

dotenv.load_dotenv()

beacon_client = BeaconClient()

# === Step 1: Create FastAPI App ===
app = FastAPI(title="Beacon FastAPI Demo")


# === Step 2: Instrument FastAPI ===
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)


# === Step 3: Define Endpoints ===
class UserRequest(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    status: str


@app.get("/")
async def root():
    """Simple GET endpoint."""
    return {"message": "Hello from Beacon FastAPI!"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """GET endpoint with path parameter."""
    if user_id > 1000:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserRequest):
    """POST endpoint with request body."""
    return UserResponse(
        id=123,
        name=user.name,
        email=user.email,
        status="created"
    )


@app.get("/search")
async def search(q: str, limit: int = 10):
    """GET endpoint with query parameters."""
    return {
        "query": q,
        "limit": limit,
        "results": [f"Result {i} for '{q}'" for i in range(min(limit, 3))]
    }


@app.get("/process")
async def process_data():
    """Endpoint with manual child spans."""
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("validate_input") as span:
        span.set_attribute("validation_type", "schema")
        valid = True

    with tracer.start_as_current_span("database_query") as span:
        span.set_attribute("query_type", "SELECT")
        span.set_attribute("rows_returned", 5)
        data = [{"id": i} for i in range(5)]

    with tracer.start_as_current_span("transform_results") as span:
        span.set_attribute("transformation", "json_serialization")
        result = {"count": len(data), "items": data}

    return result


@app.get("/error")
async def trigger_error():
    """Endpoint that raises an exception."""
    raise ValueError("This is a simulated error for testing")


# === Step 4: Test the Instrumented App ===

client = TestClient(app)

response = client.get("/")
print(f"Root: {response.json()['message']}")

response = client.get("/users/42")
print(f"User: {response.json()['name']}")

response = client.post(
    "/users",
    json={"name": "Alice Smith", "email": "alice@example.com"}
)
print(f"Created user: {response.json()['name']}")

response = client.get("/search?q=python&limit=5")
print(f"Search results: {len(response.json()['results'])} items")

response = client.get("/process")
print(f"Processed: {response.json()['count']} items")

try:
    response = client.get("/error")
except Exception:
    print("Error endpoint raised exception (captured in span)")


provider = trace.get_tracer_provider()
if hasattr(provider, 'shutdown'):
    provider.shutdown()

# All HTTP requests are automatically traced including path, method, status code,
# request/response timing, query parameters, and error details.
