"""JSON serialization utilities for complex types."""

import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


def serialize_for_json(obj: Any) -> Any:
    """Recursively serialize an object to ensure JSON compatibility.

    This function handles LangChain-specific objects, Pydantic models, and other
    complex types that aren't natively JSON serializable. It's useful for converting
    objects from integrations (LangChain, etc.) to JSON-compatible formats.

    Supported types:
    - Primitives: str, int, float, bool, None
    - UUID: converted to string
    - datetime: converted to ISO format
    - Pydantic models (v1 and v2): converted via dict() or model_dump()
    - LangChain BaseMessage: converted to {role, content, additional_kwargs}
    - LangChain Document: converted to {page_content, metadata}
    - dict: recursively serialized
    - list/tuple: recursively serialized
    - set: converted to list
    - Other objects: converted to string representation

    Args:
        obj: Object to serialize

    Returns:
        JSON-compatible representation of the object
    """
    # Handle None
    if obj is None:
        return None

    # Handle primitives
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # Handle UUID
    if isinstance(obj, UUID):
        return str(obj)

    # Handle datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle object self conversion (for objects with .json() method)
    if hasattr(obj, 'json') and callable(obj.json):
        try:
            dump = obj.json()
            if isinstance(dump, str):
                return json.loads(dump)
            else:
                return dump
        except Exception:
            pass

    # Handle Pydantic models (v2 and v1)
    if hasattr(obj, "model_dump"):
        # Pydantic v2
        try:
            return serialize_for_json(obj.model_dump())
        except Exception as e:
            logger.debug(f"Error calling model_dump: {e}")
    elif hasattr(obj, "dict"):
        # Pydantic v1 or other objects with dict() method
        try:
            return serialize_for_json(obj.dict())
        except Exception as e:
            logger.debug(f"Error calling dict: {e}")

    # Handle LangChain BaseMessage objects
    try:
        from langchain_core.messages import BaseMessage
        if isinstance(obj, BaseMessage):
            result = {
                "role": obj.type if hasattr(obj, "type") else "unknown",
                "content": obj.content if hasattr(obj, "content") else str(obj),
            }
            # Include additional_kwargs if present and not empty
            if hasattr(obj, "additional_kwargs") and obj.additional_kwargs:
                result["additional_kwargs"] = serialize_for_json(obj.additional_kwargs)
            return result
    except ImportError:
        pass

    # Handle LangChain Document objects
    try:
        from langchain_core.documents import Document
        if isinstance(obj, Document):
            return {
                "page_content": obj.page_content,
                "metadata": serialize_for_json(obj.metadata) if hasattr(obj, "metadata") else {},
            }
    except ImportError:
        pass

    # Handle dictionaries
    if isinstance(obj, dict):
        return {
            key: serialize_for_json(value)
            for key, value in obj.items()
        }

    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]

    # Handle sets
    if isinstance(obj, set):
        return [serialize_for_json(item) for item in obj]

    # Fallback: convert to string
    try:
        return str(obj)
    except Exception as e:
        logger.debug(f"Error converting object to string: {e}")
        return "<unserializable>"
