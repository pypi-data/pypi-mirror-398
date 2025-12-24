"""Experiment model with ActiveRecord-style API."""

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

from lumenova_beacon.datasets.types import PaginatedResponse
from lumenova_beacon.exceptions import (
    ExperimentError,
    ExperimentNotFoundError,
    ExperimentValidationError,
)
from lumenova_beacon.experiments.types import ExperimentConfig, ExperimentStatus
from lumenova_beacon.utils.client_helpers import get_base_url, get_transport
from lumenova_beacon.utils.http_errors import HTTPErrorHandler
from lumenova_beacon.utils.datetime import parse_iso_datetime

logger = logging.getLogger(__name__)


# Centralized error handler for experiments
_error_handler = HTTPErrorHandler(
    not_found_exc=ExperimentNotFoundError,
    validation_exc=ExperimentValidationError,
    base_exc=ExperimentError,
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


class Experiment:
    """Experiment model with ActiveRecord-style API.

    Experiments are batch evaluation runs that execute prompt configurations
    against dataset records.

    The API provides both sync and async methods:
    - Sync methods (simple names): Experiment.method(...) or experiment.method(...)
    - Async methods ('a' prefix): await Experiment.amethod(...) or await experiment.amethod(...)

    Examples:
        Create a new experiment with typed configs (recommended):
            >>> from lumenova_beacon import BeaconClient
            >>> from lumenova_beacon.prompts import Prompt
            >>> from lumenova_beacon.llm_configs import LLMConfig
            >>> from lumenova_beacon.experiments import Experiment, ExperimentConfig
            >>>
            >>> client = BeaconClient(...)
            >>> prompt = Prompt.get(name="greeting", label="production")
            >>> llm = LLMConfig.list()[0]
            >>>
            >>> experiment = Experiment.create(
            ...     name="Model Comparison",
            ...     dataset_id="dataset-uuid",
            ...     configurations=[
            ...         ExperimentConfig(label="A", prompt=prompt, llm_config=llm),
            ...         ExperimentConfig(label="B", prompt=prompt, llm_config=llm,
            ...                          model_parameters={"temperature": 0.9}),
            ...     ]
            ... )

        Create a new experiment (async):
            >>> experiment = await Experiment.acreate(
            ...     name="Model Comparison",
            ...     dataset_id="dataset-uuid",
            ...     configurations=[...]
            ... )

        Get an experiment by ID (sync):
            >>> experiment = Experiment.get("experiment-uuid")

        Get an experiment by ID (async):
            >>> experiment = await Experiment.aget("experiment-uuid")

        Start an experiment (sync):
            >>> experiment.start()
            >>> progress = experiment.get_progress()
            >>> print(f"Progress: {progress['progress_percentage']}%")

        Start an experiment (async):
            >>> await experiment.astart()
            >>> progress = await experiment.aget_progress()
            >>> print(f"Progress: {progress['progress_percentage']}%")

        Cancel a running experiment (sync):
            >>> experiment.cancel()

        Cancel a running experiment (async):
            >>> await experiment.acancel()

        Get associated datasets (sync):
            >>> source_dataset = experiment.get_dataset()
            >>> print(f"Source: {source_dataset.name}")
            >>>
            >>> if experiment.status == ExperimentStatus.COMPLETED:
            ...     result_dataset = experiment.get_result_dataset()
            ...     if result_dataset:
            ...         records, _ = result_dataset.list_records()

        Get associated datasets (async):
            >>> source_dataset = await experiment.aget_dataset()
            >>> print(f"Source: {source_dataset.name}")
            >>>
            >>> if experiment.status == ExperimentStatus.COMPLETED:
            ...     result_dataset = await experiment.aget_result_dataset()
            ...     if result_dataset:
            ...         records, _ = await result_dataset.alist_records()

        List all experiments (sync):
            >>> experiments, pagination = Experiment.list(page=1, page_size=20)

        List all experiments (async):
            >>> experiments, pagination = await Experiment.alist(page=1, page_size=20)

        Filter by status (sync):
            >>> running_experiments, _ = Experiment.list(status=ExperimentStatus.RUNNING)

        Filter by status (async):
            >>> running_experiments, _ = await Experiment.alist(status=ExperimentStatus.RUNNING)
    """

    def __init__(
        self,
        id: str,
        name: str,
        dataset_id: str,
        status: int,
        created_at: datetime,
        description: str | None = None,
        variable_mappings: dict[str, Any] | None = None,
        result_dataset_id: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        updated_at: datetime | None = None,
        dataset_name: str | None = None,
        record_count: int = 0,
        configuration_count: int = 0,
        project_id: str | None = None,
    ):
        """Initialize an Experiment instance.

        Args:
            id: Experiment UUID
            name: Name of the experiment
            dataset_id: Dataset ID
            status: Experiment status (1=DRAFT, 2=QUEUED, 3=RUNNING, 4=COMPLETED, 5=FAILED, 6=CANCELLED)
            created_at: Creation timestamp
            description: Optional description
            variable_mappings: Global variable mappings (maps prompt variables to dataset fields)
            result_dataset_id: Result dataset ID (populated after completion)
            started_at: Timestamp when experiment started
            completed_at: Timestamp when experiment completed
            updated_at: Last update timestamp
            dataset_name: Name of the source dataset
            record_count: Number of records in the dataset
            configuration_count: Number of prompt configurations
            project_id: Project ID the experiment belongs to (set by server)
        """
        self.id = id
        self.name = name
        self.description = description
        self.variable_mappings = variable_mappings or {}
        self.dataset_id = dataset_id
        self.result_dataset_id = result_dataset_id
        self.status = ExperimentStatus(status)
        self.started_at = started_at
        self.completed_at = completed_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.dataset_name = dataset_name
        self.record_count = record_count
        self.configuration_count = configuration_count
        self.project_id = project_id

    # === Async Methods ===

    @classmethod
    @_retry_async
    async def aget(cls, experiment_id: str) -> "Experiment":
        """Get a single experiment by ID (async).

        Args:
            experiment_id: UUID of the experiment

        Returns:
            Experiment instance with configurations

        Raises:
            ExperimentNotFoundError: If experiment not found
            ExperimentError: If fetch fails
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments/{experiment_id}"

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
            raise ExperimentError(f"Failed to fetch experiment: {e}")

    @classmethod
    @_retry_async
    async def acreate(
        cls,
        name: str,
        dataset_id: str,
        configurations: list[dict[str, Any] | ExperimentConfig],
        description: str | None = None,
        variable_mappings: dict[str, Any] | None = None,
    ) -> "Experiment":
        """Create a new experiment (async).

        The experiment is created in DRAFT status. Use the astart() method to begin execution.

        The experiment will be created in the project specified by the active BeaconClient.

        Args:
            name: Name of the experiment
            dataset_id: Dataset ID to run experiment on
            configurations: List of prompt configurations to test. Can be either:
                - ExperimentConfig objects (recommended): Type-safe configs using Prompt and LLMConfig
                - Raw dicts: With keys 'label', 'prompt_content', 'model_config_id', 'model_parameters'
            description: Optional description
            variable_mappings: Global variable mappings (maps prompt variables to dataset fields)

        Returns:
            Created Experiment instance

        Raises:
            ExperimentValidationError: If validation fails
            ExperimentError: If creation fails

        Example:
            Using ExperimentConfig (recommended):
                >>> from lumenova_beacon.prompts import Prompt
                >>> from lumenova_beacon.llm_configs import LLMConfig
                >>> from lumenova_beacon.experiments import Experiment, ExperimentConfig
                >>>
                >>> prompt = Prompt.get(name="greeting", label="production")
                >>> llm = LLMConfig.list()[0]
                >>>
                >>> experiment = await Experiment.acreate(
                ...     name="Model Comparison",
                ...     dataset_id="dataset-uuid",
                ...     configurations=[
                ...         ExperimentConfig(label="A", prompt=prompt, llm_config=llm),
                ...         ExperimentConfig(label="B", prompt=prompt, llm_config=llm,
                ...                          model_parameters={"temperature": 0.9}),
                ...     ]
                ... )
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments"

        # Convert ExperimentConfig objects to dicts
        config_dicts = [
            cfg.to_dict() if isinstance(cfg, ExperimentConfig) else cfg
            for cfg in configurations
        ]

        payload: dict[str, Any] = {
            "name": name,
            "dataset_id": dataset_id,
            "configurations": config_dicts,
        }
        if description is not None:
            payload["description"] = description
        if variable_mappings is not None:
            payload["variable_mappings"] = variable_mappings

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                logger.debug(f"Created experiment: {data['id']}")
                return cls._from_dict(data)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise ExperimentError(f"Failed to create experiment: {e}")

    @classmethod
    @_retry_async
    async def alist(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: ExperimentStatus | int | None = None,
    ) -> tuple[list["Experiment"], PaginatedResponse]:
        """List all experiments with pagination and filtering (async).

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            search: Optional search query for name/description
            status: Filter by status (ExperimentStatus enum or int)

        Returns:
            Tuple of (list of experiments, pagination metadata)

        Raises:
            ExperimentError: If listing fails
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments"

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if search:
            params["search"] = search
        if status is not None:
            # Convert ExperimentStatus enum to int if needed
            params["status"] = int(status) if isinstance(status, ExperimentStatus) else status

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.get(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                experiments = [cls._from_dict(item) for item in data["items"]]
                pagination = PaginatedResponse(
                    total=data["total"],
                    page=data["page"],
                    page_size=data["page_size"],
                    total_pages=data["total_pages"],
                )

                return experiments, pagination
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise ExperimentError(f"Failed to list experiments: {e}")

    @_retry_async
    async def astart(self) -> "Experiment":
        """Start executing this experiment (async).

        This will:
        1. Update status to QUEUED
        2. Enqueue the experiment for execution via ARQ workers
        3. Process all configurations against all dataset records
        4. Create a result dataset when complete

        Returns:
            Updated Experiment instance

        Raises:
            ExperimentError: If starting fails
            ExperimentNotFoundError: If experiment not found
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments/{self.id}/start"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.post(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                # Update this instance with the response
                self.status = ExperimentStatus(data["status"])
                if data.get("started_at"):
                    self.started_at = parse_iso_datetime(data["started_at"])
                if data.get("updated_at"):
                    self.updated_at = parse_iso_datetime(data["updated_at"])

                logger.debug(f"Started experiment: {self.id}")
                return self
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise ExperimentError(f"Failed to start experiment: {e}")

    @_retry_async
    async def acancel(self) -> "Experiment":
        """Cancel this running or queued experiment (async).

        Already completed runs will not be rolled back.

        Returns:
            Updated Experiment instance

        Raises:
            ExperimentError: If cancellation fails
            ExperimentNotFoundError: If experiment not found
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments/{self.id}/cancel"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.post(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                # Update this instance with the response
                self.status = ExperimentStatus(data["status"])
                if data.get("completed_at"):
                    self.completed_at = parse_iso_datetime(data["completed_at"])
                if data.get("updated_at"):
                    self.updated_at = parse_iso_datetime(data["updated_at"])

                logger.debug(f"Cancelled experiment: {self.id}")
                return self
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise ExperimentError(f"Failed to cancel experiment: {e}")

    @_retry_async
    async def aupdate(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Update experiment metadata asynchronously.

        Args:
            name: New name for the experiment
            description: New description

        Raises:
            ExperimentNotFoundError: If experiment not found
            ExperimentError: If update fails
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments/{self.id}"

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description

        if not payload:
            return  # Nothing to update

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.patch(
                    url,
                    json=payload,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()

                # Update local instance
                if name is not None:
                    self.name = name
                if description is not None:
                    self.description = description

                logger.debug(f"Updated experiment: {self.id}")
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise ExperimentError(f"Failed to update experiment: {e}")

    @_retry_async
    async def adelete(self) -> None:
        """Delete this experiment asynchronously.

        Raises:
            ExperimentNotFoundError: If experiment not found
            ExperimentError: If deletion fails
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments/{self.id}"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.delete(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                logger.debug(f"Deleted experiment: {self.id}")
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise ExperimentError(f"Failed to delete experiment: {e}")

    @_retry_async
    async def aget_progress(self) -> dict[str, Any]:
        """Get real-time execution progress for this experiment (async).

        Returns:
            Dictionary with progress information:
            - experiment_id: Experiment UUID
            - total_records: Total records in the dataset
            - total_configurations: Total configurations
            - total_runs: Total runs (records × configurations)
            - completed_runs: Number of completed runs
            - failed_runs: Number of failed runs
            - progress_percent: Progress percentage (0-100)

        Raises:
            ExperimentError: If fetching progress fails
            ExperimentNotFoundError: If experiment not found
        """
        base_url = get_base_url()
        transport = get_transport("Experiment operations")
        url = f"{base_url}/api/v1/experiments/{self.id}/progress"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.get(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise ExperimentError(f"Failed to get experiment progress: {e}")

    async def aget_dataset(self):
        """Get the source Dataset instance for this experiment (async).

        Returns:
            Dataset instance for the source dataset

        Raises:
            ExperimentError: If fetching dataset fails
            DatasetNotFoundError: If dataset not found
        """
        from lumenova_beacon.datasets import Dataset

        try:
            return await Dataset.aget(self.dataset_id)
        except Exception as e:
            raise ExperimentError(f"Failed to get source dataset: {e}") from e

    async def aget_result_dataset(self):
        """Get the result Dataset instance for this experiment (async).

        Returns:
            Dataset instance for the result dataset, or None if not yet completed

        Raises:
            ExperimentError: If fetching dataset fails
            DatasetNotFoundError: If dataset not found
        """
        if self.result_dataset_id is None:
            return None

        from lumenova_beacon.datasets import Dataset

        try:
            return await Dataset.aget(self.result_dataset_id)
        except Exception as e:
            raise ExperimentError(f"Failed to get result dataset: {e}") from e

    # === Sync Methods ===

    @classmethod
    def get(cls, experiment_id: str) -> "Experiment":
        """Get a single experiment by ID.

        Args:
            experiment_id: UUID of the experiment

        Returns:
            Experiment instance with configurations

        Raises:
            ExperimentNotFoundError: If experiment not found
            ExperimentError: If fetch fails
        """
        return asyncio.run(cls.aget(experiment_id))

    @classmethod
    def create(
        cls,
        name: str,
        dataset_id: str,
        configurations: list[dict[str, Any] | ExperimentConfig],
        description: str | None = None,
        variable_mappings: dict[str, Any] | None = None,
    ) -> "Experiment":
        """Create a new experiment.

        The experiment is created in DRAFT status. Use the start() method to begin execution.

        The experiment will be created in the project specified by the active BeaconClient.

        Args:
            name: Name of the experiment
            dataset_id: Dataset ID to run experiment on
            configurations: List of prompt configurations to test. Can be either:
                - ExperimentConfig objects (recommended): Type-safe configs using Prompt and LLMConfig
                - Raw dicts: With keys 'label', 'prompt_content', 'model_config_id', 'model_parameters'
            description: Optional description
            variable_mappings: Global variable mappings (maps prompt variables to dataset fields)

        Returns:
            Created Experiment instance

        Raises:
            ExperimentValidationError: If validation fails
            ExperimentError: If creation fails

        Example:
            Using ExperimentConfig (recommended):
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
                ...         ExperimentConfig(label="B", prompt=prompt, llm_config=llm,
                ...                          model_parameters={"temperature": 0.9}),
                ...     ]
                ... )
        """
        return asyncio.run(
            cls.acreate(
                name=name,
                dataset_id=dataset_id,
                configurations=configurations,
                description=description,
                variable_mappings=variable_mappings,
            )
        )

    @classmethod
    def list(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: ExperimentStatus | int | None = None,
    ) -> tuple[list["Experiment"], PaginatedResponse]:
        """List all experiments with pagination and filtering.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            search: Optional search query for name/description
            status: Filter by status (ExperimentStatus enum or int)

        Returns:
            Tuple of (list of experiments, pagination metadata)

        Raises:
            ExperimentError: If listing fails
        """
        return asyncio.run(
            cls.alist(
                page=page,
                page_size=page_size,
                search=search,
                status=status,
            )
        )

    def start(self) -> "Experiment":
        """Start executing this experiment.

        This will:
        1. Update status to QUEUED
        2. Enqueue the experiment for execution via ARQ workers
        3. Process all configurations against all dataset records
        4. Create a result dataset when complete

        Returns:
            Updated Experiment instance

        Raises:
            ExperimentError: If starting fails
            ExperimentNotFoundError: If experiment not found

        Example:
            >>> experiment = Experiment.get("experiment-uuid")
            >>> experiment.start()
            >>> print(experiment.status)  # ExperimentStatus.QUEUED
        """
        return asyncio.run(self.astart())

    def cancel(self) -> "Experiment":
        """Cancel this running or queued experiment.

        Already completed runs will not be rolled back.

        Returns:
            Updated Experiment instance

        Raises:
            ExperimentError: If cancellation fails
            ExperimentNotFoundError: If experiment not found

        Example:
            >>> experiment = Experiment.get("experiment-uuid")
            >>> experiment.cancel()
            >>> print(experiment.status)  # ExperimentStatus.CANCELLED
        """
        return asyncio.run(self.acancel())

    def update(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Update experiment metadata.

        Args:
            name: New name for the experiment
            description: New description

        Raises:
            ExperimentNotFoundError: If experiment not found
            ExperimentError: If update fails

        Example:
            >>> experiment = Experiment.get("experiment-uuid")
            >>> experiment.update(name="New Name", description="Updated description")
        """
        asyncio.run(self.aupdate(name=name, description=description))

    def delete(self) -> None:
        """Delete this experiment.

        Raises:
            ExperimentNotFoundError: If experiment not found
            ExperimentError: If deletion fails

        Example:
            >>> experiment = Experiment.get("experiment-uuid")
            >>> experiment.delete()
        """
        asyncio.run(self.adelete())

    def get_progress(self) -> dict[str, Any]:
        """Get real-time execution progress for this experiment.

        Returns:
            Dictionary with progress information:
            - experiment_id: Experiment UUID
            - total_records: Total records in the dataset
            - total_configurations: Total configurations
            - total_runs: Total runs (records × configurations)
            - completed_runs: Number of completed runs
            - failed_runs: Number of failed runs
            - progress_percent: Progress percentage (0-100)

        Raises:
            ExperimentError: If fetching progress fails
            ExperimentNotFoundError: If experiment not found

        Example:
            >>> experiment = Experiment.get("experiment-uuid")
            >>> progress = experiment.get_progress()
            >>> print(f"Progress: {progress['progress_percent']}%")
            >>> print(f"Completed: {progress['completed_runs']}/{progress['total_runs']}")
        """
        return asyncio.run(self.aget_progress())

    def get_dataset(self):
        """Get the source Dataset instance for this experiment.

        Returns:
            Dataset instance for the source dataset

        Raises:
            ExperimentError: If fetching dataset fails
            DatasetNotFoundError: If dataset not found

        Example:
            >>> experiment = Experiment.get("experiment-uuid")
            >>> dataset = experiment.get_dataset()
            >>> print(f"Source dataset: {dataset.name}")
            >>> records, _ = dataset.list_records()
        """
        return asyncio.run(self.aget_dataset())

    def get_result_dataset(self):
        """Get the result Dataset instance for this experiment.

        Returns:
            Dataset instance for the result dataset, or None if not yet completed

        Raises:
            ExperimentError: If fetching dataset fails
            DatasetNotFoundError: If dataset not found

        Example:
            >>> experiment = Experiment.get("experiment-uuid")
            >>> if experiment.status == ExperimentStatus.COMPLETED:
            ...     result_dataset = experiment.get_result_dataset()
            ...     if result_dataset:
            ...         print(f"Results: {result_dataset.name}")
            ...         records, _ = result_dataset.list_records()
        """
        return asyncio.run(self.aget_result_dataset())

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Experiment":
        """Create an Experiment instance from API response data."""
        created_at = parse_iso_datetime(data["created_at"])

        started_at = None
        if data.get("started_at"):
            started_at = parse_iso_datetime(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = parse_iso_datetime(data["completed_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = parse_iso_datetime(data["updated_at"])

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            variable_mappings=data.get("variable_mappings"),
            dataset_id=data["dataset_id"],
            result_dataset_id=data.get("result_dataset_id"),
            status=data["status"],
            started_at=started_at,
            completed_at=completed_at,
            created_at=created_at,
            updated_at=updated_at,
            dataset_name=data.get("dataset_name"),
            record_count=data.get("record_count", 0),
            configuration_count=data.get("configuration_count", 0),
            project_id=data.get("project_id"),
        )

    def __repr__(self) -> str:
        return (
            f"Experiment(id={self.id!r}, name={self.name!r}, "
            f"status={self.status.name}, record_count={self.record_count})"
        )
