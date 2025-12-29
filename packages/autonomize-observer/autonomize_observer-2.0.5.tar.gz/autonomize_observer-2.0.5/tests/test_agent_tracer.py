"""Tests for AgentTracer."""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest


class TestStreamingTraceContext:
    """Tests for StreamingTraceContext."""

    def test_basic_creation(self) -> None:
        """Test basic context creation."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
        )

        assert context.trace_id == "trace-123"
        assert context.flow_id == "flow-456"
        assert context.trace_name == "Test Flow"
        assert context.project_name == "GenesisStudio"
        assert context.user_id is None
        assert context.session_id is None
        assert context.start_time > 0

    def test_full_creation(self) -> None:
        """Test full context creation."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
            project_name="CustomProject",
            user_id="user-789",
            session_id="session-abc",
        )

        assert context.project_name == "CustomProject"
        assert context.user_id == "user-789"
        assert context.session_id == "session-abc"

    def test_add_and_complete_span(self) -> None:
        """Test adding and completing spans."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
        )

        # Add a span
        span_info = {"span_id": "span-1", "component_name": "Test"}
        context.add_span("span-1", span_info)

        assert context.get_span_count() == 1

        # Complete the span
        completed = context.complete_span("span-1")
        assert completed == span_info
        assert context.get_span_count() == 1  # Still counts completed

    def test_complete_unknown_span(self) -> None:
        """Test completing an unknown span."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
        )

        result = context.complete_span("unknown-span")
        assert result is None

    def test_update_tags(self) -> None:
        """Test updating tags."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
        )

        context.update_tags({"env": "test", "version": "1.0"})
        assert context.tags == {"env": "test", "version": "1.0"}

        context.update_tags({"env": "prod"})
        assert context.tags == {"env": "prod", "version": "1.0"}

    def test_set_param(self) -> None:
        """Test setting parameters."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
        )

        context.set_param("model", "gpt-4")
        context.set_param("temperature", 0.7)
        assert context.params == {"model": "gpt-4", "temperature": 0.7}

    def test_set_metric(self) -> None:
        """Test setting metrics."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
        )

        context.set_metric("latency", 100.5)
        context.set_metric("tokens", 500.0)
        assert context.metrics == {"latency": 100.5, "tokens": 500.0}

    def test_add_token_usage(self) -> None:
        """Test adding token usage."""
        from autonomize_observer.tracing.agent_tracer import StreamingTraceContext

        context = StreamingTraceContext(
            trace_id="trace-123",
            flow_id="flow-456",
            trace_name="Test Flow",
        )

        context.add_token_usage(100, 50, 0.005)
        assert context.total_input_tokens == 100
        assert context.total_output_tokens == 50
        assert context.total_cost == 0.005

        context.add_token_usage(200, 100, 0.01)
        assert context.total_input_tokens == 300
        assert context.total_output_tokens == 150
        assert context.total_cost == 0.015


class TestAgentTracerInit:
    """Tests for AgentTracer initialization."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", False)
    def test_init_without_kafka(self) -> None:
        """Test initialization when Kafka is not available."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        # Should not be ready since Kafka isn't available
        assert tracer.ready is False

    def test_init_without_bootstrap_servers(self) -> None:
        """Test initialization without bootstrap servers."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        assert tracer.ready is False

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_init_with_kafka(self, mock_producer_class: MagicMock) -> None:
        """Test initialization with Kafka configured."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow - UUID",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            project_name="TestProject",
            user_id="user-456",
            session_id="session-789",
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic="test-topic",
            kafka_username="user",
            kafka_password="pass",
        )

        assert tracer.ready is True
        assert tracer.trace_name == "Test Flow"  # Cleaned
        assert tracer.flow_id == "flow-123"
        assert tracer.project_name == "TestProject"
        assert tracer.user_id == "user-456"
        assert tracer.session_id == "session-789"


class TestAgentTracerMethods:
    """Tests for AgentTracer methods."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_start_trace(self, mock_producer_class: MagicMock) -> None:
        """Test starting a trace."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        mock_producer.send_trace_start.assert_called_once()
        assert tracer._trace_context is not None

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_add_trace(self, mock_producer_class: MagicMock) -> None:
        """Test adding a trace (starting a span)."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_trace(
            trace_id="component-1",
            trace_name="LLMComponent",
            trace_type="llm",
            inputs={"prompt": "Hello"},
            metadata={"model": "gpt-4"},
        )

        mock_producer.send_span_start.assert_called_once()

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_trace_span(self, mock_producer_class: MagicMock) -> None:
        """Test ending a trace (ending a span)."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = True
        mock_producer.send_span_end.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_trace(
            trace_id="component-1",
            trace_name="LLMComponent",
            trace_type="llm",
            inputs={"prompt": "Hello"},
        )
        tracer.end_trace(
            trace_id="component-1",
            trace_name="LLMComponent",
            outputs={"response": "World"},
        )

        mock_producer.send_span_end.assert_called_once()

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_trace_with_error(self, mock_producer_class: MagicMock) -> None:
        """Test ending a trace with an error."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = True
        mock_producer.send_span_end.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_trace(
            trace_id="component-1",
            trace_name="LLMComponent",
            trace_type="llm",
            inputs={"prompt": "Hello"},
        )

        error = Exception("Test error")
        tracer.end_trace(
            trace_id="component-1",
            trace_name="LLMComponent",
            error=error,
        )

        # Check that error was passed
        call_args = mock_producer.send_span_end.call_args
        assert "Test error" in str(call_args)

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end(self, mock_producer_class: MagicMock) -> None:
        """Test ending the entire trace."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_trace_end.return_value = True
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.end(
            inputs={"input": "test"},
            outputs={"output": "result"},
        )

        mock_producer.send_trace_end.assert_called_once()
        mock_producer.flush.assert_called()

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_add_tags(self, mock_producer_class: MagicMock) -> None:
        """Test adding tags."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_tags({"env": "test"})

        assert tracer._trace_context.tags == {"env": "test"}

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_log_param(self, mock_producer_class: MagicMock) -> None:
        """Test logging a parameter."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.log_param("model", "gpt-4")

        assert tracer._trace_context.params == {"model": "gpt-4"}

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_log_metric(self, mock_producer_class: MagicMock) -> None:
        """Test logging a metric."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.log_metric("latency", 100.5)

        assert tracer._trace_context.metrics == {"latency": 100.5}

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_get_langchain_callback(self, mock_producer_class: MagicMock) -> None:
        """Test getting LangChain callback."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        callback = tracer.get_langchain_callback()
        # Currently returns None
        assert callback is None

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_close(self, mock_producer_class: MagicMock) -> None:
        """Test closing the tracer."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.close()

        mock_producer.flush.assert_called()
        mock_producer.close.assert_called()
        assert tracer.ready is False

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_context_manager(self, mock_producer_class: MagicMock) -> None:
        """Test context manager usage."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        with AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        ) as tracer:
            assert tracer is not None

        mock_producer.close.assert_called()


class TestAgentTracerTokenExtraction:
    """Tests for token extraction from outputs."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_direct_tokens(self, mock_producer_class: MagicMock) -> None:
        """Test extracting tokens from direct fields."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        outputs = {
            "input_tokens": 100,
            "output_tokens": 50,
            "model": "gpt-4",
        }

        # Use token extractor chain (Strategy pattern)
        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["model"] == "gpt-4"

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_openai_format_tokens(self, mock_producer_class: MagicMock) -> None:
        """Test extracting tokens from OpenAI format."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        outputs = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
            },
            "model": "gpt-4",
        }

        # Use token extractor chain (Strategy pattern)
        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_langchain_format_tokens(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test extracting tokens from LangChain format."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        outputs = {
            "response_metadata": {
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                },
                "model_name": "gpt-4",
            }
        }

        # Use token extractor chain (Strategy pattern)
        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["model"] == "gpt-4"

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_empty_outputs(self, mock_producer_class: MagicMock) -> None:
        """Test extracting from empty outputs."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        # Use token extractor chain (Strategy pattern)
        assert tracer._token_extractor.extract({}) is None
        assert tracer._token_extractor.extract(None) is None


class TestAgentTracerCleanTraceName:
    """Tests for trace name cleaning."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_clean_trace_name_with_uuid(self, mock_producer_class: MagicMock) -> None:
        """Test cleaning trace name with UUID suffix."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="My Flow - 12345678-1234-5678-1234-567812345678",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        assert tracer.trace_name == "My Flow"

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_clean_trace_name_without_suffix(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test cleaning trace name without suffix."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Simple Flow Name",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        assert tracer.trace_name == "Simple Flow Name"

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_clean_empty_trace_name(self, mock_producer_class: MagicMock) -> None:
        """Test cleaning empty trace name."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        assert tracer.trace_name == "unknown"


