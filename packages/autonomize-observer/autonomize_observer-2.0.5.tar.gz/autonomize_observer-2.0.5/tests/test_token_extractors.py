"""Tests for token extraction using Strategy pattern."""

from __future__ import annotations

import pytest


class TestDirectFieldExtractor:
    """Tests for DirectFieldExtractor."""

    def test_can_extract_with_input_tokens(self) -> None:
        """Test detection of input_tokens field."""
        from autonomize_observer.tracing.utils.token_extractors import (
            DirectFieldExtractor,
        )

        extractor = DirectFieldExtractor()
        assert extractor.can_extract({"input_tokens": 100})
        assert extractor.can_extract({"output_tokens": 50})
        assert extractor.can_extract({"prompt_tokens": 100})
        assert extractor.can_extract({"completion_tokens": 50})
        assert not extractor.can_extract({"other": "data"})

    def test_extract_direct_fields(self) -> None:
        """Test extraction of direct token fields."""
        from autonomize_observer.tracing.utils.token_extractors import (
            DirectFieldExtractor,
        )

        extractor = DirectFieldExtractor()

        # Input/output tokens
        result = extractor.extract(
            {
                "input_tokens": 100,
                "output_tokens": 50,
                "model": "gpt-4",
            }
        )
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["model"] == "gpt-4"

        # Prompt/completion tokens
        result = extractor.extract(
            {
                "prompt_tokens": 200,
                "completion_tokens": 100,
            }
        )
        assert result["input_tokens"] == 200
        assert result["output_tokens"] == 100

    def test_extract_model_name_variant(self) -> None:
        """Test extraction of model_name field."""
        from autonomize_observer.tracing.utils.token_extractors import (
            DirectFieldExtractor,
        )

        extractor = DirectFieldExtractor()
        result = extractor.extract(
            {
                "input_tokens": 100,
                "model_name": "claude-3",
            }
        )
        assert result["model"] == "claude-3"


class TestOpenAIUsageExtractor:
    """Tests for OpenAI-style usage extraction."""

    def test_can_extract_openai_format(self) -> None:
        """Test detection of OpenAI usage format."""
        from autonomize_observer.tracing.utils.token_extractors import (
            OpenAIUsageExtractor,
        )

        extractor = OpenAIUsageExtractor()
        assert extractor.can_extract(
            {"usage": {"prompt_tokens": 100, "completion_tokens": 50}}
        )
        assert not extractor.can_extract({"usage": "invalid"})
        assert not extractor.can_extract({"other": "data"})

    def test_extract_openai_format(self) -> None:
        """Test extraction from OpenAI usage format."""
        from autonomize_observer.tracing.utils.token_extractors import (
            OpenAIUsageExtractor,
        )

        extractor = OpenAIUsageExtractor()
        result = extractor.extract(
            {
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                },
                "model": "gpt-4o",
            }
        )
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["model"] == "gpt-4o"

    def test_extract_input_output_variant(self) -> None:
        """Test extraction with input_tokens/output_tokens keys."""
        from autonomize_observer.tracing.utils.token_extractors import (
            OpenAIUsageExtractor,
        )

        extractor = OpenAIUsageExtractor()
        result = extractor.extract(
            {
                "usage": {
                    "input_tokens": 200,
                    "output_tokens": 100,
                }
            }
        )
        assert result["input_tokens"] == 200
        assert result["output_tokens"] == 100


class TestAnthropicUsageExtractor:
    """Tests for Anthropic-style usage extraction."""

    def test_can_extract_anthropic_format(self) -> None:
        """Test detection of Anthropic usage format."""
        from autonomize_observer.tracing.utils.token_extractors import (
            AnthropicUsageExtractor,
        )

        extractor = AnthropicUsageExtractor()
        assert extractor.can_extract(
            {"usage": {"input_tokens": 100, "output_tokens": 50}}
        )
        assert not extractor.can_extract(
            {"usage": {"prompt_tokens": 100}}  # OpenAI format
        )

    def test_extract_anthropic_format(self) -> None:
        """Test extraction from Anthropic usage format."""
        from autonomize_observer.tracing.utils.token_extractors import (
            AnthropicUsageExtractor,
        )

        extractor = AnthropicUsageExtractor()
        result = extractor.extract(
            {
                "usage": {
                    "input_tokens": 150,
                    "output_tokens": 75,
                },
                "model": "claude-3-opus-20240229",
            }
        )
        assert result["input_tokens"] == 150
        assert result["output_tokens"] == 75
        assert result["model"] == "claude-3-opus-20240229"


