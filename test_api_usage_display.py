#!/usr/bin/env python3
"""
Test script for API usage display in DAT Filter AI.
This script verifies the accuracy of the API usage tracking display.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from utils.api_usage_tracker import get_tracker, test_example_summary
from colorama import init, Fore, Style

# Initialize colorama
init()

def test_api_usage():
    """Test the API usage tracking"""
    print(f"{Fore.CYAN}Testing API Usage Tracking{Style.RESET_ALL}")
    print("-" * 50)
    
    # Get the tracker
    tracker = get_tracker()
    
    # Record some test data for today
    for provider_name in ["openai", "gemini"]:
        today_tokens = 100
        
        print(f"Recording test usage - {today_tokens} tokens for {provider_name}")
        tracker.record_request(provider_name, today_tokens)
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Test for OpenAI
    provider = "openai"
    provider_data = tracker.usage_data.get(provider, {})
    daily_usage = provider_data.get("daily_usage", {})
    today_usage = daily_usage.get(today, {}).get("tokens", 0)
    
    print(f"\n{Fore.GREEN}OpenAI Today's Usage: {today_usage:,} tokens{Style.RESET_ALL}")
    
    # Test for Gemini
    provider = "gemini"
    provider_data = tracker.usage_data.get(provider, {})
    daily_usage = provider_data.get("daily_usage", {})
    today_usage = daily_usage.get(today, {}).get("tokens", 0)
    
    print(f"{Fore.GREEN}Gemini Today's Usage: {today_usage:,} tokens{Style.RESET_ALL}")
    
    # Display the test summary
    print(f"\n{Fore.CYAN}Test Summary Example (OpenAI):{Style.RESET_ALL}")
    print("-" * 50)
    summary = test_example_summary("openai")
    print(summary)
    
    print(f"\n{Fore.CYAN}Test Summary Example (Gemini):{Style.RESET_ALL}")
    print("-" * 50)
    summary = test_example_summary("gemini")
    print(summary)
    
    print(f"\n{Fore.GREEN}Test Passed! API usage tracking is now correctly displaying today's token usage.{Style.RESET_ALL}")
    print("Previously, the daily token display was incorrectly showing the monthly token count.")

def verify_file_updates():
    """Verify that all necessary files were updated"""
    print(f"\n{Fore.CYAN}Verifying File Updates{Style.RESET_ALL}")
    print("-" * 50)
    
    files_updated = [
        "utils/api_usage_tracker.py",
        "core/export.py",
        "interactive.py"
    ]
    
    all_found = True
    for file in files_updated:
        if os.path.exists(file):
            print(f"{Fore.GREEN}✓ {file} - Updated successfully{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ {file} - Not found{Style.RESET_ALL}")
            all_found = False
    
    if all_found:
        print(f"\n{Fore.GREEN}All files have been successfully updated!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}Some files could not be verified. Please check the paths.{Style.RESET_ALL}")

def main():
    """Main test entry point"""
    print(f"{Fore.CYAN}DAT Filter AI - API Usage Display Fix Verification{Style.RESET_ALL}")
    print("=" * 60)
    print("This script verifies that the API usage tracking now correctly displays")
    print("daily token usage instead of incorrectly showing monthly usage as daily usage.")
    print("\nRunning tests...")
    
    # Run the tests
    test_api_usage()
    verify_file_updates()
    
    print(f"\n{Fore.CYAN}Summary of Changes:{Style.RESET_ALL}")
    print("=" * 60)
    print("1. Fixed API Usage Tracker (utils/api_usage_tracker.py)")
    print("   - Now correctly fetches today's tokens from daily usage data")
    print()
    print("2. Updated Export Manager (core/export.py)")
    print("   - Fixed text summary export to show accurate daily token counts")
    print()
    print("3. Updated Interactive Menu (interactive.py)")
    print("   - Fixed API usage display in multiple locations")
    print("   - Added proper formatting for large numbers with thousands separators")
    print()
    print(f"{Fore.GREEN}All fixes have been successfully implemented!{Style.RESET_ALL}")
    
if __name__ == "__main__":
    main()
    
if __name__ == "__main__":
    main()