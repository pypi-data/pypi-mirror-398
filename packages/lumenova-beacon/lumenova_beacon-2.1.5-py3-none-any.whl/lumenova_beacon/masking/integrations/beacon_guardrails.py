"""Beacon API Guardrails integration for sensitive data masking.

This module provides integration with Beacon's built-in guardrail functionality
for automatic PII detection and redaction. It is the RECOMMENDED approach for
sensitive data masking in Beacon SDK.

The Beacon Guardrails API supports:
- Automatic PII detection using Presidio (PERSON, EMAIL_ADDRESS, US_SSN, PHONE_NUMBER, etc.)
- Custom regex patterns for domain-specific sensitive data
- Multiple masking modes (TAG, REDACT, PARTIALLY_REDACT)

Usage:
    from lumenova_beacon.masking.integrations.beacon_guardrails import (
        create_beacon_masking_function,
        MaskingMode,
        PIIType
    )

    # Simple usage - inherits endpoint and api_key from BeaconClient
    masking_fn = create_beacon_masking_function(
        pii_types=[PIIType.PERSON, PIIType.EMAIL_ADDRESS, PIIType.US_SSN],
        mode=MaskingMode.TAG
    )

    client = BeaconClient(
        endpoint="https://api.beacon.ai",  # Guardrails endpoint derived as {endpoint}/guardrails
        api_key="your-api-key",            # Shared with guardrails
        masking_function=masking_fn
    )

    # Explicit endpoint (when guardrails service is at a different location)
    masking_fn = create_beacon_masking_function(
        guardrails_endpoint="https://guardrails.beacon.ai",
        api_key="your-guardrails-api-key",
        pii_types=[PIIType.PERSON, PIIType.EMAIL_ADDRESS],
        mode=MaskingMode.TAG
    )
"""

from __future__ import annotations

import json

from typing import Any

import httpx

from lumenova_beacon.core.transport import HTTPTransport
from lumenova_beacon.exceptions import (
    ConfigurationError,
    MaskingAPIError,
    MaskingNotFoundError,
    MaskingValidationError,
)
from lumenova_beacon.utils.http_errors import HTTPErrorHandler
from lumenova_beacon.masking.types import MaskingFunction, MaskingMode, PIIType


def _get_client():
    """Get the active BeaconClient."""
    from lumenova_beacon.core.client import get_client

    return get_client()


def _get_transport() -> HTTPTransport:
    """Get the HTTPTransport from the active client."""
    client = _get_client()
    transport = client.transport
    if not isinstance(transport, HTTPTransport):
        raise ConfigurationError(
            'Guardrails operations require HTTPTransport. '
            'File transport is not supported for guardrails.'
        )
    return transport


def _get_base_url() -> str:
    """Get the base URL for API requests."""
    client = _get_client()
    return client.get_base_url()


# Centralized error handler
_error_handler = HTTPErrorHandler(
    not_found_exc=MaskingNotFoundError,
    validation_exc=MaskingValidationError,
    base_exc=MaskingAPIError,
)


