"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from autonomize_observer.core.config import KafkaConfig, LogLevel, ObserverConfig


class TestKafkaConfig:
    """Tests for KafkaConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = KafkaConfig()
        assert config.bootstrap_servers == "localhost:9092"
        assert config.client_id == "autonomize-observer"
        assert config.audit_topic == "genesis-audit-events"
        assert config.security_protocol is None
        assert config.sasl_mechanism is None
        assert config.sasl_username is None
        assert config.sasl_password is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = KafkaConfig(
            bootstrap_servers="kafka:9092",
            client_id="custom-client",
            audit_topic="custom-audit",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
            sasl_username="user",
            sasl_password="pass",
        )
        assert config.bootstrap_servers == "kafka:9092"
        assert config.client_id == "custom-client"
        assert config.audit_topic == "custom-audit"
        assert config.security_protocol == "SASL_SSL"
        assert config.sasl_mechanism == "PLAIN"
        assert config.sasl_username == "user"
        assert config.sasl_password == "pass"

    def test_from_env(self):
        """Test configuration from environment variables."""
        env_vars = {
            "KAFKA_BOOTSTRAP_SERVERS": "env-kafka:9092",
            "KAFKA_CLIENT_ID": "env-client",
            "KAFKA_AUDIT_TOPIC": "env-audit",
            "KAFKA_SECURITY_PROTOCOL": "SASL_PLAINTEXT",
            "KAFKA_SASL_MECHANISM": "SCRAM-SHA-256",
            "KAFKA_SASL_USERNAME": "env-user",
            "KAFKA_SASL_PASSWORD": "env-pass",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = KafkaConfig.from_env()
            assert config.bootstrap_servers == "env-kafka:9092"
            assert config.client_id == "env-client"
            assert config.audit_topic == "env-audit"
            assert config.security_protocol == "SASL_PLAINTEXT"
            assert config.sasl_mechanism == "SCRAM-SHA-256"
            assert config.sasl_username == "env-user"
            assert config.sasl_password == "env-pass"


class TestObserverConfig:
    """Tests for ObserverConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ObserverConfig()
        assert config.service_name == "autonomize-service"
        assert config.service_version == "1.0.0"
        assert config.environment == "production"
        assert config.send_to_logfire is False
        assert config.kafka_enabled is True
        assert config.audit_enabled is True
        assert config.audit_retention_days == 365
        assert config.log_level == LogLevel.INFO

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ObserverConfig(
            service_name="my-service",
            service_version="2.0.0",
            environment="staging",
            send_to_logfire=True,
            kafka_enabled=False,
            audit_enabled=False,
            audit_retention_days=90,
            log_level=LogLevel.DEBUG,
        )
        assert config.service_name == "my-service"
        assert config.service_version == "2.0.0"
        assert config.environment == "staging"
        assert config.send_to_logfire is True
        assert config.kafka_enabled is False
        assert config.audit_enabled is False
        assert config.audit_retention_days == 90
        assert config.log_level == LogLevel.DEBUG

    def test_from_env(self):
        """Test configuration from environment variables."""
        env_vars = {
            "SERVICE_NAME": "env-service",
            "SERVICE_VERSION": "3.0.0",
            "ENVIRONMENT": "development",
            "SEND_TO_LOGFIRE": "true",
            "KAFKA_ENABLED": "false",
            "AUDIT_ENABLED": "false",
            "AUDIT_RETENTION_DAYS": "30",
            "LOG_LEVEL": "debug",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = ObserverConfig.from_env()
            assert config.service_name == "env-service"
            assert config.service_version == "3.0.0"
            assert config.environment == "development"
            assert config.send_to_logfire is True
            assert config.kafka_enabled is False
            assert config.audit_enabled is False
            assert config.audit_retention_days == 30
            assert config.log_level == LogLevel.DEBUG

    def test_kafka_config_nested(self):
        """Test nested Kafka configuration."""
        kafka = KafkaConfig(bootstrap_servers="custom:9092")
        config = ObserverConfig(kafka=kafka)
        assert config.kafka.bootstrap_servers == "custom:9092"

    def test_keycloak_claim_mappings(self):
        """Test Keycloak claim mappings."""
        mappings = {"tenant_id": "custom_tenant"}
        config = ObserverConfig(keycloak_claim_mappings=mappings)
        assert config.keycloak_claim_mappings == mappings

    def test_actor_context_provider(self):
        """Test custom actor context provider."""

        def custom_provider():
            return None

        config = ObserverConfig(actor_context_provider=custom_provider)
        assert config.actor_context_provider is custom_provider


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_levels(self):
        """Test all log level values."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"

    def test_log_level_from_string(self):
        """Test creating log level from string."""
        assert LogLevel("debug") == LogLevel.DEBUG
        assert LogLevel("info") == LogLevel.INFO
        assert LogLevel("warning") == LogLevel.WARNING
        assert LogLevel("error") == LogLevel.ERROR
