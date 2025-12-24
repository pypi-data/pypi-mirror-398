"""Type definitions and enums for the Beacon SDK."""

from enum import Enum
from typing import Any, TypeAlias

# Type aliases
Attributes: TypeAlias = dict[str, Any]
TraceState: TypeAlias = list[str]


class SpanKind(str, Enum):
    """OpenTelemetry span kinds."""

    INTERNAL = "SpanKind.INTERNAL"
    SERVER = "SpanKind.SERVER"
    CLIENT = "SpanKind.CLIENT"
    PRODUCER = "SpanKind.PRODUCER"
    CONSUMER = "SpanKind.CONSUMER"


class StatusCode(str, Enum):
    """OpenTelemetry status codes."""

    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


class SpanType(str, Enum):
    """Types of spans in the Beacon system."""

    SPAN = "span"
    GENERATION = "generation"
    CHAIN = "chain"
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    AGENT = "agent"
    FUNCTION = "function"
    REQUEST = "request"
    SERVER = "server"
    TASK = "task"
    CACHE = "cache"
    EMBEDDING = "embedding"