class TestAgentTracerNotReady:
    """Tests for AgentTracer when not ready."""

    def test_start_trace_not_ready(self) -> None:
        """Test start_trace when Kafka not ready (still creates context for OTEL)."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,  # No Kafka
        )

        # Should not raise - trace context is created even without Kafka (for OTEL support)
        tracer.start_trace()
        # Trace context is now always created to support OTEL-only mode
        assert tracer._trace_context is not None
        assert tracer._trace_context.trace_id == "12345678-1234-5678-1234-567812345678"
        assert tracer.ready is False  # Still not ready for Kafka

    def test_add_trace_not_ready(self) -> None:
        """Test add_trace when not ready."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        # Should not raise
        tracer.add_trace("comp-1", "Component", "llm", {})

    def test_end_trace_not_ready(self) -> None:
        """Test end_trace when not ready."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        # Should not raise
        tracer.end_trace("comp-1", "Component", {})

    def test_end_not_ready(self) -> None:
        """Test end when not ready."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        # Should not raise
        tracer.end({}, {})

    def test_add_tags_no_context(self) -> None:
        """Test add_tags without context."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        # Should not raise
        tracer.add_tags({"env": "test"})

    def test_log_param_no_context(self) -> None:
        """Test log_param without context."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        # Should not raise
        tracer.log_param("key", "value")

    def test_log_metric_no_context(self) -> None:
        """Test log_metric without context."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        # Should not raise
        tracer.log_metric("key", 100.0)


class TestAgentTracerExceptionHandling:
    """Tests for exception handling."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_setup_producer_exception(self, mock_producer_class: MagicMock) -> None:
        """Test producer setup exception handling."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer_class.side_effect = Exception("Connection failed")

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        assert tracer.ready is False

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_start_trace_exception(self, mock_producer_class: MagicMock) -> None:
        """Test start_trace exception handling."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.side_effect = Exception("Send failed")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        # Should not raise
        tracer.start_trace()

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_start_trace_send_failure(self, mock_producer_class: MagicMock) -> None:
        """Test start_trace when send returns False."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = False
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        # Should still create context even if send fails
        assert tracer._trace_context is not None

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_add_trace_exception(self, mock_producer_class: MagicMock) -> None:
        """Test add_trace exception handling."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.side_effect = Exception("Send failed")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        # Should not raise
        tracer.add_trace("comp-1", "Component", "llm", {})

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_add_trace_send_failure(self, mock_producer_class: MagicMock) -> None:
        """Test add_trace when send returns False."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = False
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "Component", "llm", {})
        # Span should still be tracked
        assert tracer._trace_context.get_span_count() == 1

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_trace_exception(self, mock_producer_class: MagicMock) -> None:
        """Test end_trace exception handling."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = True
        mock_producer.send_span_end.side_effect = Exception("Send failed")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "Component", "llm", {})
        # Should not raise
        tracer.end_trace("comp-1", "Component")

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_trace_send_failure(self, mock_producer_class: MagicMock) -> None:
        """Test end_trace when send returns False."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = True
        mock_producer.send_span_end.return_value = False
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "Component", "llm", {})
        tracer.end_trace("comp-1", "Component")

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_trace_unknown_span(self, mock_producer_class: MagicMock) -> None:
        """Test end_trace for unknown span."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        # Try to end a span that was never started
        tracer.end_trace("unknown-span", "Component")
        # Should just log warning, not raise

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_exception(self, mock_producer_class: MagicMock) -> None:
        """Test end exception handling."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_trace_end.side_effect = Exception("Send failed")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        # Should not raise
        tracer.end({}, {})

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_send_failure(self, mock_producer_class: MagicMock) -> None:
        """Test end when send returns False."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_trace_end.return_value = False
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.end({}, {})

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_close_exception(self, mock_producer_class: MagicMock) -> None:
        """Test close exception handling."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.flush.side_effect = Exception("Flush failed")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        # Should not raise
        tracer.close()

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_flush_exception(self, mock_producer_class: MagicMock) -> None:
        """Test flush exception handling."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_trace_end.return_value = True
        mock_producer.flush.side_effect = Exception("Flush failed")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        # Should not raise even if flush fails
        tracer.end({}, {})


