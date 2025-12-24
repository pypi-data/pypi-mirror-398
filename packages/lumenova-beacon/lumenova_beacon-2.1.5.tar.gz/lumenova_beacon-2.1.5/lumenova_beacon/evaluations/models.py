"""Evaluation models with ActiveRecord-style API."""

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
    EvaluationError,
    EvaluationNotFoundError,
    EvaluationValidationError,
)
from lumenova_beacon.evaluations.types import EvaluationRunStatus
from lumenova_beacon.utils.client_helpers import get_base_url, get_transport
from lumenova_beacon.utils.datetime import parse_iso_datetime
from lumenova_beacon.utils.http_errors import HTTPErrorHandler


logger = logging.getLogger(__name__)

# Centralized error handler for evaluations
_error_handler = HTTPErrorHandler(
    not_found_exc=EvaluationNotFoundError,
    validation_exc=EvaluationValidationError,
    base_exc=EvaluationError,
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


class Evaluation:
    """Evaluation model with ActiveRecord-style API.

    Evaluations define how an evaluator should be applied to traces or dataset records.
    They can be trace-based (with filter rules) or dataset-based.

    The API provides both sync and async methods:
    - Sync methods (simple names): Evaluation.method(...) or evaluation.method(...)
    - Async methods ('a' prefix): await Evaluation.amethod(...) or await evaluation.amethod(...)

    Examples:
        Create a trace-based evaluation (sync):
            >>> from lumenova_beacon import BeaconClient
            >>> client = BeaconClient(...)
            >>> evaluation = Evaluation.create(
            ...     name="Answer Accuracy",
            ...     evaluator_id="evaluator-uuid",
            ...     variable_mappings={"question": "span.input", "answer": "span.output"},
            ...     filter_rules={"logic": "AND", "rules": []},
            ...     active=True
            ... )

        Create a dataset-based evaluation (async):
            >>> evaluation = await Evaluation.acreate(
            ...     name="Dataset Evaluation",
            ...     evaluator_id="evaluator-uuid",
            ...     variable_mappings={"question": "input", "answer": "output"},
            ...     dataset_id="dataset-uuid"
            ... )

        Get an evaluation by ID (sync):
            >>> evaluation = Evaluation.get("evaluation-uuid")

        Get an evaluation by ID (async):
            >>> evaluation = await Evaluation.aget("evaluation-uuid")

        Run evaluation on a single trace (sync):
            >>> run = evaluation.run(trace_id="trace-123")
            >>> print(f"Run status: {run.status}")

        Run evaluation on a single trace (async):
            >>> run = await evaluation.arun(trace_id="trace-123")

        Execute evaluation on all matching traces/records (sync):
            >>> result = evaluation.execute()
            >>> print(f"Created {result['runs_created']} runs")

        Execute evaluation on all matching traces/records (async):
            >>> result = await evaluation.aexecute()

        List evaluations (sync):
            >>> evaluations, pagination = Evaluation.list(page=1, page_size=20)

        List evaluations (async):
            >>> evaluations, pagination = await Evaluation.alist(page=1, page_size=20)

        List runs for this evaluation (sync):
            >>> runs, pagination = evaluation.list_runs()

        List runs for this evaluation (async):
            >>> runs, pagination = await evaluation.alist_runs()
    """

    def __init__(
        self,
        id: str,
        name: str,
        evaluator_id: str | None,
        variable_mappings: dict[str, str],
        active: bool,
        filter_rules: dict[str, Any] | None,
        dataset_id: str | None,
        result_dataset_id: str | None,
        description: str | None = None,
        project_id: str | None = None,
        score_type: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        statistics: dict[str, Any] | None = None,
        evaluator: dict[str, Any] | None = None,
    ):
        """Initialize an Evaluation instance.

        Args:
            id: Evaluation UUID
            name: Evaluation name
            evaluator_id: Evaluator UUID (None if evaluator was deleted)
            variable_mappings: Variable mappings dict
            active: Whether auto-run on new traces (trace evals only)
            filter_rules: Filter rules for trace-based evaluations
            dataset_id: Dataset ID for dataset-based evaluations
            result_dataset_id: Result dataset ID (for merging results)
            description: Optional description
            project_id: Project ID (read-only, inferred from API key)
            score_type: Score type snapshot ('percent', 'numeric', 'categorical')
            created_at: Creation timestamp
            updated_at: Last update timestamp
            statistics: Optional statistics (if include_statistics=true)
            evaluator: Optional evaluator data (if include_evaluator=true)
        """
        self.id = id
        self.name = name
        self.evaluator_id = evaluator_id
        self.variable_mappings = variable_mappings
        self.active = active
        self.filter_rules = filter_rules
        self.dataset_id = dataset_id
        self.result_dataset_id = result_dataset_id
        self.description = description
        self.project_id = project_id
        self.score_type = score_type
        self.created_at = created_at
        self.updated_at = updated_at
        self.statistics = statistics
        self.evaluator = evaluator

    # === Async Methods ===

    @classmethod
    @_retry_async
    async def aget(
        cls,
        evaluation_id: str,
        include_evaluator: bool = False,
        include_statistics: bool = False,
    ) -> "Evaluation":
        """Get a single evaluation by ID (async).

        Args:
            evaluation_id: UUID of the evaluation
            include_evaluator: Include evaluator data in response
            include_statistics: Include statistics in response

        Returns:
            Evaluation instance

        Raises:
            EvaluationNotFoundError: If evaluation not found
            EvaluationError: If fetch fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations/{evaluation_id}"

        params = {
            "include_evaluator": include_evaluator,
            "include_statistics": include_statistics,
        }

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

                return cls._from_dict(data)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to fetch evaluation: {e}")

    @classmethod
    @_retry_async
    async def acreate(
        cls,
        name: str,
        evaluator_id: str,
        variable_mappings: dict[str, str],
        filter_rules: dict[str, Any] | None = None,
        dataset_id: str | None = None,
        result_dataset_id: str | None = None,
        active: bool = False,
        description: str | None = None,
    ) -> "Evaluation":
        """Create a new evaluation (async).

        Either filter_rules OR dataset_id must be provided, but not both.
        - filter_rules: For trace-based evaluations (can be active=True)
        - dataset_id: For dataset-based evaluations (must be active=False)

        Args:
            name: Evaluation name
            evaluator_id: UUID of the evaluator to use
            variable_mappings: Variable mappings (e.g., {"question": "span.input"})
            filter_rules: Filter rules for trace-based evaluations
            dataset_id: Dataset ID for dataset-based evaluations
            result_dataset_id: Optional result dataset ID
            active: Auto-run on new traces (trace evals only)
            description: Optional description

        Returns:
            Created Evaluation instance

        Raises:
            EvaluationValidationError: If validation fails
            EvaluationError: If creation fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations"

        payload: dict[str, Any] = {
            "name": name,
            "evaluator_id": evaluator_id,
            "variable_mappings": variable_mappings,
            "active": active,
        }

        if filter_rules is not None:
            payload["filter_rules"] = filter_rules
        if dataset_id is not None:
            payload["dataset_id"] = dataset_id
        if result_dataset_id is not None:
            payload["result_dataset_id"] = result_dataset_id
        if description is not None:
            payload["description"] = description

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

                logger.debug(f"Created evaluation: {data['id']}")
                return cls._from_dict(data)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to create evaluation: {e}")

    @classmethod
    @_retry_async
    async def alist(
        cls,
        page: int = 1,
        page_size: int = 20,
        evaluator_id: str | None = None,
        search: str | None = None,
        include_evaluator: bool = False,
        include_statistics: bool = False,
    ) -> tuple[list["Evaluation"], PaginatedResponse]:
        """List all evaluations with pagination and filtering (async).

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            evaluator_id: Filter by evaluator ID
            search: Optional search query
            include_evaluator: Include evaluator data in responses
            include_statistics: Include statistics in responses

        Returns:
            Tuple of (list of evaluations, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations"

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "include_evaluator": include_evaluator,
            "include_statistics": include_statistics,
        }
        if evaluator_id:
            params["evaluator_id"] = evaluator_id
        if search:
            params["search"] = search

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

                evaluations = [cls._from_dict(item) for item in data["evaluations"]]
                pagination = PaginatedResponse(
                    total=data["total"],
                    page=data["page"],
                    page_size=data["page_size"],
                    total_pages=data["total_pages"],
                )

                return evaluations, pagination
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to list evaluations: {e}")

    @_retry_async
    async def aupdate(
        self,
        name: str | None = None,
        description: str | None = None,
        active: bool | None = None,
        variable_mappings: dict[str, str] | None = None,
        filter_rules: dict[str, Any] | None = None,
        dataset_id: str | None = None,
        result_dataset_id: str | None = None,
    ) -> "Evaluation":
        """Update this evaluation (async).

        Only provided fields will be updated.

        Args:
            name: New name
            description: New description
            active: New active status
            variable_mappings: New variable mappings
            filter_rules: New filter rules
            dataset_id: New dataset ID
            result_dataset_id: New result dataset ID

        Returns:
            Updated Evaluation instance

        Raises:
            EvaluationError: If update fails
            EvaluationNotFoundError: If evaluation not found
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations/{self.id}"

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if active is not None:
            payload["active"] = active
        if variable_mappings is not None:
            payload["variable_mappings"] = variable_mappings
        if filter_rules is not None:
            payload["filter_rules"] = filter_rules
        if dataset_id is not None:
            payload["dataset_id"] = dataset_id
        if result_dataset_id is not None:
            payload["result_dataset_id"] = result_dataset_id

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.put(
                    url,
                    json=payload,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                # Update this instance with the response
                updated = self._from_dict(data)
                self.name = updated.name
                self.description = updated.description
                self.active = updated.active
                self.variable_mappings = updated.variable_mappings
                self.filter_rules = updated.filter_rules
                self.dataset_id = updated.dataset_id
                self.result_dataset_id = updated.result_dataset_id
                self.updated_at = updated.updated_at

                logger.debug(f"Updated evaluation: {self.id}")
                return self
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to update evaluation: {e}")

    @_retry_async
    async def adelete(self) -> None:
        """Delete this evaluation (async).

        This will cascade delete all associated evaluation runs.

        Raises:
            EvaluationError: If deletion fails
            EvaluationNotFoundError: If evaluation not found
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations/{self.id}"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.delete(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                logger.debug(f"Deleted evaluation: {self.id}")
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to delete evaluation: {e}")

    @_retry_async
    async def arun(
        self,
        trace_id: str | None = None,
        dataset_record_id: str | None = None,
    ) -> "EvaluationRun":
        """Run this evaluation on a single trace or dataset record (async).

        Provide either trace_id OR dataset_record_id, depending on evaluation type.

        Args:
            trace_id: Trace ID (for trace-based evaluations)
            dataset_record_id: Dataset record ID (for dataset-based evaluations)

        Returns:
            Created EvaluationRun instance (with PENDING status)

        Raises:
            EvaluationValidationError: If validation fails
            EvaluationError: If run creation fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations/{self.id}/run"

        payload: dict[str, Any] = {}
        if trace_id is not None:
            payload["trace_id"] = trace_id
        if dataset_record_id is not None:
            payload["dataset_record_id"] = dataset_record_id

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

                logger.debug(f"Created evaluation run: {data['id']}")
                return EvaluationRun._from_dict(data)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to run evaluation: {e}")

    @_retry_async
    async def aexecute(self) -> dict[str, Any]:
        """Execute this evaluation on all matching traces/records (async).

        For trace-based evaluations: runs on all traces matching filter_rules.
        For dataset-based evaluations: runs on all records in the dataset.

        Returns:
            Dictionary with execution summary:
            - evaluation_id: Evaluation UUID
            - total_targets: Number of traces/records matched
            - runs_created: Number of runs created
            - message: Summary message

        Raises:
            EvaluationError: If execution fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations/{self.id}/execute"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.post(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                data = response.json()

                logger.debug(f"Executed evaluation: {self.id}, created {data['runs_created']} runs")
                return data
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to execute evaluation: {e}")

    @_retry_async
    async def alist_runs(
        self,
        page: int = 1,
        page_size: int = 20,
        trace_id: str | None = None,
        status: EvaluationRunStatus | str | None = None,
    ) -> tuple[list["EvaluationRun"], PaginatedResponse]:
        """List evaluation runs for this evaluation (async).

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            trace_id: Filter by trace ID
            status: Filter by status (EvaluationRunStatus enum or string)

        Returns:
            Tuple of (list of runs, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations/{self.id}/runs"

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if trace_id:
            params["trace_id"] = trace_id
        if status is not None:
            params["status"] = str(status) if isinstance(status, EvaluationRunStatus) else status

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

                runs = [EvaluationRun._from_dict(item) for item in data["evaluation_runs"]]
                pagination = PaginatedResponse(
                    total=data["total"],
                    page=data["page"],
                    page_size=data["page_size"],
                    total_pages=data["total_pages"],
                )

                return runs, pagination
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to list evaluation runs: {e}")

    # === Sync Methods ===

    @classmethod
    def get(
        cls,
        evaluation_id: str,
        include_evaluator: bool = False,
        include_statistics: bool = False,
    ) -> "Evaluation":
        """Get a single evaluation by ID.

        Args:
            evaluation_id: UUID of the evaluation
            include_evaluator: Include evaluator data in response
            include_statistics: Include statistics in response

        Returns:
            Evaluation instance

        Raises:
            EvaluationNotFoundError: If evaluation not found
            EvaluationError: If fetch fails
        """
        return asyncio.run(
            cls.aget(
                evaluation_id,
                include_evaluator=include_evaluator,
                include_statistics=include_statistics,
            )
        )

    @classmethod
    def create(
        cls,
        name: str,
        evaluator_id: str,
        variable_mappings: dict[str, str],
        filter_rules: dict[str, Any] | None = None,
        dataset_id: str | None = None,
        result_dataset_id: str | None = None,
        active: bool = False,
        description: str | None = None,
    ) -> "Evaluation":
        """Create a new evaluation.

        Either filter_rules OR dataset_id must be provided, but not both.
        - filter_rules: For trace-based evaluations (can be active=True)
        - dataset_id: For dataset-based evaluations (must be active=False)

        Args:
            name: Evaluation name
            evaluator_id: UUID of the evaluator to use
            variable_mappings: Variable mappings (e.g., {"question": "span.input"})
            filter_rules: Filter rules for trace-based evaluations
            dataset_id: Dataset ID for dataset-based evaluations
            result_dataset_id: Optional result dataset ID
            active: Auto-run on new traces (trace evals only)
            description: Optional description

        Returns:
            Created Evaluation instance

        Raises:
            EvaluationValidationError: If validation fails
            EvaluationError: If creation fails
        """
        return asyncio.run(
            cls.acreate(
                name=name,
                evaluator_id=evaluator_id,
                variable_mappings=variable_mappings,
                filter_rules=filter_rules,
                dataset_id=dataset_id,
                result_dataset_id=result_dataset_id,
                active=active,
                description=description,
            )
        )

    @classmethod
    def list(
        cls,
        page: int = 1,
        page_size: int = 20,
        evaluator_id: str | None = None,
        search: str | None = None,
        include_evaluator: bool = False,
        include_statistics: bool = False,
    ) -> tuple[list["Evaluation"], PaginatedResponse]:
        """List all evaluations with pagination and filtering.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            evaluator_id: Filter by evaluator ID
            search: Optional search query
            include_evaluator: Include evaluator data in responses
            include_statistics: Include statistics in responses

        Returns:
            Tuple of (list of evaluations, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        return asyncio.run(
            cls.alist(
                page=page,
                page_size=page_size,
                evaluator_id=evaluator_id,
                search=search,
                include_evaluator=include_evaluator,
                include_statistics=include_statistics,
            )
        )

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        active: bool | None = None,
        variable_mappings: dict[str, str] | None = None,
        filter_rules: dict[str, Any] | None = None,
        dataset_id: str | None = None,
        result_dataset_id: str | None = None,
    ) -> "Evaluation":
        """Update this evaluation.

        Only provided fields will be updated.

        Args:
            name: New name
            description: New description
            active: New active status
            variable_mappings: New variable mappings
            filter_rules: New filter rules
            dataset_id: New dataset ID
            result_dataset_id: New result dataset ID

        Returns:
            Updated Evaluation instance

        Raises:
            EvaluationError: If update fails
            EvaluationNotFoundError: If evaluation not found
        """
        return asyncio.run(
            self.aupdate(
                name=name,
                description=description,
                active=active,
                variable_mappings=variable_mappings,
                filter_rules=filter_rules,
                dataset_id=dataset_id,
                result_dataset_id=result_dataset_id,
            )
        )

    def delete(self) -> None:
        """Delete this evaluation.

        This will cascade delete all associated evaluation runs.

        Raises:
            EvaluationError: If deletion fails
            EvaluationNotFoundError: If evaluation not found
        """
        return asyncio.run(self.adelete())

    def run(
        self,
        trace_id: str | None = None,
        dataset_record_id: str | None = None,
    ) -> "EvaluationRun":
        """Run this evaluation on a single trace or dataset record.

        Provide either trace_id OR dataset_record_id, depending on evaluation type.

        Args:
            trace_id: Trace ID (for trace-based evaluations)
            dataset_record_id: Dataset record ID (for dataset-based evaluations)

        Returns:
            Created EvaluationRun instance (with PENDING status)

        Raises:
            EvaluationValidationError: If validation fails
            EvaluationError: If run creation fails
        """
        return asyncio.run(self.arun(trace_id=trace_id, dataset_record_id=dataset_record_id))

    def execute(self) -> dict[str, Any]:
        """Execute this evaluation on all matching traces/records.

        For trace-based evaluations: runs on all traces matching filter_rules.
        For dataset-based evaluations: runs on all records in the dataset.

        Returns:
            Dictionary with execution summary:
            - evaluation_id: Evaluation UUID
            - total_targets: Number of traces/records matched
            - runs_created: Number of runs created
            - message: Summary message

        Raises:
            EvaluationError: If execution fails
        """
        return asyncio.run(self.aexecute())

    def list_runs(
        self,
        page: int = 1,
        page_size: int = 20,
        trace_id: str | None = None,
        status: EvaluationRunStatus | str | None = None,
    ) -> tuple[list["EvaluationRun"], PaginatedResponse]:
        """List evaluation runs for this evaluation.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            trace_id: Filter by trace ID
            status: Filter by status (EvaluationRunStatus enum or string)

        Returns:
            Tuple of (list of runs, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        return asyncio.run(
            self.alist_runs(page=page, page_size=page_size, trace_id=trace_id, status=status)
        )

    @classmethod
    @_retry_async
    async def abulk_delete(cls, evaluation_ids: list[str]) -> dict[str, Any]:
        """Delete multiple evaluations by their IDs (async).

        This will cascade delete all associated evaluation runs for each evaluation.

        Args:
            evaluation_ids: List of evaluation UUIDs to delete

        Returns:
            Dictionary with deletion summary (deleted_count, etc.)

        Raises:
            EvaluationError: If bulk deletion fails
            EvaluationValidationError: If validation fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluations/bulk-delete"

        payload = {"ids": evaluation_ids}

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

                logger.debug(f"Bulk deleted {data.get('deleted_count', len(evaluation_ids))} evaluations")
                return data
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to bulk delete evaluations: {e}")

    @classmethod
    def bulk_delete(cls, evaluation_ids: list[str]) -> dict[str, Any]:
        """Delete multiple evaluations by their IDs.

        This will cascade delete all associated evaluation runs for each evaluation.

        Args:
            evaluation_ids: List of evaluation UUIDs to delete

        Returns:
            Dictionary with deletion summary (deleted_count, etc.)

        Raises:
            EvaluationError: If bulk deletion fails
            EvaluationValidationError: If validation fails
        """
        return asyncio.run(cls.abulk_delete(evaluation_ids))

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Evaluation":
        """Create an Evaluation instance from API response data."""
        created_at = parse_iso_datetime(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = parse_iso_datetime(data["updated_at"])

        return cls(
            id=data["id"],
            name=data["name"],
            evaluator_id=data.get("evaluator_id"),
            variable_mappings=data["variable_mappings"],
            active=data["active"],
            filter_rules=data.get("filter_rules"),
            dataset_id=data.get("dataset_id"),
            result_dataset_id=data.get("result_dataset_id"),
            description=data.get("description"),
            project_id=data.get("project_id"),
            score_type=data.get("score_type"),
            created_at=created_at,
            updated_at=updated_at,
            statistics=data.get("statistics"),
            evaluator=data.get("evaluator"),
        )

    def __repr__(self) -> str:
        eval_type = "trace-based" if self.filter_rules else "dataset-based"
        return (
            f"Evaluation(id={self.id!r}, name={self.name!r}, "
            f"type={eval_type}, active={self.active})"
        )


class EvaluationRun:
    """Evaluation run model with ActiveRecord-style API.

    Evaluation runs represent individual executions of an evaluation on a trace or dataset record.
    They are created via Evaluation.run() or Evaluation.execute() methods.

    The API provides both sync and async methods:
    - Sync methods (simple names): EvaluationRun.method(...) or run.method(...)
    - Async methods ('a' prefix): await EvaluationRun.amethod(...) or await run.amethod(...)

    Examples:
        Get a run by ID (sync):
            >>> run = EvaluationRun.get("run-uuid")
            >>> print(f"Status: {run.status}, Score: {run.score}")

        Get a run by ID (async):
            >>> run = await EvaluationRun.aget("run-uuid")

        List all runs (sync):
            >>> runs, pagination = EvaluationRun.list(page=1, page_size=20)

        List all runs (async):
            >>> runs, pagination = await EvaluationRun.alist(page=1, page_size=20)

        Filter runs by evaluation (sync):
            >>> runs, pagination = EvaluationRun.list(evaluation_id="eval-uuid")

        Filter runs by status (async):
            >>> from lumenova_beacon.evaluations import EvaluationRunStatus
            >>> runs, pagination = await EvaluationRun.alist(status=EvaluationRunStatus.COMPLETED)
    """

    def __init__(
        self,
        id: str,
        evaluation_id: str,
        evaluation_name: str,
        status: EvaluationRunStatus | str,
        trace_id: str | None = None,
        dataset_record_id: str | None = None,
        result: dict[str, Any] | None = None,
        score: float | None = None,
        score_data: dict[str, Any] | None = None,
        error_message: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ):
        """Initialize an EvaluationRun instance.

        Args:
            id: Run UUID
            evaluation_id: Evaluation UUID
            evaluation_name: Evaluation name (denormalized snapshot)
            status: Run status (PENDING, RUNNING, COMPLETED, FAILED)
            trace_id: Trace ID (for trace-based evaluations)
            dataset_record_id: Dataset record ID (for dataset-based evaluations)
            result: LLM response result
            score: Legacy numeric score (deprecated, use score_data instead)
            score_data: Typed score with format {type: 'numeric'|'percent'|'categorical', value: ...}
            error_message: Error message if failed
            created_at: Creation timestamp
            updated_at: Last update timestamp
            started_at: Start timestamp
            completed_at: Completion timestamp
        """
        self.id = id
        self.evaluation_id = evaluation_id
        self.evaluation_name = evaluation_name
        self.status = EvaluationRunStatus(status) if isinstance(status, str) else status
        self.trace_id = trace_id
        self.dataset_record_id = dataset_record_id
        self.result = result
        self.score = score
        self.score_data = score_data
        self.error_message = error_message
        self.created_at = created_at
        self.updated_at = updated_at
        self.started_at = started_at
        self.completed_at = completed_at

    # === Async Methods ===

    @classmethod
    @_retry_async
    async def aget(cls, run_id: str) -> "EvaluationRun":
        """Get a single evaluation run by ID (async).

        Args:
            run_id: UUID of the evaluation run

        Returns:
            EvaluationRun instance

        Raises:
            EvaluationNotFoundError: If run not found
            EvaluationError: If fetch fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluation-runs/{run_id}"

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
            raise EvaluationError(f"Failed to fetch evaluation run: {e}")

    @classmethod
    @_retry_async
    async def alist(
        cls,
        page: int = 1,
        page_size: int = 20,
        evaluation_id: str | None = None,
        trace_id: str | None = None,
        dataset_record_id: str | None = None,
        status: EvaluationRunStatus | str | None = None,
    ) -> tuple[list["EvaluationRun"], PaginatedResponse]:
        """List all evaluation runs with pagination and filtering (async).

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            evaluation_id: Filter by evaluation ID
            trace_id: Filter by trace ID
            dataset_record_id: Filter by dataset record ID
            status: Filter by status (EvaluationRunStatus enum or string)

        Returns:
            Tuple of (list of runs, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluation-runs"

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if evaluation_id:
            params["evaluation_id"] = evaluation_id
        if trace_id:
            params["trace_id"] = trace_id
        if dataset_record_id:
            params["dataset_record_id"] = dataset_record_id
        if status is not None:
            params["status"] = str(status) if isinstance(status, EvaluationRunStatus) else status

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

                runs = [cls._from_dict(item) for item in data["evaluation_runs"]]
                pagination = PaginatedResponse(
                    total=data["total"],
                    page=data["page"],
                    page_size=data["page_size"],
                    total_pages=data["total_pages"],
                )

                return runs, pagination
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to list evaluation runs: {e}")

    # === Sync Methods ===

    @classmethod
    def get(cls, run_id: str) -> "EvaluationRun":
        """Get a single evaluation run by ID.

        Args:
            run_id: UUID of the evaluation run

        Returns:
            EvaluationRun instance

        Raises:
            EvaluationNotFoundError: If run not found
            EvaluationError: If fetch fails
        """
        return asyncio.run(cls.aget(run_id))

    @classmethod
    def list(
        cls,
        page: int = 1,
        page_size: int = 20,
        evaluation_id: str | None = None,
        trace_id: str | None = None,
        dataset_record_id: str | None = None,
        status: EvaluationRunStatus | str | None = None,
    ) -> tuple[list["EvaluationRun"], PaginatedResponse]:
        """List all evaluation runs with pagination and filtering.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            evaluation_id: Filter by evaluation ID
            trace_id: Filter by trace ID
            dataset_record_id: Filter by dataset record ID
            status: Filter by status (EvaluationRunStatus enum or string)

        Returns:
            Tuple of (list of runs, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        return asyncio.run(
            cls.alist(
                page=page,
                page_size=page_size,
                evaluation_id=evaluation_id,
                trace_id=trace_id,
                dataset_record_id=dataset_record_id,
                status=status,
            )
        )

    @classmethod
    @_retry_async
    async def abulk_delete(cls, run_ids: list[str]) -> dict[str, Any]:
        """Delete multiple evaluation runs by their IDs (async).

        Args:
            run_ids: List of evaluation run UUIDs to delete

        Returns:
            Dictionary with deletion summary (deleted_count, etc.)

        Raises:
            EvaluationError: If bulk deletion fails
            EvaluationValidationError: If validation fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluation-runs/bulk-delete"

        payload = {"ids": run_ids}

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

                logger.debug(f"Bulk deleted {data.get('deleted_count', len(run_ids))} evaluation runs")
                return data
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to bulk delete evaluation runs: {e}")

    @classmethod
    def bulk_delete(cls, run_ids: list[str]) -> dict[str, Any]:
        """Delete multiple evaluation runs by their IDs.

        Args:
            run_ids: List of evaluation run UUIDs to delete

        Returns:
            Dictionary with deletion summary (deleted_count, etc.)

        Raises:
            EvaluationError: If bulk deletion fails
            EvaluationValidationError: If validation fails
        """
        return asyncio.run(cls.abulk_delete(run_ids))

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "EvaluationRun":
        """Create an EvaluationRun instance from API response data."""
        created_at = None
        if data.get("created_at"):
            created_at = parse_iso_datetime(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = parse_iso_datetime(data["updated_at"])

        started_at = None
        if data.get("started_at"):
            started_at = parse_iso_datetime(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = parse_iso_datetime(data["completed_at"])

        return cls(
            id=data["id"],
            evaluation_id=data["evaluation_id"],
            evaluation_name=data["evaluation_name"],
            status=data["status"],
            trace_id=data.get("trace_id"),
            dataset_record_id=data.get("dataset_record_id"),
            result=data.get("result"),
            score=data.get("score"),
            score_data=data.get("score_data"),
            error_message=data.get("error_message"),
            created_at=created_at,
            updated_at=updated_at,
            started_at=started_at,
            completed_at=completed_at,
        )

    def __repr__(self) -> str:
        return (
            f"EvaluationRun(id={self.id!r}, evaluation_id={self.evaluation_id!r}, "
            f"status={self.status.value}, score={self.score})"
        )


class Evaluator:
    """Evaluator model with ActiveRecord-style API.

    Evaluators define the logic for evaluating traces or dataset records.
    They can be LLM-as-judge or code-based evaluators.

    The API provides both sync and async methods:
    - Sync methods (simple names): Evaluator.method(...) or evaluator.method(...)
    - Async methods ('a' prefix): await Evaluator.amethod(...) or await evaluator.amethod(...)

    Examples:
        Get an evaluator by ID (sync):
            >>> evaluator = Evaluator.get("evaluator-uuid")
            >>> print(f"Name: {evaluator.name}")
            >>> print(f"Type: {evaluator.evaluator_type}")

        Get an evaluator by ID (async):
            >>> evaluator = await Evaluator.aget("evaluator-uuid")

        List all evaluators (sync):
            >>> evaluators, pagination = Evaluator.list(page=1, page_size=20)

        List all evaluators (async):
            >>> evaluators, pagination = await Evaluator.alist(page=1, page_size=20)

        Search evaluators (sync):
            >>> evaluators, _ = Evaluator.list(search="accuracy")

        Search evaluators (async):
            >>> evaluators, _ = await Evaluator.alist(search="accuracy")
    """

    def __init__(
        self,
        id: str,
        name: str,
        evaluator_type: str,
        is_predefined: bool,
        description: str | None = None,
        category: str | None = None,
        icon: str | None = None,
        prompt_template: str | None = None,
        code: str | None = None,
        score_config: dict[str, Any] | None = None,
        code_parameters: list[dict[str, Any]] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize an Evaluator instance.

        Args:
            id: Evaluator UUID
            name: Evaluator name
            evaluator_type: Type of evaluator ("llm-as-judge" or "code")
            is_predefined: Whether this is a predefined evaluator
            description: Optional description
            category: Optional category (e.g., "accuracy", "relevance")
            icon: Optional Lucide-react icon name
            prompt_template: Prompt template for llm-as-judge evaluators
            code: Python code for code-based evaluators
            score_config: Score configuration with type ('percent', 'numeric', 'categorical'),
                         scoring_instructions, values (for categorical), and value_colors
            code_parameters: List of parameters extracted from code evaluator function
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.name = name
        self.evaluator_type = evaluator_type
        self.is_predefined = is_predefined
        self.description = description
        self.category = category
        self.icon = icon
        self.prompt_template = prompt_template
        self.code = code
        self.score_config = score_config
        self.code_parameters = code_parameters
        self.created_at = created_at
        self.updated_at = updated_at

    # === Async Methods ===

    @classmethod
    @_retry_async
    async def aget(cls, evaluator_id: str) -> "Evaluator":
        """Get a single evaluator by ID (async).

        Args:
            evaluator_id: UUID of the evaluator

        Returns:
            Evaluator instance

        Raises:
            EvaluationNotFoundError: If evaluator not found
            EvaluationError: If fetch fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluators/{evaluator_id}"

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
            raise EvaluationError(f"Failed to fetch evaluator: {e}")

    @classmethod
    @_retry_async
    async def alist(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list["Evaluator"], PaginatedResponse]:
        """List all evaluators with pagination and filtering (async).

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            search: Optional search query for name/description

        Returns:
            Tuple of (list of evaluators, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        base_url = get_base_url()
        transport = get_transport("Evaluation operations")
        url = f"{base_url}/api/v1/evaluators"

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if search:
            params["search"] = search

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

                evaluators = [cls._from_dict(item) for item in data["evaluators"]]
                pagination = PaginatedResponse(
                    total=data["total"],
                    page=data["page"],
                    page_size=data["page_size"],
                    total_pages=data["total_pages"],
                )

                return evaluators, pagination
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise EvaluationError(f"Failed to list evaluators: {e}")

    # === Sync Methods ===

    @classmethod
    def get(cls, evaluator_id: str) -> "Evaluator":
        """Get a single evaluator by ID.

        Args:
            evaluator_id: UUID of the evaluator

        Returns:
            Evaluator instance

        Raises:
            EvaluationNotFoundError: If evaluator not found
            EvaluationError: If fetch fails
        """
        return asyncio.run(cls.aget(evaluator_id))

    @classmethod
    def list(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list["Evaluator"], PaginatedResponse]:
        """List all evaluators with pagination and filtering.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            search: Optional search query for name/description

        Returns:
            Tuple of (list of evaluators, pagination metadata)

        Raises:
            EvaluationError: If listing fails
        """
        return asyncio.run(
            cls.alist(
                page=page,
                page_size=page_size,
                search=search,
            )
        )

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Evaluator":
        """Create an Evaluator instance from API response data."""
        created_at = None
        if data.get("created_at"):
            created_at = parse_iso_datetime(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = parse_iso_datetime(data["updated_at"])

        return cls(
            id=data["id"],
            name=data["name"],
            evaluator_type=data.get("evaluator_type", "llm-as-judge"),
            is_predefined=data.get("is_predefined", False),
            description=data.get("description"),
            category=data.get("category"),
            icon=data.get("icon"),
            prompt_template=data.get("prompt_template"),
            code=data.get("code"),
            score_config=data.get("score_config"),
            code_parameters=data.get("code_parameters"),
            created_at=created_at,
            updated_at=updated_at,
        )

    def __repr__(self) -> str:
        return (
            f"Evaluator(id={self.id!r}, name={self.name!r}, "
            f"type={self.evaluator_type}, predefined={self.is_predefined})"
        )
