"""Model name utilities for LLM provider detection and cleaning.

Provides utilities for inferring providers from model names
and cleaning/normalizing model names for consistent tracking.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Provider pattern mapping
PROVIDER_PATTERNS: dict[str, list[str]] = {
    "openai": [
        "gpt",
        "openai",
        "o1",
        "o3",
        "o4",
        "davinci",
        "babbage",
        "whisper",
        "tts",
    ],
    "anthropic": ["claude", "anthropic"],
    "google": ["gemini", "google", "palm", "bard"],
    "meta": ["llama", "meta"],
    "mistral": ["mistral", "mixtral", "codestral", "pixtral"],
    "amazon": ["nova", "amazon", "bedrock"],
    "deepseek": ["deepseek"],
    "cohere": ["command", "cohere"],
    "xai": ["grok", "xai"],
    "alibaba": ["qwen", "alibaba"],
    "perplexity": ["perplexity", "sonar"],
    "nvidia": ["nemotron", "nvidia"],
}

# Component type patterns
COMPONENT_TYPE_PATTERNS: dict[str, list[str]] = {
    "agent": ["agent", "executor", "workflow", "orchestrator"],
    "input": ["input", "prompt", "question", "query"],
    "output": ["output", "response", "result", "answer"],
    "retrieval": ["retrieval", "vector", "search", "rag", "knowledge"],
    "memory": ["memory", "history", "context", "conversation"],
    "tool": ["tool", "function", "api", "external", "utility"],
    "processing": ["process", "transform", "parse", "format"],
    "llm": ["llm", "model", "chat", "completion"],
}


def guess_provider_from_model(model_name: str | list[str] | Any) -> str:
    """Guess provider from model name using pattern matching.

    Args:
        model_name: Model name, can be string, list, or other type

    Returns:
        Provider name or "unknown" if not detected
    """
    if not model_name:
        return "unknown"

    # Ensure we have a string
    if isinstance(model_name, list):
        if len(model_name) > 0:
            for item in model_name:
                if isinstance(item, str) and item.strip():
                    model_name = item
                    break
            else:
                model_name = str(model_name[0]) if model_name else "unknown"
        else:
            return "unknown"
    elif not isinstance(model_name, str):
        model_name = str(model_name)

    model_lower = model_name.lower()

    for provider, patterns in PROVIDER_PATTERNS.items():
        if any(pattern in model_lower for pattern in patterns):
            return provider

    return "unknown"


def clean_model_name(model_name: str | list[str] | Any) -> str:
    """Clean and normalize model name.

    Args:
        model_name: Model name to clean

    Returns:
        Cleaned and normalized model name
    """
    if not model_name:
        return "unknown"

    # Ensure we have a string
    if isinstance(model_name, list):
        if len(model_name) > 0:
            for item in model_name:
                if isinstance(item, str) and item.strip():
                    model_name = item
                    break
            else:
                model_name = str(model_name[0]) if model_name else "unknown"
        else:
            return "unknown"
    elif not isinstance(model_name, str):
        if isinstance(model_name, (int, float, bool, dict, set, tuple)):
            return "unknown"
        model_name = str(model_name)

    cleaned = model_name.lower().strip()

    # Remove common deployment prefixes
    prefixes_to_remove = ["azure/", "azure-", "bedrock/", "openrouter/"]
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]

    # OpenAI models
    if "gpt-4.1" in cleaned:
        if "nano" in cleaned:
            return "gpt-4.1-nano"
        elif "mini" in cleaned:
            return "gpt-4.1-mini"
        return "gpt-4.1"
    elif "gpt-4o" in cleaned or "gpt4o" in cleaned:
        if "mini" in cleaned:
            return "gpt-4o-mini"
        return "gpt-4o"
    elif "gpt-4" in cleaned:
        if "turbo" in cleaned:
            return "gpt-4-turbo"
        elif "32k" in cleaned:
            return "gpt-4-32k"
        return "gpt-4"
    elif "gpt-3.5" in cleaned or "gpt-35" in cleaned:
        if "16k" in cleaned:
            return "gpt-3.5-turbo-16k"
        return "gpt-3.5-turbo"
    elif "o1" in cleaned:
        if "mini" in cleaned:
            return "o1-mini"
        elif "preview" in cleaned:
            return "o1-preview"
        return "o1"
    elif "o3" in cleaned:
        if "mini" in cleaned:
            return "o3-mini"
        return "o3"

    # Anthropic models
    elif "claude" in cleaned:
        # Check instant first since it contains version numbers that could match
        if "instant" in cleaned:
            return "claude-instant-1.2"
        elif "4" in cleaned:
            if "opus" in cleaned:
                return "claude-sonnet-4"  # Claude 4 uses sonnet naming
            elif "sonnet" in cleaned:
                return "claude-sonnet-4"
            return "claude-sonnet-4"
        elif "3.7" in cleaned or "3-7" in cleaned:
            return "claude-3-7-sonnet"
        elif "3.5" in cleaned or "3-5" in cleaned:
            if "haiku" in cleaned:
                return "claude-3-5-haiku"
            return "claude-3-5-sonnet"
        elif "3" in cleaned:
            if "opus" in cleaned:
                return "claude-3-opus"
            elif "haiku" in cleaned:
                return "claude-3-haiku"
            return "claude-3-sonnet"
        elif "2" in cleaned:
            return "claude-2.1"
        return "claude-3-5-sonnet"

    # Google models
    elif "gemini" in cleaned:
        if "2.5" in cleaned:
            if "flash" in cleaned:
                if "lite" in cleaned:
                    return "gemini-2.5-flash-lite"
                return "gemini-2.5-flash"
            return "gemini-2.5-pro"
        elif "2.0" in cleaned or "2-0" in cleaned:
            if "flash" in cleaned:
                return "gemini-2.0-flash"
            return "gemini-2.0-pro"
        elif "1.5" in cleaned:
            if "flash" in cleaned:
                return "gemini-1.5-flash"
            return "gemini-1.5-pro"
        return "gemini-1.5-pro"

    # Meta Llama models
    elif "llama" in cleaned:
        if "3.3" in cleaned:
            return "llama-3.3-70b"
        elif "3.2" in cleaned:
            if "90b" in cleaned:
                return "llama-3.2-90b"
            elif "11b" in cleaned:
                return "llama-3.2-11b"
            elif "3b" in cleaned:
                return "llama-3.2-3b"
            elif "1b" in cleaned:
                return "llama-3.2-1b"
            return "llama-3.2-8b"
        elif "3.1" in cleaned:
            if "405b" in cleaned:
                return "llama-3.1-405b"
            elif "70b" in cleaned:
                return "llama-3.1-70b"
            elif "8b" in cleaned:
                return "llama-3.1-8b"
            return "llama-3.1-8b"
        elif "4" in cleaned and "405" not in cleaned:
            if "scout" in cleaned:
                return "llama-4-scout"
            elif "maverick" in cleaned:
                return "llama-4-maverick"
            return "llama-4"
        return "llama-3-8b"

    # Mistral models
    elif "codestral" in cleaned:
        return "codestral"
    elif "pixtral" in cleaned:
        return "pixtral"
    elif "mistral" in cleaned or "mixtral" in cleaned:
        if "large" in cleaned:
            return "mistral-large"
        elif "medium" in cleaned:
            return "mistral-medium"
        elif "small" in cleaned:
            return "mistral-small"
        elif "8x22b" in cleaned:
            return "mixtral-8x22b"
        elif "8x7b" in cleaned:
            return "mixtral-8x7b"
        elif "nemo" in cleaned:
            return "mistral-nemo"
        return "mistral-small"

    # DeepSeek models
    elif "deepseek" in cleaned:
        if "coder" in cleaned:
            return "deepseek-coder"
        elif "chat" in cleaned:
            return "deepseek-chat"
        elif "r1" in cleaned:
            return "deepseek-r1"
        elif "v3" in cleaned:
            return "deepseek-v3"
        return "deepseek-chat"

    # Return cleaned version if no pattern matched
    return cleaned if cleaned else "unknown"


def infer_component_type(
    component_name: str,
    model_name: str | None = None,
) -> str:
    """Infer component type using pattern matching.

    Args:
        component_name: Name of the component
        model_name: Optional model name (if present, indicates LLM component)

    Returns:
        Component type string
    """
    if model_name:
        return "llm"

    name_lower = component_name.lower()

    for component_type, patterns in COMPONENT_TYPE_PATTERNS.items():
        if any(pattern in name_lower for pattern in patterns):
            return component_type

    return "component"
