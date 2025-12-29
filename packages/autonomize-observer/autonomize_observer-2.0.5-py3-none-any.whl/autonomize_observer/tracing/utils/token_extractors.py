"""Token extraction using Strategy pattern.

This module provides extensible token extraction from various LLM
output formats, replacing the monolithic if/else chain.

Usage:
    from autonomize_observer.tracing.utils.token_extractors import TokenExtractorChain

    chain = TokenExtractorChain()
    result = chain.extract(outputs)
    if result:
        print(f"Input: {result.get('input_tokens')}")
        print(f"Output: {result.get('output_tokens')}")
        print(f"Model: {result.get('model')}")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TokenExtractor(ABC):
    """Base class for token extractors.

    Each extractor handles a specific output format from an LLM provider.
    Extractors are tried in order until one successfully extracts tokens.
    """

    @abstractmethod
    def can_extract(self, outputs: dict[str, Any]) -> bool:
        """Check if this extractor can handle the output format.

        Args:
            outputs: Output dictionary from LLM call

        Returns:
            True if this extractor can extract from this format
        """
        ...

    @abstractmethod
    def extract(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Extract token usage and model info.

        Args:
            outputs: Output dictionary from LLM call

        Returns:
            Dictionary with keys: input_tokens, output_tokens, model
        """
        ...