class TestAgentTracerTokenCostCalculation:
    """Tests for token usage and cost calculation in end_trace."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_trace_with_token_usage(self, mock_producer_class: MagicMock) -> None:
        """Test end_trace extracts tokens and calculates cost."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = True
        mock_producer.send_span_end.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {"prompt": "Hello"})
        tracer.end_trace(
            "comp-1",
            "LLMComponent",
            outputs={
                "response": "World",
                "model": "gpt-4",  # model key triggers token aggregation
                "input_tokens": 100,
                "output_tokens": 50,
            },
        )

        # Tokens were extracted and aggregated
        assert tracer._trace_context.total_input_tokens == 100
        assert tracer._trace_context.total_output_tokens == 50
        assert tracer._trace_context.total_cost >= 0  # Cost should be calculated

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_llm_output_format(self, mock_producer_class: MagicMock) -> None:
        """Test extracting tokens from llm_output format."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        outputs = {
            "llm_output": {
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                },
                "model_name": "gpt-4",
            }
        }

        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["model"] == "gpt-4"

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_prompt_completion_tokens(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test extracting prompt_tokens/completion_tokens format."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        outputs = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "model_name": "gpt-4",
        }

        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_usage_input_output_tokens(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test extracting input_tokens/output_tokens from usage object."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        outputs = {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
            }
        }

        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_with_error(self, mock_producer_class: MagicMock) -> None:
        """Test end() with an error."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_trace_end.return_value = True
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        error = ValueError("Something went wrong")
        tracer.end({}, {}, error=error)

        # Check that error was passed
        call_args = mock_producer.send_trace_end.call_args
        assert "Something went wrong" in str(call_args)

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_end_with_metadata(self, mock_producer_class: MagicMock) -> None:
        """Test end() with additional metadata."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_trace_end.return_value = True
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.add_tags({"env": "test"})
        tracer.log_param("model", "gpt-4")
        tracer.log_metric("latency", 100.0)
        tracer.end({}, {}, metadata={"custom": "data"})

        mock_producer.send_trace_end.assert_called_once()


class TestAgentTracerFlushPending:
    """Tests for flush with pending messages."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_flush_with_pending(self, mock_producer_class: MagicMock) -> None:
        """Test flush when messages are still pending."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_trace_end.return_value = True
        mock_producer.flush.return_value = 5  # 5 messages still pending
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()
        tracer.end({}, {})

        # Should still complete without error


class TestAgentTracerDestructor:
    """Tests for destructor (__del__)."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_del_calls_close(self, mock_producer_class: MagicMock) -> None:
        """Test that __del__ calls close."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        # Manually call __del__
        tracer.__del__()

        mock_producer.close.assert_called()

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_del_exception_handling(self, mock_producer_class: MagicMock) -> None:
        """Test that __del__ handles exceptions."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.flush.side_effect = Exception("Close failed")
        mock_producer.close.side_effect = Exception("Close failed")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        # Should not raise
        tracer.__del__()

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_close_logs_error(self, mock_producer_class: MagicMock) -> None:
        """Test that close logs errors."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.flush.side_effect = Exception("Flush error")
        mock_producer.close.side_effect = Exception("Close error")
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        # Should log error, not raise
        tracer.close()


class TestAgentTracerBranchCoverage:
    """Additional tests for branch coverage."""

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_response_metadata_token_usage(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test extracting from response_metadata.token_usage format."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        # LangChain format with token_usage and model_name
        outputs = {
            "response_metadata": {
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                },
                "model_name": "claude-3-sonnet",
            }
        }

        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["model"] == "claude-3-sonnet"

    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_extract_llm_output_with_token_usage(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test extracting from llm_output.token_usage format."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer_class.return_value = mock_producer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
        )

        tracer.start_trace()

        outputs = {
            "llm_output": {
                "token_usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 75,
                },
                "model_name": "gpt-3.5-turbo",
            }
        }

        usage = tracer._token_extractor.extract(outputs)

        assert usage is not None
        assert usage["input_tokens"] == 200
        assert usage["output_tokens"] == 75
        assert usage["model"] == "gpt-3.5-turbo"


class TestAgentTracerOTEL:
    """Tests for OTEL/Logfire support in AgentTracer."""

    def test_otel_disabled_by_default(self) -> None:
        """Test that OTEL is disabled by default."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,
        )

        assert tracer._enable_otel is False
        assert tracer._otel_trace_span is None

    def test_otel_enabled_without_kafka(self) -> None:
        """Test OTEL can be enabled without Kafka."""
        from autonomize_observer.core.imports import LOGFIRE_AVAILABLE
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers=None,  # No Kafka
            enable_otel=True,
        )

        # OTEL enabled depends on logfire availability
        assert tracer._enable_otel == LOGFIRE_AVAILABLE
        assert tracer.ready is False  # Kafka not ready
        # But trace operations should still work for OTEL
        tracer.start_trace()
        assert tracer._trace_context is not None

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False)
    def test_otel_disabled_when_logfire_not_available(self) -> None:
        """Test OTEL is disabled when logfire is not installed."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,  # Try to enable
        )

        # Should be disabled since OTELManager won't be available
        # When LOGFIRE_AVAILABLE is False, _otel_manager will be None
        assert tracer._otel_manager is None or not tracer._otel_manager.is_available

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_setup_success(self, mock_logfire: MagicMock) -> None:
        """Test OTEL setup succeeds."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
            otel_service_name="test-service",
            send_to_logfire=False,
        )

        mock_logfire.configure.assert_called_once()
        # Check OTEL manager is configured and available
        assert tracer._otel_manager is not None
        assert tracer._otel_manager.is_available is True

    def test_otel_manager_injected(self) -> None:
        """Test that an OTELManager can be injected."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer
        from autonomize_observer.tracing.otel_utils import OTELManager

        # Create a mock OTELManager
        mock_manager = MagicMock(spec=OTELManager)
        mock_manager.is_available = True

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            otel_manager=mock_manager,  # Inject the manager
        )

        # Should use the injected manager
        assert tracer._otel_manager is mock_manager
        assert tracer._enable_otel is True

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_start_trace_creates_span(self, mock_logfire: MagicMock) -> None:
        """Test start_trace creates OTEL span."""
        mock_span = MagicMock()
        mock_logfire.span.return_value.__enter__ = MagicMock(return_value=mock_span)

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()

        mock_logfire.span.assert_called()
        assert tracer._otel_trace_span is not None

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_start_trace_exception(self, mock_logfire: MagicMock) -> None:
        """Test start_trace handles OTEL span exception."""
        mock_logfire.span.side_effect = Exception("Span failed")

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        # Should not raise
        tracer.start_trace()
        assert tracer._trace_context is not None

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_add_trace_creates_child_span(self, mock_logfire: MagicMock) -> None:
        """Test add_trace creates OTEL child span."""
        mock_span = MagicMock()
        mock_logfire.span.return_value.__enter__ = MagicMock(return_value=mock_span)

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {"prompt": "test"})

        # Should have created a child span
        assert "comp-1" in tracer._otel_spans

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_add_trace_exception(self, mock_logfire: MagicMock) -> None:
        """Test add_trace handles OTEL span exception."""
        # First call for trace span succeeds
        mock_trace_span = MagicMock()
        mock_trace_span.__enter__ = MagicMock(return_value=mock_trace_span)
        # Second call for component span fails
        mock_logfire.span.side_effect = [mock_trace_span, Exception("Span failed")]

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        # Should not raise
        tracer.add_trace("comp-1", "LLMComponent", "llm", {})

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_end_trace_closes_child_span(self, mock_logfire: MagicMock) -> None:
        """Test end_trace closes OTEL child span."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {})
        tracer.end_trace("comp-1", "LLMComponent", {"response": "test"})

        # Span should be closed and removed
        assert "comp-1" not in tracer._otel_spans
        mock_span.__exit__.assert_called()

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_end_trace_with_error(self, mock_logfire: MagicMock) -> None:
        """Test end_trace passes error to OTEL span."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {})
        error = ValueError("Test error")
        tracer.end_trace("comp-1", "LLMComponent", error=error)

        # Should have set error attribute
        mock_span.set_attribute.assert_any_call("error", "Test error")

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_end_trace_close_exception(self, mock_logfire: MagicMock) -> None:
        """Test end_trace handles OTEL span close exception."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(side_effect=Exception("Close failed"))
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {})
        # Should not raise
        tracer.end_trace("comp-1", "LLMComponent")

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_end_closes_trace_span(self, mock_logfire: MagicMock) -> None:
        """Test end() closes OTEL trace span."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.end({}, {})

        # Trace span should be closed
        assert tracer._otel_trace_span is None
        mock_span.__exit__.assert_called()

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_end_close_exception(self, mock_logfire: MagicMock) -> None:
        """Test end() handles OTEL span close exception."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(side_effect=Exception("Close failed"))
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        # Should not raise
        tracer.end({}, {})

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_close_cleans_up_spans(self, mock_logfire: MagicMock) -> None:
        """Test close() cleans up OTEL spans."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {})
        # Close without ending spans
        tracer.close()

        # All spans should be cleaned up
        assert len(tracer._otel_spans) == 0
        assert tracer._otel_trace_span is None

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_close_handles_span_exceptions(self, mock_logfire: MagicMock) -> None:
        """Test close() handles exceptions when closing spans."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(side_effect=Exception("Close failed"))
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {})
        # Should not raise
        tracer.close()


