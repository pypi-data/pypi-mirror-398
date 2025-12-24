"""
Provider routing and configuration.

This module handles provider registration, lazy loading, and configuration
using a table-driven approach for maintainability and testability.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Provider


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for a provider."""

    module_name: str  # Module to import (e.g., "anthropic", "openai")
    package_name: str  # PyPI package name for error messages
    install_extra: str  # Extra to install (e.g., "anthropic", "ollama")
    error_keywords: tuple[str, ...]  # Keywords to detect missing package
    env_var: str | None = None  # Environment variable for API key
    base_url: str | None = None  # Default base URL (for OpenAI-compatible)


# Provider configuration table
# Each provider maps to its configuration for loading and setup
PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    "anthropic": ProviderConfig(
        module_name="anthropic",
        package_name="anthropic",
        install_extra="anthropic",
        error_keywords=("anthropic",),
        env_var="ANTHROPIC_API_KEY",
    ),
    "openai": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="OPENAI_API_KEY",
    ),
    "google": ProviderConfig(
        module_name="google",
        package_name="google-generativeai",
        install_extra="google",
        error_keywords=("google",),
        env_var="GOOGLE_API_KEY",
    ),
    "vertex": ProviderConfig(
        module_name="vertex",
        package_name="google-cloud-aiplatform",
        install_extra="vertex",
        error_keywords=("vertexai", "google.cloud"),
        env_var="GOOGLE_CLOUD_PROJECT",  # Uses ADC, project as marker
    ),
    # OpenAI-compatible providers
    "openrouter": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
    ),
    "ollama": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="ollama",
        error_keywords=("openai",),
        env_var=None,  # Local, no API key needed
        base_url="http://localhost:11434/v1",
    ),
    "lmstudio": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="lmstudio",
        error_keywords=("openai",),
        env_var=None,  # Local, no API key needed
        base_url="http://localhost:1234/v1",
    ),
    "cerebras": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="CEREBRAS_API_KEY",
        base_url="https://api.cerebras.ai/v1",
    ),
    "groq": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
    ),
    "zai-org": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="ZAI_API_KEY",
        base_url="https://api.z.ai/api/paas/v4",
    ),
    "zai-coding": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="ZAI_API_KEY",
        base_url="https://api.z.ai/api/coding/paas/v4",
    ),
    "mlx": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var=None,  # Local, no API key needed
        base_url="http://localhost:8080/v1",
    ),
    "azure": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="AZURE_OPENAI_API_KEY",
        base_url=None,  # User must provide endpoint
    ),
    "together": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1",
    ),
    "fireworks": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="FIREWORKS_API_KEY",
        base_url="https://api.fireworks.ai/inference/v1",
    ),
    "perplexity": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="PERPLEXITY_API_KEY",
        base_url="https://api.perplexity.ai",
    ),
    "deepseek": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
    ),
    "nvidia": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="NVIDIA_API_KEY",
        base_url="https://integrate.api.nvidia.com/v1",
    ),
    "xai": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="XAI_API_KEY",
        base_url="https://api.x.ai/v1",
    ),
    "mistral": ProviderConfig(
        module_name="openai",
        package_name="openai",
        install_extra="openai",
        error_keywords=("openai",),
        env_var="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
    ),
}

# Provider registry - populated as providers are imported
_PROVIDERS: dict[str, type[Provider]] = {}


def register_provider(name: str, provider_class: type[Provider]) -> None:
    """Register a provider class."""
    _PROVIDERS[name] = provider_class


def _resolve_api_key(provider_name: str, explicit_key: str | None) -> str | None:
    """
    Resolve API key for a provider.

    Priority: explicit key > provider-specific env var

    Args:
        provider_name: The provider name (e.g., "openrouter", "groq")
        explicit_key: Explicitly provided API key, if any

    Returns:
        The resolved API key, or None if not found (some providers don't need one)
    """
    if explicit_key is not None:
        return explicit_key

    config = PROVIDER_CONFIGS.get(provider_name)
    if config and config.env_var:
        return os.environ.get(config.env_var)

    return None


def _parse_model_string(model: str) -> tuple[str, str]:
    """
    Parse model string into provider and model_id.

    Examples:
        "anthropic/claude-sonnet-4" -> ("anthropic", "claude-sonnet-4")
        "openrouter/meta-llama/llama-3" -> ("openrouter", "meta-llama/llama-3")
        "ollama/llama3" -> ("ollama", "llama3")
    """
    if "/" not in model:
        raise ValueError(
            f"Invalid model string: {model!r}. "
            f"Expected format: 'provider/model-id' (e.g., 'anthropic/claude-sonnet-4')"
        )

    parts = model.split("/", 1)
    provider_name = parts[0].lower()
    model_id = parts[1]

    return provider_name, model_id


def _load_provider(name: str) -> None:
    """
    Lazy-load a provider module.

    Uses the PROVIDER_CONFIGS table to determine which module to import
    and provides helpful error messages when packages are missing.
    """
    config = PROVIDER_CONFIGS.get(name)
    if config is None:
        return  # Unknown provider, will be caught later

    try:
        importlib.import_module(f".{config.module_name}", "innerloop.providers")
    except ImportError as e:
        if any(kw in str(e) for kw in config.error_keywords):
            raise ImportError(
                f"Provider '{name}' requires the '{config.package_name}' package. "
                f"Install with: pip install innerloop[{config.install_extra}]"
            ) from e
        raise


def get_provider(
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> Provider:
    """
    Get a provider instance for a model string.

    Args:
        model: Full model string (e.g., "anthropic/claude-sonnet-4")
        api_key: Optional explicit API key (uses env var if not provided)
        base_url: Optional base URL override (for local models)

    Returns:
        Provider instance configured for the model
    """
    provider_name, model_id = _parse_model_string(model)

    # Lazy import providers to avoid loading all SDKs
    if provider_name not in _PROVIDERS:
        _load_provider(provider_name)

    if provider_name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name!r}")

    provider_class = _PROVIDERS[provider_name]

    # Resolve API key: explicit > provider-specific env var
    resolved_key = _resolve_api_key(provider_name, api_key)

    # Resolve base URL: explicit > config default
    if base_url is None:
        config = PROVIDER_CONFIGS.get(provider_name)
        if config:
            base_url = config.base_url

    return provider_class(model_id=model_id, api_key=resolved_key, base_url=base_url)


__all__ = [
    "PROVIDER_CONFIGS",
    "ProviderConfig",
    "get_provider",
    "register_provider",
]
