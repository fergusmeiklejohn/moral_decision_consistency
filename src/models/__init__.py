"""
Model providers for LLM abstraction.

This module provides a unified interface for working with different LLM providers,
allowing seamless swapping of models in experiments.
"""

from typing import Optional, Dict, Any
from .base import BaseLLMProvider, MockLLMProvider
from .openai_model import OpenAIProvider
from .anthropic_model import AnthropicProvider
from .google_model import GoogleProvider
from .local_model import LocalVLLMProvider, OllamaProvider


# Model registry
MODEL_PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "vllm": LocalVLLMProvider,
    "ollama": OllamaProvider,
    "mock": MockLLMProvider,
}


def create_provider(
    provider_name: str,
    model_name: str,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """
    Factory function to create an LLM provider.

    Args:
        provider_name: Name of the provider ("openai", "anthropic", "google", etc.)
        model_name: Name of the specific model to use
        api_key: API key for authentication (if required)
        **kwargs: Additional provider-specific configuration

    Returns:
        Initialized LLM provider

    Raises:
        ValueError: If provider_name is not recognized

    Examples:
        >>> # Create OpenAI provider
        >>> provider = create_provider("openai", "gpt-4o", api_key="sk-...")
        >>>
        >>> # Create local vLLM provider
        >>> provider = create_provider(
        ...     "vllm",
        ...     "meta-llama/Llama-3-8b",
        ...     endpoint="http://localhost:8000/v1/completions"
        ... )
    """
    if provider_name not in MODEL_PROVIDERS:
        available = ", ".join(MODEL_PROVIDERS.keys())
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available providers: {available}"
        )

    provider_class = MODEL_PROVIDERS[provider_name]
    return provider_class(model_name=model_name, api_key=api_key, **kwargs)


def get_provider_from_model_name(model_name: str) -> str:
    """
    Infer provider from model name.

    Args:
        model_name: The model name

    Returns:
        Provider name (e.g., "openai", "anthropic")

    Examples:
        >>> get_provider_from_model_name("gpt-4o")
        'openai'
        >>> get_provider_from_model_name("claude-3.5-sonnet")
        'anthropic'
    """
    model_lower = model_name.lower()

    if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
        return "openai"
    elif "claude" in model_lower:
        return "anthropic"
    elif "gemini" in model_lower:
        return "google"
    elif "llama" in model_lower or "qwen" in model_lower or "mistral" in model_lower:
        return "vllm"  # Default local models to vLLM
    else:
        raise ValueError(
            f"Cannot infer provider from model name '{model_name}'. "
            "Please specify provider explicitly."
        )


__all__ = [
    "BaseLLMProvider",
    "MockLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "LocalVLLMProvider",
    "OllamaProvider",
    "create_provider",
    "get_provider_from_model_name",
    "MODEL_PROVIDERS",
]
