"""Dataset and DatasetRecord models with ActiveRecord-style API."""

from __future__ import annotations

import asyncio
import csv
import logging
from datetime import datetime
from pathlib import Path
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
    DatasetError,
    DatasetNotFoundError,
    DatasetValidationError,
)
from lumenova_beacon.utils.client_helpers import get_base_url, get_transport
from lumenova_beacon.utils.datetime import parse_iso_datetime
from lumenova_beacon.utils.http_errors import HTTPErrorHandler

logger = logging.getLogger(__name__)


# Centralized error handler for datasets
_error_handler = HTTPErrorHandler(
    not_found_exc=DatasetNotFoundError,
    validation_exc=DatasetValidationError,
    base_exc=DatasetError,
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


class Dataset:
    """Dataset model with ActiveRecord-style API.

    Datasets are collections of records with flexible column-based data that can be
    used for batch evaluations. Each record contains a 'data' field with arbitrary
    key-value pairs representing columns.

    The API provides both sync and async methods:
    - Sync methods (simple names): Dataset.method(...) or dataset.method(...)
    - Async methods ('a' prefix): await Dataset.amethod(...) or await dataset.amethod(...)

    Examples:
        Create a new dataset (sync):
            >>> dataset = Dataset.create(name="test-dataset", description="My dataset")

        Create a new dataset (async):
            >>> dataset = await Dataset.acreate(name="test-dataset", description="My dataset")

        Load an existing dataset (sync):
            >>> dataset = Dataset.get(dataset_id="uuid-here")

        Load an existing dataset (async):
            >>> dataset = await Dataset.aget(dataset_id="uuid-here")

        List all datasets (sync):
            >>> datasets, pagination = Dataset.list(page=1, page_size=20)

        List all datasets (async):
            >>> datasets, pagination = await Dataset.alist(page=1, page_size=20)

        Update a dataset (sync):
            >>> dataset.update(name="New name")
            >>> # or
            >>> dataset.name = "New name"
            >>> dataset.save()

        Update a dataset (async):
            >>> await dataset.aupdate(name="New name")
            >>> # or
            >>> dataset.name = "New name"
            >>> await dataset.asave()

        Delete a dataset (sync):
            >>> dataset.delete()

        Delete a dataset (async):
            >>> await dataset.adelete()
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        record_count: int | None = None,
        column_schema: list[dict[str, Any]] | None = None,
        project_id: str | None = None,
        source_dataset_id: str | None = None,
    ):
        """Initialize a Dataset instance.

        Args:
            name: Name of the dataset
            description: Optional description
            id: Dataset ID (set by server)
            created_at: Creation timestamp (set by server)
            updated_at: Last update timestamp (set by server)
            record_count: Number of records in the dataset (set by server)
            column_schema: Column schema defining the dataset structure
            project_id: Project ID the dataset belongs to (set by server)
            source_dataset_id: Source dataset ID for experiment result datasets (set by server)
        """
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at
        self.record_count = record_count
        self.column_schema = column_schema
        self.project_id = project_id
        self.source_dataset_id = source_dataset_id
        self._is_new = id is None

    # === Async Methods ===

    @classmethod
    @_retry_async
    async def acreate(
        cls,
        name: str,
        column_schema: list[dict[str, Any]],
        description: str | None = None,
    ) -> "Dataset":
        """Create a new dataset and save it to the server (async).

        Args:
            name: Name of the dataset
            column_schema: Column schema defining dataset structure. Must have at least
                one column. Each column is a dict with 'name' (required) and 'order' (optional).
                Example: [{"name": "prompt", "order": 0}, {"name": "response", "order": 1}]
            description: Optional description

        Returns:
            Created Dataset instance

        Raises:
            DatasetError: If creation fails
            DatasetValidationError: If validation fails (e.g., empty column_schema)
        """
        if not column_schema:
            raise DatasetValidationError("column_schema must have at least one column")
        dataset = cls(name=name, description=description, column_schema=column_schema)
        return await dataset.asave()

    @classmethod
    @_retry_async
    async def aget(cls, dataset_id: str, include_records: bool = False) -> "Dataset":
        """Load a dataset from the server by ID (async).

        Args:
            dataset_id: UUID of the dataset
            include_records: Whether to include all records in response

        Returns:
            Dataset instance

        Raises:
            DatasetNotFoundError: If dataset not found
            DatasetError: If fetch fails
        """
        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{dataset_id}"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.get(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                    params={"include_records": include_records},
                )
                response.raise_for_status()
                data = response.json()

                return cls._from_dict(data)
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to fetch dataset: {e}")

    @classmethod
    @_retry_async
    async def alist(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        exclude_experiment_results: bool = True,
    ) -> tuple[list["Dataset"], PaginatedResponse]:
        """List all datasets with pagination (async).

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            search: Optional search query for name/description
            exclude_experiment_results: If True (default), excludes datasets that are
                experiment results. Set to False to include all datasets.

        Returns:
            Tuple of (list of datasets, pagination metadata)

        Raises:
            DatasetError: If listing fails
        """
        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets"

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "exclude_experiment_results": exclude_experiment_results,
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

                datasets = [cls._from_dict(d) for d in data["datasets"]]
                pagination = PaginatedResponse(
                    total=data["total"],
                    page=data["page"],
                    page_size=data["page_size"],
                    total_pages=data["total_pages"],
                )

                return datasets, pagination
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to list datasets: {e}")

    async def asave(self) -> "Dataset":
        """Save the dataset to the server (create or update) (async).

        Returns:
            Self for chaining

        Raises:
            DatasetError: If save fails
            DatasetValidationError: If validation fails
        """
        if self._is_new:
            return await self._acreate()
        else:
            return await self._aupdate()

    @_retry_async
    async def _acreate(self) -> "Dataset":
        """Create a new dataset on the server (async)."""
        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets"

        payload = {
            "name": self.name,
        }
        if self.description is not None:
            payload["description"] = self.description
        if self.column_schema is not None:
            payload["column_schema"] = self.column_schema

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

                # Update instance with server response
                self.id = data["id"]
                self.created_at = parse_iso_datetime(data["created_at"])
                if data.get("updated_at"):
                    self.updated_at = parse_iso_datetime(data["updated_at"])
                self.record_count = data.get("record_count")
                self.column_schema = data.get("column_schema")
                self._is_new = False

                logger.debug(f"Created dataset: {self.id}")
                return self
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to create dataset: {e}")

    @_retry_async
    async def _aupdate(self) -> "Dataset":
        """Update the dataset on the server (async)."""
        if self._is_new:
            raise DatasetError("Cannot update a dataset that hasn't been saved yet")

        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{self.id}"

        payload = {}
        if self.name is not None:
            payload["name"] = self.name
        if self.description is not None:
            payload["description"] = self.description

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

                # Update instance with server response
                self.name = data["name"]
                self.description = data.get("description")
                if data.get("updated_at"):
                    self.updated_at = parse_iso_datetime(data["updated_at"])
                self.record_count = data.get("record_count")

                logger.debug(f"Updated dataset: {self.id}")
                return self
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to update dataset: {e}")

    async def aupdate(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> "Dataset":
        """Update dataset fields and save to server (async).

        Args:
            name: New name (optional)
            description: New description (optional)

        Returns:
            Self for chaining

        Raises:
            DatasetError: If update fails
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        return await self.asave()

    @_retry_async
    async def adelete(self) -> None:
        """Delete the dataset from the server (async).

        This will also cascade delete all associated records.

        Raises:
            DatasetError: If deletion fails
            DatasetNotFoundError: If dataset not found
        """
        if self._is_new:
            raise DatasetError("Cannot delete a dataset that hasn't been saved yet")

        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{self.id}"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.delete(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                logger.debug(f"Deleted dataset: {self.id}")
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to delete dataset: {e}")

    async def acreate_record(
        self,
        data: dict[str, Any],
    ) -> "DatasetRecord":
        """Create a new record in this dataset (async).

        Args:
            data: Record data with column values (JSON dict with arbitrary keys)

        Returns:
            Created DatasetRecord instance

        Raises:
            DatasetError: If creation fails or dataset not saved yet
        """
        if self._is_new:
            raise DatasetError(
                "Cannot create records for a dataset that hasn't been saved yet"
            )

        record = DatasetRecord(
            dataset_id=self.id,
            data=data,
        )
        return await record.asave()

    async def alist_records(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list["DatasetRecord"], PaginatedResponse]:
        """List all records in this dataset with pagination (async).

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)

        Returns:
            Tuple of (list of records, pagination metadata)

        Raises:
            DatasetError: If listing fails or dataset not saved yet
        """
        if self._is_new:
            raise DatasetError(
                "Cannot list records for a dataset that hasn't been saved yet"
            )

        return await DatasetRecord.alist(dataset_id=self.id, page=page, page_size=page_size)

    @_retry_async
    async def abulk_create_records(
        self, records: list[dict[str, Any]]
    ) -> list["DatasetRecord"]:
        """Bulk create multiple records in this dataset (async).

        Args:
            records: List of record dicts, each with a "data" key containing
                    the record data with column values (JSON dict)

        Returns:
            List of created DatasetRecord instances

        Raises:
            DatasetError: If creation fails or dataset not saved yet
            DatasetValidationError: If validation fails
        """
        if self._is_new:
            raise DatasetError(
                "Cannot create records for a dataset that hasn't been saved yet"
            )

        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{self.id}/records/bulk"

        payload = {"records": records}

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

                logger.debug(f"Bulk created {len(data)} records in dataset {self.id}")
                return [DatasetRecord._from_dict(r) for r in data]
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to bulk create records: {e}")

    async def aimport_from_csv(
        self,
        file_path: str | Path,
        column_mapping: dict[str, str | list[str]],
        delimiter: str = ",",
        has_header: bool = True,
    ) -> int:
        """Import records from a CSV file into this dataset (async).

        This allows you to populate a dataset by reading a CSV file and mapping
        its columns to dataset columns. Multiple CSV columns can be combined
        into a single dataset column as a JSON object.

        Args:
            file_path: Path to the CSV file
            column_mapping: Maps dataset column names to CSV column(s).
                - Single column: {"input": "question"} - value copied directly
                - Multiple columns: {"ground_truth": ["answer", "category"]} -
                  combined into a JSON object like {"answer": "...", "category": "..."}
            delimiter: CSV delimiter character (default: comma)
            has_header: Whether the CSV has a header row (default: True).
                If False, use column indices as strings ("0", "1", etc.)

        Returns:
            Number of records imported

        Raises:
            DatasetError: If import fails or dataset not saved yet

        Example:
            >>> dataset = Dataset.create(
            ...     name="QA Dataset",
            ...     column_schema=[
            ...         {"name": "input", "order": 0},
            ...         {"name": "ground_truth", "order": 1},
            ...     ],
            ... )
            >>> count = await dataset.aimport_from_csv(
            ...     "evaluation_data.csv",
            ...     column_mapping={
            ...         "input": "question",
            ...         "ground_truth": ["correct_answer", "category"],
            ...     }
            ... )
            >>> print(f"Imported {count} records")
        """
        if self._is_new:
            raise DatasetError(
                "Cannot import CSV into a dataset that hasn't been saved yet"
            )

        file_path = Path(file_path)
        if not file_path.exists():
            raise DatasetError(f"CSV file not found: {file_path}")

        records: list[dict[str, Any]] = []
        with open(file_path, newline="", encoding="utf-8") as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    data: dict[str, Any] = {}
                    for dataset_col, csv_cols in column_mapping.items():
                        if isinstance(csv_cols, str):
                            # Single column mapping - copy value directly
                            data[dataset_col] = row.get(csv_cols, "")
                        else:
                            # Multi-column mapping - combine into object
                            data[dataset_col] = {
                                col: row.get(col, "") for col in csv_cols
                            }
                    records.append({"data": data})
            else:
                # No header - use column indices as keys
                raw_reader = csv.reader(f, delimiter=delimiter)
                for row_list in raw_reader:
                    row = {str(i): val for i, val in enumerate(row_list)}
                    data = {}
                    for dataset_col, csv_cols in column_mapping.items():
                        if isinstance(csv_cols, str):
                            data[dataset_col] = row.get(csv_cols, "")
                        else:
                            data[dataset_col] = {
                                col: row.get(col, "") for col in csv_cols
                            }
                    records.append({"data": data})

        if records:
            await self.abulk_create_records(records)
            # Refresh record count
            self.record_count = (self.record_count or 0) + len(records)

        logger.debug(f"Imported {len(records)} records from CSV into dataset {self.id}")
        return len(records)

    # === Sync Methods ===

    @classmethod
    def create(
        cls,
        name: str,
        column_schema: list[dict[str, Any]],
        description: str | None = None,
    ) -> "Dataset":
        """Create a new dataset and save it to the server.

        Args:
            name: Name of the dataset
            column_schema: Column schema defining dataset structure. Must have at least
                one column. Each column is a dict with 'name' (required) and 'order' (optional).
                Example: [{"name": "prompt", "order": 0}, {"name": "response", "order": 1}]
            description: Optional description

        Returns:
            Created Dataset instance

        Raises:
            DatasetError: If creation fails
            DatasetValidationError: If validation fails (e.g., empty column_schema)
        """
        return asyncio.run(cls.acreate(name=name, column_schema=column_schema, description=description))

    @classmethod
    def get(cls, dataset_id: str, include_records: bool = False) -> "Dataset":
        """Load a dataset from the server by ID.

        Args:
            dataset_id: UUID of the dataset
            include_records: Whether to include all records in response

        Returns:
            Dataset instance

        Raises:
            DatasetNotFoundError: If dataset not found
            DatasetError: If fetch fails
        """
        return asyncio.run(cls.aget(dataset_id=dataset_id, include_records=include_records))

    @classmethod
    def list(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        exclude_experiment_results: bool = True,
    ) -> tuple[list["Dataset"], PaginatedResponse]:
        """List all datasets with pagination.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)
            search: Optional search query for name/description
            exclude_experiment_results: If True (default), excludes datasets that are
                experiment results. Set to False to include all datasets.

        Returns:
            Tuple of (list of datasets, pagination metadata)

        Raises:
            DatasetError: If listing fails
        """
        return asyncio.run(
            cls.alist(
                page=page,
                page_size=page_size,
                search=search,
                exclude_experiment_results=exclude_experiment_results,
            )
        )

    def save(self) -> "Dataset":
        """Save the dataset to the server (create or update).

        Returns:
            Self for chaining

        Raises:
            DatasetError: If save fails
            DatasetValidationError: If validation fails
        """
        return asyncio.run(self.asave())

    def _create(self) -> "Dataset":
        """Create a new dataset on the server."""
        return asyncio.run(self._acreate())

    def _update(self) -> "Dataset":
        """Update the dataset on the server."""
        return asyncio.run(self._aupdate())

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> "Dataset":
        """Update dataset fields and save to server.

        Args:
            name: New name (optional)
            description: New description (optional)

        Returns:
            Self for chaining

        Raises:
            DatasetError: If update fails
        """
        return asyncio.run(self.aupdate(name=name, description=description))

    def delete(self) -> None:
        """Delete the dataset from the server.

        This will also cascade delete all associated records.

        Raises:
            DatasetError: If deletion fails
            DatasetNotFoundError: If dataset not found
        """
        return asyncio.run(self.adelete())

    def create_record(
        self,
        data: dict[str, Any],
    ) -> "DatasetRecord":
        """Create a new record in this dataset.

        Args:
            data: Record data with column values (JSON dict with arbitrary keys)

        Returns:
            Created DatasetRecord instance

        Raises:
            DatasetError: If creation fails or dataset not saved yet
        """
        return asyncio.run(self.acreate_record(data=data))

    def list_records(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list["DatasetRecord"], PaginatedResponse]:
        """List all records in this dataset with pagination.

        Args:
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)

        Returns:
            Tuple of (list of records, pagination metadata)

        Raises:
            DatasetError: If listing fails or dataset not saved yet
        """
        return asyncio.run(self.alist_records(page=page, page_size=page_size))

    def bulk_create_records(
        self, records: list[dict[str, Any]]
    ) -> list["DatasetRecord"]:
        """Bulk create multiple records in this dataset.

        Args:
            records: List of record dicts, each with a "data" key containing
                    the record data with column values (JSON dict)

        Returns:
            List of created DatasetRecord instances

        Raises:
            DatasetError: If creation fails or dataset not saved yet
            DatasetValidationError: If validation fails
        """
        return asyncio.run(self.abulk_create_records(records=records))

    def import_from_csv(
        self,
        file_path: str | Path,
        column_mapping: dict[str, str | list[str]],
        delimiter: str = ",",
        has_header: bool = True,
    ) -> int:
        """Import records from a CSV file into this dataset.

        This allows you to populate a dataset by reading a CSV file and mapping
        its columns to dataset columns. Multiple CSV columns can be combined
        into a single dataset column as a JSON object.

        Args:
            file_path: Path to the CSV file
            column_mapping: Maps dataset column names to CSV column(s).
                - Single column: {"input": "question"} - value copied directly
                - Multiple columns: {"ground_truth": ["answer", "category"]} -
                  combined into a JSON object like {"answer": "...", "category": "..."}
            delimiter: CSV delimiter character (default: comma)
            has_header: Whether the CSV has a header row (default: True).
                If False, use column indices as strings ("0", "1", etc.)

        Returns:
            Number of records imported

        Raises:
            DatasetError: If import fails or dataset not saved yet

        Example:
            >>> dataset = Dataset.create(
            ...     name="QA Dataset",
            ...     column_schema=[
            ...         {"name": "input", "order": 0},
            ...         {"name": "ground_truth", "order": 1},
            ...     ],
            ... )
            >>> count = dataset.import_from_csv(
            ...     "evaluation_data.csv",
            ...     column_mapping={
            ...         "input": "question",
            ...         "ground_truth": ["correct_answer", "category"],
            ...     }
            ... )
            >>> print(f"Imported {count} records")
        """
        return asyncio.run(
            self.aimport_from_csv(
                file_path=file_path,
                column_mapping=column_mapping,
                delimiter=delimiter,
                has_header=has_header,
            )
        )

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Dataset":
        """Create a Dataset instance from API response data."""
        created_at = None
        if data.get("created_at"):
            created_at = parse_iso_datetime(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = parse_iso_datetime(data["updated_at"])

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            created_at=created_at,
            updated_at=updated_at,
            record_count=data.get("record_count"),
            column_schema=data.get("column_schema"),
            project_id=data.get("project_id"),
            source_dataset_id=data.get("source_dataset_id"),
        )

    def __repr__(self) -> str:
        return f"Dataset(id={self.id!r}, name={self.name!r}, record_count={self.record_count})"


class DatasetRecord:
    """Dataset record model with ActiveRecord-style API.

    Records contain flexible column-based data in a 'data' field with arbitrary
    key-value pairs. Column names and structure are user-defined.

    The API provides both sync and async methods:
    - Sync methods (simple names): DatasetRecord.method(...) or record.method(...)
    - Async methods ('a' prefix): await DatasetRecord.amethod(...) or await record.amethod(...)

    Examples:
        Create a new record (sync):
            >>> record = DatasetRecord(
            ...     dataset_id="uuid-here",
            ...     data={"prompt": "What is AI?", "expected_answer": "..."}
            ... )
            >>> record.save()

        Create a new record (async):
            >>> record = DatasetRecord(
            ...     dataset_id="uuid-here",
            ...     data={"prompt": "What is AI?", "expected_answer": "..."}
            ... )
            >>> await record.asave()

        Get an existing record (sync):
            >>> record = DatasetRecord.get(dataset_id="uuid", record_id="uuid")

        Get an existing record (async):
            >>> record = await DatasetRecord.aget(dataset_id="uuid", record_id="uuid")

        Update a record (sync):
            >>> record.update(data={"prompt": "What is AI?", "answer": "Updated answer"})

        Update a record (async):
            >>> await record.aupdate(data={"prompt": "What is AI?", "answer": "Updated answer"})

        Delete a record (sync):
            >>> record.delete()

        Delete a record (async):
            >>> await record.adelete()
    """

    def __init__(
        self,
        dataset_id: str,
        data: dict[str, Any],
        id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize a DatasetRecord instance.

        Args:
            dataset_id: UUID of the parent dataset
            data: Record data with column values (JSON dict with arbitrary keys)
            id: Record ID (set by server)
            created_at: Creation timestamp (set by server)
            updated_at: Last update timestamp (set by server)
        """
        self.id = id
        self.dataset_id = dataset_id
        self.data = data
        self.created_at = created_at
        self.updated_at = updated_at
        self._is_new = id is None

    # === Async Methods ===

    @classmethod
    @_retry_async
    async def aget(cls, dataset_id: str, record_id: str) -> "DatasetRecord":
        """Load a record from the server by ID (async).

        Args:
            dataset_id: UUID of the parent dataset
            record_id: UUID of the record

        Returns:
            DatasetRecord instance

        Raises:
            DatasetNotFoundError: If record not found
            DatasetError: If fetch fails
        """
        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{dataset_id}/records/{record_id}"

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
            raise DatasetError(f"Failed to fetch record: {e}")

    @classmethod
    @_retry_async
    async def alist(
        cls,
        dataset_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list["DatasetRecord"], PaginatedResponse]:
        """List all records in a dataset with pagination (async).

        Args:
            dataset_id: UUID of the parent dataset
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)

        Returns:
            Tuple of (list of records, pagination metadata)

        Raises:
            DatasetError: If listing fails
        """
        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{dataset_id}/records"

        params = {"page": page, "page_size": page_size}

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

                records = [cls._from_dict(r) for r in data["records"]]
                pagination = PaginatedResponse(
                    total=data["total"],
                    page=data["page"],
                    page_size=data["page_size"],
                    total_pages=data["total_pages"],
                )

                return records, pagination
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to list records: {e}")

    async def asave(self) -> "DatasetRecord":
        """Save the record to the server (create or update) (async).

        Returns:
            Self for chaining

        Raises:
            DatasetError: If save fails
            DatasetValidationError: If validation fails
        """
        if self._is_new:
            return await self._acreate()
        else:
            return await self._aupdate()

    @_retry_async
    async def _acreate(self) -> "DatasetRecord":
        """Create a new record on the server (async)."""
        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{self.dataset_id}/records"

        payload = {"data": self.data}

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

                # Update instance with server response
                self.id = data["id"]
                self.dataset_id = data["dataset_id"]
                self.created_at = parse_iso_datetime(data["created_at"])
                if data.get("updated_at"):
                    self.updated_at = parse_iso_datetime(data["updated_at"])
                self._is_new = False

                logger.debug(f"Created record: {self.id}")
                return self
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to create record: {e}")

    @_retry_async
    async def _aupdate(self) -> "DatasetRecord":
        """Update the record on the server (async)."""
        if self._is_new:
            raise DatasetError("Cannot update a record that hasn't been saved yet")

        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{self.dataset_id}/records/{self.id}"

        payload = {}
        if self.data is not None:
            payload["data"] = self.data

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

                # Update instance with server response
                self.data = data["data"]
                if data.get("updated_at"):
                    self.updated_at = parse_iso_datetime(data["updated_at"])

                logger.debug(f"Updated record: {self.id}")
                return self
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to update record: {e}")

    async def aupdate(
        self,
        data: dict[str, Any] | None = None,
    ) -> "DatasetRecord":
        """Update record fields and save to server (async).

        Args:
            data: New record data with column values (optional)

        Returns:
            Self for chaining

        Raises:
            DatasetError: If update fails
        """
        if data is not None:
            self.data = data
        return await self.asave()

    @_retry_async
    async def adelete(self) -> None:
        """Delete the record from the server (async).

        Raises:
            DatasetError: If deletion fails
            DatasetNotFoundError: If record not found
        """
        if self._is_new:
            raise DatasetError("Cannot delete a record that hasn't been saved yet")

        base_url = get_base_url()
        transport = get_transport("Dataset operations")
        url = f"{base_url}/api/v1/datasets/{self.dataset_id}/records/{self.id}"

        try:
            async with httpx.AsyncClient(verify=transport.verify) as client:
                response = await client.delete(
                    url,
                    headers=transport.headers,
                    timeout=transport.timeout,
                )
                response.raise_for_status()
                logger.debug(f"Deleted record: {self.id}")
        except httpx.HTTPStatusError as e:
            _error_handler.handle(e)
        except httpx.HTTPError as e:
            raise DatasetError(f"Failed to delete record: {e}")

    # === Sync Methods ===

    @classmethod
    def get(cls, dataset_id: str, record_id: str) -> "DatasetRecord":
        """Load a record from the server by ID.

        Args:
            dataset_id: UUID of the parent dataset
            record_id: UUID of the record

        Returns:
            DatasetRecord instance

        Raises:
            DatasetNotFoundError: If record not found
            DatasetError: If fetch fails
        """
        return asyncio.run(cls.aget(dataset_id=dataset_id, record_id=record_id))

    @classmethod
    def list(
        cls,
        dataset_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list["DatasetRecord"], PaginatedResponse]:
        """List all records in a dataset with pagination.

        Args:
            dataset_id: UUID of the parent dataset
            page: Page number (starting from 1)
            page_size: Number of items per page (max 100)

        Returns:
            Tuple of (list of records, pagination metadata)

        Raises:
            DatasetError: If listing fails
        """
        return asyncio.run(cls.alist(dataset_id=dataset_id, page=page, page_size=page_size))

    def save(self) -> "DatasetRecord":
        """Save the record to the server (create or update).

        Returns:
            Self for chaining

        Raises:
            DatasetError: If save fails
            DatasetValidationError: If validation fails
        """
        return asyncio.run(self.asave())

    def _create(self) -> "DatasetRecord":
        """Create a new record on the server."""
        return asyncio.run(self._acreate())

    def _update(self) -> "DatasetRecord":
        """Update the record on the server."""
        return asyncio.run(self._aupdate())

    def update(
        self,
        data: dict[str, Any] | None = None,
    ) -> "DatasetRecord":
        """Update record fields and save to server.

        Args:
            data: New record data with column values (optional)

        Returns:
            Self for chaining

        Raises:
            DatasetError: If update fails
        """
        return asyncio.run(self.aupdate(data=data))

    def delete(self) -> None:
        """Delete the record from the server.

        Raises:
            DatasetError: If deletion fails
            DatasetNotFoundError: If record not found
        """
        return asyncio.run(self.adelete())

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "DatasetRecord":
        """Create a DatasetRecord instance from API response data."""
        created_at = None
        if data.get("created_at"):
            created_at = parse_iso_datetime(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = parse_iso_datetime(data["updated_at"])

        return cls(
            id=data["id"],
            dataset_id=data["dataset_id"],
            data=data["data"],
            created_at=created_at,
            updated_at=updated_at,
        )

    def __repr__(self) -> str:
        return f"DatasetRecord(id={self.id!r}, dataset_id={self.dataset_id!r})"
