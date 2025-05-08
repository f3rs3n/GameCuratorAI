#!/usr/bin/env python3
"""
Test script for verifying API usage summary formatting.
"""

import sys
from utils.api_usage_tracker import test_example_summary, get_tracker

def main():
    """Main entry point"""
    print("\n=== Testing API Usage Summary Formatting ===\n")
    
    # Get current usage data
    tracker = get_tracker()
    openai_usage = tracker.get_usage_report("openai")
    gemini_usage = tracker.get_usage_report("gemini")
    
    print("Current OpenAI Usage:")
    if "openai" in openai_usage:
        data = openai_usage["openai"]
        print(f"  Total requests: {data.get('total_requests', 0)}")
        print(f"  Total tokens: {data.get('total_tokens', 0)}")
    else:
        print("  No data available")
    
    print("\nCurrent Gemini Usage:")
    if "gemini" in gemini_usage:
        data = gemini_usage["gemini"]
        print(f"  Total requests: {data.get('total_requests', 0)}")
        print(f"  Total tokens: {data.get('total_tokens', 0)}")
    else:
        print("  No data available")
    
    # Test summary formatting for both providers
    print("\n=== Example Summaries ===\n")
    
    # OpenAI summary
    print("OpenAI Summary:")
    print("--------------")
    print(test_example_summary("openai"))
    
    print("\nGemini Summary:")
    print("--------------")
    print(test_example_summary("gemini"))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())