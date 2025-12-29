"""Tests for streaming event schemas."""

import pytest

from autonomize_observer.schemas.streaming import StreamingEventType, TraceEvent


class TestStreamingEventType:
    """Tests for StreamingEventType enum."""

    def test_event_types(self) -> None:
        """Test all event types exist."""
        assert StreamingEventType.TRACE_START == "trace_start"
        assert StreamingEventType.TRACE_END == "trace_end"
        assert StreamingEventType.SPAN_START == "span_start"
        assert StreamingEventType.SPAN_END == "span_end"
        assert StreamingEventType.LLM_CALL_START == "llm_call_start"
        assert StreamingEventType.LLM_CALL_END == "llm_call_end"
        assert StreamingEventType.CUSTOM == "custom"


class TestTraceEvent:
    """Tests for TraceEvent model."""

    def test_basic_creation(self) -> None:
        """Test basic event creation."""
        event = TraceEvent(
            event_type=StreamingEventType.TRACE_START,
            trace_id="test-trace-123",
        )
        assert event.event_type == StreamingEventType.TRACE_START
        assert event.trace_id == "test-trace-123"
        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.project_name == "GenesisStudio"

    def test_full_creation(self) -> None:
        """Test full event creation with all fields."""
        event = TraceEvent(
            event_type=StreamingEventType.SPAN_END,
            trace_id="trace-123",
            span_id="span-456",
            parent_span_id="span-parent",
            flow_id="flow-789",
            flow_name="Test Flow",
            component_name="TestComponent",
            component_type="llm",
            duration_ms=150.5,
            input_data={"prompt": "Hello"},
            output_data={"response": "World"},
            error="Test error",
            user_id="user-123",
            session_id="session-456",
            project_name="TestProject",
            metadata={"key": "value"},
        )
        assert event.trace_id == "trace-123"
        assert event.span_id == "span-456"
        assert event.parent_span_id == "span-parent"
        assert event.flow_id == "flow-789"
        assert event.flow_name == "Test Flow"
        assert event.component_name == "TestComponent"
        assert event.component_type == "llm"
        assert event.duration_ms == 150.5
        assert event.input_data == {"prompt": "Hello"}
        assert event.output_data == {"response": "World"}
        assert event.error == "Test error"
        assert event.user_id == "user-123"
        assert event.session_id == "session-456"
        assert event.project_name == "TestProject"
        assert event.metadata == {"key": "value"}


