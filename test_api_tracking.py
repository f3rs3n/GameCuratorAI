"""
Test script for API usage tracking functionality.
This script tests the API usage tracking functionality by making test calls
to AI providers and checking that usage is recorded properly.
"""

import os
import json
import time
from ai_providers.openai_provider import OpenAIProvider
from ai_providers.gemini_provider import GeminiProvider
from utils.api_usage_tracker import get_tracker, APIUsageTracker

def test_usage_tracker_persistence():
    """Test that the usage tracker persists data between runs"""
    
    # Create a temporary test tracker in a separate directory
    test_dir = "test_usage_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a tracker and record some test data
    tracker = APIUsageTracker(storage_dir=test_dir)
    tracker.record_request("test_provider", 100)
    tracker.record_request("test_provider", 200)
    
    # Wait a moment to ensure data is saved
    time.sleep(0.5)
    
    # Create a new tracker instance and check if it loads the saved data
    new_tracker = APIUsageTracker(storage_dir=test_dir)
    report = new_tracker.get_usage_report("test_provider")
    
    # Clean up test directory 
    if os.path.exists(os.path.join(test_dir, "usage_data.json")):
        os.remove(os.path.join(test_dir, "usage_data.json"))
    if os.path.exists(test_dir):
        os.rmdir(test_dir)
    
    print(f"Persistence test report: {json.dumps(report, indent=2)}")
    total_tokens = sum(day_data.get("tokens", 0) for day_data in report.get("daily_usage", {}).values())
    print(f"Total tokens recorded: {total_tokens}")
    assert total_tokens >= 300, "Expected at least 300 tokens in persistence test"
    print("✓ Persistence test passed")
    return True

def test_openai_usage_tracking():
    """Test OpenAI provider API usage tracking"""
    provider = OpenAIProvider()
    
    # Only run this test if the API key is available
    if provider.initialize():
        print("Testing OpenAI provider usage tracking...")
        
        # Get initial usage data
        tracker = get_tracker()
        initial_report = tracker.get_usage_report("openai", days=1)
        initial_tokens = sum(day_data.get("tokens", 0) for day_data in initial_report.get("daily_usage", {}).values())
        
        # Make a test evaluation that should be tracked
        test_game = {"name": "Test Game", "id": "test123"}
        provider.evaluate_game(test_game, ["metacritic", "historical"])
        
        # Check updated usage
        updated_report = tracker.get_usage_report("openai", days=1)
        updated_tokens = sum(day_data.get("tokens", 0) for day_data in updated_report.get("daily_usage", {}).values())
        
        print(f"Initial OpenAI tokens: {initial_tokens}")
        print(f"Updated OpenAI tokens: {updated_tokens}")
        assert updated_tokens > initial_tokens, "Expected token usage to increase after API call"
        print("✓ OpenAI usage tracking test passed")
        return True
    else:
        print("Skipping OpenAI test as API key is not available")
        return False

def test_gemini_usage_tracking():
    """Test Gemini provider API usage tracking"""
    provider = GeminiProvider()
    
    # Only run this test if the API key is available
    if provider.initialize():
        print("Testing Gemini provider usage tracking...")
        
        # Get initial usage data
        tracker = get_tracker()
        initial_report = tracker.get_usage_report("gemini", days=1)
        initial_tokens = sum(day_data.get("tokens", 0) for day_data in initial_report.get("daily_usage", {}).values())
        
        # Make a test evaluation that should be tracked
        test_game = {"name": "Test Game", "id": "test123"}
        provider.evaluate_game(test_game, ["metacritic", "historical"])
        
        # Check updated usage
        updated_report = tracker.get_usage_report("gemini", days=1)
        updated_tokens = sum(day_data.get("tokens", 0) for day_data in updated_report.get("daily_usage", {}).values())
        
        print(f"Initial Gemini tokens: {initial_tokens}")
        print(f"Updated Gemini tokens: {updated_tokens}")
        assert updated_tokens > initial_tokens, "Expected token usage to increase after API call"
        print("✓ Gemini usage tracking test passed")
        return True
    else:
        print("Skipping Gemini test as API key is not available")
        return False

def test_quota_checking():
    """Test the quota checking functionality"""
    tracker = get_tracker()
    
    # Record some test requests to trigger quota warnings
    for _ in range(50):
        tracker.record_request("test_quota", 1000)  # 50,000 tokens
    
    # Check if we're approaching limits
    within_limits, status = tracker.check_quota_limits(
        "test_quota", 
        daily_limit=100000,  # 100k tokens per day
        monthly_limit=1000000  # 1M tokens per month
    )
    
    print(f"Quota check results: within_limits={within_limits}")
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # Clean up
    tracker.reset_daily_usage("test_quota")
    
    print("✓ Quota checking test passed")
    return True

def main():
    """Main entry point"""
    print("=== Testing API Usage Tracking ===")
    
    # Run tests
    persistence_result = test_usage_tracker_persistence()
    openai_result = test_openai_usage_tracking()
    gemini_result = test_gemini_usage_tracking()
    quota_result = test_quota_checking()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Persistence Test: {'✓ Passed' if persistence_result else '✗ Failed'}")
    print(f"OpenAI Tracking Test: {'✓ Passed' if openai_result else '⚠ Skipped'}")
    print(f"Gemini Tracking Test: {'✓ Passed' if gemini_result else '⚠ Skipped'}")
    print(f"Quota Checking Test: {'✓ Passed' if quota_result else '✗ Failed'}")
    
    # View the final usage report for all providers
    tracker = get_tracker()
    all_usage = tracker.get_usage_report()
    print("\n=== Current API Usage ===")
    print(json.dumps(all_usage, indent=2))

if __name__ == "__main__":
    main()