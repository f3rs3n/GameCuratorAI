#!/usr/bin/env python3
"""
Test script specifically for Gemini provider.
This handles just a single game evaluation for quick testing.
"""

import json
import logging
import os
import sys

from ai_providers import get_provider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def test_gemini_single_game():
    """Test the Gemini provider with a single game"""
    logger.info("Testing Gemini provider with a single game evaluation...")
    
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
    
    # Test game evaluation with a simple test game
    game_info = {
        "name": "Super Mario Bros.",
        "description": "The classic platformer that defined the genre",
        "year": 1985,
        "platform": "Nintendo Entertainment System",
        "developer": "Nintendo",
        "publisher": "Nintendo"
    }
    
    criteria = ["metacritic", "historical", "v_list"]
    
    logger.info("Evaluating test game with Gemini provider...")
    result = provider.evaluate_game(game_info, criteria)
    
    # Output the result
    logger.info("Gemini provider evaluation result:")
    logger.info(json.dumps(result, indent=2))
    
    logger.info("Gemini provider test completed successfully")
    return True

def main():
    """Main entry point"""
    logger.info("Starting Gemini provider single game test")
    
    success = test_gemini_single_game()
    logger.info(f"Gemini provider test {'successful' if success else 'failed'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())