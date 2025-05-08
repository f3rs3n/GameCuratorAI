#!/usr/bin/env python3
"""
API key testing tool for DAT Filter AI.
This script checks API keys and verifies they work with the respective providers.
Can be used as a standalone tool or imported by other scripts.
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, Any, Tuple, List, Optional

from utils.check_api_keys import check_api_key, request_api_key, set_api_key
from ai_providers import get_provider, AVAILABLE_PROVIDERS

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_key(provider_name: str) -> Tuple[bool, str]:
    """
    Test if the API key for the given provider works.
    
    Args:
        provider_name: Name of the provider to test (openai, gemini)
        
    Returns:
        Tuple of (success, message)
    """
    if provider_name.lower() == "random":
        return (True, "Random provider doesn't require an API key")
    
    # First check if API key exists
    key_exists, key_name = check_api_key(provider_name)
    
    if not key_exists:
        return (False, f"No API key found for {provider_name.upper()}")
    
    # Initialize provider
    try:
        provider = get_provider(provider_name)
        initialized = provider.initialize()
        
        if initialized:
            # Test a simple API request
            test_request_success = False
            
            try:
                # Simple game info for testing
                test_game_info = {
                    "name": "Test Game",
                    "description": "A test game for API validation"
                }
                
                # Test criteria (keep minimal for validation)
                test_criteria = ["metacritic"]
                
                # Execute a minimal evaluation to verify API access
                start_time = time.time()
                result = provider.evaluate_game(test_game_info, test_criteria)
                elapsed = time.time() - start_time
                
                # Check if result has the expected structure
                test_request_success = isinstance(result, dict) and "scores" in result
                
                if test_request_success:
                    return (True, f"API key validated successfully (response time: {elapsed:.2f}s)")
                else:
                    return (False, f"API response format unexpected: {result}")
                    
            except Exception as e:
                return (False, f"API request failed: {str(e)}")
        else:
            return (False, "Provider initialization failed")
            
    except Exception as e:
        return (False, f"Error testing API key: {str(e)}")

def test_and_request_api_key(provider_name: str, max_attempts: int = 3) -> Tuple[bool, str]:
    """
    Test API key and request a new one if it doesn't work.
    
    Args:
        provider_name: Name of the provider to test (openai, gemini)
        max_attempts: Maximum number of attempts to get a working API key
        
    Returns:
        Tuple of (success, message)
    """
    if provider_name.lower() == "random":
        return (True, "Random provider doesn't require an API key")
    
    for attempt in range(max_attempts):
        # Check if key exists
        key_exists, key_name = check_api_key(provider_name)
        
        if not key_exists:
            print(f"\nNo API key found for {provider_name.upper()}")
            api_key = request_api_key(provider_name)
            
            if not api_key:
                return (False, "API key entry cancelled by user")
            
            set_api_key(provider_name, api_key)
        
        # Test the key
        print(f"\nTesting {provider_name.upper()} API key...")
        success, message = test_api_key(provider_name)
        
        if success:
            print(f"✓ SUCCESS: {message}")
            return (True, message)
        else:
            print(f"✗ ERROR: {message}")
            
            if attempt < max_attempts - 1:
                print(f"Attempt {attempt+1} of {max_attempts} failed. Let's try again.")
                retry = input("Enter a new API key? (Y/n): ").strip().lower()
                
                if retry != "n":
                    api_key = request_api_key(provider_name)
                    
                    if not api_key:
                        return (False, "API key entry cancelled by user")
                    
                    set_api_key(provider_name, api_key)
                else:
                    return (False, "User cancelled retry")
            else:
                return (False, f"Failed after {max_attempts} attempts")
    
    return (False, "Maximum attempts reached")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="API Key Testing Tool for DAT Filter AI")
    parser.add_argument("--provider", "-p", 
                       choices=list(AVAILABLE_PROVIDERS.keys()),
                       default="all",
                       help="Provider to test (default: all)")
    parser.add_argument("--request", "-r", action="store_true",
                       help="Request API key if missing or invalid")
    args = parser.parse_args()
    
    providers_to_test = []
    if args.provider == "all":
        providers_to_test = ["openai", "gemini"]
    else:
        providers_to_test = [args.provider]
    
    # Test each provider
    all_success = True
    for provider in providers_to_test:
        print(f"\n{'='*50}")
        print(f"Testing {provider.upper()} API key")
        print(f"{'='*50}")
        
        if args.request:
            success, message = test_and_request_api_key(provider)
        else:
            success, message = test_api_key(provider)
            print(f"{'✓' if success else '✗'} {message}")
        
        all_success = all_success and success
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())