"""Core modules for Beacon SDK.

This package contains the central client, configuration, and transport layer:
- BeaconClient: Main client for creating and sending spans
- BeaconConfig: Configuration management
"""

from lumenova_beacon.core.client import BeaconClient, get_client
from lumenova_beacon.core.config import BeaconConfig

__all__ = [
    "BeaconClient",
    "get_client",
    "BeaconConfig",
]
