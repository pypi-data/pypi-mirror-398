"""LLMConfig model with ActiveRecord-style API."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from lumenova_beacon.exceptions import (
    LLMConfigError,
    LLMConfigNotFoundError,
)
from lumenova_beacon.llm_configs.types import UserBasicInfo
from lumenova_beacon.utils.client_helpers import get_base_url, get_transport
from lumenova_beacon.utils.datetime import parse_iso_datetime
from lumenova_beacon.utils.http_errors import HTTPErrorHandler

logger = logging.getLogger(__name__)


# Centralized error handler for LLM configs
_error_handler = HTTPErrorHandler(
    not_found_exc=LLMConfigNotFoundError,
    validation_exc=LLMConfigError,  # No specific validation error for read-only resource
    base_exc=LLMConfigError,
)

# Retry decorator for async functions
_retry_async = retry(
    retry=retry_if_exception_type(
        (httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError)
    ),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)


async def _aget_project_id() -> str:
    """Get the project ID from the API.

    For project-scoped API keys, GET /api/v1/projects returns
    only the project the key has access to.

    Returns:
        The project ID string

    Raises:
        LLMConfigError: If no accessible projects found or request fails
    """
    base_url = get_base_url()
    transport = get_transport("LLM config operations")
    url = f"{base_url}/api/v1/projects"

    try:
        async with httpx.AsyncClient(verify=transport.verify) as client:
            response = await client.get(
                url,
                headers=transport.headers,
                timeout=transport.timeout,
            )
            response.raise_for_status()
            projects = response.json()

            if not projects:
                raise LLMConfigError("No accessible projects found for this API key")

            return projects[0]["id"]
    except httpx.HTTPError as e:
        raise LLMConfigError(f"Failed to get project ID: {e}")


class LLMConfig:
    """LLM configuration model with ActiveRecord-style API.

    LLM configurations define the model provider, model name, and default parameters
    for LLM calls. These are read-only from the SDK - they are managed via the web UI.

    The API provides both sync and async methods:
    - Sync methods (simple names): LLMConfig.method(...)
    - Async methods ('a' prefix): await LLMConfig.amethod(...)

    Examples:
        List all LLM configs (sync):
            >>> configs = LLMConfig.list()
            >>> for cfg in configs:
            ...     print(f"{cfg.name}: {cfg.provider}/{cfg.litellm_model}")

        List all LLM configs (async):
            >>> configs = await LLMConfig.alist()

        Get a specific config by ID (sync):
            >>> config = LLMConfig.get("config-uuid")

        Get a specific config by ID (async):
            >>> config = await LLMConfig.aget("config-uuid")

        Use with experiments:
            >>> from lumenova_beacon.prompts import Prompt
            >>> from lumenova_beacon.llm_configs import LLMConfig
            >>>
            >>> prompt = Prompt.get(name="greeting", label="production")
            >>> llm = LLMConfig.list()[0]
            >>>
            >>> experiment = Experiment.create(
            ...     name="Test",
            ...     dataset_id="...",
            ...     configurations=[
            ...         ExperimentConfig(
            ...             label="A",
            ...             prompt=prompt,
            ...             llm_config=llm,
            ...         )
            ...     ]
            ... )
    """

    def __init__(
        self,
        id: str,
        name: str,
        provider: str,
        litellm_model: str,
        max_tokens: int,
        temperature: float,
        is_active: bool,
        has_api_key: bool,
        project_id: str | None = None,
        api_base: str | None = None,
        config: dict[str, Any] | None = None,
        created_by: str | None = None,
        created_by_user: UserBasicInfo | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize an LLMConfig instance.

        Args:
            id: Configuration ID (UUID)
            name: Configuration name (e.g., "GPT-4o", "Claude 3.5 Sonnet")
            provider: LLM provider (e.g., "openai", "anthropic")
            litellm_model: LiteLLM model identifier (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation (0.0-1.0)
            is_active: Whether this configuration is active
            has_api_key: Whether an API key is configured
            project_id: Project ID (set by server)
            api_base: Custom API base URL (optional)
            config: Additional configuration parameters
            created_by: User ID who created the config
            created_by_user: Creator user details
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.name = name
        self.provider = provider
        self.litellm_model = litellm_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.is_active = is_active
        self.has_api_key = has_api_key
        self.project_id = project_id
        self.api_base = api_base
        self.config = config or {}
        self.created_by = created_by
        self.created_by_user = created_by_user
        self.created_at = created_at
        self.updated_at = updated_at

    # === Async Methods ===

    @classmethod
    async def aget(cls, config_id: str) -> "LLMConfig":
        """Load an LLM configuration from the server by ID (async).

        Args:
            config_id: UUID of the LLM configuration

        Returns:
            LLMConfig instance

        Raises:
            LLMConfigNotFoundError: If configuration not found
            LLMConfigError: If fetch fails
        """
        # Get project_id first (required for the endpoint)
        project_id = await _aget_project_id()

        base_url = get_base_url()
        transport = get_transport("LLM config operations")
        url = f"{base_url}/api/v1/projects/{project_id}/llm-configs/{config_id}"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.get(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                return cls._from_dict(data)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise LLMConfigError(f"Failed to fetch LLM config: {e}")

    @classmethod
    async def alist(
        cls,
        active_only: bool = True,
    ) -> list["LLMConfig"]:
        """List all LLM configurations (async).

        Args:
            active_only: If True (default), only return active configurations

        Returns:
            List of LLMConfig instances

        Raises:
            LLMConfigError: If listing fails
        """
        # Get project_id first (required for the endpoint)
        project_id = await _aget_project_id()

        base_url = get_base_url()
        transport = get_transport("LLM config operations")
        url = f"{base_url}/api/v1/projects/{project_id}/llm-configs"

        params: dict[str, Any] = {}
        if active_only:
            params["is_active"] = True

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.get(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                    params=params if params else None,
                )
                response.raise_for_status()
                data = response.json()

                # API returns a list directly
                return [cls._from_dict(cfg) for cfg in data]
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise LLMConfigError(f"Failed to list LLM configs: {e}")

    # === Sync Methods ===

    @classmethod
    def get(cls, config_id: str) -> "LLMConfig":
        """Load an LLM configuration from the server by ID.

        Args:
            config_id: UUID of the LLM configuration

        Returns:
            LLMConfig instance

        Raises:
            LLMConfigNotFoundError: If configuration not found
            LLMConfigError: If fetch fails
        """
        return asyncio.run(cls.aget(config_id=config_id))

    @classmethod
    def list(
        cls,
        active_only: bool = True,
    ) -> list["LLMConfig"]:
        """List all LLM configurations.

        Args:
            active_only: If True (default), only return active configurations

        Returns:
            List of LLMConfig instances

        Raises:
            LLMConfigError: If listing fails
        """
        return asyncio.run(cls.alist(active_only=active_only))

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "LLMConfig":
        """Create an LLMConfig instance from API response data."""
        created_at = None
        if data.get("created_at"):
            created_at = parse_iso_datetime(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = parse_iso_datetime(data["updated_at"])

        created_by_user = None
        if data.get("created_by_user"):
            user_data = data["created_by_user"]
            created_by_user = UserBasicInfo(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("name"),
            )

        return cls(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            litellm_model=data["litellm_model"],
            max_tokens=data["max_tokens"],
            temperature=data["temperature"],
            is_active=data["is_active"],
            has_api_key=data["has_api_key"],
            project_id=data.get("project_id"),
            api_base=data.get("api_base"),
            config=data.get("config", {}),
            created_by=data.get("created_by"),
            created_by_user=created_by_user,
            created_at=created_at,
            updated_at=updated_at,
        )

    def __repr__(self) -> str:
        return (
            f"LLMConfig(id={self.id!r}, name={self.name!r}, "
            f"provider={self.provider!r}, model={self.litellm_model!r})"
        )
