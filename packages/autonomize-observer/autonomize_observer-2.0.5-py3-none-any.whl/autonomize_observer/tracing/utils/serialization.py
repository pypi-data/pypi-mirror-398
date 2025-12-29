"""Serialization utilities for trace data.

Provides safe serialization of complex objects for Kafka transport.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


def safe_serialize(value: Any, max_depth: int = 10) -> Any:
    """Safely serialize a value for JSON transport.

    Handles complex types like datetime, UUID, custom objects, etc.

    Args:
        value: Value to serialize
        max_depth: Maximum recursion depth

    Returns:
        JSON-serializable value
    """
    if max_depth <= 0:
        return str(value)

    if value is None:
        return None

    # Basic types
    if isinstance(value, (str, int, float, bool)):
        return value

    # UUID
    if isinstance(value, UUID):
        return str(value)

    # Datetime
    if isinstance(value, datetime):
        return value.isoformat()

    # Bytes
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return f"<bytes: {len(value)} bytes>"

    # Dictionary
    if isinstance(value, dict):
        return {
            safe_serialize(k, max_depth - 1): safe_serialize(v, max_depth - 1)
            for k, v in value.items()
        }

    # List/Tuple
    if isinstance(value, (list, tuple)):
        return [safe_serialize(item, max_depth - 1) for item in value]

    # Set
    if isinstance(value, set):
        return [safe_serialize(item, max_depth - 1) for item in value]

    # Langflow Message objects (check before __dict__)
    if hasattr(value, "text") and isinstance(getattr(value, "text", None), str):
        return getattr(value, "text")

    # LangChain message objects (check before __dict__)
    if hasattr(value, "content") and isinstance(getattr(value, "content", None), str):
        return getattr(value, "content")

    # LangChain document objects (check before __dict__)
    if hasattr(value, "page_content") and isinstance(
        getattr(value, "page_content", None), str
    ):
        return getattr(value, "page_content")

    # Pydantic models
    if hasattr(value, "model_dump"):
        try:
            return safe_serialize(value.model_dump(), max_depth - 1)
        except Exception:
            pass

    # Objects with to_dict method
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict", None)):
        try:
            result = value.to_dict()
            if result is not None:
                return safe_serialize(result, max_depth - 1)
        except Exception:
            pass

    # Objects with __dict__ (fallback)
    try:
        obj_dict = getattr(value, "__dict__", None)
        if obj_dict:
            return safe_serialize(obj_dict, max_depth - 1)
    except Exception:
        pass

    # Fallback to string representation
    try:
        return str(value)
    except Exception as e:
        logger.warning(f"Failed to serialize value of type {type(value)}: {e}")
        return f"<unserializable: {type(value).__name__}>"
