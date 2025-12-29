"""Tests for core imports module."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestAvailabilityFlags:
    """Tests for availability flags."""

    def test_confluent_kafka_flag_exists(self) -> None:
        """Test that CONFLUENT_KAFKA_AVAILABLE is defined."""
        from autonomize_observer.core.imports import CONFLUENT_KAFKA_AVAILABLE

        assert isinstance(CONFLUENT_KAFKA_AVAILABLE, bool)

    def test_logfire_flag_exists(self) -> None:
        """Test that LOGFIRE_AVAILABLE is defined."""
        from autonomize_observer.core.imports import LOGFIRE_AVAILABLE

        assert isinstance(LOGFIRE_AVAILABLE, bool)

    def test_genai_prices_flag_exists(self) -> None:
        """Test that GENAI_PRICES_AVAILABLE is defined."""
        from autonomize_observer.core.imports import GENAI_PRICES_AVAILABLE

        assert isinstance(GENAI_PRICES_AVAILABLE, bool)


class TestCheckKafkaAvailable:
    """Tests for check_kafka_available function."""

    @patch("autonomize_observer.core.imports.CONFLUENT_KAFKA_AVAILABLE", True)
    def test_check_kafka_available_true(self) -> None:
        """Test check_kafka_available when Kafka is available."""
        from autonomize_observer.core.imports import check_kafka_available

        assert check_kafka_available() is True

    @patch("autonomize_observer.core.imports.CONFLUENT_KAFKA_AVAILABLE", False)
    def test_check_kafka_available_false(self) -> None:
        """Test check_kafka_available when Kafka is not available."""
        from autonomize_observer.core.imports import check_kafka_available

        assert check_kafka_available() is False


class TestCheckLogfireAvailable:
    """Tests for check_logfire_available function."""

    @patch("autonomize_observer.core.imports.LOGFIRE_AVAILABLE", True)
    def test_check_logfire_available_true(self) -> None:
        """Test check_logfire_available when Logfire is available."""
        from autonomize_observer.core.imports import check_logfire_available

        assert check_logfire_available() is True

    @patch("autonomize_observer.core.imports.LOGFIRE_AVAILABLE", False)
    def test_check_logfire_available_false(self) -> None:
        """Test check_logfire_available when Logfire is not available."""
        from autonomize_observer.core.imports import check_logfire_available

        assert check_logfire_available() is False


class TestModuleExports:
    """Tests for module __all__ exports."""

    def test_all_exports(self) -> None:
        """Test that all expected items are exported."""
        from autonomize_observer.core import imports

        expected_exports = [
            "CONFLUENT_KAFKA_AVAILABLE",
            "ConfluentProducer",
            "ConfluentKafkaError",
            "check_kafka_available",
            "LOGFIRE_AVAILABLE",
            "logfire",
            "check_logfire_available",
            "GENAI_PRICES_AVAILABLE",
            "get_model_price",
        ]

        for export in expected_exports:
            assert hasattr(imports, export), f"Missing export: {export}"

    def test_all_list_complete(self) -> None:
        """Test that __all__ contains all expected exports."""
        from autonomize_observer.core.imports import __all__

        expected = [
            "CONFLUENT_KAFKA_AVAILABLE",
            "ConfluentProducer",
            "ConfluentKafkaError",
            "check_kafka_available",
            "LOGFIRE_AVAILABLE",
            "logfire",
            "check_logfire_available",
            "GENAI_PRICES_AVAILABLE",
            "get_model_price",
        ]

        for item in expected:
            assert item in __all__, f"Missing from __all__: {item}"


class TestConditionalImports:
    """Tests for conditional import behavior."""

    def test_confluent_producer_available(self) -> None:
        """Test ConfluentProducer is available or None."""
        from autonomize_observer.core.imports import (
            CONFLUENT_KAFKA_AVAILABLE,
            ConfluentProducer,
        )

        if CONFLUENT_KAFKA_AVAILABLE:
            assert ConfluentProducer is not None
        else:
            assert ConfluentProducer is None

    def test_logfire_available(self) -> None:
        """Test logfire is available or None."""
        from autonomize_observer.core.imports import LOGFIRE_AVAILABLE, logfire

        if LOGFIRE_AVAILABLE:
            assert logfire is not None
        else:
            assert logfire is None

    def test_genai_prices_available(self) -> None:
        """Test get_model_price is available or None."""
        from autonomize_observer.core.imports import (
            GENAI_PRICES_AVAILABLE,
            get_model_price,
        )

        if GENAI_PRICES_AVAILABLE:
            assert get_model_price is not None
        else:
            assert get_model_price is None
