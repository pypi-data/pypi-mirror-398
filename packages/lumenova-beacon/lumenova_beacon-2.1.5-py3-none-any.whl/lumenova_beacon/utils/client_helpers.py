"""Shared helper functions for accessing BeaconClient configuration and transport."""

from lumenova_beacon import get_client
from lumenova_beacon.core.transport import HTTPTransport


def get_transport(operation_name: str = "This operation") -> HTTPTransport:
    """Get the HTTPTransport from the active client.

    Args:
        operation_name: Name of the operation for error messages
                       (e.g., "Dataset operations", "Prompt operations")

    Returns:
        HTTPTransport instance from the active client

    Raises:
        ConfigurationError: If transport is not HTTPTransport
    """
    from lumenova_beacon.exceptions import ConfigurationError

    client = get_client()
    transport = client.transport
    if not isinstance(transport, HTTPTransport):
        raise ConfigurationError(
            f"{operation_name} require HTTPTransport. "
            "File transport is not supported."
        )
    return transport


def get_base_url() -> str:
    """Get the base URL for API requests.

    Returns:
        Base URL from the active client
    """
    client = get_client()
    return client.get_base_url()
