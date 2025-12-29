"""Centralized optional dependency checks.

This module provides availability flags for optional dependencies,
eliminating duplicated import checks across the codebase.

Usage:
    from autonomize_observer.core.imports import (
        CONFLUENT_KAFKA_AVAILABLE,
        ConfluentProducer,
        LOGFIRE_AVAILABLE,
        logfire,
    )

    if CONFLUENT_KAFKA_AVAILABLE:
        producer = ConfluentProducer(config)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# =============================================================================
# Confluent Kafka (production-grade Kafka client)
# =============================================================================
try:
    from confluent_kafka import KafkaError as ConfluentKafkaError
    from confluent_kafka import Producer as ConfluentProducer

    CONFLUENT_KAFKA_AVAILABLE = True
except ImportError:
    CONFLUENT_KAFKA_AVAILABLE = False
    ConfluentProducer = None  # type: ignore[misc, assignment]
    ConfluentKafkaError = None  # type: ignore[misc, assignment]

# =============================================================================
# Logfire (OTEL tracing via Pydantic)
# =============================================================================
try:
    import logfire as _logfire

    LOGFIRE_AVAILABLE = True
    logfire: Any = _logfire
except ImportError:
    LOGFIRE_AVAILABLE = False
    logfire = None  # type: ignore[assignment]

# =============================================================================
# genai-prices (LLM cost calculation)
# =============================================================================
try:
    from genai_prices import get_model_price

    GENAI_PRICES_AVAILABLE = True
except ImportError:
    GENAI_PRICES_AVAILABLE = False
    get_model_price = None  # type: ignore[misc, assignment]


def check_kafka_available() -> bool:
    """Check if Kafka client is available.

    Returns:
        True if confluent-kafka is installed
    """
    if not CONFLUENT_KAFKA_AVAILABLE:
        logger.warning(
            "confluent-kafka not installed. "
            "Install with: pip install confluent-kafka"
        )
        return False
    return True


def check_logfire_available() -> bool:
    """Check if Logfire is available.

    Returns:
        True if logfire is installed
    """
    if not LOGFIRE_AVAILABLE:
        logger.debug(
            "logfire not installed. OTEL tracing disabled. "
            "Install with: pip install logfire"
        )
        return False
    return True


__all__ = [
    # Confluent Kafka
    "CONFLUENT_KAFKA_AVAILABLE",
    "ConfluentProducer",
    "ConfluentKafkaError",
    "check_kafka_available",
    # Logfire
    "LOGFIRE_AVAILABLE",
    "logfire",
    "check_logfire_available",
    # genai-prices
    "GENAI_PRICES_AVAILABLE",
    "get_model_price",
]
