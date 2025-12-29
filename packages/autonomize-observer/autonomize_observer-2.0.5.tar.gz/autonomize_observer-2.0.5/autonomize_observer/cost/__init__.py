"""Cost calculation module - wraps genai-prices library.

genai-prices provides:
- Cost calculation for 28+ LLM providers
- Model matching with fuzzy matching
- Historic prices and price changes
- Tiered pricing (Gemini context-based)
- Cached token pricing

We expose a simple interface to calculate costs.
"""

from autonomize_observer.cost.pricing import calculate_cost, get_price

__all__ = [
    "calculate_cost",
    "get_price",
]