class BeaconGuardrailsClient:
    """Client for Beacon Guardrails API.

    This client communicates with the Beacon Guardrails REST API to perform
    server-side PII detection and masking. It reuses transport configuration
    from the active BeaconClient for consistency.

    Args:
        endpoint: The Beacon Guardrails API endpoint URL. If not provided,
            will be derived from BeaconClient's endpoint.
        api_key: Optional API key for authentication. If not provided,
            will be inherited from BeaconClient's api_key.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
    ):
        """Initialize the Beacon Guardrails client.

        Args:
            endpoint: The Beacon Guardrails API endpoint URL. If not provided,
                will be derived from BeaconClient's endpoint.
            api_key: Optional API key for authentication. If not provided,
                will be inherited from BeaconClient's api_key.
        """
        self._configured_endpoint = endpoint
        self._configured_api_key = api_key

    def mask_text(
        self,
        text: str,
        pii_types: list[PIIType] | None = None,
        custom_patterns: list[str] | None = None,
        mode: MaskingMode = MaskingMode.TAG,
    ) -> str:
        """Mask sensitive information in text using Beacon Guardrails API.

        Args:
            text: The text to mask.
            pii_types: List of PII types to detect and mask.
            custom_patterns: List of custom regex patterns to mask.
            mode: The masking mode to use.

        Returns:
            The masked text.

        Raises:
            MaskingAPIError: If the API call fails.
        """
        # Get endpoint and construct URL
        base_url = _get_base_url()
        url = f'{base_url}/api/v1/sanitize'

        # Get transport for headers, timeout, verify
        transport = _get_transport()

        payload = self._build_payload(text, pii_types, custom_patterns, mode)

        try:
            response = httpx.post(
                url,
                json=payload,
                headers=transport.headers,
                timeout=transport.timeout,
                verify=transport.verify,
            )
            response.raise_for_status()
            result = response.json()
            return result.get('masked_text', text)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.RequestError as e:
            raise MaskingAPIError(f'Failed to connect to Beacon Guardrails API: {e}') from e
        except (json.JSONDecodeError, KeyError) as e:
            raise MaskingAPIError(f'Invalid response from Beacon Guardrails API: {e}') from e

    async def mask_text_async(
        self,
        text: str,
        pii_types: list[PIIType] | None = None,
        custom_patterns: list[str] | None = None,
        mode: MaskingMode = MaskingMode.TAG,
    ) -> str:
        """Async version of mask_text.

        Args:
            text: The text to mask.
            pii_types: List of PII types to detect and mask.
            custom_patterns: List of custom regex patterns to mask.
            mode: The masking mode to use.

        Returns:
            The masked text.

        Raises:
            MaskingAPIError: If the API call fails.
        """
        # Get endpoint and construct URL
        base_url = _get_base_url()
        url = f'{base_url}/api/v1/sanitize'

        # Get transport for headers, timeout, verify
        transport = _get_transport()

        payload = self._build_payload(text, pii_types, custom_patterns, mode)

        try:
            async with httpx.AsyncClient(
                timeout=transport.timeout, verify=transport.verify
            ) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=transport.headers,
                )
                response.raise_for_status()
                result = response.json()
                return result.get('masked_text', text)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.RequestError as e:
            raise MaskingAPIError(f'Failed to connect to Beacon Guardrails API: {e}') from e
        except (json.JSONDecodeError, KeyError) as e:
            raise MaskingAPIError(f'Invalid response from Beacon Guardrails API: {e}') from e

    def _build_payload(
        self,
        text: str,
        pii_types: list[PIIType] | None,
        custom_patterns: list[str] | None,
        mode: MaskingMode,
    ) -> dict[str, Any]:
        """Build the request payload for the Guardrails API.

        Args:
            text: The text to mask.
            pii_types: List of PII types to detect.
            custom_patterns: List of custom regex patterns.
            mode: The masking mode.

        Returns:
            The request payload dictionary.
        """
        payload: dict[str, Any] = {
            'text': text,
            'mode': mode.value,
        }

        if pii_types:
            payload['pii_types'] = [pii_type.value for pii_type in pii_types]

        if custom_patterns:
            # Convert simple regex patterns to RegexFilter objects
            payload['custom_patterns'] = [
                {
                    'name': f'CUSTOM_{i}',
                    'pattern': pattern,
                    'action': 'MASK',
                    'masking_mode': mode.value,
                }
                for i, pattern in enumerate(custom_patterns)
            ]

        return payload

    def _get_endpoint(self) -> str:
        """Get the guardrails endpoint, inheriting from BeaconClient if needed."""
        endpoint = self._configured_endpoint

        if endpoint is None:
            try:
                base_url = _get_base_url()
                endpoint = f'{base_url}/guardrails'
            except Exception:
                raise ConfigurationError(
                    'Guardrails endpoint not configured. Either provide endpoint '
                    'or ensure BeaconClient is initialized with an endpoint.'
                )

        return endpoint.rstrip('/')


def create_beacon_masking_function(
    guardrails_endpoint: str | None = None,
    api_key: str | None = None,
    pii_types: list[PIIType] | None = None,
    custom_patterns: list[str] | None = None,
    mode: MaskingMode = MaskingMode.TAG,
) -> MaskingFunction:
    """Create a masking function that uses Beacon Guardrails API.

    This is the RECOMMENDED approach for sensitive data masking. The returned
    function can be passed directly to BeaconClient's masking_function parameter.

    When guardrails_endpoint and api_key are not provided, they will be inherited
    from the BeaconClient at runtime. This allows for simpler configuration where
    the same endpoint and credentials are shared between tracing and guardrails.

    Args:
        guardrails_endpoint: The Beacon Guardrails API endpoint URL. If not provided,
            will be derived from BeaconClient's endpoint by appending '/guardrails'.
        api_key: Optional API key for authentication. If not provided, will be
            inherited from BeaconClient's api_key.
        pii_types: List of PII types to detect and mask (based on Presidio entities).
            Default: [PIIType.PERSON, PIIType.EMAIL_ADDRESS, PIIType.US_SSN, PIIType.PHONE_NUMBER]
        custom_patterns: List of custom regex patterns to mask.
        mode: The masking mode to use:
            - TAG: Replace with category label (e.g., "<PERSON>")
            - REDACT: Replace with asterisks (e.g., "**** ***")
            - PARTIALLY_REDACT: Preserve structure (e.g., "J*** D**", "j***.*@e******.c**")

    Returns:
        A masking function compatible with BeaconClient.

    Example:
        >>> # Simple usage - inherits endpoint and api_key from BeaconClient
        >>> masking_fn = create_beacon_masking_function(
        ...     pii_types=[PIIType.PERSON, PIIType.EMAIL_ADDRESS],
        ...     mode=MaskingMode.TAG
        ... )
        >>> client = BeaconClient(
        ...     endpoint="https://api.beacon.ai",
        ...     api_key="your-api-key",
        ...     masking_function=masking_fn
        ... )

        >>> # Explicit endpoint
        >>> masking_fn = create_beacon_masking_function(
        ...     guardrails_endpoint="https://api.beacon.ai/guardrails",
        ...     api_key="your-api-key",
        ...     pii_types=[PIIType.PERSON, PIIType.EMAIL_ADDRESS],
        ...     mode=MaskingMode.TAG
        ... )
    """
    # Set default PII types if not specified
    if pii_types is None:
        pii_types = [PIIType.PERSON, PIIType.EMAIL_ADDRESS, PIIType.US_SSN, PIIType.PHONE_NUMBER]

    # Store configuration for lazy initialization
    _client: BeaconGuardrailsClient | None = None

    def _get_guardrails_client() -> BeaconGuardrailsClient:
        """Get or create the guardrails client."""
        nonlocal _client

        if _client is None:
            _client = BeaconGuardrailsClient(
                endpoint=guardrails_endpoint,
                api_key=api_key,
            )

        return _client

    def beacon_masking_function(value: Any) -> Any:
        """Mask sensitive data using Beacon Guardrails API.

        Args:
            value: The value to mask. Only strings are processed;
                   other types are returned unchanged.

        Returns:
            The masked value.
        """
        if not isinstance(value, str):
            return value

        # Only mask non-empty strings
        if not value.strip():
            return value

        try:
            client = _get_guardrails_client()
            return client.mask_text(
                text=value,
                pii_types=pii_types,
                custom_patterns=custom_patterns,
                mode=mode,
            )
        except Exception:
            # If API call fails, return original value to avoid blocking telemetry
            # In production, you may want to log this error
            return value

    return beacon_masking_function


__all__ = [
    'BeaconGuardrailsClient',
    'create_beacon_masking_function',
]
