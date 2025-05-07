"""
AI provider module initialization.
This module provides a factory to get the appropriate AI provider.
"""

from typing import Dict, Any, Optional
from ai_providers.base import BaseAIProvider
from ai_providers.openai_provider import OpenAIProvider
from ai_providers.random_provider import RandomProvider
from ai_providers.gemini_provider import GeminiProvider

# Dictionary of available providers
AVAILABLE_PROVIDERS = {
    'openai': OpenAIProvider,
    'random': RandomProvider,
    'gemini': GeminiProvider,
}

def get_provider(provider_name: str, config: Optional[Dict[str, Any]] = None) -> BaseAIProvider:
    """
    Get an instance of the specified AI provider
    
    Args:
        provider_name: Name of the provider to use
        config: Optional configuration for the provider
        
    Returns:
        Instance of the requested AI provider
        
    Raises:
        ValueError: If the requested provider is not available
    """
    provider_class = AVAILABLE_PROVIDERS.get(provider_name.lower())
    
    if provider_class is None:
        raise ValueError(f"AI provider '{provider_name}' not found. Available providers: {list(AVAILABLE_PROVIDERS.keys())}")
    
    provider = provider_class(**(config or {}))
    return provider
