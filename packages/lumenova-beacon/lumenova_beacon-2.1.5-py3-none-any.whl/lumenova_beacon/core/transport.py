"""Transport layer configuration and file-based span storage."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from lumenova_beacon.tracing.span import Span

logger = logging.getLogger(__name__)


class HTTPTransport:
    """HTTP transport configuration holder.

    This class stores HTTP configuration (endpoint, API key, headers, etc.)
    used by the SDK. Span sending is handled via OpenTelemetry's OTLPSpanExporter.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str | None = None,
        timeout: float = 10.0,
        headers: dict[str, str] | None = None,
        verify: bool = True,
    ):
        """Initialize the HTTP transport configuration.

        Args:
            endpoint: The base server URL (e.g., "https://api.example.com")
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 10.0)
            headers: Additional headers to send with requests
            verify: Enable SSL certificate verification (default: True)
        """
        # Store the base endpoint (domain only)
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        # Create a copy of headers to avoid modifying the original dict
        self.headers = dict(headers) if headers else {}
        self.verify = verify

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        self.headers["Content-Type"] = "application/json"


class FileTransport:
    """File transport for saving spans to local JSON files.

    Note: This transport uses synchronous file I/O. The async methods
    (send_span_async, send_spans_async) are provided for API compatibility
    but internally call the synchronous methods. For true async file I/O,
    consider using the aiofiles library in a custom transport implementation.
    """

    def __init__(
        self,
        directory: str = "./spans",
        filename_pattern: str = "{span_id}.json",
        pretty_print: bool = True,
        create_dir: bool = True,
    ):
        """Initialize the file transport.

        Args:
            directory: Directory to save span files (default: ./spans)
            filename_pattern: Pattern for filenames. Available variables:
                - {span_id}: The span ID
                - {trace_id}: The trace ID
                - {name}: The span name
                - {timestamp}: ISO timestamp
            pretty_print: Format JSON with indentation (default: True)
            create_dir: Automatically create directory if it doesn't exist (default: True)
        """
        self.directory = Path(directory)
        self.filename_pattern = filename_pattern
        self.pretty_print = pretty_print

        if create_dir:
            self.directory.mkdir(parents=True, exist_ok=True)

    def _get_filename(self, span: Span) -> Path:
        """Generate filename for a span.

        Args:
            span: The span to generate filename for

        Returns:
            Path object for the span file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = self.filename_pattern.format(
            span_id=span.span_id,
            trace_id=span.trace_id,
            name=span.name.replace("/", "_").replace("\\", "_"),
            timestamp=timestamp,
        )
        return self.directory / filename

    def send_span(self, span: Span) -> bool:
        """Save a single span to a JSON file.

        Args:
            span: The span to save

        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = self._get_filename(span)
            with open(filepath, "w", encoding="utf-8") as f:
                if self.pretty_print:
                    json.dump(span.to_dict(), f, indent=2, ensure_ascii=False)
                else:
                    json.dump(span.to_dict(), f, ensure_ascii=False)
            logger.debug(f"Successfully saved span {span.span_id} to {filepath}")
            return True
        except (OSError, IOError) as e:
            logger.error(f"Failed to save span {span.span_id}: {e}")
            return False

    def send_spans(self, spans: list[Span]) -> bool:
        """Save multiple spans to JSON files.

        Args:
            spans: List of spans to save

        Returns:
            True if all successful, False if any failed
        """
        success = True
        for span in spans:
            if not self.send_span(span):
                success = False
        return success

    async def send_span_async(self, span: Span) -> bool:
        """Save a single span to a JSON file.

        WARNING: This method uses synchronous file I/O and blocks the event loop.
        It's provided for API compatibility with the Transport protocol.
        For true async file I/O, consider using aiofiles in a custom transport.

        Args:
            span: The span to save

        Returns:
            True if successful, False otherwise
        """
        return self.send_span(span)

    async def send_spans_async(self, spans: list[Span]) -> bool:
        """Save multiple spans to JSON files.

        WARNING: This method uses synchronous file I/O and blocks the event loop.
        It's provided for API compatibility with the Transport protocol.
        For true async file I/O, consider using aiofiles in a custom transport.

        Args:
            spans: List of spans to save

        Returns:
            True if all successful, False if any failed
        """
        return self.send_spans(spans)
