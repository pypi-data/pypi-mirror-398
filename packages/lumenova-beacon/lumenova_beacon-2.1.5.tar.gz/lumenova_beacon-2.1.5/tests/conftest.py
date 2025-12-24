"""Shared fixtures for Beacon SDK tests."""

from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import httpx
import pytest

from lumenova_beacon import BeaconClient
from lumenova_beacon.core.config import BeaconConfig
from lumenova_beacon.core.transport import HTTPTransport, FileTransport
from lumenova_beacon.tracing.span import Span
from lumenova_beacon.tracing.trace import TraceContext
from lumenova_beacon.types import SpanKind, SpanType, StatusCode


@pytest.fixture
def mock_beacon_client():
    """Create a mock BeaconClient for testing.

    Returns:
        MagicMock instance configured as a BeaconClient
    """
    client = MagicMock(spec=BeaconClient)
    client.config = MagicMock(spec=BeaconConfig)
    client.config.session_id = "test-session"
    client.config.enabled = True
    client.should_sample = MagicMock(return_value=True)
    return client


@pytest.fixture
def sample_span():
    """Create a sample span for testing.

    Returns:
        Span instance with predefined values
    """
    return Span(
        name="test_operation",
        trace_id="trace-123",
        span_id="span-456",
        parent_id="parent-789",
        kind=SpanKind.INTERNAL,
        span_type=SpanType.SPAN,
        session_id="test-session",
    )


@pytest.fixture
def sample_trace_context(sample_span, mock_beacon_client):
    """Create a sample TraceContext for testing.

    Args:
        sample_span: Sample span fixture
        mock_beacon_client: Mock client fixture

    Returns:
        TraceContext instance
    """
    return TraceContext(sample_span, client=mock_beacon_client)


@pytest.fixture
def temp_span_directory(tmp_path):
    """Create a temporary directory for file transport tests.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        Path object for temporary span directory
    """
    span_dir = tmp_path / "spans"
    span_dir.mkdir()
    return span_dir


@pytest.fixture
def http_transport():
    """Create an HTTPTransport instance for testing.

    Returns:
        HTTPTransport configured for tests
    """
    return HTTPTransport(
        endpoint="https://api.test.com",
        api_key="test-key-123",
        timeout=5.0,
    )


@pytest.fixture
def file_transport(temp_span_directory):
    """Create a FileTransport instance for testing.

    Args:
        temp_span_directory: Temporary directory fixture

    Returns:
        FileTransport configured for tests
    """
    return FileTransport(
        directory=str(temp_span_directory),
        filename_pattern="{span_id}.json",
        pretty_print=True,
    )


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response for successful requests.

    Returns:
        MagicMock configured as an httpx.Response
    """
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {"status": "success"}
    response.text = '{"status": "success"}'
    return response


@pytest.fixture
def mock_http_error_response():
    """Create a mock HTTP error response.

    Returns:
        MagicMock configured as an httpx.Response with error
    """
    response = MagicMock(spec=httpx.Response)
    response.status_code = 400
    response.json.return_value = {"error": "Bad Request"}
    response.text = '{"error": "Bad Request"}'
    return response


@pytest.fixture
def sample_attributes():
    """Create sample span attributes for testing.

    Returns:
        Dictionary of test attributes
    """
    return {
        "span.type": "span",
        "span.input": '{"query": "test question"}',
        "span.output": '{"answer": "test answer"}',
        "span.metadata.user_id": "user-123",
        "span.metadata.tags": '["test", "example"]',
    }


@pytest.fixture
def run_id():
    """Generate a UUID for run tracking.

    Returns:
        UUID4 instance
    """
    return uuid4()


@pytest.fixture(autouse=True)
def reset_context():
    """Automatically reset trace context before each test.

    This fixture runs before every test to ensure clean state.
    """
    from lumenova_beacon.tracing.trace import clear_context
    clear_context()
    yield
    clear_context()


@pytest.fixture
def mock_opentelemetry():
    """Mock OpenTelemetry SDK for testing OTel integration.

    Returns:
        Dictionary containing mocked OTel components
    """
    from unittest.mock import MagicMock

    mock_tracer_provider = MagicMock()
    mock_span = MagicMock()
    mock_span.get_span_context.return_value = MagicMock(
        trace_id=12345,
        span_id=67890,
        trace_flags=1,
    )
    mock_span.name = "test_span"
    mock_span.start_time = 1000000000
    mock_span.end_time = 1000000100
    mock_span.status = MagicMock(
        status_code=MagicMock(value=0)
    )
    mock_span.kind = MagicMock(value=1)
    mock_span.attributes = {"key": "value"}
    mock_span.parent = None

    return {
        "tracer_provider": mock_tracer_provider,
        "span": mock_span,
    }


@pytest.fixture
def sample_dataset_data():
    """Create sample data for dataset testing.

    Returns:
        List of dictionaries representing dataset records
    """
    return [
        {
            "input": {"query": "What is Python?"},
            "expected_output": "Python is a programming language",
            "metadata": {"difficulty": "easy"},
        },
        {
            "input": {"query": "What is async?"},
            "expected_output": "Async is asynchronous programming",
            "metadata": {"difficulty": "medium"},
        },
    ]


@pytest.fixture
def sample_prompt_template():
    """Create a sample prompt template for testing.

    Returns:
        Dictionary with prompt template data
    """
    return {
        "name": "test_prompt",
        "template": "Hello {{name}}, welcome to {{service}}!",
        "variables": {"name": "User", "service": "Beacon"},
    }


@pytest.fixture
def sample_chat_messages():
    """Create sample chat messages for prompt testing.

    Returns:
        List of chat message dictionaries
    """
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, {{name}}!"},
    ]
