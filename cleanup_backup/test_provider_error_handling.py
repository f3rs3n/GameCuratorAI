"""
Test script to verify the provider error handling
"""

import os
import sys
import time
import logging
import json
from typing import Dict, Any, List, Optional, Tuple

# Add current directory to path
sys.path.append('.')

# Import internal modules
from ai_providers.base import BaseAIProvider
from ai_providers.random_provider import RandomProvider
from ai_providers.gemini_provider import GeminiProvider
from ai_providers.openai_provider import OpenAIProvider

from core.filter_engine import FilterEngine
from core.dat_parser import DatParser
from core.rule_engine import RuleEngine

from colorama import Fore, Style, init
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("provider_error_test")

def progress_callback(current, total):
    """Simple progress callback"""
    percentage = round(current / total * 100) if total > 0 else 0
    progress_chars = round(percentage / 2)
    bar = '[' + '█' * progress_chars + '░' * (50 - progress_chars) + ']'
    print(f"\r{bar} {percentage}% ({current}/{total})", end='')

def test_provider_error_handling():
    """Test the provider error handling"""
    print("\n=== Provider Error Handling Test ===\n")
    
    # First, let's test with a missing API key
    print(f"{Fore.CYAN}Testing Gemini provider with missing API key...{Style.RESET_ALL}")
    
    # Temporarily clear API key if it exists
    original_key = os.environ.get('GEMINI_API_KEY', '')
    if 'GEMINI_API_KEY' in os.environ:
        del os.environ['GEMINI_API_KEY']
    
    # Create provider
    gemini_provider = GeminiProvider()
    
    # Check if available (should be false)
    is_available = gemini_provider.is_available()
    print(f"Provider available: {is_available}")
    
    # Create filter engine
    filter_engine = FilterEngine(gemini_provider)
    
    # Load a small test collection
    test_collection = [
        {"name": "Test Game 1", "id": "test1"},
        {"name": "Test Game 2", "id": "test2"},
        {"name": "Test Game 3", "id": "test3"},
        {"name": "Test Game 4", "id": "test4"},
        {"name": "Test Game 5", "id": "test5"},
    ]
    
    # Attempt to filter with invalid provider
    print("Attempting to filter collection with invalid provider...")
    filtered_games, evaluations, provider_error = filter_engine.filter_collection(
        test_collection,
        ["metacritic", "historical"],
        batch_size=2,
        progress_callback=progress_callback
    )
    
    # Check error
    print("\nChecking error response...")
    if provider_error:
        print(f"{Fore.GREEN}✓ Success: Provider error detected:{Style.RESET_ALL}")
        print(f"  {provider_error}")
    else:
        print(f"{Fore.RED}✗ Failure: Provider error not detected{Style.RESET_ALL}")
    
    # Test with a valid provider (random)
    print(f"\n{Fore.CYAN}Testing with Random provider (should always work)...{Style.RESET_ALL}")
    
    # Create random provider and filter engine
    random_provider = RandomProvider()
    filter_engine = FilterEngine(random_provider)
    
    # Filter with random provider
    filtered_games, evaluations, provider_error = filter_engine.filter_collection(
        test_collection,
        ["metacritic", "historical"],
        batch_size=2,
        progress_callback=progress_callback
    )
    
    # Check results
    print("\nChecking results...")
    if provider_error:
        print(f"{Fore.RED}✗ Failure: Random provider reported an error:{Style.RESET_ALL}")
        print(f"  {provider_error}")
    else:
        print(f"{Fore.GREEN}✓ Success: Random provider worked without errors{Style.RESET_ALL}")
        print(f"  Filtered games: {len(filtered_games)} of {len(test_collection)}")
        print(f"  Evaluations: {len(evaluations)}")
    
    # Restore original key if it existed
    if original_key:
        os.environ['GEMINI_API_KEY'] = original_key
    
    print("\nTest completed.")

if __name__ == "__main__":
    test_provider_error_handling()