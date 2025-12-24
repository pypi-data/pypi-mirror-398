"""HTTP utility classes and functions for centralized error handling."""

from typing import NoReturn

import httpx


class HTTPErrorHandler:
    """Centralized HTTP error handling for consistent error mapping.

    This class provides a reusable way to map HTTP status codes to
    domain-specific exceptions across different modules (datasets, prompts, etc.).

    Example:
        >>> from lumenova_beacon.exceptions import (
        ...     DatasetError, DatasetNotFoundError, DatasetValidationError
        ... )
        >>> handler = HTTPErrorHandler(
        ...     not_found_exc=DatasetNotFoundError,
        ...     validation_exc=DatasetValidationError,
        ...     base_exc=DatasetError
        ... )
        >>> try:
        ...     # Some HTTP request that returns 404
        ...     pass
        ... except httpx.HTTPStatusError as e:
        ...     handler.handle(e)  # Raises DatasetNotFoundError
    """

    def __init__(
        self,
        not_found_exc: type[Exception],
        validation_exc: type[Exception],
        base_exc: type[Exception],
    ):
        """Initialize the error handler with exception types.

        Args:
            not_found_exc: Exception to raise for 404 errors
            validation_exc: Exception to raise for 422 errors
            base_exc: Exception to raise for all other errors
        """
        self.not_found_exc = not_found_exc
        self.validation_exc = validation_exc
        self.base_exc = base_exc

    def handle(self, e: httpx.HTTPStatusError) -> NoReturn:
        """Handle HTTP status errors by raising appropriate exceptions.

        Args:
            e: The HTTP status error to handle

        Raises:
            not_found_exc: If status code is 404
            validation_exc: If status code is 422
            base_exc: For all other status codes
        """
        if e.response.status_code == 404:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except Exception:
                error_detail = e.response.text
            raise self.not_found_exc(f"Not found: {error_detail}") from e

        elif e.response.status_code == 422:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except Exception:
                error_detail = e.response.text
            raise self.validation_exc(f"Validation error: {error_detail}") from e

        else:
            raise self.base_exc(
                f"API error ({e.response.status_code}): {e.response.text}"
            ) from e
