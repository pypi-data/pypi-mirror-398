"""
Kaizen Configuration Module

Provides unified configuration for:
- Model providers (OpenAI, Ollama, etc.)
- Framework settings
- Performance optimization
"""

from .providers import (
    ConfigurationError,
    ProviderConfig,
    ProviderType,
    auto_detect_provider,
    check_ollama_available,
    get_default_model_config,
    get_provider_config,
    provider_config_to_dict,
)

__all__ = [
    "ProviderConfig",
    "ProviderType",
    "ConfigurationError",
    "auto_detect_provider",
    "get_provider_config",
    "get_default_model_config",
    "provider_config_to_dict",
    "check_ollama_available",
]
