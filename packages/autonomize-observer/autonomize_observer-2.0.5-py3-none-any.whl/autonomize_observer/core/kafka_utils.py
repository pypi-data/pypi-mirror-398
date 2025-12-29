"""Shared Kafka utilities.

This module provides common Kafka configuration builders and utilities
used across the SDK to eliminate code duplication.

Usage:
    from autonomize_observer.core.kafka_utils import build_producer_config

    config = build_producer_config(
        bootstrap_servers="kafka:9092",
        client_id="my-service",
        username="user",
        password="pass",
    )
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from autonomize_observer.core.config import KafkaConfig

logger = logging.getLogger(__name__)


def build_auth_config(
    username: str | None = None,
    password: str | None = None,
    security_protocol: str = "PLAINTEXT",
    sasl_mechanism: str = "PLAIN",
) -> dict[str, Any]:
    """Build Kafka authentication configuration.

    Args:
        username: SASL username
        password: SASL password
        security_protocol: Security protocol (PLAINTEXT, SASL_PLAINTEXT, SASL_SSL, SSL)
        sasl_mechanism: SASL mechanism (PLAIN, SCRAM-SHA-256, SCRAM-SHA-512)

    Returns:
        Dictionary with authentication settings for confluent-kafka
    """
    config: dict[str, Any] = {}

    if username and password:
        config["security.protocol"] = security_protocol
        if "SASL" in security_protocol:
            config["sasl.mechanism"] = sasl_mechanism
            config["sasl.username"] = username
            config["sasl.password"] = password

    return config


def build_producer_config(
    bootstrap_servers: str,
    client_id: str = "autonomize-observer",
    username: str | None = None,
    password: str | None = None,
    security_protocol: str = "PLAINTEXT",
    sasl_mechanism: str = "PLAIN",
    # Performance settings
    linger_ms: int = 5,
    batch_num_messages: int = 100,
    queue_buffering_max_messages: int = 100000,
    acks: str = "all",
    retries: int = 3,
    # Low-latency mode (for streaming)
    low_latency: bool = False,
) -> dict[str, Any]:
    """Build complete Kafka producer configuration.

    Args:
        bootstrap_servers: Kafka bootstrap servers
        client_id: Client identifier
        username: SASL username
        password: SASL password
        security_protocol: Security protocol
        sasl_mechanism: SASL mechanism
        linger_ms: Time to wait for batching (ignored if low_latency=True)
        batch_num_messages: Messages per batch (ignored if low_latency=True)
        queue_buffering_max_messages: Max messages in queue
        acks: Acknowledgment level ("0", "1", "all")
        retries: Number of retries
        low_latency: If True, use fire-and-forget settings for streaming

    Returns:
        Complete producer configuration for confluent-kafka
    """
    config: dict[str, Any] = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": client_id,
        "queue.buffering.max.messages": queue_buffering_max_messages,
        "retries": retries,
    }

    # Add authentication
    auth_config = build_auth_config(
        username=username,
        password=password,
        security_protocol=security_protocol,
        sasl_mechanism=sasl_mechanism,
    )
    config.update(auth_config)

    # Performance settings based on mode
    if low_latency:
        # Fire-and-forget mode for streaming traces
        config["linger.ms"] = 0
        config["batch.num.messages"] = 1
        config["request.required.acks"] = 0  # No ack wait
    else:
        # Batch mode for audit events
        config["linger.ms"] = linger_ms
        config["batch.num.messages"] = batch_num_messages
        config["request.required.acks"] = -1 if acks == "all" else int(acks)

    return config


def build_producer_config_from_kafka_config(
    kafka_config: KafkaConfig,
    client_id: str = "autonomize-observer",
    low_latency: bool = False,
) -> dict[str, Any]:
    """Build producer config from KafkaConfig object.

    Args:
        kafka_config: KafkaConfig instance
        client_id: Client identifier
        low_latency: If True, use fire-and-forget settings

    Returns:
        Complete producer configuration for confluent-kafka
    """
    return build_producer_config(
        bootstrap_servers=kafka_config.bootstrap_servers,
        client_id=client_id,
        username=kafka_config.sasl_username,
        password=kafka_config.sasl_password,
        security_protocol=kafka_config.security_protocol or "PLAINTEXT",
        sasl_mechanism=kafka_config.sasl_mechanism or "PLAIN",
        linger_ms=kafka_config.linger_ms,
        batch_num_messages=kafka_config.batch_size,
        acks=kafka_config.acks,
        retries=kafka_config.retries,
        low_latency=low_latency,
    )


__all__ = [
    "build_auth_config",
    "build_producer_config",
    "build_producer_config_from_kafka_config",
]