class TestTraceEventFactories:
    """Tests for TraceEvent factory methods."""

    def test_create_trace_start(self) -> None:
        """Test trace_start event creation."""
        event = TraceEvent.create_trace_start(
            trace_id="trace-123",
            flow_id="flow-456",
            flow_name="My Flow",
            user_id="user-789",
            session_id="session-abc",
            project_name="TestProject",
            metadata={"env": "test"},
        )
        assert event.event_type == StreamingEventType.TRACE_START
        assert event.trace_id == "trace-123"
        assert event.flow_id == "flow-456"
        assert event.flow_name == "My Flow"
        assert event.user_id == "user-789"
        assert event.session_id == "session-abc"
        assert event.project_name == "TestProject"
        assert event.metadata == {"env": "test"}

    def test_create_trace_end(self) -> None:
        """Test trace_end event creation."""
        event = TraceEvent.create_trace_end(
            trace_id="trace-123",
            duration_ms=500.0,
            flow_id="flow-456",
            flow_name="My Flow",
            error="Something went wrong",
            output_data={"result": "done"},
            metadata={"spans": 5},
        )
        assert event.event_type == StreamingEventType.TRACE_END
        assert event.trace_id == "trace-123"
        assert event.duration_ms == 500.0
        assert event.flow_id == "flow-456"
        assert event.flow_name == "My Flow"
        assert event.error == "Something went wrong"
        assert event.output_data == {"result": "done"}
        assert event.metadata == {"spans": 5}

    def test_create_span_start(self) -> None:
        """Test span_start event creation."""
        event = TraceEvent.create_span_start(
            trace_id="trace-123",
            span_id="span-456",
            parent_span_id="span-parent",
            component_name="LLMComponent",
            component_type="llm",
            input_data={"prompt": "Hello"},
            metadata={"model": "gpt-4"},
        )
        assert event.event_type == StreamingEventType.SPAN_START
        assert event.trace_id == "trace-123"
        assert event.span_id == "span-456"
        assert event.parent_span_id == "span-parent"
        assert event.component_name == "LLMComponent"
        assert event.component_type == "llm"
        assert event.input_data == {"prompt": "Hello"}
        assert event.metadata == {"model": "gpt-4"}

    def test_create_span_start_generates_span_id(self) -> None:
        """Test span_start generates span_id if not provided."""
        event = TraceEvent.create_span_start(
            trace_id="trace-123",
            component_name="Component",
        )
        assert event.span_id is not None
        assert len(event.span_id) == 16  # 8 bytes = 16 hex chars

    def test_create_span_end(self) -> None:
        """Test span_end event creation."""
        event = TraceEvent.create_span_end(
            trace_id="trace-123",
            span_id="span-456",
            duration_ms=100.0,
            component_name="LLMComponent",
            output_data={"response": "World"},
            error="Error occurred",
            metadata={"tokens": 150},
        )
        assert event.event_type == StreamingEventType.SPAN_END
        assert event.trace_id == "trace-123"
        assert event.span_id == "span-456"
        assert event.duration_ms == 100.0
        assert event.component_name == "LLMComponent"
        assert event.output_data == {"response": "World"}
        assert event.error == "Error occurred"
        assert event.metadata == {"tokens": 150}

    def test_create_llm_call_start(self) -> None:
        """Test llm_call_start event creation."""
        event = TraceEvent.create_llm_call_start(
            trace_id="trace-123",
            span_id="span-456",
            parent_span_id="span-parent",
            model="gpt-4",
            provider="openai",
            input_data={"messages": [{"role": "user", "content": "Hi"}]},
            metadata={"temperature": 0.7},
        )
        assert event.event_type == StreamingEventType.LLM_CALL_START
        assert event.trace_id == "trace-123"
        assert event.span_id == "span-456"
        assert event.parent_span_id == "span-parent"
        assert event.component_type == "llm"
        assert event.metadata["model"] == "gpt-4"
        assert event.metadata["provider"] == "openai"
        assert event.metadata["temperature"] == 0.7

    def test_create_llm_call_start_generates_span_id(self) -> None:
        """Test llm_call_start generates span_id if not provided."""
        event = TraceEvent.create_llm_call_start(
            trace_id="trace-123",
        )
        assert event.span_id is not None
        assert len(event.span_id) == 16

    def test_create_llm_call_end(self) -> None:
        """Test llm_call_end event creation."""
        event = TraceEvent.create_llm_call_end(
            trace_id="trace-123",
            span_id="span-456",
            duration_ms=250.0,
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            cost=0.005,
            output_data={"response": "Hello!"},
            error=None,
            metadata={"finish_reason": "stop"},
        )
        assert event.event_type == StreamingEventType.LLM_CALL_END
        assert event.trace_id == "trace-123"
        assert event.span_id == "span-456"
        assert event.duration_ms == 250.0
        assert event.component_type == "llm"
        assert event.output_data == {"response": "Hello!"}
        assert event.metadata["model"] == "gpt-4"
        assert event.metadata["provider"] == "openai"
        assert event.metadata["input_tokens"] == 100
        assert event.metadata["output_tokens"] == 50
        assert event.metadata["cost"] == 0.005
        assert event.metadata["finish_reason"] == "stop"

    def test_create_llm_call_end_with_error(self) -> None:
        """Test llm_call_end with error."""
        event = TraceEvent.create_llm_call_end(
            trace_id="trace-123",
            span_id="span-456",
            duration_ms=50.0,
            error="Rate limit exceeded",
        )
        assert event.error == "Rate limit exceeded"


class TestTraceEventSerialization:
    """Tests for TraceEvent serialization."""

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        event = TraceEvent(
            event_type=StreamingEventType.TRACE_START,
            trace_id="trace-123",
            flow_id="flow-456",
        )
        result = event.to_dict()
        assert isinstance(result, dict)
        assert result["event_type"] == "trace_start"
        assert result["trace_id"] == "trace-123"
        assert result["flow_id"] == "flow-456"
        assert "event_id" in result
        assert "timestamp" in result
        # None values should be excluded
        assert "span_id" not in result
        assert "error" not in result

    def test_to_json(self) -> None:
        """Test conversion to JSON string."""
        event = TraceEvent(
            event_type=StreamingEventType.SPAN_START,
            trace_id="trace-123",
            span_id="span-456",
        )
        result = event.to_json()
        assert isinstance(result, str)
        assert '"event_type":"span_start"' in result
        assert '"trace_id":"trace-123"' in result
        assert '"span_id":"span-456"' in result

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        event = TraceEvent(
            event_type=StreamingEventType.CUSTOM,
            trace_id="trace-123",
            custom_field="custom_value",  # Extra field
        )
        assert event.trace_id == "trace-123"
        # Extra field should be accessible
        assert event.model_extra.get("custom_field") == "custom_value"
