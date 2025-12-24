"""LLM configuration management for the Lumenova Beacon SDK.

This module provides models for listing and accessing LLM configurations.

Examples:
    List available LLM configs:
        >>> from lumenova_beacon import BeaconClient
        >>> from lumenova_beacon.llm_configs import LLMConfig
        >>> client = BeaconClient(...)
        >>> configs = LLMConfig.list()
        >>> for cfg in configs:
        ...     print(f"{cfg.name}: {cfg.provider}/{cfg.litellm_model}")

    Get a specific config by ID:
        >>> config = LLMConfig.get("config-uuid")
        >>> print(f"Model: {config.litellm_model}")
"""

from lumenova_beacon.llm_configs.models import LLMConfig

__all__ = [
    "LLMConfig",
]
