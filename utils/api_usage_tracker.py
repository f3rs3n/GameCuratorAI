"""
API Usage Tracker module for monitoring API usage across sessions.
This module provides functionality to track, persist, and report API usage.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class APIUsageTracker:
    """
    Tracks and persists API usage across sessions.
    
    Features:
    - Tracks requests by API provider
    - Persists usage counts between application runs
    - Tracks daily and monthly usage
    - Provides usage reports and warnings for quota limits
    """
    
    def __init__(self, storage_dir: str = "usage_data"):
        """
        Initialize the API usage tracker.
        
        Args:
            storage_dir: Directory to store usage data (default: "usage_data")
        """
        self.storage_dir = storage_dir
        self.usage_file = os.path.join(storage_dir, "api_usage.json")
        self.usage_data = {
            "openai": {
                "total_requests": 0,
                "total_tokens": 0,
                "daily_usage": {},
                "monthly_usage": {},
                "last_updated": ""
            },
            "gemini": {
                "total_requests": 0,
                "total_tokens": 0,
                "daily_usage": {},
                "monthly_usage": {},
                "last_updated": ""
            }
        }
        
        # Check for existing usage data directory
        if not os.path.exists(storage_dir):
            try:
                os.makedirs(storage_dir)
                logger.info(f"Created API usage storage directory: {storage_dir}")
            except Exception as e:
                logger.error(f"Failed to create storage directory: {e}")
        
        # Load existing usage data if available
        self._load_usage_data()
    
    def _load_usage_data(self) -> bool:
        """
        Load existing usage data from file.
        
        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.usage_data.update(data)
                logger.debug(f"Loaded API usage data from {self.usage_file}")
                return True
        except Exception as e:
            logger.error(f"Error loading API usage data: {e}")
        return False
    
    def _save_usage_data(self) -> bool:
        """
        Save current usage data to file.
        
        Returns:
            True if data was saved successfully, False otherwise
        """
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, indent=2)
            logger.debug(f"Saved API usage data to {self.usage_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving API usage data: {e}")
        return False
    
    def record_request(self, provider: str, tokens: int = 0, timestamp: Optional[datetime] = None) -> bool:
        """
        Record an API request.
        
        Args:
            provider: API provider name (e.g., "openai", "gemini")
            tokens: Number of tokens used in the request (default: 0)
            timestamp: Optional timestamp (default: current time)
            
        Returns:
            True if the request was recorded successfully, False otherwise
        """
        if provider.lower() not in self.usage_data:
            logger.warning(f"Unknown API provider: {provider}")
            return False
        
        provider = provider.lower()
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime("%Y-%m-%d")
        month_str = timestamp.strftime("%Y-%m")
        
        # Update provider data
        provider_data = self.usage_data[provider]
        provider_data["total_requests"] += 1
        provider_data["total_tokens"] += tokens
        provider_data["last_updated"] = timestamp.isoformat()
        
        # Update daily usage
        if date_str not in provider_data["daily_usage"]:
            provider_data["daily_usage"][date_str] = {"requests": 0, "tokens": 0}
        provider_data["daily_usage"][date_str]["requests"] += 1
        provider_data["daily_usage"][date_str]["tokens"] += tokens
        
        # Update monthly usage
        if month_str not in provider_data["monthly_usage"]:
            provider_data["monthly_usage"][month_str] = {"requests": 0, "tokens": 0}
        provider_data["monthly_usage"][month_str]["requests"] += 1
        provider_data["monthly_usage"][month_str]["tokens"] += tokens
        
        # Save after update
        return self._save_usage_data()
    
    def get_usage_report(self, provider: Optional[str] = None, 
                        days: int = 30) -> Dict[str, Any]:
        """
        Get a usage report for the specified provider.
        
        Args:
            provider: API provider name, or None for all providers
            days: Number of days to include in the report (default: 30)
            
        Returns:
            Dictionary with usage statistics
        """
        result = {}
        
        providers = [provider.lower()] if provider else list(self.usage_data.keys())
        for p in providers:
            if p not in self.usage_data:
                continue
                
            provider_data = self.usage_data[p]
            
            # Calculate recent usage
            today = datetime.now()
            start_date = today - timedelta(days=days)
            
            recent_requests = 0
            recent_tokens = 0
            
            # Sum up requests in the specified period
            for date_str, usage in provider_data["daily_usage"].items():
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if date >= start_date:
                        recent_requests += usage["requests"]
                        recent_tokens += usage["tokens"]
                except ValueError:
                    continue
            
            # Get current month usage
            current_month = today.strftime("%Y-%m")
            monthly_requests = 0
            monthly_tokens = 0
            if current_month in provider_data["monthly_usage"]:
                monthly_requests = provider_data["monthly_usage"][current_month]["requests"]
                monthly_tokens = provider_data["monthly_usage"][current_month]["tokens"]
            
            result[p] = {
                "total_requests": provider_data["total_requests"],
                "total_tokens": provider_data["total_tokens"],
                f"last_{days}_days_requests": recent_requests,
                f"last_{days}_days_tokens": recent_tokens,
                "current_month_requests": monthly_requests,
                "current_month_tokens": monthly_tokens,
                "last_updated": provider_data["last_updated"]
            }
        
        return result
    
    def check_quota_limits(self, provider: str, 
                          daily_limit: Optional[int] = None,
                          monthly_limit: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if usage is approaching or exceeding quota limits.
        
        Args:
            provider: API provider name
            daily_limit: Optional daily token limit
            monthly_limit: Optional monthly token limit
            
        Returns:
            Tuple of (within_limits, status_info)
            within_limits is True if usage is within limits, False otherwise
            status_info contains detailed status information
        """
        if provider.lower() not in self.usage_data:
            return True, {"error": f"Unknown provider: {provider}"}
        
        provider = provider.lower()
        provider_data = self.usage_data[provider]
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        month_str = today.strftime("%Y-%m")
        
        # Get today's usage
        daily_usage = 0
        if date_str in provider_data["daily_usage"]:
            daily_usage = provider_data["daily_usage"][date_str]["tokens"]
        
        # Get this month's usage
        monthly_usage = 0
        if month_str in provider_data["monthly_usage"]:
            monthly_usage = provider_data["monthly_usage"][month_str]["tokens"]
        
        status = {
            "provider": provider,
            "daily_usage": daily_usage,
            "monthly_usage": monthly_usage,
            "daily_limit": daily_limit,
            "monthly_limit": monthly_limit,
            "daily_percent": None,
            "monthly_percent": None,
            "warnings": []
        }
        
        # Check daily limit
        daily_percent = None
        if daily_limit:
            daily_percent = (daily_usage / daily_limit) * 100
            status["daily_percent"] = daily_percent
            
            if daily_percent >= 90:
                status["warnings"].append(f"Daily usage at {daily_percent:.1f}% of limit")
        
        # Check monthly limit
        monthly_percent = None
        if monthly_limit:
            monthly_percent = (monthly_usage / monthly_limit) * 100
            status["monthly_percent"] = monthly_percent
            
            if monthly_percent >= 90:
                status["warnings"].append(f"Monthly usage at {monthly_percent:.1f}% of limit")
        
        # Determine if we're within limits
        within_limits = True
        if (daily_limit and daily_usage >= daily_limit) or (monthly_limit and monthly_usage >= monthly_limit):
            within_limits = False
            status["warnings"].append("Usage limit exceeded")
        
        return within_limits, status
    
    def reset_daily_usage(self, provider: Optional[str] = None) -> bool:
        """
        Reset daily usage statistics for testing or recovery.
        
        Args:
            provider: API provider name, or None for all providers
            
        Returns:
            True if the reset was successful, False otherwise
        """
        providers = [provider.lower()] if provider else list(self.usage_data.keys())
        
        for p in providers:
            if p in self.usage_data:
                self.usage_data[p]["daily_usage"] = {}
        
        return self._save_usage_data()
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Remove usage data older than the specified number of days.
        
        Args:
            days_to_keep: Number of days of data to retain
            
        Returns:
            Number of days of data removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for provider in self.usage_data:
            provider_data = self.usage_data[provider]
            
            # Clean up daily usage
            daily_to_keep = {}
            for date_str, usage in provider_data["daily_usage"].items():
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if date >= cutoff_date:
                        daily_to_keep[date_str] = usage
                    else:
                        removed_count += 1
                except ValueError:
                    # Keep entries with invalid dates to avoid data loss
                    daily_to_keep[date_str] = usage
            
            provider_data["daily_usage"] = daily_to_keep
            
            # Clean up monthly usage (only if more than 3 months old)
            monthly_cutoff = cutoff_date - timedelta(days=60)  # Keep at least ~5 months
            monthly_to_keep = {}
            for month_str, usage in provider_data["monthly_usage"].items():
                try:
                    # Parse as first day of month
                    date = datetime.strptime(month_str + "-01", "%Y-%m-%d")
                    if date >= monthly_cutoff:
                        monthly_to_keep[month_str] = usage
                except ValueError:
                    # Keep entries with invalid dates to avoid data loss
                    monthly_to_keep[month_str] = usage
            
            provider_data["monthly_usage"] = monthly_to_keep
        
        self._save_usage_data()
        return removed_count

# Global instance for easy import and use
_tracker = None

def get_tracker(storage_dir: str = "usage_data") -> APIUsageTracker:
    """
    Get the global APIUsageTracker instance.
    
    Args:
        storage_dir: Directory for usage data storage
        
    Returns:
        APIUsageTracker instance
    """
    global _tracker
    if _tracker is None:
        _tracker = APIUsageTracker(storage_dir)
    return _tracker

def test_example_summary(provider_name: str = "gemini") -> str:
    """
    Generate an example summary of API usage for testing purposes.
    
    Args:
        provider_name: Name of the provider to generate summary for
        
    Returns:
        A formatted string with API usage information
    """
    # Get the tracker
    tracker = get_tracker()
    
    # Add some test data
    tracker.record_request(provider_name, 500)
    
    # Get a usage report
    usage_report = tracker.get_usage_report(provider_name, days=30)
    
    # Format a summary similar to what would appear in export_text_summary
    lines = []
    lines.append("API Usage Information:")
    lines.append("----------------------")
    lines.append(f"Provider: {provider_name.upper()}")
    
    # Calculate today's tokens
    today_tokens = 0
    month_tokens = 0
    
    if usage_report and provider_name in usage_report:
        provider_data = usage_report[provider_name]
        
        # Get today's usage specifically
        today = datetime.now().strftime("%Y-%m-%d")
        provider_obj = tracker.usage_data.get(provider_name.lower(), {})
        daily_usage = provider_obj.get("daily_usage", {})
        today_tokens = daily_usage.get(today, {}).get("tokens", 0)
        
        # Get monthly token count
        month_tokens = provider_data.get(f"last_30_days_tokens", 0)
        
    lines.append(f"Today's usage: {today_tokens:,} tokens")
    lines.append(f"30-day usage: {month_tokens:,} tokens")
    
    return "\n".join(lines)