class TestAgentTracerDualExport:
    """Tests for dual export (Kafka + OTEL) mode."""

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    @patch("autonomize_observer.tracing.agent_tracer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.agent_tracer.KafkaTraceProducer")
    def test_dual_export_full_workflow(
        self,
        mock_producer_class: MagicMock,
        mock_logfire: MagicMock,
    ) -> None:
        """Test full workflow with both Kafka and OTEL enabled."""
        # Setup mocks
        mock_producer = MagicMock()
        mock_producer.send_trace_start.return_value = True
        mock_producer.send_span_start.return_value = True
        mock_producer.send_span_end.return_value = True
        mock_producer.send_trace_end.return_value = True
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_span.set_attribute = MagicMock()
        mock_logfire.span.return_value = mock_span

        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
            enable_otel=True,
        )

        # Full workflow
        tracer.start_trace()
        tracer.add_trace("comp-1", "LLMComponent", "llm", {"prompt": "test"})
        tracer.end_trace(
            "comp-1",
            "LLMComponent",
            {
                "response": "test",
                "model": "gpt-4",
                "input_tokens": 100,
                "output_tokens": 50,
            },
        )
        tracer.end({}, {})

        # Verify both Kafka and OTEL calls
        mock_producer.send_trace_start.assert_called_once()
        mock_producer.send_span_start.assert_called_once()
        mock_producer.send_span_end.assert_called_once()
        mock_producer.send_trace_end.assert_called_once()

        # OTEL spans created and closed
        assert mock_logfire.span.call_count >= 2  # Trace + component spans
        assert mock_span.__exit__.call_count >= 2


