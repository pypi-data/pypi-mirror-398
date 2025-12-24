"""Type definitions for experiment operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lumenova_beacon.llm_configs import LLMConfig
    from lumenova_beacon.prompts import Prompt


class ExperimentStatus(IntEnum):
    """Experiment status enum matching API values."""

    DRAFT = 1
    QUEUED = 2
    RUNNING = 3
    COMPLETED = 4
    FAILED = 5
    CANCELLED = 6


@dataclass
class ExperimentConfig:
    """Configuration for an experiment run.

    Combines a prompt template with an LLM configuration for testing.

    Examples:
        Create a configuration:
            >>> from lumenova_beacon.prompts import Prompt
            >>> from lumenova_beacon.llm_configs import LLMConfig
            >>>
            >>> prompt = Prompt.get(name="greeting", label="production")
            >>> llm = LLMConfig.list()[0]
            >>>
            >>> config = ExperimentConfig(
            ...     label="A",
            ...     prompt=prompt,
            ...     llm_config=llm,
            ...     model_parameters={"temperature": 0.9}
            ... )

        Use with Experiment.create():
            >>> experiment = Experiment.create(
            ...     name="My Experiment",
            ...     dataset_id="dataset-uuid",
            ...     configurations=[config]
            ... )
    """

    label: str
    """Configuration label (e.g., "A", "B", "C") for identifying this config in results."""

    prompt: Prompt
    """Prompt template to use for this configuration."""

    llm_config: LLMConfig
    """LLM configuration (model/provider) to use."""

    model_parameters: dict[str, Any] = field(default_factory=dict)
    """Optional model parameter overrides (temperature, max_tokens, etc.)."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request format.

        Returns:
            Dictionary in PromptConfigurationCreate format:
            - label: Configuration label
            - prompt_content: Prompt template content
            - model_config_id: LLM config UUID
            - model_parameters: Optional overrides
        """
        result: dict[str, Any] = {
            "label": self.label,
            "prompt_content": self.prompt._content,
            "model_config_id": self.llm_config.id,
        }
        if self.model_parameters:
            result["model_parameters"] = self.model_parameters
        return result
