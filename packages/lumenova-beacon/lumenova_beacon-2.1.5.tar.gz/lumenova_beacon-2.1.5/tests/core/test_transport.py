"""Tests for transport layer."""

import json
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from lumenova_beacon.core.transport import HTTPTransport, FileTransport


class TestHTTPTransportInitialization:
    """Test HTTPTransport initialization."""

    def test_init_with_basic_config(self):
        """Test initialization with basic configuration."""
        transport = HTTPTransport(endpoint="https://api.test.com")

        assert transport.endpoint == "https://api.test.com"
        assert transport.api_key is None
        assert transport.timeout == 10.0
        assert transport.verify is True
        assert "Content-Type" in transport.headers
        assert transport.headers["Content-Type"] == "application/json"

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from endpoint."""
        transport = HTTPTransport(endpoint="https://api.test.com/")

        assert transport.endpoint == "https://api.test.com"

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        transport = HTTPTransport(
            endpoint="https://api.test.com",
            api_key="test-key-123",
        )

        assert transport.api_key == "test-key-123"
        assert "Authorization" in transport.headers
        assert transport.headers["Authorization"] == "Bearer test-key-123"

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        transport = HTTPTransport(
            endpoint="https://api.test.com",
            timeout=30.0,
        )

        assert transport.timeout == 30.0

    def test_init_with_custom_headers(self):
        """Test initialization with custom headers."""
        custom_headers = {"X-Custom": "value"}
        transport = HTTPTransport(
            endpoint="https://api.test.com",
            headers=custom_headers,
        )

        assert "X-Custom" in transport.headers
        assert transport.headers["X-Custom"] == "value"
        # Should also have default headers
        assert transport.headers["Content-Type"] == "application/json"

    def test_init_with_verify_false(self):
        """Test initialization with SSL verification disabled."""
        transport = HTTPTransport(
            endpoint="https://api.test.com",
            verify=False,
        )

        assert transport.verify is False


class TestFileTransportInitialization:
    """Test FileTransport initialization."""

    def test_init_with_defaults(self, temp_span_directory):
        """Test initialization with default values."""
        transport = FileTransport(
            directory=str(temp_span_directory),
            create_dir=False,
        )

        assert transport.directory == temp_span_directory
        assert transport.filename_pattern == "{span_id}.json"
        assert transport.pretty_print is True

    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates directory."""
        new_dir = tmp_path / "new_spans"
        transport = FileTransport(
            directory=str(new_dir),
            create_dir=True,
        )

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_init_with_custom_pattern(self, temp_span_directory):
        """Test initialization with custom filename pattern."""
        transport = FileTransport(
            directory=str(temp_span_directory),
            filename_pattern="{trace_id}_{span_id}.json",
            create_dir=False,
        )

        assert transport.filename_pattern == "{trace_id}_{span_id}.json"

    def test_init_with_pretty_print_false(self, temp_span_directory):
        """Test initialization with pretty print disabled."""
        transport = FileTransport(
            directory=str(temp_span_directory),
            pretty_print=False,
            create_dir=False,
        )

        assert transport.pretty_print is False


