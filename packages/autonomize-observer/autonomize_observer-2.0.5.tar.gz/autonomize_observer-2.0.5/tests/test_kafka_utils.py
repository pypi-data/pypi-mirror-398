"""Tests for Kafka utilities."""

from __future__ import annotations

import pytest


class TestBuildAuthConfig:
    """Tests for build_auth_config function."""

    def test_no_credentials(self) -> None:
        """Test auth config without credentials."""
        from autonomize_observer.core.kafka_utils import build_auth_config

        result = build_auth_config()
        assert result == {}

    def test_with_credentials_sasl_ssl(self) -> None:
        """Test auth config with SASL_SSL credentials."""
        from autonomize_observer.core.kafka_utils import build_auth_config

        result = build_auth_config(
            username="user",
            password="pass",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
        )
        assert result["security.protocol"] == "SASL_SSL"
        assert result["sasl.mechanism"] == "PLAIN"
        assert result["sasl.username"] == "user"
        assert result["sasl.password"] == "pass"

    def test_with_credentials_plaintext(self) -> None:
        """Test auth config with PLAINTEXT protocol."""
        from autonomize_observer.core.kafka_utils import build_auth_config

        result = build_auth_config(
            username="user",
            password="pass",
            security_protocol="PLAINTEXT",
        )
        # PLAINTEXT doesn't need SASL mechanism
        assert result["security.protocol"] == "PLAINTEXT"
        assert "sasl.mechanism" not in result

    def test_missing_password(self) -> None:
        """Test auth config with missing password."""
        from autonomize_observer.core.kafka_utils import build_auth_config

        result = build_auth_config(username="user", password=None)
        assert result == {}


class TestBuildProducerConfig:
    """Tests for build_producer_config function."""

    def test_basic_config(self) -> None:
        """Test basic producer config."""
        from autonomize_observer.core.kafka_utils import build_producer_config

        result = build_producer_config(
            bootstrap_servers="kafka:9092",
            client_id="test-client",
        )
        assert result["bootstrap.servers"] == "kafka:9092"
        assert result["client.id"] == "test-client"
        assert result["retries"] == 3

    def test_batch_mode(self) -> None:
        """Test batch mode (default) producer config."""
        from autonomize_observer.core.kafka_utils import build_producer_config

        result = build_producer_config(
            bootstrap_servers="kafka:9092",
            low_latency=False,
        )
        assert result["linger.ms"] == 5
        assert result["batch.num.messages"] == 100
        assert result["request.required.acks"] == -1  # "all"

    def test_low_latency_mode(self) -> None:
        """Test low-latency mode producer config."""
        from autonomize_observer.core.kafka_utils import build_producer_config

        result = build_producer_config(
            bootstrap_servers="kafka:9092",
            low_latency=True,
        )
        assert result["linger.ms"] == 0
        assert result["batch.num.messages"] == 1
        assert result["request.required.acks"] == 0  # Fire and forget

    def test_with_authentication(self) -> None:
        """Test producer config with authentication."""
        from autonomize_observer.core.kafka_utils import build_producer_config

        result = build_producer_config(
            bootstrap_servers="kafka:9092",
            username="user",
            password="pass",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
        )
        assert result["security.protocol"] == "SASL_SSL"
        assert result["sasl.mechanism"] == "PLAIN"
        assert result["sasl.username"] == "user"
        assert result["sasl.password"] == "pass"

    def test_custom_performance_settings(self) -> None:
        """Test producer config with custom performance settings."""
        from autonomize_observer.core.kafka_utils import build_producer_config

        result = build_producer_config(
            bootstrap_servers="kafka:9092",
            linger_ms=10,
            batch_num_messages=200,
            acks="1",
            retries=5,
        )
        assert result["linger.ms"] == 10
        assert result["batch.num.messages"] == 200
        assert result["request.required.acks"] == 1
        assert result["retries"] == 5


class TestBuildProducerConfigFromKafkaConfig:
    """Tests for build_producer_config_from_kafka_config function."""

    def test_from_kafka_config(self) -> None:
        """Test building producer config from KafkaConfig."""
        from autonomize_observer.core.config import KafkaConfig
        from autonomize_observer.core.kafka_utils import (
            build_producer_config_from_kafka_config,
        )

        kafka_config = KafkaConfig(
            bootstrap_servers="kafka:9092",
            sasl_username="user",
            sasl_password="pass",
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
            linger_ms=10,
            batch_size=200,
            acks="all",
            retries=5,
        )

        result = build_producer_config_from_kafka_config(kafka_config)
        assert result["bootstrap.servers"] == "kafka:9092"
        assert result["security.protocol"] == "SASL_SSL"
        assert result["sasl.username"] == "user"
        assert result["linger.ms"] == 10
        assert result["batch.num.messages"] == 200

    def test_from_kafka_config_low_latency(self) -> None:
        """Test building low-latency config from KafkaConfig."""
        from autonomize_observer.core.config import KafkaConfig
        from autonomize_observer.core.kafka_utils import (
            build_producer_config_from_kafka_config,
        )

        kafka_config = KafkaConfig(bootstrap_servers="kafka:9092")

        result = build_producer_config_from_kafka_config(
            kafka_config,
            low_latency=True,
        )
        assert result["linger.ms"] == 0
        assert result["request.required.acks"] == 0
