"""Base event schema for all Autonomize Observer events."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from autonomize_observer.schemas.enums import EventCategory


def generate_event_id() -> str:
    """Generate unique event ID (16 hex chars)."""
    return secrets.token_hex(8)


def generate_trace_id() -> str:
    """Generate W3C trace ID (32 hex chars)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate W3C span ID (16 hex chars)."""
    return secrets.token_hex(8)


def current_time_iso() -> str:
    """Get current time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def current_time_nano() -> int:
    """Get current time in nanoseconds since epoch."""
    return int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)


class BaseEvent(BaseModel):
    """Base class for all events in the system.

    All events share common metadata for:
    - Identification (event_id, timestamp)
    - Correlation (trace_id, span_id)
    - Context (user_id, session_id, project_name)
    - Schema versioning
    """

    # === Event Identity ===
    event_id: str = Field(default_factory=generate_event_id)
    event_category: EventCategory = EventCategory.TRACE
    event_type: str = "unknown"
    timestamp: str = Field(default_factory=current_time_iso)
    timestamp_unix_nano: int = Field(default_factory=current_time_nano)

    # === Correlation ===
    trace_id: str | None = None  # W3C trace ID for correlation
    span_id: str | None = None  # W3C span ID
    parent_span_id: str | None = None
    correlation_id: str | None = None  # Business correlation

    # === Context ===
    user_id: str | None = None
    session_id: str | None = None
    project_name: str = "GenesisStudio"
    environment: str = "production"

    # === Source ===
    service_name: str = "autonomize-observer"
    service_version: str = "2.0.0"
    source_ip: str | None = None
    user_agent: str | None = None

    # === Schema ===
    schema_version: str = "2.0.0"

    # === Extensibility ===
    attributes: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    model_config = {
        "use_enum_values": True,
        "extra": "allow",
    }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(exclude_none=True, mode="json")

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseEvent:
        """Create event from dictionary."""
        return cls.model_validate(data)
