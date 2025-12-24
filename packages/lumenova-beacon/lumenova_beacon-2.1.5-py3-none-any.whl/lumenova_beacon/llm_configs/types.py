"""Type definitions for LLM configurations."""

from dataclasses import dataclass


@dataclass
class UserBasicInfo:
    """Basic user information."""

    id: str
    email: str
    name: str | None = None
