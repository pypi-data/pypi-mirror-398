"""Tests for Kafka trace producer."""

from unittest.mock import MagicMock, patch

import pytest

from autonomize_observer.schemas.streaming import StreamingEventType, TraceEvent


class TestKafkaTraceProducerInit:
    """Tests for KafkaTraceProducer initialization."""

    def test_init_without_kafka(self) -> None:
        """Test initialization when kafka is not available."""
        with patch(
            "autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", False
        ):
            from autonomize_observer.tracing.kafka_trace_producer import (
                KafkaTraceProducer,
            )

            with pytest.raises(ImportError, match="confluent-kafka"):
                KafkaTraceProducer(bootstrap_servers="localhost:9092")

    def test_init_without_bootstrap_servers(self) -> None:
        """Test initialization without bootstrap_servers."""
        with patch(
            "autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True
        ):
            from autonomize_observer.tracing.kafka_trace_producer import (
                KafkaTraceProducer,
            )

            with pytest.raises(ValueError, match="bootstrap_servers is required"):
                KafkaTraceProducer(bootstrap_servers=None)

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_init_with_defaults(self, mock_producer: MagicMock) -> None:
        """Test initialization with default values."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        assert producer.topic == "genesis-traces-streaming"
        assert producer.client_id == "autonomize-observer"
        assert "bootstrap.servers" in producer.config
        assert producer.config["bootstrap.servers"] == "localhost:9092"

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_init_with_custom_values(self, mock_producer: MagicMock) -> None:
        """Test initialization with custom values."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(
            bootstrap_servers="kafka.example.com:9092",
            topic="custom-topic",
            client_id="custom-client",
        )

        assert producer.topic == "custom-topic"
        assert producer.client_id == "custom-client"

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_init_with_authentication(self, mock_producer: MagicMock) -> None:
        """Test initialization with SASL authentication."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(
            bootstrap_servers="kafka.example.com:9092",
            kafka_username="user",
            kafka_password="pass",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
        )

        assert producer.config["security.protocol"] == "SASL_SSL"
        assert producer.config["sasl.mechanisms"] == "PLAIN"
        assert producer.config["sasl.username"] == "user"
        assert producer.config["sasl.password"] == "pass"


class TestKafkaTraceProducerMethods:
    """Tests for KafkaTraceProducer methods."""

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_calculate_partition(self, mock_producer: MagicMock) -> None:
        """Test partition calculation is consistent."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        # Same trace_id should always get same partition
        partition1 = producer._calculate_partition("trace-123")
        partition2 = producer._calculate_partition("trace-123")
        assert partition1 == partition2

        # Different trace_ids may get different partitions
        partition3 = producer._calculate_partition("trace-456")
        # Just verify it returns an int
        assert isinstance(partition3, int)
        assert 0 <= partition3 < 3  # Default num_partitions

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_event(self, mock_producer_class: MagicMock) -> None:
        """Test sending a trace event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        event = TraceEvent(
            event_type=StreamingEventType.TRACE_START,
            trace_id="test-trace-123",
        )

        result = producer.send_event(event)

        assert result is True
        mock_producer.produce.assert_called_once()
        mock_producer.poll.assert_called_once_with(0)

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_trace_start(self, mock_producer_class: MagicMock) -> None:
        """Test sending trace_start event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        result = producer.send_trace_start(
            trace_id="trace-123",
            flow_id="flow-456",
            flow_name="Test Flow",
            user_id="user-789",
            session_id="session-abc",
        )

        assert result is True
        mock_producer.produce.assert_called_once()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_trace_end(self, mock_producer_class: MagicMock) -> None:
        """Test sending trace_end event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        result = producer.send_trace_end(
            trace_id="trace-123",
            duration_ms=500.0,
            error="Test error",
        )

        assert result is True
        mock_producer.produce.assert_called_once()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_span_start(self, mock_producer_class: MagicMock) -> None:
        """Test sending span_start event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        result = producer.send_span_start(
            trace_id="trace-123",
            span_id="span-456",
            component_name="TestComponent",
            component_type="llm",
            input_data={"prompt": "Hello"},
        )

        assert result is True
        mock_producer.produce.assert_called_once()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_span_end(self, mock_producer_class: MagicMock) -> None:
        """Test sending span_end event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        result = producer.send_span_end(
            trace_id="trace-123",
            span_id="span-456",
            duration_ms=100.0,
            output_data={"response": "World"},
        )

        assert result is True
        mock_producer.produce.assert_called_once()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_llm_call_start(self, mock_producer_class: MagicMock) -> None:
        """Test sending llm_call_start event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        result = producer.send_llm_call_start(
            trace_id="trace-123",
            span_id="span-456",
            model="gpt-4",
            provider="openai",
        )

        assert result is True
        mock_producer.produce.assert_called_once()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_llm_call_end(self, mock_producer_class: MagicMock) -> None:
        """Test sending llm_call_end event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        result = producer.send_llm_call_end(
            trace_id="trace-123",
            span_id="span-456",
            duration_ms=250.0,
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            cost=0.005,
        )

        assert result is True
        mock_producer.produce.assert_called_once()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_custom_event(self, mock_producer_class: MagicMock) -> None:
        """Test sending custom event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        result = producer.send_custom_event(
            trace_id="trace-123",
            event_type_name="my_custom_event",
            data={"key": "value"},
        )

        assert result is True
        mock_producer.produce.assert_called_once()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_flush(self, mock_producer_class: MagicMock) -> None:
        """Test flushing producer."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")
        # Access producer to initialize it
        producer._get_producer()

        result = producer.flush(timeout=5.0)

        assert result == 0
        mock_producer.flush.assert_called_once_with(5.0)

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_flush_without_producer(self, mock_producer_class: MagicMock) -> None:
        """Test flush when producer is not initialized."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")
        # Don't initialize the producer
        producer._producer = None

        result = producer.flush()

        assert result == 0

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_get_stats(self, mock_producer_class: MagicMock) -> None:
        """Test getting producer statistics."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        stats = producer.get_stats()

        assert "messages_sent" in stats
        assert "messages_failed" in stats
        assert "topic" in stats
        assert stats["topic"] == "genesis-traces-streaming"

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_close(self, mock_producer_class: MagicMock) -> None:
        """Test closing producer."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")
        # Initialize the producer
        producer._get_producer()

        producer.close()

        mock_producer.flush.assert_called_once()
        assert producer._producer is None

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_context_manager(self, mock_producer_class: MagicMock) -> None:
        """Test context manager usage."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer.produce = MagicMock()
        mock_producer.poll = MagicMock()
        mock_producer.flush = MagicMock(return_value=0)
        mock_producer_class.return_value = mock_producer

        with KafkaTraceProducer(bootstrap_servers="localhost:9092") as producer:
            assert producer is not None
            # Force producer creation by calling a method
            producer.send_trace_start("trace-1", "flow-1", "Test")

        # After context, producer should be closed
        mock_producer.flush.assert_called()

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_send_event_exception_handling(
        self, mock_producer_class: MagicMock
    ) -> None:
        """Test exception handling in send_event."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        mock_producer = MagicMock()
        mock_producer.produce.side_effect = Exception("Kafka error")
        mock_producer_class.return_value = mock_producer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        event = TraceEvent(
            event_type=StreamingEventType.TRACE_START,
            trace_id="test-trace",
        )

        result = producer.send_event(event)

        assert result is False
        assert producer._stats["messages_failed"] == 1
        assert producer._stats["last_error"] is not None


class TestKafkaTraceProducerDeliveryCallback:
    """Tests for delivery callback."""

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_delivery_callback_success(self, mock_producer_class: MagicMock) -> None:
        """Test delivery callback on success."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        mock_message = MagicMock()
        mock_message.topic.return_value = "test-topic"
        mock_message.partition.return_value = 0

        producer._delivery_callback(None, mock_message)

        assert producer._stats["messages_sent"] == 1
        assert producer._stats["last_sent"] is not None

    @patch("autonomize_observer.tracing.kafka_trace_producer.KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.tracing.kafka_trace_producer.Producer")
    def test_delivery_callback_error(self, mock_producer_class: MagicMock) -> None:
        """Test delivery callback on error."""
        from autonomize_observer.tracing.kafka_trace_producer import KafkaTraceProducer

        producer = KafkaTraceProducer(bootstrap_servers="localhost:9092")

        mock_error = MagicMock()
        mock_error.__str__ = lambda x: "Test error"
        mock_message = MagicMock()

        producer._delivery_callback(mock_error, mock_message)

        assert producer._stats["messages_failed"] == 1
        assert producer._stats["last_error"] is not None
