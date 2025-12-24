"""This example demonstrates automatic requests library tracing using OpenTelemetry RequestsInstrumentor.

The requests library is one of the most popular HTTP clients in Python. After calling
RequestsInstrumentor().instrument(), all requests operations are automatically traced.

Requirements:
    pip install lumenova-beacon[opentelemetry,examples]
"""

import dotenv
from opentelemetry import trace
from lumenova_beacon.core.client import BeaconClient

dotenv.load_dotenv()

beacon_client = BeaconClient()

# === Step 1: Instrument Requests ===
from opentelemetry.instrumentation.requests import RequestsInstrumentor

RequestsInstrumentor().instrument()


# === Step 2: Use Requests Normally ===
import requests

DEFAULT_TIMEOUT = 15.0

# === Example 1: Simple GET Request ===
try:
    response = requests.get(
        "https://api.github.com/repos/anthropics/anthropic-sdk-python",
        timeout=DEFAULT_TIMEOUT
    )
    repo_data = response.json()
    print(f"Repository: {repo_data['full_name']} - {repo_data['stargazers_count']} stars")
except (requests.Timeout, requests.ConnectionError, Exception):
    print("Note: External API unavailable")


# === Example 2: POST Request with JSON Body ===
try:
    response = requests.post(
        "https://httpbin.org/post",
        json={
            "name": "Beacon SDK",
            "type": "observability",
            "features": ["tracing", "OpenTelemetry", "monitoring"]
        },
        timeout=DEFAULT_TIMEOUT
    )
    print(f"POST status: {response.status_code}")
except (requests.Timeout, requests.ConnectionError, Exception):
    pass


# === Example 3: Request with Custom Headers ===
try:
    response = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": "opentelemetry", "sort": "stars", "per_page": 3},
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=DEFAULT_TIMEOUT
    )
    search_results = response.json()
    print(f"Found {search_results['total_count']} repositories")
except (requests.Timeout, requests.ConnectionError, Exception):
    pass


# === Example 4: Session with Connection Pooling ===
try:
    session = requests.Session()
    session.headers.update({"User-Agent": "Beacon-SDK-Example/1.0"})

    urls = [
        "https://httpbin.org/uuid",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers"
    ]

    for url in urls:
        try:
            response = session.get(url, timeout=DEFAULT_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            pass

    session.close()
    print("Made 3 requests with session (connection pooling)")
except Exception:
    pass


# === Example 5: Timeout Handling ===
try:
    response = requests.get("https://httpbin.org/delay/10", timeout=2.0)
except requests.Timeout:
    print("Timeout captured in span")


# === Example 6: Connection Error Handling ===
try:
    response = requests.get("https://this-domain-does-not-exist-12345.com")
except requests.ConnectionError:
    print("Connection error captured in span")


# === Example 7: Manual Spans with Requests ===
tracer = trace.get_tracer(__name__)

try:
    with tracer.start_as_current_span("fetch_weather_data") as span:
        span.set_attribute("location", "New York")

        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 40.7128,
                "longitude": -74.0060,
                "current_weather": "true"
            },
            timeout=DEFAULT_TIMEOUT
        )

        weather = response.json()
        current = weather.get("current_weather", {})

        span.set_attribute("temperature", current.get("temperature", 0))
        span.set_attribute("windspeed", current.get("windspeed", 0))

        print(f"Temperature in NYC: {current.get('temperature')}°C")
except Exception:
    pass


# === Example 8: Multiple API Calls in One Operation ===
try:
    with tracer.start_as_current_span("aggregate_data") as span:
        span.set_attribute("operation", "fetch_multiple_apis")

        try:
            response1 = requests.get("https://api.github.com/zen", timeout=DEFAULT_TIMEOUT)
            github_zen = response1.text
        except Exception:
            github_zen = None

        try:
            response2 = requests.get("https://httpbin.org/uuid", timeout=DEFAULT_TIMEOUT)
            uuid_data = response2.json()
        except Exception:
            uuid_data = None

        apis_called = sum([github_zen is not None, uuid_data is not None])
        span.set_attribute("apis_successfully_called", apis_called)

        if github_zen:
            print(f"GitHub Zen: {github_zen.strip()}")
except Exception:
    pass


# === Example 9: Form Data POST ===
try:
    response = requests.post(
        "https://httpbin.org/post",
        data={"field1": "value1", "field2": "value2"},
        timeout=DEFAULT_TIMEOUT
    )
    print(f"Form POST status: {response.status_code}")
except (requests.Timeout, requests.ConnectionError, Exception):
    pass


# === Example 10: Authentication Headers ===
try:
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": "token DUMMY_TOKEN_FOR_EXAMPLE"},
        timeout=DEFAULT_TIMEOUT
    )
    print(f"Auth request status: {response.status_code}")
except Exception:
    pass


provider = trace.get_tracer_provider()
if hasattr(provider, 'shutdown'):
    provider.shutdown()

# All HTTP requests are automatically traced including GET/POST, query parameters,
# headers, timeouts, and connection errors.
