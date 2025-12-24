"""Integration modules for tracing with external frameworks.

This module uses lazy loading to avoid importing heavy dependencies unless needed.
Each integration only loads when explicitly imported.
"""

__all__ = [
    "BeaconCallbackHandler",
    "BeaconLiteLLMLogger",
]

def __getattr__(name: str):
    """Lazy load integrations to avoid importing heavy dependencies.

    This prevents importing one integration from triggering others to load.
    For example, importing BeaconCallbackHandler won't load litellm.
    """
    if name == "BeaconCallbackHandler":
        from lumenova_beacon.tracing.integrations.langchain import BeaconCallbackHandler
        return BeaconCallbackHandler
    elif name == "BeaconLiteLLMLogger":
        from lumenova_beacon.tracing.integrations.litellm import BeaconLiteLLMLogger
        return BeaconLiteLLMLogger
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
