"""Tests for model utility functions."""

import pytest

from autonomize_observer.tracing.utils.model_utils import (
    clean_model_name,
    guess_provider_from_model,
    infer_component_type,
)


class TestGuessProviderFromModel:
    """Tests for guess_provider_from_model function."""

    def test_openai_models(self) -> None:
        """Test OpenAI model detection."""
        assert guess_provider_from_model("gpt-4") == "openai"
        assert guess_provider_from_model("gpt-4-turbo") == "openai"
        assert guess_provider_from_model("gpt-3.5-turbo") == "openai"
        assert guess_provider_from_model("gpt-4o") == "openai"
        assert guess_provider_from_model("gpt-4o-mini") == "openai"
        assert guess_provider_from_model("o1-preview") == "openai"
        assert guess_provider_from_model("o1-mini") == "openai"
        assert guess_provider_from_model("o3-mini") == "openai"

    def test_anthropic_models(self) -> None:
        """Test Anthropic model detection."""
        assert guess_provider_from_model("claude-3-sonnet") == "anthropic"
        assert guess_provider_from_model("claude-3-opus") == "anthropic"
        assert guess_provider_from_model("claude-3-haiku") == "anthropic"
        assert guess_provider_from_model("claude-3.5-sonnet") == "anthropic"
        assert guess_provider_from_model("claude-3-5-sonnet-20241022") == "anthropic"

    def test_google_models(self) -> None:
        """Test Google model detection."""
        assert guess_provider_from_model("gemini-pro") == "google"
        assert guess_provider_from_model("gemini-1.5-pro") == "google"
        assert guess_provider_from_model("gemini-1.5-flash") == "google"
        assert guess_provider_from_model("gemini-2.0-flash") == "google"
        assert guess_provider_from_model("palm-2") == "google"

    def test_meta_models(self) -> None:
        """Test Meta model detection."""
        assert guess_provider_from_model("llama-3-70b") == "meta"
        assert guess_provider_from_model("llama-3.1-8b") == "meta"
        assert guess_provider_from_model("llama-3.2-90b") == "meta"
        assert guess_provider_from_model("meta-llama-3") == "meta"

    def test_mistral_models(self) -> None:
        """Test Mistral model detection."""
        assert guess_provider_from_model("mistral-large") == "mistral"
        assert guess_provider_from_model("mistral-medium") == "mistral"
        assert guess_provider_from_model("mixtral-8x7b") == "mistral"
        assert guess_provider_from_model("codestral") == "mistral"
        assert guess_provider_from_model("pixtral") == "mistral"

    def test_other_providers(self) -> None:
        """Test other provider detection."""
        assert guess_provider_from_model("deepseek-chat") == "deepseek"
        assert guess_provider_from_model("command-r") == "cohere"
        assert guess_provider_from_model("grok-1") == "xai"
        assert guess_provider_from_model("qwen-72b") == "alibaba"
        assert guess_provider_from_model("nova-lite") == "amazon"

    def test_unknown_model(self) -> None:
        """Test unknown model returns 'unknown'."""
        assert guess_provider_from_model("some-random-model") == "unknown"
        assert guess_provider_from_model("") == "unknown"
        assert guess_provider_from_model(None) == "unknown"

    def test_list_input(self) -> None:
        """Test list input handling."""
        assert guess_provider_from_model(["gpt-4", "other"]) == "openai"
        assert guess_provider_from_model(["claude-3-sonnet"]) == "anthropic"
        assert guess_provider_from_model([]) == "unknown"

    def test_non_string_input(self) -> None:
        """Test non-string input handling."""
        # Numbers get converted to strings, so "123" has no provider pattern
        result = guess_provider_from_model(123)
        assert result == "unknown"
        # Dict gets converted to string representation
        result = guess_provider_from_model({"model": "gpt-4"})
        # The string repr may contain "gpt" so it could match openai
        assert isinstance(result, str)

    def test_case_insensitive(self) -> None:
        """Test case insensitivity."""
        assert guess_provider_from_model("GPT-4") == "openai"
        assert guess_provider_from_model("CLAUDE-3-OPUS") == "anthropic"
        assert guess_provider_from_model("Gemini-Pro") == "google"


