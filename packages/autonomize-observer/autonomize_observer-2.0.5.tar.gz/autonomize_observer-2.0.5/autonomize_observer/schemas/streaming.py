"""Streaming trace event schemas for AI Studio (Langflow) integration.

These schemas define the custom streaming format used by AI Studio.
Events are sent to the genesis-traces-streaming Kafka topic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from autonomize_observer.schemas.base import generate_event_id, generate_span_id


class StreamingEventType(str, Enum):
    """Event types for streaming traces."""

    TRACE_START = "trace_start"
    TRACE_END = "trace_end"
    SPAN_START = "span_start"
    SPAN_END = "span_end"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    CUSTOM = "custom"


class TraceEvent(BaseModel):
    """Streaming trace event for Kafka.

    This is the format expected by the monitoring service's legacy consumer.
    """

    # Event identity
    event_id: str = Field(default_factory=generate_event_id)
    event_type: StreamingEventType
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Trace correlation
    trace_id: str
    span_id: str | None = None
    parent_span_id: str | None = None

    # Flow context
    flow_id: str | None = None
    flow_name: str | None = None

    # Component info
    component_name: str | None = None
    component_type: str | None = None
    component_index: int | None = None

    # Timing
    duration_ms: float | None = None

    # Data
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error: str | None = None

    # User context
    user_id: str | None = None
    session_id: str | None = None
    project_name: str = "GenesisStudio"

    # Extensibility
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "use_enum_values": True,
        "extra": "allow",
    }

    @classmethod
    def create_trace_start(
        cls,
        trace_id: str,
        flow_id: str,
        flow_name: str,
        user_id: str | None = None,
        session_id: str | None = None,
        project_name: str = "GenesisStudio",
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Create a trace_start event."""
        return cls(
            event_type=StreamingEventType.TRACE_START,
            trace_id=trace_id,
            flow_id=flow_id,
            flow_name=flow_name,
            user_id=user_id,
            session_id=session_id,
            project_name=project_name,
            metadata=metadata or {},
        )

    @classmethod
    def create_trace_end(
        cls,
        trace_id: str,
        duration_ms: float,
        flow_id: str | None = None,
        flow_name: str | None = None,
        error: str | None = None,
        output_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Create a trace_end event."""
        return cls(
            event_type=StreamingEventType.TRACE_END,
            trace_id=trace_id,
            duration_ms=duration_ms,
            flow_id=flow_id,
            flow_name=flow_name,
            error=error,
            output_data=output_data,
            metadata=metadata or {},
        )

    @classmethod
    def create_span_start(
        cls,
        trace_id: str,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        component_name: str | None = None,
        component_type: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Create a span_start event."""
        return cls(
            event_type=StreamingEventType.SPAN_START,
            trace_id=trace_id,
            span_id=span_id or generate_span_id(),
            parent_span_id=parent_span_id,
            component_name=component_name,
            component_type=component_type,
            input_data=input_data,
            metadata=metadata or {},
        )

    @classmethod
    def create_span_end(
        cls,
        trace_id: str,
        span_id: str,
        duration_ms: float,
        component_name: str | None = None,
        output_data: dict[str, Any] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Create a span_end event."""
        return cls(
            event_type=StreamingEventType.SPAN_END,
            trace_id=trace_id,
            span_id=span_id,
            duration_ms=duration_ms,
            component_name=component_name,
            output_data=output_data,
            error=error,
            metadata=metadata or {},
        )

    @classmethod
    def create_llm_call_start(
        cls,
        trace_id: str,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Create an llm_call_start event."""
        meta = metadata or {}
        if model:
            meta["model"] = model
        if provider:
            meta["provider"] = provider

        return cls(
            event_type=StreamingEventType.LLM_CALL_START,
            trace_id=trace_id,
            span_id=span_id or generate_span_id(),
            parent_span_id=parent_span_id,
            component_type="llm",
            input_data=input_data,
            metadata=meta,
        )

    @classmethod
    def create_llm_call_end(
        cls,
        trace_id: str,
        span_id: str,
        duration_ms: float,
        model: str | None = None,
        provider: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost: float | None = None,
        output_data: dict[str, Any] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Create an llm_call_end event."""
        meta = metadata or {}
        if model:
            meta["model"] = model
        if provider:
            meta["provider"] = provider
        if input_tokens is not None:
            meta["input_tokens"] = input_tokens
        if output_tokens is not None:
            meta["output_tokens"] = output_tokens
        if cost is not None:
            meta["cost"] = cost

        return cls(
            event_type=StreamingEventType.LLM_CALL_END,
            trace_id=trace_id,
            span_id=span_id,
            duration_ms=duration_ms,
            component_type="llm",
            output_data=output_data,
            error=error,
            metadata=meta,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(exclude_none=True, mode="json")

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(exclude_none=True)
