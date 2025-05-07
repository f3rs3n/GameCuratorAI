#!/usr/bin/env python3
"""
Test script for AI providers in DAT Filter AI.
This script tests both the Random provider and the OpenAI provider.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import providers
from ai_providers import get_provider

def test_random_provider():
    """Test the RandomProvider"""
    logger.info("Testing RandomProvider...")
    
    provider = get_provider("random")
    if not provider.initialize():
        logger.error("Failed to initialize random provider")
        return False
    
    # Check if provider is available
    if not provider.is_available():
        logger.error("Random provider is not available")
        return False
    
    logger.info("Random provider initialized and available")
    
    # Test game evaluation
    game_info = {
        "name": "Test Game",
        "description": "A test game for the random provider",
        "year": 2025,
        "platform": "Test Platform"
    }
    
    criteria = ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"]
    
    logger.info("Evaluating test game with random provider...")
    result = provider.evaluate_game(game_info, criteria)
    
    # Output the result
    logger.info("Random provider evaluation result:")
    logger.info(json.dumps(result, indent=2))
    
    logger.info("Random provider test completed successfully")
    return True

def test_openai_provider():
    """Test the OpenAIProvider"""
    logger.info("Testing OpenAIProvider...")
    
    # Check if OpenAI API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OpenAI API key not found in environment variables")
        logger.info("Please set the OPENAI_API_KEY environment variable and try again")
        return False
    
    provider = get_provider("openai")
    if not provider.initialize():
        logger.error("Failed to initialize OpenAI provider")
        return False
    
    # Check if provider is available
    if not provider.is_available():
        logger.error("OpenAI provider is not available")
        return False
    
    logger.info("OpenAI provider initialized and available")
    
    # Test game evaluation
    game_info = {
        "name": "Super Mario World",
        "description": "A classic platformer for the Super Nintendo",
        "year": 1990,
        "platform": "Super Nintendo Entertainment System",
        "developer": "Nintendo",
        "publisher": "Nintendo"
    }
    
    criteria = ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"]
    
    logger.info("Evaluating test game with OpenAI provider...")
    result = provider.evaluate_game(game_info, criteria)
    
    # Output the result
    logger.info("OpenAI provider evaluation result:")
    logger.info(json.dumps(result, indent=2))
    
    logger.info("OpenAI provider test completed successfully")
    return True

def test_gemini_provider():
    """Test the GeminiProvider"""
    logger.info("Testing GeminiProvider...")
    
    # Check if Gemini API key is available
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error("Gemini API key not found in environment variables")
        logger.info("Please set the GEMINI_API_KEY environment variable and try again")
        return False
    
    provider = get_provider("gemini")
    if not provider.initialize():
        logger.error("Failed to initialize Gemini provider")
        return False
    
    # Check if provider is available
    if not provider.is_available():
        logger.error("Gemini provider is not available")
        return False
    
    logger.info("Gemini provider initialized and available")
    
    # Test game evaluation
    game_info = {
        "name": "Super Mario World",
        "description": "A classic platformer for the Super Nintendo",
        "year": 1990,
        "platform": "Super Nintendo Entertainment System",
        "developer": "Nintendo",
        "publisher": "Nintendo"
    }
    
    criteria = ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"]
    
    logger.info("Evaluating test game with Gemini provider...")
    result = provider.evaluate_game(game_info, criteria)
    
    # Output the result
    logger.info("Gemini provider evaluation result:")
    logger.info(json.dumps(result, indent=2))
    
    logger.info("Gemini provider test completed successfully")
    return True

def main():
    """Main entry point"""
    logger.info("Starting AI provider tests")
    
    # Test random provider first (should always work)
    random_success = test_random_provider()
    logger.info(f"Random provider test {'successful' if random_success else 'failed'}")
    
    # Setup flag variables for other providers
    openai_success = None
    gemini_success = None
    
    # Check command line arguments
    for arg in sys.argv[1:]:
        if arg == "--openai":
            openai_success = test_openai_provider()
            logger.info(f"OpenAI provider test {'successful' if openai_success else 'failed'}")
        elif arg == "--gemini":
            gemini_success = test_gemini_provider()
            logger.info(f"Gemini provider test {'successful' if gemini_success else 'failed'}")
    
    # Log skipped providers
    if openai_success is None:
        logger.info("Skipping OpenAI provider test (use --openai flag to test)")
    if gemini_success is None:
        logger.info("Skipping Gemini provider test (use --gemini flag to test)")
    
    logger.info("AI provider tests completed")
    
    # Return exit code based on test results
    if not random_success:
        return 1
    if openai_success is False:  # Only fail if the test was run and failed
        return 2
    if gemini_success is False:  # Only fail if the test was run and failed
        return 3
    return 0

if __name__ == "__main__":
    sys.exit(main())