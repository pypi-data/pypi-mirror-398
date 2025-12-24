"""Tests for BeaconClient."""

import os
from unittest.mock import MagicMock, patch

import pytest

from lumenova_beacon import BeaconClient
from lumenova_beacon.core.transport import HTTPTransport, FileTransport
from lumenova_beacon.tracing.trace import TraceContext
from lumenova_beacon.types import SpanKind, SpanType
from lumenova_beacon.exceptions import ConfigurationError


class TestBeaconClientInitialization:
    """Test BeaconClient initialization."""

    def test_init_with_endpoint(self):
        """Test initialization with HTTP endpoint."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            api_key="test-key",
            auto_instrument_opentelemetry=False,
        )

        assert client.config.endpoint == "https://api.test.com"
        assert client.config.api_key == "test-key"
        assert isinstance(client.transport, HTTPTransport)
        assert client.transport.endpoint == "https://api.test.com"

    def test_init_with_file_directory(self, temp_span_directory):
        """Test initialization with file directory."""
        client = BeaconClient(
            file_directory=str(temp_span_directory),
            auto_instrument_opentelemetry=False,
        )

        assert client.config.file_directory == str(temp_span_directory)
        assert isinstance(client.transport, FileTransport)
        assert client.transport.directory == temp_span_directory

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(
            os.environ,
            {
                "BEACON_ENDPOINT": "https://env.test.com",
                "BEACON_API_KEY": "env-key",
                "BEACON_SESSION_ID": "env-session",
            },
        ):
            client = BeaconClient(auto_instrument_opentelemetry=False)

            assert client.config.endpoint == "https://env.test.com"
            assert client.config.api_key == "env-key"
            assert client.config.session_id == "env-session"

    def test_init_params_override_env_vars(self):
        """Test that constructor parameters override environment variables."""
        with patch.dict(
            os.environ,
            {
                "BEACON_ENDPOINT": "https://env.test.com",
                "BEACON_API_KEY": "env-key",
            },
        ):
            client = BeaconClient(
                endpoint="https://param.test.com",
                api_key="param-key",
                auto_instrument_opentelemetry=False,
            )

            assert client.config.endpoint == "https://param.test.com"
            assert client.config.api_key == "param-key"

    def test_init_with_verify_ssl(self):
        """Test initialization with SSL verification options."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            verify=False,
            auto_instrument_opentelemetry=False,
        )

        assert client.config.verify is False
        assert client.transport.verify is False

    def test_init_with_verify_env_var(self):
        """Test SSL verification from environment variable."""
        with patch.dict(os.environ, {"BEACON_VERIFY": "false"}):
            client = BeaconClient(
                endpoint="https://api.test.com",
                auto_instrument_opentelemetry=False,
            )
            assert client.config.verify is False

    def test_init_with_custom_headers(self):
        """Test initialization with custom headers."""
        custom_headers = {"X-Custom-Header": "test-value"}
        client = BeaconClient(
            endpoint="https://api.test.com",
            headers=custom_headers,
            auto_instrument_opentelemetry=False,
        )

        assert "X-Custom-Header" in client.transport.headers
        assert client.transport.headers["X-Custom-Header"] == "test-value"

    def test_init_sets_current_client(self):
        """Test that initialization sets the current client in context."""
        from lumenova_beacon.core.client import get_client

        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=False,
        )

        assert get_client() == client

    @patch("lumenova_beacon.core.client.BeaconClient._setup_opentelemetry")
    def test_init_with_auto_instrument(self, mock_setup):
        """Test initialization with auto instrumentation enabled."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=True,
        )

        mock_setup.assert_called_once()

    def test_init_without_auto_instrument(self):
        """Test initialization with auto instrumentation disabled."""
        with patch(
            "lumenova_beacon.core.client.BeaconClient._setup_opentelemetry"
        ) as mock_setup:
            client = BeaconClient(
                endpoint="https://api.test.com",
                auto_instrument_opentelemetry=False,
            )

            mock_setup.assert_not_called()


class TestBeaconClientSpanCreation:
    """Test BeaconClient span creation methods."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return BeaconClient(
            endpoint="https://api.test.com",
            session_id="test-session",
            auto_instrument_opentelemetry=False,
        )

    def test_create_span_basic(self, client):
        """Test creating a basic span."""
        span = client.create_span("test_operation")

        assert span.name == "test_operation"
        assert span.kind == SpanKind.INTERNAL
        assert span.span_type == SpanType.SPAN
        assert span.session_id == "test-session"
        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.parent_id is None

    def test_create_span_with_custom_kind_and_type(self, client):
        """Test creating a span with custom kind and type."""
        span = client.create_span(
            "llm_call",
            kind=SpanKind.CLIENT,
            span_type=SpanType.GENERATION,
        )

        assert span.name == "llm_call"
        assert span.kind == SpanKind.CLIENT
        assert span.span_type == SpanType.GENERATION

    def test_create_span_with_explicit_session_id(self, client):
        """Test creating a span with explicit session ID."""
        span = client.create_span(
            "test_op",
            session_id="custom-session",
        )

        assert span.session_id == "custom-session"

    def test_create_span_with_parent_context(self, client):
        """Test creating a span with parent context."""
        # Create parent span and set it in context
        parent_span = client.create_span("parent_operation")
        parent_span.start()

        from lumenova_beacon.tracing.trace import set_current_span

        set_current_span(parent_span)

        # Create child span
        child_span = client.create_span("child_operation")

        assert child_span.parent_id == parent_span.span_id
        assert child_span.trace_id == parent_span.trace_id
        assert child_span.session_id == parent_span.session_id

    def test_create_span_without_auto_parent(self, client):
        """Test creating a span without auto-parenting.

        When auto_parent=False, the span should not have a parent_id set,
        but it may still share the trace_id from the current context.
        """
        # Create parent span and set it in context
        parent_span = client.create_span("parent_operation")

        from lumenova_beacon.tracing.trace import set_current_span

        set_current_span(parent_span)

        # Create child span with auto_parent=False
        child_span = client.create_span("child_operation", auto_parent=False)

        # With auto_parent=False, no parent_id is set
        assert child_span.parent_id is None
        # Note: trace_id can still be inherited from context
        # The key difference is that there's no parent-child relationship

    def test_trace_context_manager(self, client):
        """Test creating a trace context manager."""
        trace_ctx = client.trace("operation_name")

        assert isinstance(trace_ctx, TraceContext)
        assert trace_ctx.span.name == "operation_name"
        assert trace_ctx.client == client

    def test_trace_context_manager_starts_span(self, client):
        """Test that trace context manager starts the span."""
        trace_ctx = client.trace("operation_name")

        assert trace_ctx.span.start_time is not None

    def test_trace_context_manager_with_params(self, client):
        """Test trace context manager with custom parameters."""
        trace_ctx = client.trace(
            "llm_call",
            kind=SpanKind.CLIENT,
            span_type=SpanType.GENERATION,
        )

        assert trace_ctx.span.kind == SpanKind.CLIENT
        assert trace_ctx.span.span_type == SpanType.GENERATION


