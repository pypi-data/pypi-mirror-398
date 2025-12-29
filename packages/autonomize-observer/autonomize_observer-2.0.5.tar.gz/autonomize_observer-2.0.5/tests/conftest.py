"""Pytest configuration and fixtures."""

from unittest.mock import MagicMock, patch

import pytest

from autonomize_observer.core.config import KafkaConfig, ObserverConfig


@pytest.fixture
def kafka_config():
    """Create a test Kafka configuration."""
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        client_id="test-client",
        audit_topic="test-audit-events",
    )


@pytest.fixture
def observer_config(kafka_config):
    """Create a test observer configuration."""
    return ObserverConfig(
        service_name="test-service",
        service_version="1.0.0",
        environment="test",
        kafka=kafka_config,
    )


@pytest.fixture
def mock_kafka_producer():
    """Create a mock Kafka producer."""
    with patch("confluent_kafka.Producer") as mock:
        producer = MagicMock()
        producer.produce = MagicMock()
        producer.poll = MagicMock(return_value=0)
        producer.flush = MagicMock(return_value=0)
        mock.return_value = producer
        yield producer


@pytest.fixture
def mock_logfire():
    """Create a mock logfire module."""
    with patch("logfire.configure") as mock_configure, patch(
        "logfire.instrument_openai"
    ) as mock_openai, patch("logfire.instrument_anthropic") as mock_anthropic, patch(
        "logfire.span"
    ) as mock_span:
        yield {
            "configure": mock_configure,
            "instrument_openai": mock_openai,
            "instrument_anthropic": mock_anthropic,
            "span": mock_span,
        }


@pytest.fixture
def sample_keycloak_token():
    """Create a sample Keycloak JWT payload."""
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "preferred_username": "testuser",
        "realm_access": {"roles": ["admin", "user"]},
        "groups": ["/org/team"],
        "session_state": "session-456",
    }
