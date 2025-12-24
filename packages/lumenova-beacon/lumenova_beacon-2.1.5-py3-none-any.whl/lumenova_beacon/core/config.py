"""Configuration management for the Beacon SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from lumenova_beacon.exceptions import ConfigurationError


@dataclass
class BeaconConfig:
    """Configuration for the Beacon SDK.

    Transport mode is automatically determined:
    - If endpoint is provided -> Spans are sent via OTLP to /v1/traces
    - If file_directory is provided without endpoint -> File transport (local storage)

    Spans are always sent via OpenTelemetry's OTLPSpanExporter to the OTLP /v1/traces endpoint.

    Attributes:
        endpoint: Base server URL (e.g., "https://api.example.com")
        api_key: API key for authentication (uses Bearer token in Authorization header)
        timeout: Request timeout in seconds
        verify: Enable SSL certificate verification (default: True)
        enabled: Whether tracing is enabled
        headers: Additional HTTP headers for OTLP requests
        debug: Enable debug logging
        session_id: Default session ID for all spans (optional)
        file_directory: Directory to save span files (File mode)
        file_filename_pattern: Pattern for filenames (File mode)
        file_pretty_print: Format JSON with indentation (File mode, default: True)
        masking_function: Custom function to mask sensitive data before transmission (optional)
        otlp_protocol: OTLP protocol to use - "http/protobuf" or "http/json" (default: "http/protobuf")
    """

    endpoint: str = ''
    api_key: str | None = None
    timeout: float = 10.0
    verify: bool = True
    enabled: bool = True
    headers: dict[str, str] = field(default_factory=dict)
    debug: bool = False
    session_id: str | None = None
    file_directory: str = ''
    file_filename_pattern: str = '{span_id}.json'
    file_pretty_print: bool = True
    masking_function: Callable[[Any], Any] | None = None
    otlp_protocol: str = "http/protobuf"


    def validate(self) -> None:
        """Validate the configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # At least one transport configuration must be provided
        if not self.endpoint and not self.file_directory:
            raise ConfigurationError('Either endpoint or file_directory must be provided')

        # Validate HTTP mode requirements
        if self.endpoint:
            if self.timeout <= 0:
                raise ConfigurationError('timeout must be positive')

        # Validate File mode requirements
        if self.file_directory:
            if not self.file_filename_pattern:
                raise ConfigurationError(
                    'file_filename_pattern is required when using file_directory'
                )
