"""Pricing utilities - thin wrapper around genai-prices.

genai-prices handles all the complexity of LLM pricing:
- Model name matching
- Provider normalization
- Historic prices
- Tiered pricing
- Cached token discounts

We just expose simple functions for the most common use cases.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PriceInfo:
    """Price information for a model."""

    provider: str
    model: str
    input_price_per_token: float
    output_price_per_token: float
    cached_input_price_per_token: float | None = None
    currency: str = "USD"

    @property
    def input_price_per_1k(self) -> float:
        """Input price per 1000 tokens."""
        return self.input_price_per_token * 1000

    @property
    def output_price_per_1k(self) -> float:
        """Output price per 1000 tokens."""
        return self.output_price_per_token * 1000


@dataclass
class CostResult:
    """Result of a cost calculation."""

    input_cost: float
    output_cost: float
    total_cost: float
    input_tokens: int
    output_tokens: int
    provider: str = ""
    model: str = ""
    currency: str = "USD"


def get_price(provider: str, model: str) -> PriceInfo | None:
    """Get pricing information for a model.

    Uses genai-prices library for accurate, up-to-date pricing.
    Note: genai-prices uses calc_price for actual cost calculation.
    This function uses a simple calculation to get per-token rates.

    Args:
        provider: LLM provider (e.g., 'openai', 'anthropic')
        model: Model name (e.g., 'gpt-4o', 'claude-3-5-sonnet-20241022')

    Returns:
        PriceInfo with pricing details, or None if not found
    """
    try:
        from genai_prices import Usage, calc_price

        # Calculate price for 1000 tokens to get per-token rate
        usage = Usage(input_tokens=1000, output_tokens=1000)
        result = calc_price(usage, model, provider_id=provider)

        if result is None:
            logger.debug(f"No price found for {provider}/{model}")
            return None

        # Extract per-token prices from result
        input_price = result.input_cost / 1000 if result.input_cost else 0.0
        output_price = result.output_cost / 1000 if result.output_cost else 0.0

        return PriceInfo(
            provider=provider,
            model=model,
            input_price_per_token=input_price,
            output_price_per_token=output_price,
            cached_input_price_per_token=None,  # genai-prices handles cached pricing internally
        )
    except ImportError:
        logger.warning(
            "genai-prices not installed. Install with: pip install genai-prices"
        )
        return None
    except Exception as e:
        logger.warning(f"Error getting price for {provider}/{model}: {e}")
        return None


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> CostResult:
    """Calculate cost for LLM usage.

    Uses genai-prices library for accurate pricing.

    Args:
        provider: LLM provider (e.g., 'openai', 'anthropic')
        model: Model name (e.g., 'gpt-4o', 'claude-3-5-sonnet-20241022')
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cached_tokens: Number of cached input tokens (discounted price)

    Returns:
        CostResult with calculated costs
    """
    try:
        from genai_prices import Usage, calc_price

        # Use genai-prices calc_price for cost calculation
        usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens)
        result = calc_price(usage, model, provider_id=provider)

        if result is None:
            logger.warning(f"No pricing found for {provider}/{model}")
            return CostResult(
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider=provider,
                model=model,
            )

        input_cost = result.input_cost or 0.0
        output_cost = result.output_cost or 0.0
        total_cost = result.total_cost or (input_cost + output_cost)

        return CostResult(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=provider,
            model=model,
        )

    except ImportError:
        logger.warning(
            "genai-prices not installed. Returning zero cost. "
            "Install with: pip install genai-prices"
        )
        return CostResult(
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=provider,
            model=model,
        )
    except Exception as e:
        logger.warning(f"Error calculating cost: {e}")
        return CostResult(
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=provider,
            model=model,
        )
