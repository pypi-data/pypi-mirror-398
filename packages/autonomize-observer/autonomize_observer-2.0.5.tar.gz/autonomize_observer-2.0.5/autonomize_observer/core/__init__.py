"""Core infrastructure for Autonomize Observer."""

from autonomize_observer.core.config import KafkaConfig, LogLevel, ObserverConfig
from autonomize_observer.core.exceptions import (
    AuditError,
    ConfigurationError,
    ExporterError,
    ObserverError,
)
from autonomize_observer.core.imports import (
    CONFLUENT_KAFKA_AVAILABLE,
    GENAI_PRICES_AVAILABLE,
    LOGFIRE_AVAILABLE,
    ConfluentKafkaError,
    ConfluentProducer,
    check_kafka_available,
    check_logfire_available,
    logfire,
)

__all__ = [
    # Config
    "ObserverConfig",
    "KafkaConfig",
    "LogLevel",
    # Exceptions
    "ObserverError",
    "ConfigurationError",
    "AuditError",
    "ExporterError",
    # Imports (availability checks)
    "CONFLUENT_KAFKA_AVAILABLE",
    "LOGFIRE_AVAILABLE",
    "GENAI_PRICES_AVAILABLE",
    "ConfluentProducer",
    "ConfluentKafkaError",
    "logfire",
    "check_kafka_available",
    "check_logfire_available",
]
