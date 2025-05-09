#!/usr/bin/env python3
"""
API key validation and request utilities.
This module provides functions to verify and request API keys for various providers.
"""

import os
import sys
import json
import logging
import requests
from typing import Tuple, Dict, Any, Optional, Union

# Setup basic logging
logger = logging.getLogger('datfilterai')

# OpenAI provider has been removed as per user request

def test_gemini_key(api_key: str) -> bool:
    """
    Test if a Gemini API key is valid by making a simple API call.
    
    Args:
        api_key: The Gemini API key to test
        
    Returns:
        True if the key is valid, False otherwise
    """
    try:
        # We'll use a simple models list request which is a lightweight call
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        
        response = requests.get(
            url,
            timeout=10  # Set a reasonable timeout
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            return True
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            logger.warning(f"Gemini API key validation failed: {error_message}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Gemini API key: {str(e)}")
        return False

def check_api_key(provider: str) -> Tuple[bool, str]:
    """
    Check if an API key for the given provider exists and is valid.
    
    Args:
        provider: The AI provider name (gemini)
        
    Returns:
        Tuple of (key_valid, message)
        - key_valid: True if the key exists and is valid
        - message: Descriptive message about the key status
    """
    provider = provider.lower()
    
    # Define API key environment variable names
    if provider == "gemini":
        key_name = "GEMINI_API_KEY"
    else:
        # Random provider doesn't need an API key
        if provider == "random":
            return (True, "No API key required for Random provider")
        else:
            return (False, f"Unknown provider: {provider}")
    
    # Check if the environment variable exists and is not empty
    api_key = os.environ.get(key_name, "")
    key_exists = bool(api_key)
    
    if not key_exists:
        return (False, f"No {key_name} found in environment variables")
    
    # Perform a simple validation check on the key format
    # Gemini keys are typically 39 characters
    if provider == "gemini":
        if len(api_key) < 30:
            return (False, f"Invalid Gemini API key format. Keys are typically 39 characters long.")
    
    # Do a basic test API call to validate the key works
    try:
        if provider == "gemini":
            valid = test_gemini_key(api_key)
            if valid:
                return (True, "Gemini API key is valid")
            else:
                return (False, "Gemini API key validation failed. The key may be invalid, expired, or have incorrect permissions.")
    except Exception as e:
        logger.error(f"Error validating {provider} API key: {str(e)}")
        return (False, f"Error validating {provider.upper()} API key: {str(e)}")
    
    return (key_exists, "API key found but validation not implemented")

def request_api_key(provider: str) -> str:
    """
    Request an API key for the given provider from the user.
    
    Args:
        provider: The AI provider name (gemini)
        
    Returns:
        The entered API key, or empty string if cancelled
    """
    provider = provider.lower()
    
    if provider == "gemini":
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
        provider: The AI provider name (gemini)
        api_key: The API key to set
        
    Returns:
        True if the API key was set, False otherwise
    """
    provider = provider.lower()
    
    if not api_key:
        return False
    
    if provider == "gemini":
        os.environ["GEMINI_API_KEY"] = api_key
        return True
    else:
        if provider == "random":
            # Random provider doesn't need an API key
            return True
        else:
            logger.error(f"Unknown provider: {provider}")
            return False

def get_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all available providers.
    
    Returns:
        Dictionary mapping provider names to information about their availability
    """
    providers = {
        "gemini": {
            "name": "Google Gemini",
            "description": "Uses Google's Gemini models for good evaluation with free tier",
            "url": "https://ai.google.dev/",
            "requires_key": True
        },
        "random": {
            "name": "Random (Testing)",
            "description": "Uses random values for testing purposes only",
            "url": None,
            "requires_key": False
        }
    }
    
    # Check each provider's availability
    for provider_id, info in providers.items():
        available, reason, has_key = check_provider_availability(provider_id)
        info["available"] = available
        info["reason"] = reason
        info["has_valid_key"] = has_key
    
    return providers

def check_provider_availability(provider: str) -> Tuple[bool, str, bool]:
    """
    Check if a provider is available (required packages installed) and has valid API keys.
    
    Args:
        provider: The AI provider name (gemini, random)
        
    Returns:
        Tuple of (available, reason, has_valid_key)
        - available: True if the provider can be used 
        - reason: Message explaining availability status
        - has_valid_key: True if the provider has a valid API key (always True for Random)
    """
    provider = provider.lower()
    
    # Random provider is always available
    if provider == "random":
        return (True, "Random provider is available (for testing only)", True)
    
    # Check if the required packages are installed
    if provider == "gemini":
        try:
            import google.generativeai
            package_available = True
        except ImportError:
            return (False, "Google Generative AI package is not installed. Please install it with 'pip install google-generativeai'", False)
    else:
        return (False, f"Unknown provider: {provider}", False)
    
    # Check if the API key is valid
    key_valid, message = check_api_key(provider)
    
    if key_valid:
        return (True, f"{provider.upper()} provider is available with valid API key", True)
    else:
        return (False, message, False)

def check_and_request_api_key(provider: str, allow_random_fallback: bool = False) -> Tuple[bool, str]:
    """
    Check if an API key exists for the provider, and request one if it doesn't.
    
    Args:
        provider: The AI provider name (gemini)
        allow_random_fallback: Whether to allow fallback to the random provider
        
    Returns:
        Tuple of (success, provider) where success indicates if the key was set
        and provider is the provider to use (may be changed to 'random' if fallback is allowed)
    """
    provider = provider.lower()
    
    # Random provider always succeeds
    if provider == "random":
        return (True, provider)
    
    # Check if API key exists and is valid
    key_valid, message = check_api_key(provider)
    
    if key_valid:
        # Key exists and is valid
        logger.info(f"API key validation for {provider}: {message}")
        return (True, provider)
    
    # No API key found or invalid key, display the error message
    print(f"\nAPI key validation failed for {provider.upper()}: {message}")
    
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