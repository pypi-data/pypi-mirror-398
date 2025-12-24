"""Type definitions for evaluation operations."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvaluationRunStatus(str, Enum):
    """Evaluation run status enum matching API values."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScoreType(str, Enum):
    """Score type enum for evaluators.

    Evaluators can produce scores in different formats:
    - PERCENT: A value between 0-100 representing a percentage
    - NUMERIC: An arbitrary numeric value
    - CATEGORICAL: A discrete value from a predefined list (e.g., "pass", "fail")
    """

    PERCENT = "percent"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"


class EvaluatorType(str, Enum):
    """Evaluator type enum.

    Two types of evaluators are supported:
    - LLM_AS_JUDGE: Uses an LLM with a prompt template to evaluate
    - CODE: Uses custom Python code to evaluate
    """

    LLM_AS_JUDGE = "llm-as-judge"
    CODE = "code"


@dataclass
class CodeParameter:
    """Parameter extracted from a code evaluator function signature.

    Attributes:
        name: Parameter name
        type_hint: Python type hint (e.g., 'str', 'int', 'dict')
        has_default: Whether the parameter has a default value
        default_value: Default value if has_default is True
    """

    name: str
    type_hint: str | None = None
    has_default: bool = False
    default_value: Any = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeParameter":
        """Create a CodeParameter from API response data."""
        return cls(
            name=data["name"],
            type_hint=data.get("type_hint"),
            has_default=data.get("has_default", False),
            default_value=data.get("default_value"),
        )
