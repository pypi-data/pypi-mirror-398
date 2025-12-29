"""Tests for exporter classes."""

from unittest.mock import MagicMock, patch

import pytest

from autonomize_observer.core.config import KafkaConfig
from autonomize_observer.exporters.base import BaseExporter, ExportResult
from autonomize_observer.exporters.kafka import KafkaExporter
from autonomize_observer.schemas.audit import AuditEvent
from autonomize_observer.schemas.enums import AuditAction, AuditEventType, ResourceType


class TestExportResult:
    """Tests for ExportResult."""

    def test_ok_result(self):
        """Test creating success result."""
        result = ExportResult.ok(events_exported=5)
        assert result.success is True
        assert result.events_exported == 5
        assert result.events_failed == 0
        assert result.errors == []

    def test_ok_result_with_message(self):
        """Test success result with message."""
        result = ExportResult.ok(events_exported=3, message="All good")
        assert result.success is True
        assert result.message == "All good"

    def test_error_result(self):
        """Test creating error result."""
        result = ExportResult.error("Connection failed")
        assert result.success is False
        assert result.events_exported == 0
        assert result.events_failed == 1
        assert "Connection failed" in result.errors

    def test_error_result_with_count(self):
        """Test error result with custom count."""
        result = ExportResult.error("Batch failed", events_failed=10)
        assert result.events_failed == 10

    def test_merge_results(self):
        """Test merging two results."""
        r1 = ExportResult.ok(events_exported=3)
        r2 = ExportResult.ok(events_exported=2)

        merged = r1.merge(r2)
        assert merged.success is True
        assert merged.events_exported == 5
        assert merged.events_failed == 0

    def test_merge_with_error(self):
        """Test merging success with error."""
        r1 = ExportResult.ok(events_exported=3)
        r2 = ExportResult.error("Failed")

        merged = r1.merge(r2)
        assert merged.success is False
        assert merged.events_exported == 3
        assert merged.events_failed == 1
        assert len(merged.errors) == 1