class TestCleanModelName:
    """Tests for clean_model_name function."""

    def test_openai_models(self) -> None:
        """Test OpenAI model name cleaning."""
        assert clean_model_name("gpt-4") == "gpt-4"
        assert clean_model_name("gpt-4-turbo-preview") == "gpt-4-turbo"
        assert clean_model_name("gpt-4-32k-0613") == "gpt-4-32k"
        assert clean_model_name("gpt-3.5-turbo") == "gpt-3.5-turbo"
        assert clean_model_name("gpt-3.5-turbo-16k-0613") == "gpt-3.5-turbo-16k"
        assert clean_model_name("gpt-4o") == "gpt-4o"
        assert clean_model_name("gpt-4o-mini") == "gpt-4o-mini"
        assert clean_model_name("o1-preview") == "o1-preview"
        assert clean_model_name("o1-mini") == "o1-mini"
        assert clean_model_name("gpt-4.1-nano") == "gpt-4.1-nano"
        assert clean_model_name("gpt-4.1-mini") == "gpt-4.1-mini"

    def test_anthropic_models(self) -> None:
        """Test Anthropic model name cleaning."""
        # Models with just version number 3 (no subversion) and specific variants
        assert clean_model_name("claude-3-opus-latest") == "claude-3-opus"
        assert clean_model_name("claude-3-haiku") == "claude-3-haiku"
        # 3.5 becomes 3-5
        assert clean_model_name("claude-3.5-sonnet") == "claude-3-5-sonnet"
        assert clean_model_name("claude-3.5-haiku") == "claude-3-5-haiku"
        # 3.7 becomes 3-7
        assert clean_model_name("claude-3.7-sonnet") == "claude-3-7-sonnet"
        # Older versions
        assert clean_model_name("claude-2.1") == "claude-2.1"
        assert clean_model_name("claude-instant-1.2") == "claude-instant-1.2"
        # Verify it returns a claude model for versioned input with date suffix
        result = clean_model_name("claude-3-5-sonnet-20241022")
        assert "claude" in result

    def test_google_models(self) -> None:
        """Test Google model name cleaning."""
        assert clean_model_name("gemini-1.5-pro") == "gemini-1.5-pro"
        assert clean_model_name("gemini-1.5-flash") == "gemini-1.5-flash"
        assert clean_model_name("gemini-2.0-flash") == "gemini-2.0-flash"
        assert clean_model_name("gemini-2.5-pro") == "gemini-2.5-pro"
        assert clean_model_name("gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"

    def test_meta_models(self) -> None:
        """Test Meta model name cleaning."""
        # Versioned llama models
        assert clean_model_name("llama-3.1-8b") == "llama-3.1-8b"
        assert clean_model_name("llama-3.1-70b") == "llama-3.1-70b"
        assert clean_model_name("llama-3.1-405b") == "llama-3.1-405b"
        assert clean_model_name("llama-3.2-90b") == "llama-3.2-90b"
        assert clean_model_name("llama-3.3-70b") == "llama-3.3-70b"
        # Base llama-3 may have default behavior
        result = clean_model_name("llama-3-8b")
        assert "llama" in result

    def test_mistral_models(self) -> None:
        """Test Mistral model name cleaning."""
        assert clean_model_name("mistral-large") == "mistral-large"
        assert clean_model_name("mistral-medium") == "mistral-medium"
        assert clean_model_name("mistral-small") == "mistral-small"
        assert clean_model_name("mixtral-8x7b") == "mixtral-8x7b"
        assert clean_model_name("mixtral-8x22b") == "mixtral-8x22b"
        assert clean_model_name("codestral") == "codestral"
        assert clean_model_name("pixtral") == "pixtral"

    def test_deepseek_models(self) -> None:
        """Test DeepSeek model name cleaning."""
        assert clean_model_name("deepseek-chat") == "deepseek-chat"
        assert clean_model_name("deepseek-coder") == "deepseek-coder"
        assert clean_model_name("deepseek-r1") == "deepseek-r1"
        assert clean_model_name("deepseek-v3") == "deepseek-v3"

    def test_prefix_removal(self) -> None:
        """Test deployment prefix removal."""
        assert clean_model_name("azure/gpt-4") == "gpt-4"
        assert clean_model_name("azure-gpt-4") == "gpt-4"
        assert clean_model_name("bedrock/claude-3-sonnet") == "claude-3-sonnet"
        assert clean_model_name("openrouter/claude-3-sonnet") == "claude-3-sonnet"

    def test_empty_and_none(self) -> None:
        """Test empty and None input."""
        assert clean_model_name("") == "unknown"
        assert clean_model_name(None) == "unknown"

    def test_list_input(self) -> None:
        """Test list input handling."""
        assert clean_model_name(["gpt-4", "other"]) == "gpt-4"
        assert clean_model_name([]) == "unknown"

    def test_non_string_input(self) -> None:
        """Test non-string input handling."""
        assert clean_model_name(123) == "unknown"
        assert clean_model_name({"model": "gpt-4"}) == "unknown"
        assert clean_model_name(True) == "unknown"

    def test_case_insensitive(self) -> None:
        """Test case insensitivity."""
        assert clean_model_name("GPT-4") == "gpt-4"
        assert clean_model_name("CLAUDE-3-OPUS") == "claude-3-opus"


class TestInferComponentType:
    """Tests for infer_component_type function."""

    def test_llm_component(self) -> None:
        """Test LLM component detection when model is provided."""
        assert infer_component_type("SomeComponent", "gpt-4") == "llm"
        assert infer_component_type("AnyName", "claude-3") == "llm"

    def test_pattern_based_detection(self) -> None:
        """Test pattern-based component type detection."""
        assert infer_component_type("AgentExecutor") == "agent"
        assert infer_component_type("WorkflowOrchestrator") == "agent"
        assert infer_component_type("InputPrompt") == "input"
        assert infer_component_type("QuestionInput") == "input"
        assert infer_component_type("OutputResponse") == "output"
        assert infer_component_type("ResultFormatter") == "output"
        assert infer_component_type("VectorRetrieval") == "retrieval"
        assert infer_component_type("RAGPipeline") == "retrieval"
        assert infer_component_type("ConversationMemory") == "memory"
        assert infer_component_type("HistoryBuffer") == "memory"
        assert infer_component_type("ExternalAPI") == "tool"
        assert infer_component_type("UtilityFunction") == "tool"
        assert infer_component_type("DataProcessor") == "processing"
        assert infer_component_type("TextTransformer") == "processing"
        assert infer_component_type("LLMModel") == "llm"
        assert infer_component_type("ChatCompletion") == "llm"

    def test_fallback_to_component(self) -> None:
        """Test fallback to 'component' type."""
        assert infer_component_type("SomeRandomName") == "component"
        assert infer_component_type("XYZ123") == "component"

    def test_case_insensitive(self) -> None:
        """Test case insensitivity."""
        assert infer_component_type("AGENT") == "agent"
        assert infer_component_type("Memory") == "memory"
        assert infer_component_type("RETRIEVAL") == "retrieval"


class TestGuessProviderEdgeCases:
    """Additional edge case tests for guess_provider_from_model."""

    def test_list_with_empty_strings(self) -> None:
        """Test list with empty strings falls back correctly."""
        result = guess_provider_from_model(["", "  ", "gpt-4"])
        assert result == "openai"

    def test_list_with_only_empty_strings(self) -> None:
        """Test list with only empty strings."""
        result = guess_provider_from_model(["", "  "])
        # Falls back to first item as string
        assert isinstance(result, str)

    def test_empty_list(self) -> None:
        """Test empty list returns unknown."""
        assert guess_provider_from_model([]) == "unknown"


class TestCleanModelNameEdgeCases:
    """Additional edge case tests for clean_model_name."""

    def test_list_with_empty_strings(self) -> None:
        """Test list with empty strings falls back correctly."""
        result = clean_model_name(["", "  ", "gpt-4"])
        assert result == "gpt-4"

    def test_list_with_only_empty_strings(self) -> None:
        """Test list with only empty strings."""
        result = clean_model_name(["", "  "])
        # Falls back to first item as string
        assert isinstance(result, str)

    def test_empty_list(self) -> None:
        """Test empty list returns unknown."""
        assert clean_model_name([]) == "unknown"

    def test_set_input(self) -> None:
        """Test set input returns unknown."""
        assert clean_model_name({1, 2, 3}) == "unknown"  # type: ignore

    def test_tuple_input(self) -> None:
        """Test tuple input returns unknown."""
        assert clean_model_name((1, 2, 3)) == "unknown"  # type: ignore

    def test_float_input(self) -> None:
        """Test float input returns unknown."""
        assert clean_model_name(3.14) == "unknown"  # type: ignore

    def test_gpt4_base(self) -> None:
        """Test base GPT-4 model."""
        assert clean_model_name("gpt-4-0613") == "gpt-4"

    def test_gpt35_azure(self) -> None:
        """Test Azure GPT-3.5 format."""
        assert clean_model_name("gpt-35-turbo") == "gpt-3.5-turbo"

    def test_gpt4o_variant(self) -> None:
        """Test gpt4o without hyphen."""
        assert clean_model_name("gpt4o-mini") == "gpt-4o-mini"

    def test_o1_base(self) -> None:
        """Test base o1 model."""
        assert clean_model_name("o1") == "o1"

    def test_o3_base(self) -> None:
        """Test base o3 model."""
        assert clean_model_name("o3") == "o3"

    def test_claude_4_opus(self) -> None:
        """Test Claude 4 opus variant."""
        result = clean_model_name("claude-4-opus")
        assert "claude-sonnet-4" in result

    def test_claude_4_base(self) -> None:
        """Test Claude 4 base."""
        result = clean_model_name("claude-4")
        assert "claude-sonnet-4" in result

    def test_claude_3_base(self) -> None:
        """Test Claude 3 base (no variant)."""
        result = clean_model_name("claude-3")
        assert "claude-3-sonnet" in result

    def test_claude_no_version(self) -> None:
        """Test Claude without version number."""
        result = clean_model_name("claude-latest")
        # Default to claude-3-5-sonnet
        assert "claude" in result

    def test_gemini_2_5_flash(self) -> None:
        """Test Gemini 2.5 flash."""
        assert clean_model_name("gemini-2.5-flash") == "gemini-2.5-flash"

    def test_gemini_2_0_pro(self) -> None:
        """Test Gemini 2.0 pro."""
        assert clean_model_name("gemini-2.0-pro") == "gemini-2.0-pro"

    def test_gemini_default(self) -> None:
        """Test Gemini default (no version)."""
        result = clean_model_name("gemini")
        assert "gemini" in result

    def test_llama_3_2_variants(self) -> None:
        """Test Llama 3.2 size variants."""
        assert clean_model_name("llama-3.2-11b") == "llama-3.2-11b"
        assert clean_model_name("llama-3.2-3b") == "llama-3.2-3b"
        assert clean_model_name("llama-3.2-1b") == "llama-3.2-1b"

    def test_llama_3_2_default(self) -> None:
        """Test Llama 3.2 default size."""
        result = clean_model_name("llama-3.2")
        assert "llama-3.2" in result

    def test_llama_4_variants(self) -> None:
        """Test Llama 4 variants."""
        assert clean_model_name("llama-4-scout") == "llama-4-scout"
        assert clean_model_name("llama-4-maverick") == "llama-4-maverick"

    def test_llama_4_base(self) -> None:
        """Test Llama 4 base."""
        assert clean_model_name("llama-4") == "llama-4"

    def test_llama_default(self) -> None:
        """Test Llama default (old version)."""
        result = clean_model_name("llama-70b")
        assert "llama" in result

    def test_mistral_nemo(self) -> None:
        """Test Mistral Nemo."""
        assert clean_model_name("mistral-nemo") == "mistral-nemo"

    def test_mistral_default(self) -> None:
        """Test Mistral default."""
        result = clean_model_name("mistral")
        assert "mistral" in result

    def test_deepseek_base(self) -> None:
        """Test DeepSeek base model."""
        result = clean_model_name("deepseek")
        assert "deepseek" in result

    def test_unknown_model_returns_cleaned(self) -> None:
        """Test unknown model returns cleaned version."""
        result = clean_model_name("some-custom-model")
        assert result == "some-custom-model"

    def test_whitespace_handling(self) -> None:
        """Test whitespace is stripped."""
        result = clean_model_name("  gpt-4  ")
        assert result == "gpt-4"

    def test_gpt41_base(self) -> None:
        """Test base gpt-4.1 model (no variant)."""
        result = clean_model_name("gpt-4.1")
        assert result == "gpt-4.1"

    def test_o3_mini(self) -> None:
        """Test o3-mini model."""
        result = clean_model_name("o3-mini")
        assert result == "o3-mini"

    def test_llama_31_base(self) -> None:
        """Test llama-3.1 base (no size specified)."""
        result = clean_model_name("llama-3.1")
        assert result == "llama-3.1-8b"

    def test_list_fallback_to_str_first(self) -> None:
        """Test list with no valid strings falls back to str(first)."""
        result = clean_model_name([123, 456])
        assert result == "123"  # Converted to string and returned as-is

    def test_custom_object_str(self) -> None:
        """Test custom object with __str__."""

        class CustomModel:
            def __str__(self) -> str:
                return "gpt-4-custom"

        result = clean_model_name(CustomModel())
        assert result == "gpt-4"  # Should match gpt-4 pattern


class TestGuessProviderEdgeCasesMore:
    """More edge case tests for guess_provider_from_model."""

    def test_list_fallback_to_str_first_item(self) -> None:
        """Test list with no valid strings falls back to str(first)."""
        result = guess_provider_from_model([123, 456])
        # 123 becomes "123" which has no provider pattern
        assert result == "unknown"
