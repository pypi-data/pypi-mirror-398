"""Tests for BaseKafkaProducer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestBaseKafkaProducerInit:
    """Tests for BaseKafkaProducer initialization."""

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", False)
    def test_init_without_kafka(self) -> None:
        """Test initialization raises error when Kafka not available."""
        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        with pytest.raises(ImportError, match="confluent-kafka is required"):
            BaseKafkaProducer(
                bootstrap_servers="localhost:9092",
                default_topic="test-topic",
            )

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    def test_init_without_bootstrap_servers(self) -> None:
        """Test initialization raises error without bootstrap servers."""
        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        with pytest.raises(ValueError, match="bootstrap_servers is required"):
            BaseKafkaProducer(
                bootstrap_servers="",
                default_topic="test-topic",
            )

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_init_success(self, mock_build_config: MagicMock) -> None:
        """Test successful initialization."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
            client_id="test-client",
        )

        assert producer._default_topic == "test-topic"
        assert producer._client_id == "test-client"
        assert producer._producer is None  # Lazy initialization
        assert producer._stats["messages_sent"] == 0
        assert producer._stats["messages_failed"] == 0

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_init_with_auth(self, mock_build_config: MagicMock) -> None:
        """Test initialization with authentication."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
            username="user",
            password="pass",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
        )

        mock_build_config.assert_called_once()
        call_args = mock_build_config.call_args
        assert call_args.kwargs["username"] == "user"
        assert call_args.kwargs["password"] == "pass"
        assert call_args.kwargs["security_protocol"] == "SASL_SSL"

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_init_low_latency(self, mock_build_config: MagicMock) -> None:
        """Test initialization with low latency mode."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
            low_latency=True,
        )

        assert producer._low_latency is True
        mock_build_config.assert_called_with(
            bootstrap_servers="localhost:9092",
            client_id="autonomize-observer",
            username=None,
            password=None,
            security_protocol="PLAINTEXT",
            sasl_mechanism="PLAIN",
            low_latency=True,
        )


class TestBaseKafkaProducerFromConfig:
    """Tests for from_config class method."""

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_from_config(self, mock_build_config: MagicMock) -> None:
        """Test creating producer from KafkaConfig."""
        mock_build_config.return_value = {"bootstrap.servers": "kafka:9092"}

        from autonomize_observer.core.config import KafkaConfig
        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        kafka_config = KafkaConfig(
            bootstrap_servers="kafka:9092",
            sasl_username="user",
            sasl_password="pass",
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-256",
        )

        producer = BaseKafkaProducer.from_config(
            kafka_config,
            default_topic="my-topic",
            client_id="my-client",
        )

        assert producer._default_topic == "my-topic"
        assert producer._client_id == "my-client"


class TestBaseKafkaProducerSend:
    """Tests for send operations."""

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_send_success(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test successful message send."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )

        result = producer._send({"key": "value"})

        assert result is True
        mock_producer.produce.assert_called_once()
        mock_producer.poll.assert_called_once_with(0)

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_send_with_key_and_partition(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test send with key and partition."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )

        result = producer._send(
            {"key": "value"},
            key="my-key",
            partition=2,
        )

        assert result is True
        call_kwargs = mock_producer.produce.call_args.kwargs
        assert call_kwargs["key"] == b"my-key"
        assert call_kwargs["partition"] == 2

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_send_to_custom_topic(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test send to custom topic."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="default-topic",
        )

        result = producer._send({"key": "value"}, topic="custom-topic")

        assert result is True
        call_kwargs = mock_producer.produce.call_args.kwargs
        assert call_kwargs["topic"] == "custom-topic"

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_send_failure(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test send failure."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer.produce.side_effect = Exception("Send failed")
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )

        result = producer._send({"key": "value"})

        assert result is False
        assert producer._stats["messages_failed"] == 1
        assert "Send failed" in producer._stats["last_error"]


class TestBaseKafkaProducerCallbacks:
    """Tests for delivery callbacks."""

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_delivery_callback_success(self, mock_build_config: MagicMock) -> None:
        """Test delivery callback on success."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )

        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.partition.return_value = 0

        producer._delivery_callback(None, mock_msg)

        assert producer._stats["messages_sent"] == 1
        assert producer._stats["last_sent_ms"] is not None

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_delivery_callback_error(self, mock_build_config: MagicMock) -> None:
        """Test delivery callback on error."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )

        mock_error = MagicMock()
        mock_error.__str__ = lambda self: "Delivery failed"
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"

        producer._delivery_callback(mock_error, mock_msg)

        assert producer._stats["messages_failed"] == 1
        assert producer._stats["last_error"] is not None


class TestBaseKafkaProducerFlushClose:
    """Tests for flush and close operations."""

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_flush(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test flush operation."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )
        # Trigger producer creation
        producer._get_producer()

        remaining = producer.flush(timeout=5.0)

        assert remaining == 0
        mock_producer.flush.assert_called_once_with(5.0)

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_flush_no_producer(self, mock_build_config: MagicMock) -> None:
        """Test flush when no producer created."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )

        remaining = producer.flush()

        assert remaining == 0

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_flush_with_pending(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test flush with pending messages."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer.flush.return_value = 5  # 5 messages pending
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )
        producer._get_producer()

        remaining = producer.flush()

        assert remaining == 5

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_flush_exception(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test flush exception handling."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer.flush.side_effect = Exception("Flush error")
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )
        producer._get_producer()

        remaining = producer.flush()

        assert remaining == -1

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_close(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test close operation."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )
        producer._get_producer()

        producer.close()

        assert producer._producer is None
        mock_producer.flush.assert_called_once_with(10.0)

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_close_flush_error(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test close with flush error."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer.flush.side_effect = Exception("Flush error")
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )
        producer._get_producer()

        # Should not raise
        producer.close()

        assert producer._producer is None


class TestBaseKafkaProducerProperties:
    """Tests for producer properties."""

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    def test_stats_property(self, mock_build_config: MagicMock) -> None:
        """Test stats property."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
            client_id="my-client",
            low_latency=True,
        )

        stats = producer.stats

        assert stats["topic"] == "test-topic"
        assert stats["client_id"] == "my-client"
        assert stats["low_latency"] is True
        assert stats["messages_sent"] == 0
        assert stats["messages_failed"] == 0

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_is_connected_property(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test is_connected property."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        producer = BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        )

        assert producer.is_connected is False

        producer._get_producer()

        assert producer.is_connected is True


class TestBaseKafkaProducerContextManager:
    """Tests for context manager."""

    @patch("autonomize_observer.exporters.kafka_base.CONFLUENT_KAFKA_AVAILABLE", True)
    @patch("autonomize_observer.exporters.kafka_base.build_producer_config")
    @patch("autonomize_observer.exporters.kafka_base.ConfluentProducer")
    def test_context_manager(
        self, mock_producer_class: MagicMock, mock_build_config: MagicMock
    ) -> None:
        """Test context manager."""
        mock_build_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_class.return_value = mock_producer

        from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

        with BaseKafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic",
        ) as producer:
            producer._get_producer()
            assert producer.is_connected is True

        assert producer._producer is None