class TestAgentTracerWithKafkaConfig:
    """Tests for AgentTracer with KafkaConfig object."""

    @patch("autonomize_observer.core.imports.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.core.imports.ConfluentProducer")
    def test_init_with_kafka_config(self, mock_producer_class: MagicMock) -> None:
        """Test AgentTracer initialization with KafkaConfig object."""
        from autonomize_observer.core.config import KafkaConfig
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        kafka_config = KafkaConfig(
            bootstrap_servers="kafka.example.com:9093",
            trace_topic="custom-traces",
            sasl_username="user123",
            sasl_password="pass456",
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-256",
        )

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_config=kafka_config,
        )

        # Verify config was applied
        assert tracer._kafka_bootstrap_servers == "kafka.example.com:9093"
        assert tracer._kafka_topic == "custom-traces"
        assert tracer._kafka_username == "user123"
        assert tracer._kafka_password == "pass456"
        assert tracer._security_protocol == "SASL_SSL"
        assert tracer._sasl_mechanism == "SCRAM-SHA-256"

        tracer.close()


class TestAgentTracerOTELExceptionHandling:
    """Tests for OTEL exception handling in AgentTracer."""

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    @patch("autonomize_observer.core.imports.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.core.imports.ConfluentProducer")
    def test_otel_manager_init_failure(
        self, mock_producer_class: MagicMock, mock_logfire: MagicMock
    ) -> None:
        """Test AgentTracer handles OTELManager init failure gracefully."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer
        from autonomize_observer.tracing.otel_utils import OTELManager

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        # Make OTELManager.__init__ raise an exception
        mock_logfire.configure.side_effect = Exception("OTEL init failed")
        OTELManager._configured_services.clear()

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            kafka_bootstrap_servers="localhost:9092",
            enable_otel=True,
        )

        # Should have handled the exception
        assert tracer._otel_manager is None or not tracer._otel_manager._configured
        tracer.close()

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_trace_span_start_failure(self, mock_logfire: MagicMock) -> None:
        """Test AgentTracer handles OTEL trace span start failure gracefully."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer
        from autonomize_observer.tracing.otel_utils import OTELManager

        OTELManager._configured_services.clear()

        # Make span creation fail after configure succeeds
        mock_logfire.span.side_effect = Exception("Span creation failed")

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        # start_trace should not raise despite OTEL failure
        tracer.start_trace()

        # OTEL span creation should have been attempted
        mock_logfire.span.assert_called()
        tracer.close()

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_span_start_failure(self, mock_logfire: MagicMock) -> None:
        """Test AgentTracer handles OTEL span start failure gracefully."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer
        from autonomize_observer.tracing.otel_utils import OTELManager

        OTELManager._configured_services.clear()

        # First call succeeds (trace span), second call fails (component span)
        call_count = [0]

        def span_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                raise Exception("Span creation failed")
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=False)
            return mock_span

        mock_logfire.span.side_effect = span_side_effect

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        # add_trace should not raise despite OTEL failure
        tracer.add_trace("comp-1", "TestComponent", "tool", {"input": "test"})

        # Both calls were made (one succeeded, one failed)
        assert mock_logfire.span.call_count >= 2
        tracer.close()

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_span_end_failure(self, mock_logfire: MagicMock) -> None:
        """Test AgentTracer handles OTEL span end failure gracefully."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer
        from autonomize_observer.tracing.otel_utils import OTELManager

        OTELManager._configured_services.clear()

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(side_effect=Exception("Span end failed"))
        mock_logfire.span.return_value = mock_span

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "TestComponent", "tool", {"input": "test"})
        # end_trace should not raise despite OTEL failure
        tracer.end_trace("comp-1", "TestComponent", {"output": "test"})

        # Span exit was called (and failed gracefully)
        mock_span.__exit__.assert_called()
        tracer.close()

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_otel_trace_span_end_failure(self, mock_logfire: MagicMock) -> None:
        """Test AgentTracer handles OTEL trace span end failure gracefully."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer
        from autonomize_observer.tracing.otel_utils import OTELManager

        OTELManager._configured_services.clear()

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.set_attribute = MagicMock()
        # Make __exit__ fail only on the second call (trace span end)
        exit_call_count = [0]

        def exit_side_effect(*args, **kwargs):
            exit_call_count[0] += 1
            if exit_call_count[0] > 1:
                raise Exception("Trace span end failed")
            return False

        mock_span.__exit__ = MagicMock(side_effect=exit_side_effect)
        mock_logfire.span.return_value = mock_span

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "TestComponent", "tool", {"input": "test"})
        tracer.end_trace("comp-1", "TestComponent", {"output": "test"})
        # end() should not raise despite OTEL failure
        tracer.end({}, {})

        # Multiple exit calls made (with graceful failure on trace span end)
        assert mock_span.__exit__.call_count >= 2
        tracer.close()

    @patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True)
    @patch("autonomize_observer.tracing.otel_utils.logfire")
    def test_close_with_otel_span_exception(self, mock_logfire: MagicMock) -> None:
        """Test close handles OTEL span cleanup exceptions gracefully."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer
        from autonomize_observer.tracing.otel_utils import OTELManager

        OTELManager._configured_services.clear()

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(side_effect=Exception("Cleanup failed"))
        mock_logfire.span.return_value = mock_span

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
            enable_otel=True,
        )

        tracer.start_trace()
        tracer.add_trace("comp-1", "TestComponent", "tool", {"input": "test"})

        # Manually add span to _otel_spans to test cleanup
        tracer._otel_spans["comp-1"] = mock_span

        # close() should not raise despite cleanup failure
        tracer.close()

    def test_destructor_handles_exception(self) -> None:
        """Test __del__ handles exceptions gracefully."""
        from autonomize_observer.tracing.agent_tracer import AgentTracer

        tracer = AgentTracer(
            trace_name="Test Flow",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            flow_id="flow-123",
        )

        # Make close() raise an exception
        tracer.close = MagicMock(side_effect=Exception("Cleanup failed"))

        # __del__ should not raise
        del tracer
