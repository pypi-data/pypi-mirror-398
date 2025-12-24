"""Experiment management for the Lumenova Beacon SDK.

This module provides ActiveRecord-style models for managing experiments.

Examples:
    List all experiments:
        >>> from lumenova_beacon import BeaconClient
        >>> from lumenova_beacon.experiments import Experiment, ExperimentStatus
        >>> client = BeaconClient(endpoint="...", api_key="...")
        >>> experiments, pagination = Experiment.list(page=1, page_size=20)
        >>> print(f"Total: {pagination.total}")

    Filter experiments by status:
        >>> running_experiments, _ = Experiment.list(status=ExperimentStatus.RUNNING)

    Search experiments:
        >>> experiments, _ = Experiment.list(search="my experiment")

    Create experiment with typed configs:
        >>> from lumenova_beacon.prompts import Prompt
        >>> from lumenova_beacon.llm_configs import LLMConfig
        >>> from lumenova_beacon.experiments import Experiment, ExperimentConfig
        >>>
        >>> prompt = Prompt.get(name="greeting", label="production")
        >>> llm = LLMConfig.list()[0]
        >>>
        >>> experiment = Experiment.create(
        ...     name="Model Comparison",
        ...     dataset_id="dataset-uuid",
        ...     configurations=[
        ...         ExperimentConfig(label="A", prompt=prompt, llm_config=llm),
        ...     ]
        ... )
"""

from lumenova_beacon.experiments.models import Experiment
from lumenova_beacon.experiments.types import ExperimentConfig, ExperimentStatus

__all__ = [
    "Experiment",
    "ExperimentConfig",
    "ExperimentStatus",
]
