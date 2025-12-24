"""Lumenova Beacon SDK - A Python SDK for observability tracing with OpenTelemetry-compatible span export."""

from lumenova_beacon.core.client import BeaconClient, get_client
from lumenova_beacon.core.config import BeaconConfig
from lumenova_beacon.tracing.decorators import trace

__version__ = '0.1.0'

__all__ = [
    # Core client
    'BeaconClient',
    'BeaconConfig',
    'get_client',
    'trace',
    'BeaconCallbackHandler'
]


def __getattr__(name: str) -> type:
    """Lazy import for optional integration classes.

    This allows the core package to be imported without optional dependencies
    like langchain-core, while still providing a convenient import path.

    Args:
        name: The attribute name being accessed.

    Returns:
        The requested class if it's a lazy-loaded integration.

    Raises:
        AttributeError: If the attribute doesn't exist.
        ImportError: If the required optional dependency is not installed.
    """
    if name == 'BeaconCallbackHandler':
        from lumenova_beacon.tracing.integrations.langchain import BeaconCallbackHandler

        return BeaconCallbackHandler

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


# Submodules are imported via their respective packages:
# from lumenova_beacon.datasets import Dataset, DatasetRecord
# from lumenova_beacon.experiments import Experiment, ExperimentConfig, ExperimentStatus
# from lumenova_beacon.prompts import Prompt
# from lumenova_beacon.evaluations import Evaluation, EvaluationRun, Evaluator, EvaluationRunStatus
# from lumenova_beacon.llm_configs import LLMConfig