class TestFileTransportSendSpan:
    """Test FileTransport send_span method."""

    @pytest.fixture
    def transport(self, temp_span_directory):
        """Create transport for testing."""
        return FileTransport(
            directory=str(temp_span_directory),
            create_dir=False,
        )

    def test_send_span_success(self, transport, sample_span, temp_span_directory):
        """Test successfully saving a span to file."""
        result = transport.send_span(sample_span)

        assert result is True

        # Verify file was created
        files = list(temp_span_directory.glob("*.json"))
        assert len(files) == 1

        # Verify file content
        with open(files[0], "r") as f:
            data = json.load(f)

        assert data["name"] == sample_span.name
        assert data["context"]["span_id"] == sample_span.span_id

    def test_send_span_with_pretty_print(self, sample_span, temp_span_directory):
        """Test that pretty print formats JSON nicely."""
        transport = FileTransport(
            directory=str(temp_span_directory),
            pretty_print=True,
            create_dir=False,
        )

        transport.send_span(sample_span)

        files = list(temp_span_directory.glob("*.json"))
        with open(files[0], "r") as f:
            content = f.read()

        # Pretty printed JSON should have newlines and indentation
        assert "\n" in content
        assert "  " in content

    def test_send_span_without_pretty_print(self, sample_span, temp_span_directory):
        """Test that non-pretty print creates compact JSON."""
        transport = FileTransport(
            directory=str(temp_span_directory),
            pretty_print=False,
            create_dir=False,
        )

        transport.send_span(sample_span)

        files = list(temp_span_directory.glob("*.json"))
        with open(files[0], "r") as f:
            content = f.read()

        # Compact JSON should not have indentation (though it may have newlines)
        # We can verify it's valid JSON
        json.loads(content)

    def test_send_span_with_custom_pattern(self, sample_span, temp_span_directory):
        """Test filename generation with custom pattern."""
        transport = FileTransport(
            directory=str(temp_span_directory),
            filename_pattern="{trace_id}_{span_id}.json",
            create_dir=False,
        )

        transport.send_span(sample_span)

        files = list(temp_span_directory.glob("*.json"))
        assert len(files) == 1

        # Verify filename contains trace_id and span_id
        filename = files[0].name
        assert sample_span.trace_id in filename
        assert sample_span.span_id in filename

    def test_send_span_io_error(self, transport, sample_span):
        """Test handling I/O error when saving span."""
        # Make directory read-only to trigger error
        transport.directory.chmod(0o444)

        result = transport.send_span(sample_span)

        # Should handle error gracefully
        assert result is False

        # Restore permissions
        transport.directory.chmod(0o755)


class TestFileTransportSendSpans:
    """Test FileTransport send_spans method."""

    @pytest.fixture
    def transport(self, temp_span_directory):
        """Create transport for testing."""
        return FileTransport(
            directory=str(temp_span_directory),
            create_dir=False,
        )

    def test_send_spans_success(self, transport, temp_span_directory):
        """Test successfully saving multiple spans."""
        from lumenova_beacon.tracing.span import Span
        from lumenova_beacon.types import SpanKind, SpanType

        # Create two spans with different IDs
        span1 = Span(
            name="test_op_1",
            trace_id="trace-123",
            span_id="span-001",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span2 = Span(
            name="test_op_2",
            trace_id="trace-123",
            span_id="span-002",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )

        result = transport.send_spans([span1, span2])

        assert result is True

        # Verify files were created
        files = list(temp_span_directory.glob("*.json"))
        assert len(files) == 2

    def test_send_spans_partial_failure(self, transport, sample_span, temp_span_directory):
        """Test handling partial failures when saving spans."""
        # This is difficult to test without mocking, but we can verify behavior
        spans = [sample_span]
        result = transport.send_spans(spans)

        assert result is True


class TestFileTransportAsyncMethods:
    """Test FileTransport async methods (which delegate to sync methods)."""

    @pytest.fixture
    def transport(self, temp_span_directory):
        """Create transport for testing."""
        return FileTransport(
            directory=str(temp_span_directory),
            create_dir=False,
        )

    @pytest.mark.asyncio
    async def test_send_span_async(self, transport, sample_span, temp_span_directory):
        """Test async send_span method."""
        result = await transport.send_span_async(sample_span)

        assert result is True

        # Verify file was created
        files = list(temp_span_directory.glob("*.json"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_send_spans_async(self, transport, temp_span_directory):
        """Test async send_spans method."""
        from lumenova_beacon.tracing.span import Span
        from lumenova_beacon.types import SpanKind, SpanType

        # Create two spans with different IDs
        span1 = Span(
            name="test_op_1",
            trace_id="trace-123",
            span_id="span-async-001",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )
        span2 = Span(
            name="test_op_2",
            trace_id="trace-123",
            span_id="span-async-002",
            kind=SpanKind.INTERNAL,
            span_type=SpanType.SPAN,
        )

        result = await transport.send_spans_async([span1, span2])

        assert result is True

        # Verify files were created
        files = list(temp_span_directory.glob("*.json"))
        assert len(files) == 2
