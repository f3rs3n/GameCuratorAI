"""
Test script to demonstrate the API key status indicators
"""

import os
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def main():
    """Main entry point for the test script"""
    print("\n=== API Key Status Indicator Test ===\n")
    
    # Check if API keys are set in environment variables
    # For testing purposes, let's simulate one API key being missing
    openai_key_set = bool(os.environ.get("OPENAI_API_KEY", ""))
    gemini_key_set = False  # Simulate Gemini key not being set
    
    # Define colors
    colors = {
        'success': Fore.GREEN,
        'error': Fore.RED,
        'info': Fore.CYAN,
        'warning': Fore.YELLOW,
        'highlight': Fore.MAGENTA
    }
    
    # Display provider options with API key status
    print("Available AI Providers:")
    print("-" * 50)
    
    # Random provider (no API key needed)
    print(f"  [1] Random (Test mode, no API key needed) ✓")
    
    # OpenAI provider
    openai_status = f"{colors['success']}[API Key Set]{Style.RESET_ALL}" if openai_key_set else f"{colors['error']}[API Key Required]{Style.RESET_ALL}"
    print(f"  [2] OpenAI (Most accurate) {openai_status}")
    
    # Gemini provider
    gemini_status = f"{colors['success']}[API Key Set]{Style.RESET_ALL}" if gemini_key_set else f"{colors['error']}[API Key Required]{Style.RESET_ALL}"
    print(f"  [3] Google Gemini (Fast, efficient) {gemini_status}")
    
    print("\nAPI Key Configuration:")
    print("-" * 50)
    print(f"  OpenAI API Key: {colors['success']}[Set]{Style.RESET_ALL}" if openai_key_set else f"  OpenAI API Key: {colors['error']}[Not Set]{Style.RESET_ALL}")
    print(f"  Gemini API Key: {colors['success']}[Set]{Style.RESET_ALL}" if gemini_key_set else f"  Gemini API Key: {colors['error']}[Not Set]{Style.RESET_ALL}")
    
    print("\nThis is how the API key status indicators appear in the menu.")
    print("The same indicators are used in both the provider selection and API key configuration menus.")

if __name__ == "__main__":
    main()