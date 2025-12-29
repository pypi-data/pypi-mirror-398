"""Kafka exporter for sending audit events to Kafka topics.

For trace/span export, use Logfire's OTEL export capabilities.
This exporter focuses on audit events and custom event types.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from autonomize_observer.exporters.base import BaseExporter, ExportResult

if TYPE_CHECKING:
    from confluent_kafka import Producer

    from autonomize_observer.core.config import KafkaConfig
    from autonomize_observer.schemas.audit import AuditEvent

logger = logging.getLogger(__name__)


class KafkaExporter(BaseExporter):
    """Exporter that sends audit events to Kafka topics.

    Used for exporting:
    - Audit events with compliance data
    - Custom events that need to go to Kafka consumers

    For OTEL span export, configure Logfire with an OTLP exporter instead.
    """

    def __init__(
        self,
        config: KafkaConfig,
        name: str = "kafka",
    ) -> None:
        """Initialize the Kafka exporter.

        Args:
            config: Kafka configuration
            name: Name of the exporter for logging
        """
        super().__init__(name=name)
        self._config = config
        self._producer: Producer | None = None
        self._pending_count = 0

    @property
    def config(self) -> KafkaConfig:
        """Get the Kafka configuration."""
        return self._config

    def initialize(self) -> None:
        """Initialize the Kafka producer."""
        if self._initialized:
            return

        try:
            from confluent_kafka import Producer

            producer_config: dict[str, Any] = {
                "bootstrap.servers": self._config.bootstrap_servers,
                "client.id": self._config.client_id,
            }

            # Add optional configuration
            if self._config.security_protocol:
                producer_config["security.protocol"] = self._config.security_protocol

            if self._config.sasl_mechanism:
                producer_config["sasl.mechanism"] = self._config.sasl_mechanism

            if self._config.sasl_username:
                producer_config["sasl.username"] = self._config.sasl_username

            if self._config.sasl_password:
                producer_config["sasl.password"] = self._config.sasl_password

            # Performance tuning
            producer_config["queue.buffering.max.messages"] = 100000
            producer_config["queue.buffering.max.kbytes"] = 1048576
            producer_config["batch.num.messages"] = 1000
            producer_config["linger.ms"] = 5

            self._producer = Producer(producer_config)
            self._initialized = True
            logger.info(
                "Kafka exporter initialized",
                extra={"bootstrap_servers": self._config.bootstrap_servers},
            )

        except ImportError as e:
            raise ImportError(
                "confluent-kafka is required for Kafka export. "
                "Install it with: pip install confluent-kafka"
            ) from e
        except Exception:
            logger.error("Failed to initialize Kafka producer", exc_info=True)
            raise

    def _delivery_callback(self, err: Any, msg: Any) -> None:
        """Callback for message delivery reports."""
        self._pending_count = max(0, self._pending_count - 1)
        if err:
            logger.error(
                "Message delivery failed",
                extra={"error": str(err), "topic": msg.topic()},
            )
        else:
            logger.debug(
                "Message delivered",
                extra={"topic": msg.topic(), "partition": msg.partition()},
            )

    def _produce(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
    ) -> None:
        """Produce a message to Kafka."""
        if not self._producer:
            raise RuntimeError("Kafka producer not initialized")

        self._pending_count += 1
        self._producer.produce(
            topic=topic,
            value=json.dumps(value, default=str).encode("utf-8"),
            key=key.encode("utf-8") if key else None,
            callback=self._delivery_callback,
        )
        # Trigger delivery callbacks
        self._producer.poll(0)

    def export_audit(self, audit_event: AuditEvent) -> ExportResult:
        """Export an audit event to Kafka.

        Args:
            audit_event: The audit event to export

        Returns:
            ExportResult indicating success or failure
        """
        if not self._initialized:
            return ExportResult.error("Exporter not initialized")

        try:
            topic = self._config.audit_topic
            if not topic:
                return ExportResult.error("No audit topic configured")

            data = audit_event.model_dump(mode="json", exclude_none=True)
            self._produce(
                topic=topic,
                value=data,
                key=audit_event.actor_id,
            )

            return ExportResult.ok(events_exported=1)

        except Exception as e:
            logger.error("Failed to export audit event", exc_info=True)
            return ExportResult.error(str(e))

    def export_audits(self, audit_events: list[AuditEvent]) -> ExportResult:
        """Export multiple audit events to Kafka.

        Args:
            audit_events: List of audit events to export

        Returns:
            ExportResult indicating success or failure
        """
        if not self._initialized:
            return ExportResult.error("Exporter not initialized")

        if not audit_events:
            return ExportResult.ok(events_exported=0)

        result = ExportResult(success=True)
        for event in audit_events:
            event_result = self.export_audit(event)
            result = result.merge(event_result)

        return result

    def export_custom_event(
        self,
        topic: str,
        event_data: dict[str, Any],
        key: str | None = None,
    ) -> ExportResult:
        """Export a custom event to a Kafka topic.

        Use this for sending arbitrary events that don't fit the
        audit event schema.

        Args:
            topic: Kafka topic to send to
            event_data: Event data dictionary
            key: Optional message key

        Returns:
            ExportResult indicating success or failure
        """
        if not self._initialized:
            return ExportResult.error("Exporter not initialized")

        try:
            self._produce(topic=topic, value=event_data, key=key)
            return ExportResult.ok(events_exported=1)
        except Exception as e:
            logger.error("Failed to export custom event", exc_info=True)
            return ExportResult.error(str(e))

    def flush(self, timeout: float = 5.0) -> int:
        """Flush pending messages to Kafka.

        Args:
            timeout: Maximum time to wait for flush in seconds

        Returns:
            Number of messages still pending after flush
        """
        if not self._producer:
            return 0

        # Convert to milliseconds for confluent-kafka
        timeout_ms = int(timeout * 1000)
        remaining = self._producer.flush(timeout_ms)

        if remaining > 0:
            logger.warning(
                "Flush timeout with pending messages",
                extra={"pending": remaining},
            )

        return remaining

    def shutdown(self) -> None:
        """Shutdown the Kafka producer."""
        if self._producer:
            # Flush with generous timeout
            remaining = self.flush(timeout=30.0)
            if remaining > 0:
                logger.warning(
                    "Shutdown with pending messages",
                    extra={"pending": remaining},
                )
            self._producer = None
            self._initialized = False
            logger.info("Kafka exporter shutdown complete")
