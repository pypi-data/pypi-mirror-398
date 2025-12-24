"""Main client for the Lumenova Beacon SDK."""

from __future__ import annotations

import logging
import os

from contextvars import ContextVar
from typing import Any, Callable

from lumenova_beacon.core.config import BeaconConfig
from lumenova_beacon.core.transport import FileTransport, HTTPTransport
from lumenova_beacon.exceptions import ConfigurationError
from lumenova_beacon.tracing.span import Span
from lumenova_beacon.tracing.trace import TraceContext, get_current_span, get_current_trace_id
from lumenova_beacon.types import SpanKind, SpanType


logger = logging.getLogger(__name__)

# Thread-safe client instance using contextvars
_current_client: ContextVar['BeaconClient | None'] = ContextVar('current_client', default=None)


class BeaconClient:
    """Main client for creating and sending spans."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        file_directory: str | None = None,
        session_id: str | None = None,
        auto_instrument_opentelemetry: bool = True,
        auto_instrument_litellm: bool = False,
        masking_function: Callable[[Any], Any] | None = None,
        verify: bool | None = None,
        **kwargs,
    ):
        """Initialize the Beacon client.

        Configuration priority (constructor params override env vars):
        - Constructor parameters take precedence
        - Environment variables as fallback

        Spans are sent via OpenTelemetry's OTLPSpanExporter to the /v1/traces endpoint.
        Authentication is handled via 'headers' parameter or OTEL_EXPORTER_OTLP_HEADERS env var.

        Args:
            endpoint: Base server URL (e.g., "https://api.example.com"). Falls back to BEACON_ENDPOINT.
            api_key: API key for authentication (falls back to BEACON_API_KEY)
            file_directory: Directory to save span files (File mode)
            session_id: Default session ID for all spans (falls back to BEACON_SESSION_ID)
            auto_instrument_opentelemetry: Automatically set up OpenTelemetry integration (default: True)
            auto_instrument_litellm: Automatically set up LiteLLM integration (default: False)
            masking_function: Custom function to mask sensitive data before transmission (optional)
            verify: Enable SSL certificate verification (default: True, falls back to BEACON_VERIFY)
            **kwargs: Additional configuration options (timeout, enabled, headers, etc.)
        """

        # Constructor params override env vars (simple priority)
        # Handle verify separately to allow env var fallback
        if verify is None:
            verify_env = os.getenv('BEACON_VERIFY', 'true').lower()
            verify = verify_env not in ('false', '0', 'no')

        api_key = api_key if api_key is not None else os.getenv('BEACON_API_KEY')

        # Build headers - start with custom headers if provided, then add auth
        headers = dict(kwargs.pop('headers', {}))
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        config = BeaconConfig(
            endpoint=endpoint if endpoint is not None else os.getenv('BEACON_ENDPOINT', ''),
            api_key=api_key,
            file_directory=file_directory or '',
            session_id=session_id if session_id is not None else os.getenv('BEACON_SESSION_ID'),
            verify=verify,
            masking_function=masking_function,
            headers=headers,
            **kwargs,
        )

        config.validate()
        self.config = config

        # Configure logger for this instance (not global logging)
        if config.debug:
            logger.setLevel(logging.DEBUG)
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)

        if config.file_directory:
            # File mode: file_directory is provided
            self.transport = FileTransport(
                directory=config.file_directory,
                filename_pattern=config.file_filename_pattern,
                pretty_print=config.file_pretty_print,
            )
        else:
            # HTTP mode: endpoint is provided
            self.transport = HTTPTransport(
                endpoint=config.endpoint,
                api_key=config.api_key,
                timeout=config.timeout,
                headers=config.headers,
                verify=config.verify,
            )

        _current_client.set(self)

        # Automatically set up OpenTelemetry integration if requested
        if auto_instrument_opentelemetry:
            self._setup_opentelemetry()

        # Automatically set up LiteLLM integration if requested
        if auto_instrument_litellm:
            self._setup_litellm()

    def _is_otlp_endpoint(self, endpoint: str) -> bool:
        """Detect if an endpoint is an OTLP endpoint.

        Args:
            endpoint: The endpoint URL to check

        Returns:
            True if endpoint appears to be OTLP, False otherwise
        """
        if not endpoint:
            return False

        endpoint_lower = endpoint.lower()

        # Check for common OTLP patterns
        otlp_patterns = [
            '/otel',           # Generic OTLP path
            '/v1/traces',      # Standard OTLP traces path
            '/v1/metrics',     # Standard OTLP metrics path
            '/v1/logs',        # Standard OTLP logs path
        ]

        return any(pattern in endpoint_lower for pattern in otlp_patterns)

    def _setup_opentelemetry(self) -> None:
        """Automatically configure OpenTelemetry to export spans via OTLP.

        This method sets up OTLPSpanExporter to send spans to the /v1/traces endpoint.
        This is called automatically when auto_instrument_opentelemetry=True (default).

        Note:
            If OpenTelemetry SDK is not installed, this method silently returns
            without raising an error (optional dependency).
        """
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
        except ImportError:
            logger.debug(
                'OpenTelemetry SDK not installed. Skipping automatic instrumentation. '
                'Install with: pip install lumenova-beacon[opentelemetry]'
            )
            return

        # Check if a tracer provider is already configured
        current_provider = trace.get_tracer_provider()
        if hasattr(current_provider, '_atexit_handler'):
            # TracerProvider from SDK is already set up, don't override
            logger.debug('OpenTelemetry TracerProvider already configured, skipping auto-setup')
            return

        try:
            # Use native OTLPSpanExporter for all span export
            exporter = self._create_otlp_exporter()
            logger.info(f"OpenTelemetry integration configured with OTLP exporter for {self.config.endpoint}")

            # Build resource attributes for session_id
            resource_attrs = {
                "service.name": "beacon-sdk",
            }

            # Add session_id as resource attributes
            if self.config.session_id:
                resource_attrs["beacon.session.id"] = self.config.session_id

            resource = Resource.create(resource_attrs)

            # Create and configure TracerProvider with resource
            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)

            # Set as global tracer provider
            trace.set_tracer_provider(provider)

            logger.info('OpenTelemetry integration configured automatically')
        except Exception as e:
            logger.warning(f'Failed to set up OpenTelemetry integration: {e}')

    def _setup_litellm(self) -> None:
        """Automatically configure LiteLLM to send spans to Beacon.

        This method creates a BeaconLiteLLMLogger and registers it with
        litellm.callbacks. This is called automatically when
        auto_instrument_litellm=True is set (default: False).

        Note:
            If litellm is not installed, this method silently returns
            without raising an error (optional dependency).

            If a BeaconLiteLLMLogger is already registered, this method
            skips registration to avoid duplicates.
        """
        try:
            import litellm
        except ImportError:
            logger.debug(
                'litellm not installed. Skipping automatic instrumentation. '
                'Install with: pip install litellm'
            )
            return

        # Check if BeaconLiteLLMLogger is already registered
        if litellm.callbacks:
            for callback in litellm.callbacks:
                if callback.__class__.__name__ == 'BeaconLiteLLMLogger':
                    logger.debug('LiteLLM already has BeaconLiteLLMLogger registered, skipping auto-setup')
                    return

        try:
            from lumenova_beacon.tracing.integrations.litellm import BeaconLiteLLMLogger

            # Create logger instance (it will use this client via get_client())
            beacon_logger = BeaconLiteLLMLogger()

            # Register with LiteLLM
            if litellm.callbacks is None:
                litellm.callbacks = [beacon_logger]
            else:
                litellm.callbacks.append(beacon_logger)

            logger.info('LiteLLM integration configured automatically')
        except Exception as e:
            logger.warning(f'Failed to set up LiteLLM integration: {e}')

    def _create_otlp_exporter(self):
        """Create and configure an OTLP exporter.

        Returns:
            Configured OTLPSpanExporter instance

        Raises:
            ImportError: If OTLP exporter package is not installed
        """
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        except ImportError:
            logger.error(
                "OTLP exporter not installed. "
                "Install with: pip install opentelemetry-exporter-otlp-proto-http"
            )
            raise

        # Build OTLP endpoint URL
        endpoint = self.config.endpoint.rstrip('/')

        # Add /v1/traces if not present (required for OTLPSpanExporter endpoint parameter)
        if not endpoint.endswith('/v1/traces'):
            endpoint = f"{endpoint}/v1/traces"

        # Build headers for OTLP
        headers = dict(self.config.headers)

        # Check for common OTLP authentication environment variables
        # These follow the OpenTelemetry specification
        otlp_headers_env = os.getenv('OTEL_EXPORTER_OTLP_HEADERS', '')
        if otlp_headers_env:
            # Parse headers from env var (format: key1=value1,key2=value2)
            for header_pair in otlp_headers_env.split(','):
                if '=' in header_pair:
                    key, value = header_pair.split('=', 1)
                    headers[key.strip()] = value.strip()

        # Add session_id as HTTP headers for backend routing
        if self.config.session_id:
            headers["x-beacon-session-id"] = self.config.session_id

        # Handle SSL verification
        # Note: OTLPSpanExporter has a bug where certificate_file=False doesn't work
        # because of `certificate_file or environ.get(..., True)` logic.
        # We work around this by using a custom session that forces verify=False.
        session = None
        if not self.config.verify:
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Create a custom session that forces verify=False on all requests
            class InsecureSession(requests.Session):
                def request(self, method, url, **kwargs):
                    kwargs['verify'] = False
                    return super().request(method, url, **kwargs)

            session = InsecureSession()

        return OTLPSpanExporter(
            endpoint=endpoint,
            headers=headers,
            timeout=int(self.config.timeout),
            session=session,
        )

    def should_sample(self) -> bool:
        """Determine if the current operation should be sampled.

        Returns:
            True if should sample, False otherwise
        """
        if not self.config.enabled:
            return False
        return True

    def create_span(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.INTERNAL,
        span_type: SpanType = SpanType.SPAN,
        auto_parent: bool = True,
        session_id: str | None = None,
    ) -> Span:
        """Create a new span.

        Args:
            name: Name of the span
            kind: Type of span (default: INTERNAL)
            span_type: Type of span (default: SPAN)
            auto_parent: Automatically set parent from context (default: True)
            session_id: Session ID (optional, inherits from parent or client default)

        Returns:
            New Span instance
        """
        trace_id = get_current_trace_id()
        parent_id = None

        if auto_parent:
            # Check SDK's ContextVar for current span
            current_span = get_current_span()
            if current_span:
                trace_id = current_span.trace_id
                parent_id = current_span.span_id

                # Inherit session_id from parent if not explicitly provided
                if session_id is None:
                    session_id = current_span.session_id

        # Fall back to client defaults if no parent and no explicit value provided
        if session_id is None:
            session_id = self.config.session_id

        return Span(
            name=name,
            trace_id=trace_id,
            parent_id=parent_id,
            kind=kind,
            span_type=span_type,
            session_id=session_id,
        )

    def trace(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.INTERNAL,
        span_type: SpanType = SpanType.SPAN,
        session_id: str | None = None,
    ) -> TraceContext:
        """Create a span and return a context manager for it.

        Usage:
            with client.trace("operation_name"):
                # Your code here
                pass

        Args:
            name: Name of the span
            kind: Type of span (default: INTERNAL)
            span_type: Type of span (default: SPAN)
            session_id: Session ID (optional, stored in attributes)

        Returns:
            TraceContext that can be used as a context manager
        """
        span = self.create_span(
            name=name,
            kind=kind,
            span_type=span_type,
            session_id=session_id,
        )
        span.start()
        return TraceContext(span, client=self)

    def export_span(self, span: Span) -> bool:
        """Export a span via the configured OpenTelemetry exporter.

        This method converts the Beacon span to an OpenTelemetry ReadableSpan
        and sends it through the configured TracerProvider's span processors.

        Args:
            span: The Beacon span to export

        Returns:
            True if export succeeded, False otherwise
        """
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider

            provider = trace.get_tracer_provider()
            if not isinstance(provider, TracerProvider):
                logger.warning("No OpenTelemetry TracerProvider configured, cannot export span")
                return False

            # Convert Beacon span to OTel ReadableSpan
            otel_span = span.to_otel_span()

            # Send through all span processors
            if hasattr(provider, '_active_span_processor'):
                provider._active_span_processor.on_end(otel_span)
                return True

            return False
        except ImportError:
            logger.warning("OpenTelemetry SDK not installed, cannot export span")
            return False
        except Exception as e:
            logger.error(f"Failed to export span: {e}")
            return False

    def export_spans(self, spans: list[Span]) -> int:
        """Export multiple spans via the configured OpenTelemetry exporter.

        Args:
            spans: List of Beacon spans to export

        Returns:
            Number of spans successfully exported
        """
        count = 0
        for span in spans:
            if self.export_span(span):
                count += 1
        return count

    def flush(self, timeout_millis: int = 30000) -> bool:
        """Flush all pending spans to the backend.

        This forces the OpenTelemetry BatchSpanProcessor to export any
        buffered spans immediately.

        Args:
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            True if flush succeeded, False otherwise
        """
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider

            provider = trace.get_tracer_provider()
            if isinstance(provider, TracerProvider):
                return provider.force_flush(timeout_millis)
            return True  # No provider to flush
        except ImportError:
            return True  # OpenTelemetry not installed, nothing to flush
        except Exception as e:
            logger.error(f"Failed to flush spans: {e}")
            return False

    def get_base_url(self) -> str:
        """Get the base URL for API requests.

        Returns the base endpoint URL (e.g., "https://api.example.com").

        Returns:
            Base URL string

        Raises:
            ConfigurationError: If transport is not HTTPTransport
        """
        if not isinstance(self.transport, HTTPTransport):
            raise ConfigurationError(
                'Dataset operations require HTTPTransport. '
                'File transport is not supported for datasets.'
            )

        return self.transport.endpoint


def get_client() -> 'BeaconClient':
    """Get the current Beacon client or init a new one.

    Returns:
        BeaconClient instance
    """
    client = _current_client.get()

    if client is None:
        client = BeaconClient()

    return client