class TestKafkaExporter:
    """Tests for KafkaExporter."""

    @pytest.fixture
    def kafka_config(self):
        """Create Kafka config for tests."""
        return KafkaConfig(
            bootstrap_servers="localhost:9092",
            client_id="test-client",
            audit_topic="test-audit",
        )

    @pytest.fixture
    def audit_event(self):
        """Create a sample audit event."""
        return AuditEvent(
            audit_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            actor_id="user-123",
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-456",
        )

    def test_create_exporter(self, kafka_config):
        """Test creating Kafka exporter."""
        exporter = KafkaExporter(kafka_config)
        assert exporter.name == "kafka"
        assert exporter.is_initialized is False
        assert exporter.config is kafka_config

    def test_create_exporter_custom_name(self, kafka_config):
        """Test creating exporter with custom name."""
        exporter = KafkaExporter(kafka_config, name="custom-kafka")
        assert exporter.name == "custom-kafka"

    def test_initialize(self, kafka_config, mock_kafka_producer):
        """Test initializing Kafka producer."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()
        assert exporter.is_initialized is True

    def test_initialize_twice(self, kafka_config, mock_kafka_producer):
        """Test that initialize is idempotent."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()
        exporter.initialize()  # Should not raise
        assert exporter.is_initialized is True

    def test_initialize_import_error(self, kafka_config):
        """Test handling import error."""
        with patch.dict("sys.modules", {"confluent_kafka": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                exporter = KafkaExporter(kafka_config)
                with pytest.raises(ImportError):
                    exporter.initialize()

    def test_export_audit_not_initialized(self, kafka_config, audit_event):
        """Test export fails if not initialized."""
        exporter = KafkaExporter(kafka_config)
        result = exporter.export_audit(audit_event)
        assert result.success is False
        assert "not initialized" in result.message.lower()

    def test_export_audit_no_topic(self, mock_kafka_producer):
        """Test export fails if no topic configured."""
        config = KafkaConfig(audit_topic="")
        exporter = KafkaExporter(config)
        exporter.initialize()

        event = AuditEvent(actor_id="user-1", resource_id="doc-1")
        result = exporter.export_audit(event)
        assert result.success is False

    def test_export_audit_success(self, kafka_config, audit_event, mock_kafka_producer):
        """Test successful audit export."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        result = exporter.export_audit(audit_event)
        assert result.success is True
        assert result.events_exported == 1

        # Verify producer was called
        mock_kafka_producer.produce.assert_called_once()

    def test_export_audits_empty(self, kafka_config, mock_kafka_producer):
        """Test export empty list."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        result = exporter.export_audits([])
        assert result.success is True
        assert result.events_exported == 0

    def test_export_audits_multiple(self, kafka_config, mock_kafka_producer):
        """Test export multiple events."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        events = [
            AuditEvent(actor_id="user-1", resource_id="doc-1"),
            AuditEvent(actor_id="user-2", resource_id="doc-2"),
            AuditEvent(actor_id="user-3", resource_id="doc-3"),
        ]
        result = exporter.export_audits(events)
        assert result.success is True
        assert result.events_exported == 3
        assert mock_kafka_producer.produce.call_count == 3

    def test_export_custom_event(self, kafka_config, mock_kafka_producer):
        """Test export custom event."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        custom_data = {"type": "custom", "data": "value"}
        result = exporter.export_custom_event(
            topic="custom-topic",
            event_data=custom_data,
            key="custom-key",
        )
        assert result.success is True
        assert result.events_exported == 1

    def test_flush(self, kafka_config, mock_kafka_producer):
        """Test flush method."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        mock_kafka_producer.flush.return_value = 0
        result = exporter.flush(timeout=5.0)
        assert result == 0
        mock_kafka_producer.flush.assert_called_once_with(5000)

    def test_flush_not_initialized(self, kafka_config):
        """Test flush when not initialized."""
        exporter = KafkaExporter(kafka_config)
        result = exporter.flush()
        assert result == 0

    def test_shutdown(self, kafka_config, mock_kafka_producer):
        """Test shutdown."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        mock_kafka_producer.flush.return_value = 0
        exporter.shutdown()

        assert exporter.is_initialized is False
        mock_kafka_producer.flush.assert_called()

    def test_delivery_callback_success(self, kafka_config, mock_kafka_producer):
        """Test delivery callback on success."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()
        exporter._pending_count = 1

        # Create mock message
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.partition.return_value = 0

        exporter._delivery_callback(None, mock_msg)
        assert exporter._pending_count == 0

    def test_delivery_callback_error(self, kafka_config, mock_kafka_producer):
        """Test delivery callback on error."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()
        exporter._pending_count = 1

        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"

        # Should not raise, just log
        exporter._delivery_callback("Connection error", mock_msg)
        assert exporter._pending_count == 0

    def test_initialize_with_security_config(self, mock_kafka_producer):
        """Test initialize with security configuration."""
        config = KafkaConfig(
            bootstrap_servers="localhost:9092",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
            sasl_username="user",
            sasl_password="password",
        )
        exporter = KafkaExporter(config)
        exporter.initialize()
        assert exporter.is_initialized is True

    def test_initialize_producer_error(self, kafka_config):
        """Test handling producer initialization error."""
        with patch(
            "confluent_kafka.Producer", side_effect=Exception("Connection failed")
        ):
            exporter = KafkaExporter(kafka_config)
            with pytest.raises(Exception, match="Connection failed"):
                exporter.initialize()

    def test_export_audit_exception(self, kafka_config, mock_kafka_producer):
        """Test export_audit handles exceptions."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        # Make produce raise an exception
        mock_kafka_producer.produce.side_effect = Exception("Produce failed")

        event = AuditEvent(actor_id="user-1", resource_id="doc-1")
        result = exporter.export_audit(event)

        assert result.success is False
        assert "Produce failed" in result.errors[0]

    def test_export_custom_event_not_initialized(self, kafka_config):
        """Test export_custom_event when not initialized."""
        exporter = KafkaExporter(kafka_config)

        result = exporter.export_custom_event(
            topic="test-topic",
            event_data={"key": "value"},
        )
        assert result.success is False
        assert "not initialized" in result.message.lower()

    def test_export_custom_event_exception(self, kafka_config, mock_kafka_producer):
        """Test export_custom_event handles exceptions."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        mock_kafka_producer.produce.side_effect = Exception("Produce failed")

        result = exporter.export_custom_event(
            topic="test-topic",
            event_data={"key": "value"},
        )
        assert result.success is False
        assert "Produce failed" in result.errors[0]

    def test_export_audits_not_initialized(self, kafka_config):
        """Test export_audits when not initialized."""
        exporter = KafkaExporter(kafka_config)

        events = [AuditEvent(actor_id="user-1", resource_id="doc-1")]
        result = exporter.export_audits(events)

        assert result.success is False
        assert "not initialized" in result.message.lower()

    def test_flush_with_remaining(self, kafka_config, mock_kafka_producer):
        """Test flush with remaining messages."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        # Simulate messages still pending
        mock_kafka_producer.flush.return_value = 5
        result = exporter.flush(timeout=1.0)

        assert result == 5
        mock_kafka_producer.flush.assert_called_once_with(1000)

    def test_shutdown_with_remaining(self, kafka_config, mock_kafka_producer):
        """Test shutdown with remaining messages."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        # Simulate messages still pending after flush
        mock_kafka_producer.flush.return_value = 3
        exporter.shutdown()

        assert exporter.is_initialized is False

    def test_produce_without_key(self, kafka_config, mock_kafka_producer):
        """Test _produce without message key."""
        exporter = KafkaExporter(kafka_config)
        exporter.initialize()

        exporter._produce(
            topic="test-topic",
            value={"data": "value"},
            key=None,
        )

        mock_kafka_producer.produce.assert_called_once()
        call_kwargs = mock_kafka_producer.produce.call_args[1]
        assert call_kwargs["key"] is None

    def test_produce_not_initialized(self, kafka_config):
        """Test _produce raises when not initialized."""
        exporter = KafkaExporter(kafka_config)

        with pytest.raises(RuntimeError, match="not initialized"):
            exporter._produce(topic="test", value={})


class TestBaseExporter:
    """Tests for BaseExporter abstract class."""

    def test_base_exporter_properties(self):
        """Test BaseExporter properties via concrete implementation."""
        config = KafkaConfig()
        exporter = KafkaExporter(config, name="test-exporter")

        assert exporter.name == "test-exporter"
        assert exporter.is_initialized is False

    def test_base_shutdown(self, mock_kafka_producer):
        """Test shutdown method."""
        config = KafkaConfig()
        exporter = KafkaExporter(config)
        exporter.initialize()

        # Call parent's shutdown behavior
        mock_kafka_producer.flush.return_value = 0
        exporter.shutdown()

        assert exporter.is_initialized is False
