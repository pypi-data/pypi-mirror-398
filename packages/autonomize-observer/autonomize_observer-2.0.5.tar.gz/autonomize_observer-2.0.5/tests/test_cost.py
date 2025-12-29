"""Tests for cost pricing module."""

from unittest.mock import MagicMock, patch

import pytest

from autonomize_observer.cost.pricing import (
    CostResult,
    PriceInfo,
    calculate_cost,
    get_price,
)


class TestPriceInfo:
    """Tests for PriceInfo dataclass."""

    def test_basic_creation(self):
        """Test basic price info creation."""
        price = PriceInfo(
            provider="openai",
            model="gpt-4o",
            input_price_per_token=0.000005,
            output_price_per_token=0.000015,
        )
        assert price.provider == "openai"
        assert price.model == "gpt-4o"
        assert price.input_price_per_token == 0.000005
        assert price.output_price_per_token == 0.000015
        assert price.currency == "USD"

    def test_cached_price(self):
        """Test with cached token price."""
        price = PriceInfo(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            input_price_per_token=0.000003,
            output_price_per_token=0.000015,
            cached_input_price_per_token=0.0000003,
        )
        assert price.cached_input_price_per_token == 0.0000003

    def test_price_per_1k(self):
        """Test price per 1000 tokens calculation."""
        price = PriceInfo(
            provider="openai",
            model="gpt-4o",
            input_price_per_token=0.000005,
            output_price_per_token=0.000015,
        )
        # Use approximate comparison for floating point
        assert abs(price.input_price_per_1k - 0.005) < 1e-10
        assert abs(price.output_price_per_1k - 0.015) < 1e-10


class TestCostResult:
    """Tests for CostResult dataclass."""

    def test_basic_creation(self):
        """Test basic cost result creation."""
        result = CostResult(
            input_cost=0.005,
            output_cost=0.015,
            total_cost=0.02,
            input_tokens=1000,
            output_tokens=1000,
        )
        assert result.input_cost == 0.005
        assert result.output_cost == 0.015
        assert result.total_cost == 0.02
        assert result.input_tokens == 1000
        assert result.output_tokens == 1000
        assert result.currency == "USD"

    def test_with_provider_model(self):
        """Test with provider and model."""
        result = CostResult(
            input_cost=0.01,
            output_cost=0.02,
            total_cost=0.03,
            input_tokens=500,
            output_tokens=300,
            provider="openai",
            model="gpt-4o",
        )
        assert result.provider == "openai"
        assert result.model == "gpt-4o"


class TestGetPrice:
    """Tests for get_price function."""

    def test_get_price_success(self):
        """Test successful price retrieval."""
        mock_result = MagicMock()
        mock_result.input_cost = 0.005
        mock_result.output_cost = 0.015

        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(return_value=mock_result),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = get_price("openai", "gpt-4o")

            assert result is not None
            assert result.provider == "openai"
            assert result.model == "gpt-4o"

    def test_get_price_not_found(self):
        """Test price not found."""
        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(return_value=None),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = get_price("unknown", "model")
            assert result is None

    def test_get_price_exception(self):
        """Test handling generic exception."""
        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(side_effect=Exception("API error")),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = get_price("openai", "gpt-4o")
            assert result is None


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_calculate_cost_success(self):
        """Test successful cost calculation."""
        mock_result = MagicMock()
        mock_result.input_cost = 0.01
        mock_result.output_cost = 0.01
        mock_result.total_cost = 0.02

        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(return_value=mock_result),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = calculate_cost(
                provider="openai",
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=1000,
            )

            assert result.total_cost == 0.02
            assert result.input_tokens == 1000
            assert result.output_tokens == 1000
            assert result.provider == "openai"
            assert result.model == "gpt-4o"

    def test_calculate_cost_with_cached_tokens(self):
        """Test cost calculation with cached tokens."""
        mock_result = MagicMock()
        mock_result.input_cost = 0.0075
        mock_result.output_cost = 0.0075
        mock_result.total_cost = 0.015

        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(return_value=mock_result),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = calculate_cost(
                provider="anthropic",
                model="claude-3-5-sonnet",
                input_tokens=1000,
                output_tokens=500,
                cached_tokens=500,
            )

            assert result.total_cost == 0.015
            assert result.input_tokens == 1000
            assert result.output_tokens == 500

    def test_calculate_cost_no_result(self):
        """Test cost calculation when no result returned."""
        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(return_value=None),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = calculate_cost(
                provider="openai",
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=2000,
            )

            assert result.total_cost == 0.0
            assert result.input_cost == 0.0
            assert result.output_cost == 0.0

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        mock_result = MagicMock()
        mock_result.input_cost = 0.0
        mock_result.output_cost = 0.0
        mock_result.total_cost = 0.0

        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(return_value=mock_result),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = calculate_cost(
                provider="openai",
                model="gpt-4o",
                input_tokens=0,
                output_tokens=0,
            )

            assert result.total_cost == 0.0
            assert result.input_cost == 0.0
            assert result.output_cost == 0.0

    def test_calculate_cost_exception(self):
        """Test handling generic exception."""
        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(side_effect=Exception("API error")),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = calculate_cost(
                provider="openai",
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=1000,
            )

            # Should return zero cost
            assert result.total_cost == 0.0
            assert result.provider == "openai"
            assert result.model == "gpt-4o"

    def test_calculate_cost_none_values(self):
        """Test cost calculation when result has None values."""
        mock_result = MagicMock()
        mock_result.input_cost = None
        mock_result.output_cost = None
        mock_result.total_cost = None

        mock_usage_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "genai_prices": MagicMock(
                    calc_price=MagicMock(return_value=mock_result),
                    Usage=mock_usage_class,
                )
            },
        ):
            result = calculate_cost(
                provider="openai",
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=1000,
            )

            # Should handle None values gracefully
            assert result.total_cost == 0.0
            assert result.input_cost == 0.0
            assert result.output_cost == 0.0


class TestCostIntegration:
    """Integration tests using actual genai_prices library."""

    def test_real_get_price(self):
        """Test get_price with real genai_prices."""
        # This should work with the actual library
        result = get_price("openai", "gpt-4o")
        # Result might be None if model not found, or a PriceInfo
        assert result is None or isinstance(result, PriceInfo)

    def test_real_calculate_cost(self):
        """Test calculate_cost with real genai_prices."""
        result = calculate_cost(
            provider="openai",
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )
        # Should always return a CostResult
        assert isinstance(result, CostResult)
        assert result.input_tokens == 1000
        assert result.output_tokens == 500
