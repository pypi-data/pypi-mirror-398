"""Type definitions for prompt management."""

from dataclasses import dataclass
from enum import Enum


class PromptType(str, Enum):
    """Enum for prompt types."""

    TEXT = 'text'
    CHAT = 'chat'


@dataclass
class ChatMessage:
    """Single message in a chat prompt."""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary format.

        Returns:
            Dictionary with role and content
        """
        return {'role': self.role, 'content': self.content}
