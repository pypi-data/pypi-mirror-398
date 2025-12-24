"""OpenTelemetry integration for Beacon.

This module previously contained BeaconSpanExporter, which has been removed.
All span export is now handled via OpenTelemetry's native OTLPSpanExporter,
which sends spans directly to the OTLP /v1/traces endpoint.

The BeaconClient automatically configures OTLPSpanExporter when
auto_instrument_opentelemetry=True (default). You typically don't need
to configure anything manually.

Example:
    >>> from lumenova_beacon import BeaconClient
    >>>
    >>> # BeaconClient automatically sets up OpenTelemetry integration
    >>> client = BeaconClient(
    ...     endpoint="http://localhost:8000",
    ...     api_key="your-api-key",
    ...     session_id="my-session"
    ... )
    >>>
    >>> # Now use any OpenTelemetry instrumentor!
    >>> from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor
    >>> AnthropicInstrumentor().instrument()
    >>>
    >>> # All traces automatically flow to Beacon via OTLP!
"""

# This module is kept for backward compatibility but no longer exports anything.
# All span export functionality uses OTLPSpanExporter directly.
