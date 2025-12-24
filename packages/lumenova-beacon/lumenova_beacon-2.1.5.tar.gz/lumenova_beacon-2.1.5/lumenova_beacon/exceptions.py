"""Custom exceptions for the Beacon SDK."""

from __future__ import annotations


class BeaconError(Exception):
    """Base exception for all Beacon SDK errors."""

    pass


class ConfigurationError(BeaconError):
    """Raised when configuration is invalid or incomplete."""

    pass


class TransportError(BeaconError):
    """Base exception for transport-related errors."""

    pass


class HTTPTransportError(TransportError):
    """Raised when HTTP transport encounters an error."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize HTTP transport error.

        Args:
            message: Error message
            status_code: HTTP status code if available
        """
        super().__init__(message)
        self.status_code = status_code


class FileTransportError(TransportError):
    """Raised when file transport encounters an error."""

    pass


class SpanError(BeaconError):
    """Raised when span operations fail."""

    pass


class DatasetError(BeaconError):
    """Base exception for dataset-related errors."""

    pass


class DatasetNotFoundError(DatasetError):
    """Raised when a dataset or record is not found (404)."""

    pass


class DatasetValidationError(DatasetError):
    """Raised when dataset/record validation fails (422)."""

    pass


class PromptError(BeaconError):
    """Base exception for prompt-related errors."""

    pass


class PromptNotFoundError(PromptError):
    """Raised when a prompt is not found (404)."""

    pass


class PromptValidationError(PromptError):
    """Raised when prompt validation fails (422)."""

    pass


class PromptCompilationError(PromptError):
    """Raised when template rendering/compilation fails."""

    pass


class PromptNetworkError(PromptError):
    """Raised when network request fails after retries."""

    pass


class MaskingError(BeaconError):
    """Base exception for masking-related errors."""

    pass


class MaskingAPIError(MaskingError):
    """Raised when masking API call fails."""

    pass


class MaskingNotFoundError(MaskingError):
    """Raised when masking resource is not found (404)."""

    pass


class MaskingValidationError(MaskingError):
    """Raised when masking validation fails (422)."""

    pass


class ExperimentError(BeaconError):
    """Base exception for experiment-related errors."""

    pass


class ExperimentNotFoundError(ExperimentError):
    """Raised when an experiment is not found (404)."""

    pass


class ExperimentValidationError(ExperimentError):
    """Raised when experiment validation fails (422)."""

    pass


class EvaluationError(BeaconError):
    """Base exception for evaluation-related errors."""

    pass


class EvaluationNotFoundError(EvaluationError):
    """Raised when an evaluation or evaluation run is not found (404)."""

    pass


class EvaluationValidationError(EvaluationError):
    """Raised when evaluation validation fails (422)."""

    pass


class LLMConfigError(BeaconError):
    """Base exception for LLM configuration-related errors."""

    pass


class LLMConfigNotFoundError(LLMConfigError):
    """Raised when an LLM configuration is not found (404)."""

    pass
