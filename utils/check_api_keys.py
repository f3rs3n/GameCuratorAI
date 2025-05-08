#!/usr/bin/env python3
"""
API key validation and request utilities.
This module provides functions to verify and request API keys for various providers.
"""

import os
import sys
import logging
from typing import Tuple, Dict, Any

# Setup basic logging
logger = logging.getLogger('datfilterai')

def check_api_key(provider: str) -> Tuple[bool, str]:
    """
    Check if an API key for the given provider exists in the environment.
    
    Args:
        provider: The AI provider name (openai, gemini)
        
    Returns:
        Tuple of (key_exists, key_name)
    """
    provider = provider.lower()
    
    if provider == "openai":
        key_name = "OPENAI_API_KEY"
    elif provider == "gemini":
        key_name = "GEMINI_API_KEY"
    else:
        # Random provider doesn't need an API key
        if provider == "random":
            return (True, "No API key required")
        else:
            return (False, f"Unknown provider: {provider}")
    
    # Check if the environment variable exists and is not empty
    api_key = os.environ.get(key_name, "")
    key_exists = bool(api_key)
    
    return (key_exists, key_name)

def request_api_key(provider: str) -> str:
    """
    Request an API key for the given provider from the user.
    
    Args:
        provider: The AI provider name (openai, gemini)
        
    Returns:
        The entered API key, or empty string if cancelled
    """
    provider = provider.lower()
    
    if provider == "openai":
        print("\nYou need an OpenAI API key to use the OpenAI provider.")
        print("This requires a paid account with access to the OpenAI API.")
        print("You can get one at: https://platform.openai.com/")
    elif provider == "gemini":
        print("\nYou need a Google Gemini API key to use the Gemini provider.")
        print("You can get one at: https://ai.google.dev/")
        print("Gemini offers a free tier with reasonable usage limits.")
    else:
        if provider == "random":
            print("\nRandom provider doesn't require an API key.")
            return ""
        else:
            print(f"\nUnknown provider: {provider}")
            return ""
    
    try:
        print("\nEnter your API key below (or just press Enter to cancel):")
        api_key = input("> ").strip()
        
        if not api_key:
            print("API key entry cancelled.")
            return ""
            
        return api_key
        
    except (KeyboardInterrupt, EOFError):
        print("\nAPI key entry cancelled.")
        return ""

def set_api_key(provider: str, api_key: str) -> bool:
    """
    Set the API key for the given provider in the environment.
    
    Args:
        provider: The AI provider name (openai, gemini)
        api_key: The API key to set
        
    Returns:
        True if the API key was set, False otherwise
    """
    provider = provider.lower()
    
    if not api_key:
        return False
    
    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
        return True
    elif provider == "gemini":
        os.environ["GEMINI_API_KEY"] = api_key
        return True
    else:
        if provider == "random":
            # Random provider doesn't need an API key
            return True
        else:
            logger.error(f"Unknown provider: {provider}")
            return False

def check_and_request_api_key(provider: str, allow_random_fallback: bool = False) -> Tuple[bool, str]:
    """
    Check if an API key exists for the provider, and request one if it doesn't.
    
    Args:
        provider: The AI provider name (openai, gemini)
        allow_random_fallback: Whether to allow fallback to the random provider
        
    Returns:
        Tuple of (success, provider) where success indicates if the key was set
        and provider is the provider to use (may be changed to 'random' if fallback is allowed)
    """
    provider = provider.lower()
    
    # Random provider always succeeds
    if provider == "random":
        return (True, provider)
    
    # Check if API key exists
    key_exists, key_name = check_api_key(provider)
    
    if key_exists:
        # Key exists, need to test if it's valid
        # This will be handled by the individual provider's initialize() method
        return (True, provider)
    
    # No API key found, request one from the user
    print(f"\nNo API key found for {provider.upper()}. This provider requires a valid API key.")
    
    if allow_random_fallback:
        print(f"\nOptions:")
        print(f"1. Enter a {provider.upper()} API key")
        print(f"2. Fall back to the RANDOM provider (for testing only)")
        print(f"3. Cancel")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                api_key = request_api_key(provider)
                
                if api_key:
                    if set_api_key(provider, api_key):
                        return (True, provider)
                    else:
                        print(f"Failed to set {provider.upper()} API key.")
                        return (False, provider)
                else:
                    print("API key entry cancelled.")
                    return (False, provider)
                    
            elif choice == "2":
                print(f"Falling back to RANDOM provider.")
                print(f"Note: The RANDOM provider uses random values and is for testing only.")
                return (True, "random")
                
            else:
                print("Operation cancelled.")
                return (False, provider)
                
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return (False, provider)
    else:
        # No random fallback allowed, must get a valid API key
        api_key = request_api_key(provider)
        
        if api_key:
            if set_api_key(provider, api_key):
                return (True, provider)
            else:
                print(f"Failed to set {provider.upper()} API key.")
                return (False, provider)
        else:
            print("API key entry cancelled.")
            return (False, provider)