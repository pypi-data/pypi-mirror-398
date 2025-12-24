"""Prompt model class with ActiveRecord-style API and utility methods."""

from __future__ import annotations

import asyncio
import logging
import re

from typing import Any

import httpx

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from lumenova_beacon.exceptions import (
    PromptCompilationError,
    PromptError,
    PromptNetworkError,
    PromptNotFoundError,
    PromptValidationError,
)
from lumenova_beacon.utils.client_helpers import get_base_url, get_transport
from lumenova_beacon.utils.http_errors import HTTPErrorHandler
from lumenova_beacon.prompts.rendering import PromptRenderer
from lumenova_beacon.prompts.types import PromptType
from lumenova_beacon.tracing.trace import get_current_span, set_pending_prompt


logger = logging.getLogger(__name__)

# Centralized error handler for prompts
_error_handler = HTTPErrorHandler(
    not_found_exc=PromptNotFoundError,
    validation_exc=PromptValidationError,
    base_exc=PromptError,
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


class Prompt:
    """Prompt model with ActiveRecord-style API and rendering utilities.

    This class represents a prompt with its content, metadata, and provides
    both class methods for fetching/creating prompts and instance methods for
    updating/deleting them.

    Examples:
        Initialize the client:
            >>> from lumenova_beacon import BeaconClient
            >>> client = BeaconClient(
            ...     endpoint="https://api.example.com",
            ...     api_key="your-key",
            ... )

        Synchronous API (simple names):
            >>> prompt = Prompt.create("greeting", template="Hello {{name}}!")
            >>> prompt = Prompt.get("greeting", label="production")
            >>> prompts = Prompt.list(search="greeting")
            >>> prompt.update(description="Updated greeting")
            >>> prompt.publish(template="Hi {{name}}!", message="More casual")

        Asynchronous API (with 'a' prefix):
            >>> prompt = await Prompt.acreate("greeting", template="Hello {{name}}!")
            >>> prompt = await Prompt.aget("greeting", label="production")
            >>> prompts = await Prompt.alist(search="greeting")
            >>> await prompt.aupdate(description="Updated greeting")
            >>> await prompt.apublish(template="Hi {{name}}!", message="More casual")

        Render template:
            >>> message = prompt.format(name="Alice")

        Convert to LangChain:
            >>> lc_prompt = prompt.to_langchain()
    """

    def __init__(
        self,
        id: str,
        name: str,
        type: str,
        version: int,
        content: dict[str, Any],
        description: str | None = None,
        tags: list[str] | None = None,
        labels: list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        commit_message: str | None = None,
        project_id: str | None = None,
    ):
        """Initialize a Prompt instance.

        Args:
            id: Prompt UUID
            name: Prompt name
            type: Prompt type ('text' or 'chat')
            version: Version number
            content: Prompt content (template or messages)
            description: Optional description
            tags: Optional list of tags
            labels: Optional list of labels
            created_at: ISO datetime string
            updated_at: ISO datetime string
            commit_message: Commit message for this version
            project_id: Project ID the prompt belongs to (set by server)
        """
        self.id = id
        self.name = name
        self.type = PromptType(type)
        self.version = version
        self._content = content
        self.description = description
        self.tags = tags or []
        self.labels = labels or []
        self.created_at = created_at
        self.updated_at = updated_at
        self.commit_message = commit_message
        self.project_id = project_id

    # ========== Properties ==========

    @property
    def template(self) -> str:
        """Get the template for text prompts.

        Returns:
            Template string with Jinja2 variables

        Raises:
            ValueError: If this is not a text prompt
        """
        if self.type != PromptType.TEXT:
            raise ValueError(f'Cannot get template for {self.type} prompt')
        return self._content.get('template', '')

    @property
    def messages(self) -> list[dict[str, str]]:
        """Get the messages for chat prompts.

        Returns:
            List of message dictionaries with role and content

        Raises:
            ValueError: If this is not a chat prompt
        """
        if self.type != PromptType.CHAT:
            raise ValueError(f'Cannot get messages for {self.type} prompt')
        return self._content.get('messages', [])

    # ========== Class Methods (Factory/Finder) ==========

    @classmethod
    @_retry_async
    async def acreate(
        cls,
        name: str,
        *,
        template: str | None = None,
        messages: list[dict[str, str]] | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        message: str | None = None,
    ) -> Prompt:
        """Create a new prompt asynchronously.

        Args:
            name: Prompt name
            template: Template string for text prompts
            messages: Messages for chat prompts
            description: Prompt description
            tags: Tags for organization
            message: Commit message

        Returns:
            Created Prompt instance

        Raises:
            PromptValidationError: If validation fails
            PromptNetworkError: If network error
            PromptError: For other errors
        """
        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                # Determine type and content
                if template is not None:
                    prompt_type = 1  # TEXT
                    content = {'template': template}
                elif messages is not None:
                    prompt_type = 2  # CHAT
                    content = {'messages': messages}
                else:
                    raise PromptValidationError('Either template or messages must be provided')

                payload: dict[str, Any] = {
                    'name': name,
                    'type': prompt_type,
                    'content': content,
                }

                if description:
                    payload['description'] = description
                if tags:
                    payload['tags'] = tags
                if message:
                    payload['commit_message'] = message

                url = f'{base_url}/api/v1/prompts/'
                response = await client.post(
                    url,
                    json=payload,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                return cls._from_dict(data)

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e
        except Exception as e:
            raise PromptError(f'Failed to create prompt: {e}') from e

    @classmethod
    def create(
        cls,
        name: str,
        *,
        template: str | None = None,
        messages: list[dict[str, str]] | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        message: str | None = None,
    ) -> Prompt:
        """Create a new prompt synchronously.

        Args:
            name: Prompt name
            template: Template string for text prompts
            messages: Messages for chat prompts
            description: Prompt description
            tags: Tags for organization
            message: Commit message

        Returns:
            Created Prompt instance
        """
        return asyncio.run(
            cls.acreate(
                name,
                template=template,
                messages=messages,
                description=description,
                tags=tags,
                message=message,
            )
        )

    @classmethod
    @_retry_async
    async def aget(
        cls,
        prompt_id: str | None = None,
        *,
        name: str | None = None,
        label: str = 'latest',
        version: int | None = None,
    ) -> Prompt:
        """Fetch a prompt asynchronously.

        Args:
            name: Prompt name (required if prompt_id not provided)
            prompt_id: Prompt ID (required if name not provided)
            label: Label to fetch (default: "latest")
            version: Specific version number

        Returns:
            Prompt instance

        Raises:
            PromptNotFoundError: If prompt not found
            PromptNetworkError: If network error
            PromptError: For other errors
        """
        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                # Determine which endpoint to use
                if prompt_id:
                    # Fetch by ID
                    url = f'{base_url}/api/v1/prompts/{prompt_id}'
                    response = await client.get(
                        url, headers=transport.headers, timeout=transport.timeout
                    )
                else:
                    # Fetch by name
                    url = f'{base_url}/api/v1/prompts/by-name'
                    payload = {'name': name}
                    response = await client.post(
                        url, json=payload, headers=transport.headers, timeout=transport.timeout
                    )

                response.raise_for_status()
                data = response.json()

                # If version is specified, fetch that specific version
                if version is not None:
                    version_url = f'{base_url}/api/v1/prompts/{data["id"]}/versions/{version}'
                    version_response = await client.get(
                        version_url, headers=transport.headers, timeout=transport.timeout
                    )
                    version_response.raise_for_status()
                    data['version'] = version_response.json()
                # If label is specified (and not version), fetch by label
                elif label:
                    label_url = f'{base_url}/api/v1/prompts/{data["id"]}/labels/{label}/version'
                    label_response = await client.get(
                        label_url, headers=transport.headers, timeout=transport.timeout
                    )
                    label_response.raise_for_status()
                    data['version'] = label_response.json()

                return cls._from_dict(data)

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e
        except Exception as e:
            raise PromptError(f'Failed to fetch prompt: {e}') from e

    @classmethod
    def get(
        cls,
        prompt_id: str | None = None,
        *,
        name: str | None = None,
        label: str = 'latest',
        version: int | None = None,
    ) -> Prompt:
        """Fetch a prompt synchronously.

        Args:
            name: Prompt name (required if prompt_id not provided)
            prompt_id: Prompt ID (required if name not provided)
            label: Label to fetch (default: "latest")
            version: Specific version number

        Returns:
            Prompt instance
        """
        return asyncio.run(
            cls.aget(prompt_id=prompt_id, name=name, label=label, version=version)
        )

    @classmethod
    @_retry_async
    async def alist(
        cls,
        *,
        page: int = 1,
        page_size: int = 10,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> list[Prompt]:
        """List prompts asynchronously.

        Args:
            page: Page number
            page_size: Items per page
            tags: Filter by tags
            search: Search query

        Returns:
            List of Prompt instances

        Raises:
            PromptNetworkError: If network error
            PromptError: For other errors
        """
        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                url = f'{base_url}/api/v1/prompts/'
                params: dict[str, Any] = {
                    'page': page,
                    'per_page': page_size,
                }

                if tags:
                    params['tags'] = tags
                if search:
                    params['search'] = search

                response = await client.get(
                    url,
                    headers=transport.headers,
                    params=params,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                # Parse each prompt
                prompts = []
                for item in data.get('data', []):
                    prompts.append(cls._from_dict(item))

                return prompts

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e
        except Exception as e:
            raise PromptError(f'Failed to list prompts: {e}') from e

    @classmethod
    def list(
        cls,
        *,
        page: int = 1,
        page_size: int = 10,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> list[Prompt]:
        """List prompts synchronously.

        Args:
            page: Page number
            page_size: Items per page
            tags: Filter by tags
            search: Search query

        Returns:
            List of Prompt instances
        """
        return asyncio.run(
            cls.alist(
                page=page, page_size=page_size, tags=tags, search=search
            )
        )

    # ========== Instance Methods (Update/Delete/Actions) ==========

    @_retry_async
    async def aupdate(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Update prompt metadata asynchronously.

        Args:
            name: New name
            description: New description
            tags: New tags

        Raises:
            PromptNotFoundError: If prompt not found
            PromptNetworkError: If network error
        """
        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                payload: dict[str, Any] = {}
                if name is not None:
                    payload['name'] = name
                    self.name = name
                if description is not None:
                    payload['description'] = description
                    self.description = description
                if tags is not None:
                    payload['tags'] = tags
                    self.tags = tags

                url = f'{base_url}/api/v1/prompts/{self.id}'
                response = await client.patch(
                    url,
                    json=payload,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e

    def update(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Update prompt metadata synchronously.

        Args:
            name: New name
            description: New description
            tags: New tags
        """
        asyncio.run(self.aupdate(name=name, description=description, tags=tags))

    @_retry_async
    async def adelete(self) -> None:
        """Delete this prompt asynchronously.

        Raises:
            PromptNotFoundError: If prompt not found
            PromptNetworkError: If network error
        """
        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                url = f'{base_url}/api/v1/prompts/{self.id}'
                response = await client.delete(
                    url, headers=transport.headers, timeout=transport.timeout
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e

    def delete(self) -> None:
        """Delete this prompt synchronously."""
        asyncio.run(self.adelete())

    @_retry_async
    async def apublish(
        self,
        *,
        template: str | None = None,
        messages: list[dict[str, str]] | None = None,
        message: str | None = None,
    ) -> Prompt:
        """Publish a new version asynchronously.

        Args:
            template: For text prompts
            messages: For chat prompts
            message: Commit message

        Returns:
            Updated Prompt instance with new version

        Raises:
            PromptValidationError: If validation fails
            PromptNetworkError: If network error
        """
        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                # Determine content
                if template is not None:
                    content = {'template': template}
                elif messages is not None:
                    content = {'messages': messages}
                else:
                    raise PromptValidationError('Either template or messages must be provided')

                payload: dict[str, Any] = {'content': content}
                if message:
                    payload['commit_message'] = message

                # Create new version
                url = f'{base_url}/api/v1/prompts/{self.id}/versions/'
                response = await client.post(
                    url,
                    json=payload,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()

                # Fetch full prompt details
                detail_url = f'{base_url}/api/v1/prompts/{self.id}'
                detail_response = await client.get(
                    detail_url, headers=transport.headers, timeout=transport.timeout
                )
                detail_response.raise_for_status()

                updated_prompt = self._from_dict(detail_response.json())

                # Update this instance
                self.version = updated_prompt.version
                self._content = updated_prompt._content
                self.commit_message = updated_prompt.commit_message

                return updated_prompt

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e
        except Exception as e:
            raise PromptError(f'Failed to publish prompt: {e}') from e

    def publish(
        self,
        *,
        template: str | None = None,
        messages: list[dict[str, str]] | None = None,
        message: str | None = None,
    ) -> Prompt:
        """Publish a new version synchronously.

        Args:
            template: For text prompts
            messages: For chat prompts
            message: Commit message

        Returns:
            Updated Prompt instance with new version
        """
        return asyncio.run(self.apublish(template=template, messages=messages, message=message))

    @_retry_async
    async def aset_label(
        self,
        label: str,
        *,
        version: int | None = None,
    ) -> None:
        """Set a label for a version asynchronously.

        Args:
            label: Label name
            version: Version number (defaults to latest)

        Raises:
            PromptNotFoundError: If prompt/version not found
            PromptNetworkError: If network error
        """
        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                # Get prompt to find version ID
                detail_url = f'{base_url}/api/v1/prompts/{self.id}'
                detail_response = await client.get(
                    detail_url, headers=transport.headers, timeout=transport.timeout
                )
                detail_response.raise_for_status()
                data = detail_response.json()

                # Find the version ID
                version_id = None
                if version is not None:
                    # Find specific version
                    for v in data.get('versions', []):
                        if v.get('version') == version:
                            version_id = v.get('id')
                            break
                else:
                    # Get latest version
                    if data.get('versions'):
                        version_id = data['versions'][0].get('id')

                if not version_id:
                    raise PromptNotFoundError(f'Version {version} not found for prompt {self.id}')

                # Create/update label
                payload = {'label': label, 'prompt_version_id': version_id}
                url = f'{base_url}/api/v1/prompts/{self.id}/labels/'
                response = await client.put(
                    url,
                    json=payload,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()

                # Update labels on this instance if it's the current version
                if version is None or version == self.version:
                    if label not in self.labels:
                        self.labels.append(label)

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e

    def set_label(
        self,
        label: str,
        *,
        version: int | None = None,
    ) -> None:
        """Set a label for a version synchronously.

        Args:
            label: Label name
            version: Version number (defaults to latest)
        """
        asyncio.run(self.aset_label(label, version=version))

    @_retry_async
    async def adelete_label(self, label: str) -> None:
        """Delete a label from this prompt asynchronously.

        Note: The 'latest' label cannot be deleted.

        Args:
            label: Label name to delete

        Raises:
            PromptValidationError: If trying to delete the 'latest' label
            PromptNotFoundError: If label not found
            PromptNetworkError: If network error
        """
        if label == 'latest':
            raise PromptValidationError("The 'latest' label cannot be deleted")

        base_url = get_base_url()
        transport = get_transport("Prompt operations")

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                url = f'{base_url}/api/v1/prompts/{self.id}/labels/{label}'
                response = await client.delete(
                    url, headers=transport.headers, timeout=transport.timeout
                )
                response.raise_for_status()

                # Remove label from this instance
                if label in self.labels:
                    self.labels.remove(label)

        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            raise PromptNetworkError(f'Network error: {e}') from e

    def delete_label(self, label: str) -> None:
        """Delete a label from this prompt synchronously.

        Note: The 'latest' label cannot be deleted.

        Args:
            label: Label name to delete
        """
        asyncio.run(self.adelete_label(label))

    # ========== Internal Methods ==========

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> Prompt:
        """Parse API response into a Prompt object.

        Args:
            data: Raw API response data

        Returns:
            Prompt instance
        """
        # Get the latest version or version by label
        version_data = None
        version_number = 1

        # Check if we have a specific version
        if 'version' in data:
            version_data = data['version']
            # Handle both 'version_number' (from prompt detail) and 'version' (from label endpoint)
            version_number = version_data.get('version_number') or version_data.get('version', 1)
        # Otherwise get the latest version
        elif 'versions' in data and data['versions']:
            # Versions are sorted by version_number descending
            version_data = data['versions'][0]
            version_number = version_data.get('version_number') or version_data.get('version', 1)

        # Extract content from version
        content = version_data.get('content', {}) if version_data else {}

        # Map API type (1=TEXT, 2=CHAT) to string
        prompt_type_map = {1: 'text', 2: 'chat'}
        prompt_type = prompt_type_map.get(data.get('type'), 'text')

        # Extract labels
        labels = [label.get('label', '') for label in data.get('labels', []) if label.get('label')]

        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            type=prompt_type,
            version=version_number,
            content=content,
            description=data.get('description'),
            tags=data.get('tags', []),
            labels=labels,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            commit_message=version_data.get('commit_message') if version_data else None,
            project_id=data.get('project_id'),
        )

    # ========== Rendering and Conversion Methods ==========

    def format(self, **kwargs: Any) -> str | list[dict[str, str]]:
        """Render the prompt with variables (convenience method).

        This is an alias for `compile()` with a more Pythonic name.

        Args:
            **kwargs: Variables to substitute in the template

        Returns:
            - For text prompts: Rendered string
            - For chat prompts: List of message dictionaries

        Raises:
            PromptCompilationError: If rendering fails

        Examples:
            >>> prompt.format(name="Alice", company="Acme")
            "Hello Alice! Welcome to Acme."
        """
        return self.compile(kwargs)

    def compile(
        self, variables: dict[str, Any], auto_link: bool = True
    ) -> str | list[dict[str, str]]:
        """Render the prompt with variable substitution.

        Uses Jinja2-style {{variable}} syntax for substitution.

        By default, automatically links this prompt to the current active span
        (if one exists) by setting prompt metadata attributes. This enables
        automatic prompt tracking in traces when using @observe decorator or
        manual span creation.

        Args:
            variables: Dictionary of variables to substitute
            auto_link: If True, automatically link prompt to current span (default: True)

        Returns:
            - For text prompts: Rendered string
            - For chat prompts: List of message dictionaries

        Raises:
            PromptCompilationError: If rendering fails or variables are missing

        Examples:
            Basic usage (auto-links to trace):
            >>> @observe()
            ... def generate():
            ...     prompt = client.get_prompt_sync("greeting")
            ...     messages = prompt.compile({"name": "Bob"})  # Auto-links!
            ...     return openai_client.chat.completions.create(
            ...         model="gpt-4o",
            ...         messages=messages
            ...     )

            Disable auto-linking:
            >>> messages = prompt.compile({"name": "Bob"}, auto_link=False)
        """
        # Automatically link to current span if enabled
        if auto_link:
            self._link_to_current_span()

        try:
            return PromptRenderer.compile_prompt(self.type, self._content, variables)
        except PromptCompilationError:
            raise
        except Exception as e:
            raise PromptCompilationError(f"Failed to compile prompt '{self.name}': {e}") from e

    def to_template(self) -> str | list[dict[str, str]]:
        """Convert Jinja2 template to Python f-string format.

        Converts {{variable}} to {variable} for use with Python f-strings.
        Works for both TEXT and CHAT prompts.

        Returns:
            - For TEXT prompts: Python-compatible template string
            - For CHAT prompts: List of messages with converted templates

        Examples:
            Text prompt:
            >>> template = prompt.to_template()
            >>> name = "Charlie"
            >>> result = eval(f'f"{template}"')

            Chat prompt:
            >>> messages = prompt.to_template()
            >>> # Returns: [{"role": "system", "content": "You are {role}"}]
        """
        return PromptRenderer.to_template(self.type, self._content)

    def to_langchain(self):
        """Convert to LangChain PromptTemplate or ChatPromptTemplate.

        Automatically attaches prompt metadata (id, name, version, labels) to the
        LangChain template. This metadata is automatically captured by
        BeaconCallbackHandler and linked to traces.

        Returns:
            - PromptTemplate for text prompts with prompt metadata
            - ChatPromptTemplate for chat prompts with prompt metadata

        Raises:
            ImportError: If langchain-core is not installed
            ValueError: If content is invalid

        Examples:
            Basic usage (metadata automatically linked to traces):
            >>> lc_prompt = prompt.to_langchain()
            >>> result = lc_prompt.format(name="Diana", company="Cloud Inc")

            Use with LangChain and BeaconCallbackHandler:
            >>> from lumenova_beacon import BeaconCallbackHandler
            >>> handler = BeaconCallbackHandler()
            >>> chain = lc_prompt | llm
            >>> # Prompt metadata automatically linked to the trace!
            >>> chain.invoke({"name": "Alice"}, config={"callbacks": [handler]})
        """
        try:
            # Prepare prompt metadata for automatic linking to traces
            prompt_metadata = {
                'beacon_prompt': {
                    'id': self.id,
                    'name': self.name,
                    'version': self.version,
                    'labels': self.labels,
                    'tags': self.tags,
                }
            }

            if self.type == PromptType.TEXT:
                from langchain_core.prompts import PromptTemplate

                # Convert {{var}} to {var} for LangChain
                lc_template = PromptRenderer.to_template_text(self.template)

                # Extract variables
                variables = re.findall(r'\{(\w+)\}', lc_template)

                lc_prompt = PromptTemplate(
                    template=lc_template,
                    input_variables=list(set(variables)),
                )
                # Attach prompt metadata for automatic trace linking
                lc_prompt.metadata = prompt_metadata
                return lc_prompt
            else:  # CHAT
                from langchain_core.prompts import ChatPromptTemplate

                # Convert messages to LangChain format
                lc_messages = []
                for msg in self.messages:
                    role = msg['role']
                    # Convert {{var}} to {var}
                    content = PromptRenderer.to_template_text(msg['content'])
                    lc_messages.append((role, content))

                lc_prompt = ChatPromptTemplate.from_messages(lc_messages)
                # Attach prompt metadata for automatic trace linking
                lc_prompt.metadata = prompt_metadata
                return lc_prompt

        except ImportError as e:
            raise ImportError(
                'LangChain integration requires langchain-core>=0.3.0. '
                'Install with: pip install langchain-core'
            ) from e

    def _link_to_current_span(self):
        """Internal method to link prompt metadata to the current active span.

        This method checks if there's an active span in the current context
        and sets prompt metadata attributes on it. It's called automatically
        by compile() and format() methods.

        Additionally, it sets a pending prompt in context so that LangChain
        LLM spans created later can pick up the prompt metadata. This handles
        the case where compile() is called and the result is used in a
        manually-created ChatPromptTemplate.
        """
        prompt_info = {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'labels': self.labels if self.labels else [],
            'tags': self.tags if self.tags else [],
        }

        try:
            # Set pending prompt for LangChain callback to pick up
            set_pending_prompt(prompt_info)

            # Also set on current span if one exists
            span = get_current_span()
            if span is not None:
                span.set_attribute('prompt.id', self.id)
                span.set_attribute('prompt.name', self.name)
                span.set_attribute('prompt.version', self.version)
                if self.labels:
                    span.set_attribute('prompt.labels', self.labels)
                if self.tags:
                    span.set_attribute('prompt.tags', self.tags)
        except Exception:
            # Silently ignore any errors to avoid breaking prompt rendering
            pass

    def link_to_span(self, span=None):
        """Manually link this prompt to a Beacon span.

        This method sets prompt metadata (id, name, version, labels, tags)
        as attributes on the specified span. If no span is provided, uses
        the current active span from the trace context.

        This is useful for manual control when you need to link a prompt
        to a span without calling compile() or when auto_link is disabled.

        Args:
            span: Span to attach metadata to (default: current span from context)

        Examples:
            Manual linking with @observe:
            >>> from lumenova_beacon import observe
            >>>
            >>> @observe()
            ... def generate_text():
            ...     prompt = client.get_prompt_sync("greeting")
            ...     prompt.link_to_span()  # Manually link to current span
            ...     # ... use prompt without compile()
            ...     return result

            Link to specific span:
            >>> span = Span(name="my-operation")
            >>> span.start()
            >>> prompt.link_to_span(span)  # Link to specific span
        """
        if span is None:
            span = get_current_span()

        if span is None:
            return  # No active span, nothing to do

        # Set prompt metadata as span attributes
        span.set_attribute('prompt.id', self.id)
        span.set_attribute('prompt.name', self.name)
        span.set_attribute('prompt.version', self.version)
        if self.labels:
            span.set_attribute('prompt.labels', self.labels)
        if self.tags:
            span.set_attribute('prompt.tags', self.tags)

    def __repr__(self) -> str:
        """String representation of the Prompt."""
        return (
            f"Prompt(id='{self.id}', name='{self.name}', "
            f"type='{self.type.value}', version={self.version})"
        )
