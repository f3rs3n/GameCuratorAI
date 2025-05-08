#!/usr/bin/env python3
"""
Test script for API usage tracking functionality.
This script verifies that API usage data is being correctly tracked and persisted.
"""

import os
import sys
import json
from utils.api_usage_tracker import get_tracker, APIUsageTracker

def show_banner(text):
    """Display a banner with the given text"""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80))
    print("=" * 80)

def main():
    """Main entry point for the test script"""
    show_banner("API USAGE TRACKER TEST")
    
    # Get the API usage tracker
    tracker = get_tracker()
    
    # Display current usage data
    show_banner("CURRENT USAGE DATA")
    try:
        with open(os.path.join("usage_data", "api_usage.json"), "r") as f:
            data = json.load(f)
            print(json.dumps(data, indent=2))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading usage data: {e}")
    
    # Test adding usage for each provider
    show_banner("ADDING TEST USAGE DATA")
    
    # Add test data for OpenAI
    print("\nAdding usage for OpenAI provider:")
    tracker.record_request("openai", 100)
    openai_usage = tracker.get_usage_report("openai")
    print(f"  Total requests: {openai_usage.get('openai', {}).get('total_requests', 0)}")
    print(f"  Total tokens: {openai_usage.get('openai', {}).get('total_tokens', 0)}")
    
    # Add test data for Gemini
    print("\nAdding usage for Gemini provider:")
    tracker.record_request("gemini", 200)
    gemini_usage = tracker.get_usage_report("gemini")
    print(f"  Total requests: {gemini_usage.get('gemini', {}).get('total_requests', 0)}")
    print(f"  Total tokens: {gemini_usage.get('gemini', {}).get('total_tokens', 0)}")
    
    # Test persistence by creating a new tracker instance
    show_banner("TESTING PERSISTENCE")
    new_tracker = APIUsageTracker()
    
    # Verify the data is still there
    openai_usage = new_tracker.get_usage_report("openai")
    gemini_usage = new_tracker.get_usage_report("gemini")
    
    print("\nVerifying OpenAI usage persisted:")
    print(f"  Total requests: {openai_usage.get('openai', {}).get('total_requests', 0)}")
    print(f"  Total tokens: {openai_usage.get('openai', {}).get('total_tokens', 0)}")
    
    print("\nVerifying Gemini usage persisted:")
    print(f"  Total requests: {gemini_usage.get('gemini', {}).get('total_requests', 0)}")
    print(f"  Total tokens: {gemini_usage.get('gemini', {}).get('total_tokens', 0)}")
    
    # Show the updated usage data file
    show_banner("UPDATED USAGE DATA")
    try:
        with open(os.path.join("usage_data", "api_usage.json"), "r") as f:
            data = json.load(f)
            print(json.dumps(data, indent=2))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading usage data: {e}")
    
    show_banner("TEST COMPLETED")
    return 0

if __name__ == "__main__":
    sys.exit(main())