class TestBeaconClientSampling:
    """Test BeaconClient sampling methods."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=False,
        )

    def test_should_sample_when_enabled(self, client):
        """Test should_sample returns True when enabled."""
        assert client.should_sample() is True

    def test_should_sample_when_disabled(self):
        """Test should_sample returns False when disabled."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            enabled=False,
            auto_instrument_opentelemetry=False,
        )

        assert client.should_sample() is False


class TestBeaconClientUtilityMethods:
    """Test BeaconClient utility methods."""

    def test_get_base_url_http_transport(self):
        """Test getting base URL with HTTP transport."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=False,
        )

        assert client.get_base_url() == "https://api.test.com"

    def test_get_base_url_file_transport_raises_error(self, temp_span_directory):
        """Test that get_base_url raises error with file transport."""
        client = BeaconClient(
            file_directory=str(temp_span_directory),
            auto_instrument_opentelemetry=False,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            client.get_base_url()

        assert "HTTPTransport" in str(exc_info.value)

    def test_flush_method(self):
        """Test flush method (currently no-op)."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=False,
        )

        # Should not raise any errors
        client.flush()


class TestGetClient:
    """Test get_client() function."""

    def test_get_client_returns_existing(self):
        """Test that get_client returns existing client."""
        from lumenova_beacon.core.client import get_client

        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=False,
        )

        retrieved = get_client()
        assert retrieved == client

    def test_get_client_creates_new_when_none(self):
        """Test that get_client creates new client when none exists."""
        from lumenova_beacon.core.client import _current_client, get_client

        # Clear the current client
        _current_client.set(None)

        # Mock the environment to provide required config
        with patch.dict(os.environ, {"BEACON_ENDPOINT": "https://api.test.com"}):
            with patch(
                "lumenova_beacon.core.client.BeaconClient._setup_opentelemetry"
            ):
                retrieved = get_client()
                assert isinstance(retrieved, BeaconClient)


class TestOpenTelemetrySetup:
    """Test OpenTelemetry auto-instrumentation setup."""

    def test_setup_opentelemetry_runs_without_error(self):
        """Test that OpenTelemetry setup completes without error."""
        # Simply verify the client can be created with auto_instrument=True
        # The setup method should handle all cases gracefully
        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=True,
        )

        # Client should be created successfully
        assert client is not None
        assert client.config.endpoint == "https://api.test.com"

    def test_setup_opentelemetry_disabled(self):
        """Test that OpenTelemetry setup can be disabled."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=False,
        )

        # Client should be created successfully
        assert client is not None

    def test_manual_setup_opentelemetry_call(self):
        """Test that _setup_opentelemetry can be called manually."""
        client = BeaconClient(
            endpoint="https://api.test.com",
            auto_instrument_opentelemetry=False,
        )

        # Calling setup manually should not raise
        client._setup_opentelemetry()
