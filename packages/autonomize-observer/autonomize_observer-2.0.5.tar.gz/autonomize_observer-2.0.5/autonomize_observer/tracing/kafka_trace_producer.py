"""Kafka producer for streaming trace events.

Sends streaming events to Kafka for real-time trace processing.
Used by AgentTracer for AI Studio (Langflow) integration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from confluent_kafka import Producer as KafkaProducer

from autonomize_observer.schemas.streaming import StreamingEventType, TraceEvent

logger = logging.getLogger(__name__)

# Check if Kafka is available
try:
    from confluent_kafka import KafkaError, Producer

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    Producer = None  # type: ignore
    KafkaError = Exception  # type: ignore


class KafkaTraceProducer:
    """High-performance Kafka producer for streaming trace events.

    Features:
    - Automatic partitioning by trace_id for ordered processing
    - Fire-and-forget delivery for minimal latency
    - Connection pooling and reuse
    - Non-blocking operations
    """

    def __init__(
        self,
        bootstrap_servers: str | None,
        topic: str = "genesis-traces-streaming",
        client_id: str = "autonomize-observer",
        # Authentication parameters
        kafka_username: str | None = None,
        kafka_password: str | None = None,
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str = "PLAIN",
        **kafka_config: Any,
    ) -> None:
        """Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Kafka topic name for trace events
            client_id: Client identifier for producer
            kafka_username: Optional SASL username for authentication
            kafka_password: Optional SASL password for authentication
            security_protocol: Security protocol (PLAINTEXT, SASL_SSL, etc.)
            sasl_mechanism: SASL mechanism (PLAIN, SCRAM-SHA-256, etc.)
            **kafka_config: Additional Kafka configuration
        """
        if not KAFKA_AVAILABLE:
            raise ImportError(
                "confluent-kafka is not installed. "
                "Install it with: pip install confluent-kafka"
            )

        if not bootstrap_servers:
            raise ValueError("bootstrap_servers is required")

        self.topic = topic
        self.client_id = client_id
        self._bootstrap_servers = bootstrap_servers

        # Default Kafka configuration optimized for low latency
        default_config: dict[str, Any] = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            # Performance optimizations
            "queue.buffering.max.ms": 0,  # Send immediately
            "linger.ms": 0,  # Don't wait for batching
            "socket.nagle.disable": True,  # Lower latency
            "request.required.acks": 0,  # Fire and forget
            "enable.idempotence": False,  # Better performance
            "retries": 0,  # Don't retry for lower latency
        }

        # Add authentication if provided
        if kafka_username and kafka_password:
            auth_config = {
                "security.protocol": security_protocol,
                "sasl.mechanisms": sasl_mechanism,
                "sasl.username": kafka_username,
                "sasl.password": kafka_password,
            }
            default_config.update(auth_config)
            logger.debug(
                f"Kafka authentication configured with protocol: {security_protocol}"
            )

        # Merge with user-provided config
        self.config = {**default_config, **kafka_config}

        # Initialize producer lazily
        self._producer: KafkaProducer | None = None

        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "last_sent": None,
            "last_error": None,
        }

        logger.info(f"Kafka trace producer initialized for topic: {topic}")

    def _get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer instance."""
        if self._producer is None:
            self._producer = Producer(self.config)
            logger.debug("Created new Kafka producer instance")
        return self._producer

    def _calculate_partition(self, trace_id: str, num_partitions: int = 3) -> int:
        """Calculate partition for trace_id to ensure ordering.

        Uses consistent hashing so same trace_id always goes to same partition.
        """
        hash_value = hashlib.sha256(trace_id.encode("utf-8")).hexdigest()
        return int(hash_value, 16) % num_partitions

    def _delivery_callback(self, error: Any, message: Any) -> None:
        """Callback for message delivery confirmation."""
        if error:
            self._stats["messages_failed"] += 1
            self._stats["last_error"] = str(error)
            logger.error(f"Message delivery failed: {error}")
        else:
            self._stats["messages_sent"] += 1
            self._stats["last_sent"] = int(time.time() * 1000)
            logger.debug(
                f"Message delivered to topic {message.topic()} "
                f"partition {message.partition()}"
            )

    def send_event(
        self,
        event: TraceEvent,
        callback: Callable[..., None] | None = None,
    ) -> bool:
        """Send a trace event to Kafka.

        Args:
            event: TraceEvent to send
            callback: Optional callback for delivery confirmation

        Returns:
            True if message was queued successfully
        """
        try:
            producer = self._get_producer()

            # Calculate partition
            partition = self._calculate_partition(event.trace_id)

            # Serialize event
            key = event.trace_id
            value = event.to_json()

            # Send message
            producer.produce(
                topic=self.topic,
                key=key.encode("utf-8"),
                value=value.encode("utf-8"),
                partition=partition,
                callback=callback or self._delivery_callback,
                timestamp=int(time.time() * 1000),
            )

            # Trigger delivery (non-blocking)
            producer.poll(0)

            logger.debug(
                f"Queued {event.event_type} event for trace {event.trace_id} "
                f"to partition {partition}"
            )

            return True

        except Exception as e:
            self._stats["messages_failed"] += 1
            self._stats["last_error"] = str(e)
            logger.error(f"Failed to send trace event: {e}")
            return False

    def send_trace_start(
        self,
        trace_id: str,
        flow_id: str,
        flow_name: str,
        user_id: str | None = None,
        session_id: str | None = None,
        project_name: str = "GenesisStudio",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send a trace start event."""
        event = TraceEvent.create_trace_start(
            trace_id=trace_id,
            flow_id=flow_id,
            flow_name=flow_name,
            user_id=user_id,
            session_id=session_id,
            project_name=project_name,
            metadata=metadata,
        )
        return self.send_event(event)

    def send_trace_end(
        self,
        trace_id: str,
        duration_ms: float,
        flow_id: str | None = None,
        flow_name: str | None = None,
        error: str | None = None,
        output_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send a trace end event."""
        event = TraceEvent.create_trace_end(
            trace_id=trace_id,
            duration_ms=duration_ms,
            flow_id=flow_id,
            flow_name=flow_name,
            error=error,
            output_data=output_data,
            metadata=metadata,
        )
        return self.send_event(event)

    def send_span_start(
        self,
        trace_id: str,
        span_id: str,
        component_name: str,
        component_type: str | None = None,
        parent_span_id: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send a span start event."""
        event = TraceEvent.create_span_start(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            component_name=component_name,
            component_type=component_type,
            input_data=input_data,
            metadata=metadata,
        )
        return self.send_event(event)

    def send_span_end(
        self,
        trace_id: str,
        span_id: str,
        duration_ms: float,
        component_name: str | None = None,
        output_data: dict[str, Any] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send a span end event."""
        event = TraceEvent.create_span_end(
            trace_id=trace_id,
            span_id=span_id,
            duration_ms=duration_ms,
            component_name=component_name,
            output_data=output_data,
            error=error,
            metadata=metadata,
        )
        return self.send_event(event)

    def send_llm_call_start(
        self,
        trace_id: str,
        span_id: str,
        model: str | None = None,
        provider: str | None = None,
        parent_span_id: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send an LLM call start event."""
        event = TraceEvent.create_llm_call_start(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            model=model,
            provider=provider,
            input_data=input_data,
            metadata=metadata,
        )
        return self.send_event(event)

    def send_llm_call_end(
        self,
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
    ) -> bool:
        """Send an LLM call end event with token usage and cost."""
        event = TraceEvent.create_llm_call_end(
            trace_id=trace_id,
            span_id=span_id,
            duration_ms=duration_ms,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            output_data=output_data,
            error=error,
            metadata=metadata,
        )
        return self.send_event(event)

    def send_custom_event(
        self,
        trace_id: str,
        event_type_name: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send a custom event."""
        combined_metadata = {
            **(metadata or {}),
            "custom_event_type": event_type_name,
            "custom_data": data,
        }

        event = TraceEvent(
            event_type=StreamingEventType.CUSTOM,
            trace_id=trace_id,
            metadata=combined_metadata,
        )
        return self.send_event(event)

    def flush(self, timeout: float = 10.0) -> int:
        """Flush pending messages.

        Args:
            timeout: Maximum time to wait for messages to be delivered

        Returns:
            Number of messages still pending after timeout
        """
        if self._producer:
            return self._producer.flush(timeout)
        return 0

    def get_stats(self) -> dict[str, Any]:
        """Get producer statistics."""
        return {
            "messages_sent": self._stats["messages_sent"],
            "messages_failed": self._stats["messages_failed"],
            "last_sent": self._stats["last_sent"],
            "last_error": self._stats["last_error"],
            "topic": self.topic,
            "client_id": self.client_id,
        }

    def close(self) -> None:
        """Close producer."""
        if self._producer:
            self._producer.flush(10.0)  # Wait up to 10 seconds
            self._producer = None
        logger.info("Kafka trace producer closed")

    def __enter__(self) -> KafkaTraceProducer:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Context manager exit."""
        self.close()
        return False