class DirectFieldExtractor(TokenExtractor):
    """Extracts tokens from direct fields.

    Handles outputs with direct token fields like:
    - input_tokens, output_tokens
    - prompt_tokens, completion_tokens
    """

    def can_extract(self, outputs: dict[str, Any]) -> bool:
        """Check for direct token fields."""
        return any(
            key in outputs
            for key in [
                "input_tokens",
                "output_tokens",
                "prompt_tokens",
                "completion_tokens",
            ]
        )

    def extract(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Extract from direct fields."""
        result: dict[str, Any] = {}

        # Token fields
        if "input_tokens" in outputs:
            result["input_tokens"] = outputs["input_tokens"]
        elif "prompt_tokens" in outputs:
            result["input_tokens"] = outputs["prompt_tokens"]

        if "output_tokens" in outputs:
            result["output_tokens"] = outputs["output_tokens"]
        elif "completion_tokens" in outputs:
            result["output_tokens"] = outputs["completion_tokens"]

        # Model name
        if "model" in outputs:
            result["model"] = outputs["model"]
        elif "model_name" in outputs:
            result["model"] = outputs["model_name"]

        return result


class OpenAIUsageExtractor(TokenExtractor):
    """Extracts tokens from OpenAI-style usage object.

    Handles outputs with nested usage dict:
    {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }
    """

    def can_extract(self, outputs: dict[str, Any]) -> bool:
        """Check for OpenAI-style usage object."""
        return "usage" in outputs and isinstance(outputs.get("usage"), dict)

    def extract(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Extract from OpenAI usage format."""
        result: dict[str, Any] = {}
        usage = outputs.get("usage", {})

        # Try OpenAI format first
        if "prompt_tokens" in usage:
            result["input_tokens"] = usage["prompt_tokens"]
        elif "input_tokens" in usage:
            result["input_tokens"] = usage["input_tokens"]

        if "completion_tokens" in usage:
            result["output_tokens"] = usage["completion_tokens"]
        elif "output_tokens" in usage:
            result["output_tokens"] = usage["output_tokens"]

        # Model from top level
        if "model" in outputs:
            result["model"] = outputs["model"]
        elif "model_name" in outputs:
            result["model"] = outputs["model_name"]

        return result


class LangChainResponseMetadataExtractor(TokenExtractor):
    """Extracts tokens from LangChain response_metadata.

    Handles outputs with response_metadata:
    {
        "response_metadata": {
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            },
            "model_name": "gpt-4"
        }
    }
    """

    def can_extract(self, outputs: dict[str, Any]) -> bool:
        """Check for LangChain response_metadata."""
        rm = outputs.get("response_metadata")
        if not isinstance(rm, dict):
            return False
        return "token_usage" in rm or "model_name" in rm

    def extract(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Extract from LangChain response_metadata format."""
        result: dict[str, Any] = {}
        rm = outputs.get("response_metadata", {})

        # Token usage
        tu = rm.get("token_usage", {})
        if isinstance(tu, dict):
            if "prompt_tokens" in tu:
                result["input_tokens"] = tu["prompt_tokens"]
            if "completion_tokens" in tu:
                result["output_tokens"] = tu["completion_tokens"]

        # Model name
        if "model_name" in rm:
            result["model"] = rm["model_name"]

        return result


class LangChainLLMOutputExtractor(TokenExtractor):
    """Extracts tokens from LangChain llm_output.

    Handles outputs with llm_output:
    {
        "llm_output": {
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            },
            "model_name": "gpt-4"
        }
    }
    """

    def can_extract(self, outputs: dict[str, Any]) -> bool:
        """Check for LangChain llm_output."""
        llm = outputs.get("llm_output")
        if not isinstance(llm, dict):
            return False
        return "token_usage" in llm or "model_name" in llm

    def extract(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Extract from LangChain llm_output format."""
        result: dict[str, Any] = {}
        llm = outputs.get("llm_output", {})

        # Token usage
        tu = llm.get("token_usage", {})
        if isinstance(tu, dict):
            if "prompt_tokens" in tu:
                result["input_tokens"] = tu["prompt_tokens"]
            if "completion_tokens" in tu:
                result["output_tokens"] = tu["completion_tokens"]

        # Model name
        if "model_name" in llm:
            result["model"] = llm["model_name"]

        return result


class AnthropicUsageExtractor(TokenExtractor):
    """Extracts tokens from Anthropic-style usage.

    Handles outputs with input_tokens/output_tokens at top level
    (already covered by DirectFieldExtractor, but this handles
    the specific Anthropic message format):
    {
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50
        },
        "model": "claude-3-opus-20240229"
    }
    """

    def can_extract(self, outputs: dict[str, Any]) -> bool:
        """Check for Anthropic-style usage."""
        usage = outputs.get("usage")
        if not isinstance(usage, dict):
            return False
        # Anthropic uses input_tokens/output_tokens directly
        return "input_tokens" in usage or "output_tokens" in usage

    def extract(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Extract from Anthropic usage format."""
        result: dict[str, Any] = {}
        usage = outputs.get("usage", {})

        if "input_tokens" in usage:
            result["input_tokens"] = usage["input_tokens"]
        if "output_tokens" in usage:
            result["output_tokens"] = usage["output_tokens"]

        # Model from top level
        if "model" in outputs:
            result["model"] = outputs["model"]

        return result


class TokenExtractorChain:
    """Chain of token extractors using Strategy pattern.

    Tries extractors in order until one successfully extracts tokens.
    New extractors can be added to support additional formats.

    Example:
        ```python
        chain = TokenExtractorChain()

        # Extract from any supported format
        result = chain.extract(outputs)

        # Add custom extractor
        chain.add_extractor(MyCustomExtractor())
        ```
    """

    def __init__(self, extractors: list[TokenExtractor] | None = None) -> None:
        """Initialize with default or custom extractors.

        Args:
            extractors: List of extractors (uses defaults if None)
        """
        self.extractors = extractors or self._default_extractors()

    @staticmethod
    def _default_extractors() -> list[TokenExtractor]:
        """Get default extractors in priority order."""
        return [
            # OpenAI format is most common
            OpenAIUsageExtractor(),
            # Anthropic format (similar but uses input_tokens/output_tokens)
            AnthropicUsageExtractor(),
            # LangChain formats
            LangChainResponseMetadataExtractor(),
            LangChainLLMOutputExtractor(),
            # Direct fields (fallback)
            DirectFieldExtractor(),
        ]

    def add_extractor(
        self,
        extractor: TokenExtractor,
        priority: int | None = None,
    ) -> None:
        """Add a custom extractor.

        Args:
            extractor: Extractor to add
            priority: Position in chain (None = append to end)
        """
        if priority is None:
            self.extractors.append(extractor)
        else:
            self.extractors.insert(priority, extractor)

    def extract(self, outputs: dict[str, Any]) -> dict[str, Any] | None:
        """Extract token usage from outputs.

        Tries each extractor in order until one succeeds.

        Args:
            outputs: Output dictionary from LLM call

        Returns:
            Dictionary with input_tokens, output_tokens, model
            or None if no extractor could handle the format
        """
        if not outputs:
            return None

        for extractor in self.extractors:
            if extractor.can_extract(outputs):
                result = extractor.extract(outputs)
                if result:
                    return result

        return None


__all__ = [
    "TokenExtractor",
    "TokenExtractorChain",
    "DirectFieldExtractor",
    "OpenAIUsageExtractor",
    "AnthropicUsageExtractor",
    "LangChainResponseMetadataExtractor",
    "LangChainLLMOutputExtractor",
]
