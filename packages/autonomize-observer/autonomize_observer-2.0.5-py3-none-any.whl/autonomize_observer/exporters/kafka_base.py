"""Base Kafka producer with common functionality.

This module provides a base class for Kafka producers, eliminating
duplication between KafkaExporter and KafkaTraceProducer.

Usage:
    from autonomize_observer.exporters.kafka_base import BaseKafkaProducer

    class MyProducer(BaseKafkaProducer):
        def send_my_event(self, data: dict) -> bool:
            return self._send("my-topic", data)
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC
from typing import TYPE_CHECKING, Any, Callable

from autonomize_observer.core.imports import (
    CONFLUENT_KAFKA_AVAILABLE,
    ConfluentKafkaError,
    ConfluentProducer,
)
from autonomize_observer.core.kafka_utils import build_producer_config

if TYPE_CHECKING:
    from autonomize_observer.core.config import KafkaConfig

logger = logging.getLogger(__name__)


class BaseKafkaProducer(ABC):
    """Base class for Kafka producers.

    Provides common functionality for:
    - Producer initialization with confluent-kafka
    - Authentication configuration
    - Message delivery with callbacks
    - Flush and close operations
    - Statistics tracking

    Subclasses should implement domain-specific send methods.

    Example:
        ```python
        class MyProducer(BaseKafkaProducer):
            def __init__(self, bootstrap_servers: str, topic: str):
                super().__init__(
                    bootstrap_servers=bootstrap_servers,
                    default_topic=topic,
                    client_id="my-producer",
                )

            def send_event(self, data: dict) -> bool:
                return self._send(data)
        ```
    """

    def __init__(
        self,
        bootstrap_servers: str,
        default_topic: str,
        client_id: str = "autonomize-observer",
        username: str | None = None,
        password: str | None = None,
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str = "PLAIN",
        low_latency: bool = False,
        **extra_config: Any,
    ) -> None:
        """Initialize base Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses
            default_topic: Default topic for messages
            client_id: Client identifier
            username: SASL username
            password: SASL password
            security_protocol: Security protocol
            sasl_mechanism: SASL mechanism
            low_latency: Use low-latency settings (fire-and-forget)
            **extra_config: Additional Kafka configuration
        """
        if not CONFLUENT_KAFKA_AVAILABLE:
            raise ImportError(
                "confluent-kafka is required. "
                "Install it with: pip install confluent-kafka"
            )

        if not bootstrap_servers:
            raise ValueError("bootstrap_servers is required")

        self._bootstrap_servers = bootstrap_servers
        self._default_topic = default_topic
        self._client_id = client_id
        self._low_latency = low_latency

        # Build producer config using shared utility
        self._config = build_producer_config(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            username=username,
            password=password,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            low_latency=low_latency,
        )

        # Merge extra config
        self._config.update(extra_config)

        # Producer instance (lazy initialization)
        self._producer: Any = None

        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "last_sent_ms": None,
            "last_error": None,
        }

        logger.debug(
            f"BaseKafkaProducer initialized for topic: {default_topic} "
            f"(low_latency={low_latency})"
        )

    @classmethod
    def from_config(
        cls,
        kafka_config: KafkaConfig,
        default_topic: str,
        client_id: str = "autonomize-observer",
        low_latency: bool = False,
    ) -> BaseKafkaProducer:
        """Create producer from KafkaConfig object.

        Args:
            kafka_config: KafkaConfig instance
            default_topic: Default topic for messages
            client_id: Client identifier
            low_latency: Use low-latency settings

        Returns:
            Configured producer instance
        """
        return cls(
            bootstrap_servers=kafka_config.bootstrap_servers,
            default_topic=default_topic,
            client_id=client_id,
            username=kafka_config.sasl_username,
            password=kafka_config.sasl_password,
            security_protocol=kafka_config.security_protocol or "PLAINTEXT",
            sasl_mechanism=kafka_config.sasl_mechanism or "PLAIN",
            low_latency=low_latency,
        )

    def _get_producer(self) -> Any:
        """Get or create the Kafka producer instance."""
        if self._producer is None:
            self._producer = ConfluentProducer(self._config)
            logger.debug("Created Kafka producer instance")
        return self._producer

    def _delivery_callback(self, err: Any, msg: Any) -> None:
        """Callback for message delivery reports.

        Args:
            err: Error if delivery failed
            msg: Message that was delivered
        """
        if err:
            self._stats["messages_failed"] += 1
            self._stats["last_error"] = str(err)
            logger.error(
                f"Message delivery failed: {err}",
                extra={"topic": msg.topic() if msg else "unknown"},
            )
        else:
            self._stats["messages_sent"] += 1
            self._stats["last_sent_ms"] = int(time.time() * 1000)
            logger.debug(f"Message delivered to {msg.topic()}[{msg.partition()}]")

    def _send(
        self,
        data: dict[str, Any],
        topic: str | None = None,
        key: str | None = None,
        partition: int | None = None,
        callback: Callable[..., None] | None = None,
    ) -> bool:
        """Send a message to Kafka.

        Args:
            data: Data dictionary to send
            topic: Topic to send to (defaults to default_topic)
            key: Message key
            partition: Partition number (None for automatic)
            callback: Custom delivery callback

        Returns:
            True if message was queued successfully
        """
        try:
            producer = self._get_producer()
            target_topic = topic or self._default_topic

            # Serialize data
            value = json.dumps(data, default=str).encode("utf-8")
            encoded_key = key.encode("utf-8") if key else None

            # Build produce kwargs
            produce_kwargs: dict[str, Any] = {
                "topic": target_topic,
                "value": value,
                "key": encoded_key,
                "callback": callback or self._delivery_callback,
            }

            if partition is not None:
                produce_kwargs["partition"] = partition

            # Send message
            producer.produce(**produce_kwargs)

            # Trigger delivery callbacks (non-blocking)
            producer.poll(0)

            logger.debug(f"Queued message to {target_topic}")
            return True

        except Exception as e:
            self._stats["messages_failed"] += 1
            self._stats["last_error"] = str(e)
            logger.error(f"Failed to send message: {e}")
            return False

    def flush(self, timeout: float = 5.0) -> int:
        """Flush pending messages.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Number of messages still pending after timeout
        """
        if not self._producer:
            return 0

        try:
            remaining = self._producer.flush(timeout)
            if remaining > 0:
                logger.warning(f"Flush timeout: {remaining} messages pending")
            return remaining
        except Exception as e:
            logger.error(f"Error during flush: {e}")
            return -1

    def close(self) -> None:
        """Close the producer."""
        if self._producer:
            try:
                self.flush(timeout=10.0)
            except Exception as e:
                logger.warning(f"Error flushing during close: {e}")
            finally:
                self._producer = None
                logger.debug("Kafka producer closed")

    @property
    def stats(self) -> dict[str, Any]:
        """Get producer statistics."""
        return {
            **self._stats,
            "topic": self._default_topic,
            "client_id": self._client_id,
            "low_latency": self._low_latency,
        }

    @property
    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._producer is not None

    def __enter__(self) -> BaseKafkaProducer:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any,
    ) -> bool:
        """Context manager exit."""
        self.close()
        return False


__all__ = ["BaseKafkaProducer"]
