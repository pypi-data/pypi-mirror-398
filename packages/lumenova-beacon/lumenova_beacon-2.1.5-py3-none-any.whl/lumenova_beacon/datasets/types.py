"""Type definitions for dataset operations."""

from dataclasses import dataclass
from typing import Any

# Type alias for JSON data
JSONData = dict[str, Any]  # noqa: F401 - exported for external use


@dataclass
class PaginatedResponse:
    """Pagination metadata for list responses."""

    total: int
    page: int
    page_size: int
    total_pages: int


@dataclass
class ColumnDefinition:
    """Dataset column definition.

    Attributes:
        name: Column name
        order: Optional display order of the column
    """

    name: str
    order: int | None = None