class TestLangChainExtractors:
    """Tests for LangChain-style extraction."""

    def test_response_metadata_extractor(self) -> None:
        """Test LangChain response_metadata extraction."""
        from autonomize_observer.tracing.utils.token_extractors import (
            LangChainResponseMetadataExtractor,
        )

        extractor = LangChainResponseMetadataExtractor()

        # Test can_extract
        assert extractor.can_extract(
            {
                "response_metadata": {
                    "token_usage": {"prompt_tokens": 100},
                    "model_name": "gpt-4",
                }
            }
        )
        assert not extractor.can_extract({"response_metadata": "invalid"})

        # Test extract
        result = extractor.extract(
            {
                "response_metadata": {
                    "token_usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                    },
                    "model_name": "gpt-4-turbo",
                }
            }
        )
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["model"] == "gpt-4-turbo"

    def test_llm_output_extractor(self) -> None:
        """Test LangChain llm_output extraction."""
        from autonomize_observer.tracing.utils.token_extractors import (
            LangChainLLMOutputExtractor,
        )

        extractor = LangChainLLMOutputExtractor()

        # Test can_extract
        assert extractor.can_extract(
            {
                "llm_output": {
                    "token_usage": {"prompt_tokens": 100},
                }
            }
        )
        assert not extractor.can_extract({"llm_output": "invalid"})

        # Test extract
        result = extractor.extract(
            {
                "llm_output": {
                    "token_usage": {
                        "prompt_tokens": 200,
                        "completion_tokens": 100,
                    },
                    "model_name": "claude-2",
                }
            }
        )
        assert result["input_tokens"] == 200
        assert result["output_tokens"] == 100
        assert result["model"] == "claude-2"


class TestTokenExtractorChain:
    """Tests for TokenExtractorChain."""

    def test_extract_openai_format(self) -> None:
        """Test chain extracts OpenAI format."""
        from autonomize_observer.tracing.utils.token_extractors import (
            TokenExtractorChain,
        )

        chain = TokenExtractorChain()
        result = chain.extract(
            {
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                },
                "model": "gpt-4o-mini",
            }
        )
        assert result is not None
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["model"] == "gpt-4o-mini"

    def test_extract_anthropic_format(self) -> None:
        """Test chain extracts Anthropic format."""
        from autonomize_observer.tracing.utils.token_extractors import (
            TokenExtractorChain,
        )

        chain = TokenExtractorChain()
        result = chain.extract(
            {
                "usage": {
                    "input_tokens": 150,
                    "output_tokens": 75,
                },
                "model": "claude-3-5-sonnet",
            }
        )
        assert result is not None
        assert result["input_tokens"] == 150
        assert result["output_tokens"] == 75

    def test_extract_langchain_format(self) -> None:
        """Test chain extracts LangChain format."""
        from autonomize_observer.tracing.utils.token_extractors import (
            TokenExtractorChain,
        )

        chain = TokenExtractorChain()
        result = chain.extract(
            {
                "response_metadata": {
                    "token_usage": {
                        "prompt_tokens": 200,
                        "completion_tokens": 100,
                    },
                    "model_name": "gpt-4",
                }
            }
        )
        assert result is not None
        assert result["input_tokens"] == 200
        assert result["output_tokens"] == 100
        assert result["model"] == "gpt-4"

    def test_extract_direct_fields(self) -> None:
        """Test chain extracts direct fields."""
        from autonomize_observer.tracing.utils.token_extractors import (
            TokenExtractorChain,
        )

        chain = TokenExtractorChain()
        result = chain.extract(
            {
                "input_tokens": 50,
                "output_tokens": 25,
            }
        )
        assert result is not None
        assert result["input_tokens"] == 50
        assert result["output_tokens"] == 25

    def test_extract_empty_returns_none(self) -> None:
        """Test chain returns None for empty outputs."""
        from autonomize_observer.tracing.utils.token_extractors import (
            TokenExtractorChain,
        )

        chain = TokenExtractorChain()
        assert chain.extract({}) is None
        assert chain.extract(None) is None  # type: ignore

    def test_extract_no_tokens_returns_none(self) -> None:
        """Test chain returns None when no tokens found."""
        from autonomize_observer.tracing.utils.token_extractors import (
            TokenExtractorChain,
        )

        chain = TokenExtractorChain()
        assert chain.extract({"other": "data"}) is None

    def test_add_custom_extractor(self) -> None:
        """Test adding custom extractor."""
        from autonomize_observer.tracing.utils.token_extractors import (
            TokenExtractor,
            TokenExtractorChain,
        )

        class CustomExtractor(TokenExtractor):
            def can_extract(self, outputs: dict) -> bool:
                return "custom_usage" in outputs

            def extract(self, outputs: dict) -> dict:
                return {
                    "input_tokens": outputs["custom_usage"]["in"],
                    "output_tokens": outputs["custom_usage"]["out"],
                }

        chain = TokenExtractorChain()
        chain.add_extractor(CustomExtractor(), priority=0)

        result = chain.extract({"custom_usage": {"in": 300, "out": 150}})
        assert result is not None
        assert result["input_tokens"] == 300
        assert result["output_tokens"] == 150
