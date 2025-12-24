"""This example demonstrates automatic HTTPX tracing using OpenTelemetry HTTPXClientInstrumentor.

HTTPX is a modern, async-capable HTTP client used internally by many SDKs. After calling
HTTPXClientInstrumentor().instrument(), all HTTPX calls are automatically traced.

Requirements:
    pip install lumenova-beacon[opentelemetry,examples]
"""

import os
import asyncio
import dotenv
from opentelemetry import trace
from lumenova_beacon.core.client import BeaconClient

dotenv.load_dotenv()

beacon_client = BeaconClient()

# === Step 1: Instrument HTTPX ===
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

HTTPXClientInstrumentor().instrument()


# === Step 2: Use HTTPX Normally ===
import httpx

DEFAULT_TIMEOUT = 15.0

# === Example 1: Simple GET Request ===
try:
    response = httpx.get(
        "https://api.github.com/repos/anthropics/anthropic-sdk-python",
        timeout=DEFAULT_TIMEOUT
    )
    repo_data = response.json()
    print(f"Repository: {repo_data['full_name']} - {repo_data['stargazers_count']} stars")
except (httpx.TimeoutException, httpx.ConnectError, Exception):
    print("Note: External API unavailable")


# === Example 2: POST Request with JSON Body ===
try:
    response = httpx.post(
        "https://httpbin.org/post",
        json={
            "name": "Beacon SDK",
            "type": "observability",
            "features": ["tracing", "OpenTelemetry", "LLM monitoring"]
        },
        timeout=DEFAULT_TIMEOUT
    )
    print(f"POST status: {response.status_code}")
except (httpx.TimeoutException, httpx.ConnectError, Exception):
    pass  # Gracefully skip if unavailable


# === Example 3: Request with Query Parameters and Headers ===
try:
    response = httpx.get(
        "https://api.github.com/search/repositories",
        params={"q": "opentelemetry", "sort": "stars", "per_page": 3},
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=DEFAULT_TIMEOUT
    )
    search_results = response.json()
    print(f"Found {search_results['total_count']} repositories matching 'opentelemetry'")
except (httpx.TimeoutException, httpx.ConnectError, Exception):
    pass


# === Example 4: Streaming Responses ===
try:
    with httpx.stream("GET", "https://httpbin.org/stream/5", timeout=DEFAULT_TIMEOUT) as response:
        bytes_received = sum(len(chunk) for chunk in response.iter_bytes())
    print(f"Streamed {bytes_received} bytes")
except (httpx.TimeoutException, httpx.ConnectError, Exception):
    pass


# === Example 5: Connection Pooling with Client ===
try:
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/uuid",
            "https://httpbin.org/user-agent"
        ]
        responses = [client.get(url) for url in urls]
        print(f"Made {len(responses)} requests with connection pooling")
except Exception:
    pass


# === Example 6: Error Handling and Timeouts ===
try:
    response = httpx.get("https://httpbin.org/delay/5", timeout=2.0)
except httpx.TimeoutException:
    print("Timeout captured in span")

try:
    response = httpx.get("https://this-domain-does-not-exist-12345.com")
except httpx.ConnectError:
    print("Connection error captured in span")


# === Example 7: Async HTTPX Operations ===
async def async_examples():
    """Async HTTPX operations."""
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get("https://api.github.com/zen")
            print(f"GitHub Zen: {response.text.strip()}")
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            tasks = [
                client.get("https://httpbin.org/uuid"),
                client.get("https://httpbin.org/uuid"),
                client.get("https://httpbin.org/uuid")
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for r in responses if not isinstance(r, Exception))
            print(f"Completed {successful}/3 concurrent async requests")
    except Exception:
        pass


asyncio.run(async_examples())


# === Example 8: Manual Spans with HTTPX Operations ===
tracer = trace.get_tracer(__name__)

try:
    with tracer.start_as_current_span("fetch_and_process_data") as parent_span:
        parent_span.set_attribute("operation", "data_pipeline")

        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            weather_response = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": 40.7128, "longitude": -74.0060, "current_weather": "true"}
            )
            time_response = client.get("https://worldtimeapi.org/api/timezone/America/New_York")

            weather = weather_response.json()
            time_data = time_response.json()

            parent_span.set_attribute("apis_called", 2)
            print(f"Temperature in NYC: {weather['current_weather']['temperature']}°C")
except Exception:
    pass


# === Example 9: Advanced Client Configuration ===
try:
    custom_client = httpx.Client(
        timeout=httpx.Timeout(DEFAULT_TIMEOUT, connect=5.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        follow_redirects=True
    )
    response = custom_client.get("https://httpbin.org/redirect/2")
    print(f"Final URL after redirects: {response.url}")
    custom_client.close()
except Exception:
    pass


# === Example 10: Integration with LLM API ===
try:
    from anthropic import Anthropic

    anthropic_client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=DEFAULT_TIMEOUT
    )

    with tracer.start_as_current_span("llm_query") as span:
        response = anthropic_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello from Beacon!' in exactly 5 words."}
            ]
        )
        print(f"Claude: {response.content[0].text}")
        span.set_attribute("response_length", len(response.content[0].text))
except ImportError:
    pass
except Exception:
    pass


provider = trace.get_tracer_provider()
if hasattr(provider, 'shutdown'):
    provider.shutdown()

# All HTTP requests are automatically traced including sync/async operations, streaming,
# connection pooling, timeouts, and errors.
