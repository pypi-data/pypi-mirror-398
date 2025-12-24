"""Dataset management for the Lumenova Beacon SDK.

This module provides ActiveRecord-style models for managing datasets and records
with flexible column-based data.

Examples:
    Create and manage datasets:
        >>> from lumenova_beacon import BeaconClient, Dataset
        >>> client = BeaconClient(endpoint="...", api_key="...")
        >>> dataset = Dataset.create(name="my-dataset")
        >>> record = dataset.create_record(data={"prompt": "Hello", "expected": "Hi"})

    List datasets with pagination:
        >>> datasets, pagination = Dataset.list(page=1, page_size=20)
        >>> print(f"Total: {pagination.total}")
"""

from lumenova_beacon.datasets.models import Dataset, DatasetRecord
from lumenova_beacon.datasets.types import (
    ColumnDefinition,
    JSONData,
    PaginatedResponse,
)

__all__ = [
    "Dataset",
    "DatasetRecord",
    "ColumnDefinition",
    "JSONData",
    "PaginatedResponse",
]
