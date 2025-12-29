"""Configuration management for Autonomize Observer.

Simple configuration focused on:
- Logfire setup (tracing)
- Kafka export (audit events)
- Keycloak JWT parsing (actor context)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class LogLevel(str, Enum):
    """Log level for internal logging."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class KafkaConfig:
    """Kafka configuration for audit, trace, and workflow event export."""

    bootstrap_servers: str = "localhost:9092"
    client_id: str = "autonomize-observer"

    # Topics
    audit_topic: str = "genesis-audit-events"
    trace_topic: str = "genesis-traces-streaming"
    workflow_topic: str = "workflow-traces"

    # Security
    security_protocol: str | None = None
    sasl_mechanism: str | None = None
    sasl_username: str | None = None
    sasl_password: str | None = None

    # Performance tuning
    linger_ms: int = 5
    batch_size: int = 100
    acks: str = "all"
    retries: int = 3

    @classmethod
    def from_env(cls) -> KafkaConfig:
        """Create KafkaConfig from environment variables."""
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            client_id=os.getenv("KAFKA_CLIENT_ID", "autonomize-observer"),
            audit_topic=os.getenv("KAFKA_AUDIT_TOPIC", "genesis-audit-events"),
            trace_topic=os.getenv("KAFKA_TRACE_TOPIC", "genesis-traces-streaming"),
            workflow_topic=os.getenv("KAFKA_WORKFLOW_TOPIC", "workflow-traces"),
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL"),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
            sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
            sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
            linger_ms=int(os.getenv("KAFKA_LINGER_MS", "5")),
            batch_size=int(os.getenv("KAFKA_BATCH_SIZE", "100")),
            acks=os.getenv("KAFKA_ACKS", "all"),
            retries=int(os.getenv("KAFKA_RETRIES", "3")),
        )


@dataclass
class ObserverConfig:
    """Main configuration for Autonomize Observer.

    Simplified configuration for:
    - Logfire (tracing via Pydantic Logfire)
    - Kafka (audit event export)
    - Keycloak (actor context from JWT)
    """

    # Service identification
    service_name: str = "autonomize-service"
    service_version: str = "1.0.0"
    environment: str = "production"

    # Logfire settings
    send_to_logfire: bool = False  # Default: keep data local

    # Kafka settings
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    kafka_enabled: bool = True

    # Keycloak claim mappings (for JWT parsing)
    keycloak_claim_mappings: dict[str, str] = field(default_factory=dict)

    # Custom actor context provider
    actor_context_provider: Callable[[], Any] | None = None

    # Feature flags
    audit_enabled: bool = True

    # Audit settings
    audit_retention_days: int = 365

    # Internal logging
    log_level: LogLevel = LogLevel.INFO

    @classmethod
    def from_env(cls) -> ObserverConfig:
        """Create ObserverConfig from environment variables."""
        log_level_str = os.getenv("LOG_LEVEL", "info").lower()

        return cls(
            service_name=os.getenv("SERVICE_NAME", "autonomize-service"),
            service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "production"),
            send_to_logfire=os.getenv("SEND_TO_LOGFIRE", "false").lower() == "true",
            kafka=KafkaConfig.from_env(),
            kafka_enabled=os.getenv("KAFKA_ENABLED", "true").lower() == "true",
            audit_enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true",
            audit_retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "365")),
            log_level=LogLevel(log_level_str),
        )
