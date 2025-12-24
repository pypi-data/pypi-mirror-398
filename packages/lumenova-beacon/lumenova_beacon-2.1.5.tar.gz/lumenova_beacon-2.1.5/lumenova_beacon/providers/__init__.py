"""Provider-specific configuration helpers for OTLP backends.

This module provides convenient configuration functions for popular
observability platforms that support OpenTelemetry Protocol (OTLP).
"""

import base64
import os
from typing import Any


def configure_for_langfuse(
    public_key: str | None = None,
    secret_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Configure Beacon client for Langfuse OTLP endpoint.

    Langfuse uses Basic Authentication with public_key:secret_key.

    Environment variables (used as fallback):
        LANGFUSE_PUBLIC_KEY: Langfuse public key (pk-lf-...)
        LANGFUSE_SECRET_KEY: Langfuse secret key (sk-lf-...)
        LANGFUSE_BASE_URL: Langfuse base URL (default: https://cloud.langfuse.com)

    Args:
        public_key: Langfuse public key (falls back to LANGFUSE_PUBLIC_KEY)
        secret_key: Langfuse secret key (falls back to LANGFUSE_SECRET_KEY)
        base_url: Langfuse base URL (falls back to LANGFUSE_BASE_URL)
        **kwargs: Additional BeaconClient configuration options

    Returns:
        Dictionary of configuration parameters for BeaconClient

    Example:
        >>> from lumenova_beacon import BeaconClient
        >>> from lumenova_beacon.providers import configure_for_langfuse
        >>>
        >>> client = BeaconClient(**configure_for_langfuse(
        ...     public_key="pk-lf-...",
        ...     secret_key="sk-lf-...",
        ... ))
    """
    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    base_url = base_url or os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        raise ValueError(
            "Langfuse requires public_key and secret_key. "
            "Provide them as arguments or set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables."
        )

    # Create Basic Auth header
    auth_string = f"{public_key}:{secret_key}"
    auth_header = base64.b64encode(auth_string.encode()).decode()

    # Build configuration
    config = {
        "endpoint": f"{base_url.rstrip('/')}/api/public/otel",
        "headers": {"Authorization": f"Basic {auth_header}"},
        **kwargs,
    }

    return config


# def configure_for_beacon(
#     endpoint: str | None = None,
#     api_key: str | None = None,
#     **kwargs: Any,
# ) -> dict[str, Any]:
#     """Configure Beacon client for Beacon OTLP endpoint.
#
#     Beacon uses Bearer token authentication with the API key.
#
#     Environment variables (used as fallback):
#         BEACON_ENDPOINT: Beacon base endpoint (e.g., http://localhost:8000)
#         BEACON_API_KEY: Beacon API key (lum_prod_...)
#
#     Args:
#         endpoint: Beacon base endpoint (falls back to BEACON_ENDPOINT)
#         api_key: Beacon API key (falls back to BEACON_API_KEY)
#         **kwargs: Additional BeaconClient configuration options
#
#     Returns:
#         Dictionary of configuration parameters for BeaconClient
#
#     Example:
#         >>> from lumenova_beacon import BeaconClient
#         >>> from lumenova_beacon.providers import configure_for_beacon
#         >>>
#         >>> client = BeaconClient(**configure_for_beacon(
#         ...     endpoint="http://localhost:8000",
#         ...     api_key="lum_prod_...",
#         ... ))
#     """
#     endpoint = endpoint or os.getenv("BEACON_ENDPOINT")
#     api_key = api_key or os.getenv("BEACON_API_KEY")
#
#     if not endpoint:
#         raise ValueError(
#             "Beacon requires an endpoint. "
#             "Provide it as an argument or set BEACON_ENDPOINT environment variable."
#         )
#
#     if not api_key:
#         raise ValueError(
#             "Beacon requires an API key. "
#             "Provide it as an argument or set BEACON_API_KEY environment variable."
#         )
#
#     # Build configuration
#     config = {
#         "endpoint": f"{endpoint.rstrip('/')}/v1/traces",
#         "headers": {"Authorization": f"Bearer {api_key}"},
#         "use_otlp": True,
#         **kwargs,
#     }
#
#     return config


__all__ = [
    "configure_for_langfuse",
]
