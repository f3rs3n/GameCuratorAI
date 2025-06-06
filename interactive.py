#!/usr/bin/env python3
"""
DAT Filter AI - Interactive CLI Interface
A text-based menu interface for the DAT Filter AI tool.
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Callable
from colorama import init, Fore, Style, Back

# Import core modules
from core.dat_parser import DatParser
from core.filter_engine import FilterEngine
from core.rule_engine import RuleEngine
from core.export import ExportManager
from ai_providers import get_provider
from utils.logging_config import setup_logging
from utils.check_api_keys import check_api_key, request_api_key, set_api_key, check_and_request_api_key, check_provider_availability, get_available_providers

# Initialize colorama for cross-platform color support
init()

# Set up logging
logger = logging.getLogger('datfilterai')

class InteractiveMenu:
    """Text-based menu for DAT Filter AI"""
    
    def __init__(self):
        """Initialize the interactive menu"""
        # Setup logging
        setup_logging()
        
        # Initialize components
        self.dat_parser = DatParser()
        self.rule_engine = RuleEngine()
        self.export_manager = ExportManager()
        self.filter_engine = None  # Will be initialized based on selected provider
        
        # State variables
        self.running = True
        self.current_dat_file = None
        self.parsed_data = None
        self.filtered_games = []
        self.evaluations = []
        self.special_cases = {}
        
        # Check if Gemini provider is available
        gemini_available, _, has_gemini_key = check_provider_availability('gemini')
        
        # Default to Gemini if it's available, otherwise use random
        default_provider = 'gemini' if gemini_available else 'random'
        
        # Default settings
        self.settings = {
            'provider': default_provider,  # Use Gemini if available, otherwise random
            'criteria': ['metacritic', 'historical', 'v_list', 'console_significance', 'mods_hacks'],
            'batch_size': 20,  # increased from 10 to 20 for optimized binary decision format
            # global_threshold removed - now using "any criteria match" approach
            'input_dir': 'ToFilter',
            'output_dir': 'Filtered',
            'show_progress': True,
            'color': True
        }
        
        # Color scheme
        self.colors = {
            'header': Fore.CYAN + Style.BRIGHT,
            'info': Fore.WHITE,
            'success': Fore.GREEN,
            'error': Fore.RED,
            'warning': Fore.YELLOW,
            'option': Fore.CYAN,
            'data': Fore.WHITE + Style.BRIGHT,
            'highlight': Fore.MAGENTA + Style.BRIGHT
        }
        
        # Initialize AI provider
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the AI provider based on current settings"""
        try:
            provider_name = self.settings['provider'].lower()
            
            # Check if the provider is available with a valid API key
            available, reason, has_valid_key = check_provider_availability(provider_name)
            
            if not available:
                # Provider is not available, show detailed error
                self._print_error(f"{provider_name.upper()} provider is not available")
                self._print_info(f"Reason: {reason}")
                
                # If it's an API key issue for Gemini, provide more specific guidance
                if provider_name == 'gemini' and not has_valid_key:
                    provider_info = {
                        'name': 'Google Gemini',
                        'key_name': 'GEMINI_API_KEY',
                        'url': 'https://ai.google.dev/',
                        'note': 'Gemini offers a free tier with generous usage limits.'
                    }
                    
                    self._print_info(f"\nTo use the {provider_info['name']} provider, you need a valid API key.")
                    self._print_info(f"Go to Settings → Configure API Keys to set your API key")
                    self._print_info(f"You can get a {provider_info['name']} API key at {provider_info['url']}")
                    self._print_info(f"{provider_info['note']}")
                return False
            
            # Get the provider
            provider = get_provider(provider_name)
            
            if not provider:
                self._print_error(f"Failed to create {provider_name.upper()} provider")
                return False
            
            # Initialize the provider
            self._print_info(f"Initializing {provider_name.upper()} provider...")
            initialization_success = provider.initialize()
            
            if not initialization_success:
                # This shouldn't happen if the check_provider_availability test passed,
                # but it might occur if the key was revoked or a network issue happened
                # in the time between the availability check and initialization
                self._print_error(f"Failed to initialize {provider_name.upper()} provider")
                self._print_warning("This may be due to a temporary issue with the API service")
                self._print_info("Please try again later or check your network connection")
                return False
            
            # Successfully initialized
            if provider_name == 'gemini':
                self._print_success(f"{provider_name.upper()} API key verified successfully")
            
            # Set up the filter engine
            self.filter_engine = FilterEngine(provider)
            # No global threshold anymore - using individual criteria matches
            return True
                
        except Exception as e:
            logger.error(f"Failed to initialize provider: {e}")
            self._print_error(f"Failed to initialize provider: {str(e)}")
            return False
    
    def _clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _print_header(self, text: str):
        """Print a simple header"""
        print("\n" + "=" * 50)
        print(self.colors['header'] + text.center(50) + Style.RESET_ALL)
        print("=" * 50 + "\n")
    
    def _print_subheader(self, text: str):
        """Print a simple subheader"""
        print("\n" + self.colors['highlight'] + text + Style.RESET_ALL)
        print("-" * 50)
    
    def _print_option(self, key: str, description: str, highlighted: bool = False):
        """Print a menu option"""
        if highlighted:
            print(f"  [{key}] " + self.colors['highlight'] + description + Style.RESET_ALL)
        else:
            print(f"  [{key}] {description}")
    
    def _print_info(self, text: str):
        """Print info text"""
        print(self.colors['info'] + text + Style.RESET_ALL)
    
    def _print_error(self, text: str):
        """Print error text"""
        print(self.colors['error'] + f"ERROR: {text}" + Style.RESET_ALL)
    
    def _print_success(self, text: str):
        """Print success text"""
        print(self.colors['success'] + text + Style.RESET_ALL)
    
    def _print_warning(self, text: str):
        """Print warning text"""
        print(self.colors['warning'] + f"WARNING: {text}" + Style.RESET_ALL)
    
    def _print_data(self, label: str, value: str):
        """Print a data item"""
        print(f"{label}: {self.colors['data']}{value}{Style.RESET_ALL}")
    
    def _print_progress_bar(self, current: int, total: int, width: int = 50, suffix: str = ""):
        """Print a game-themed progress bar"""
        filled_length = int(width * current // total)
        percent = f"{100 * current / total:.1f}"
        
        # Game-themed progress characters
        game_icons = ['🎮', '🕹️', '👾', '🎯', '🏆']
        
        # Use different colors based on progress
        if current / total < 0.3:  # First third
            color = Fore.BLUE
        elif current / total < 0.7:  # Middle third
            color = Fore.YELLOW
        else:  # Last third
            color = Fore.GREEN
        
        if filled_length < width:
            # Add game icon at current progress position
            icon = random.choice(game_icons) if current > 0 else '▶️'
            bar = '█' * filled_length
            
            if self.settings.get('color', True):
                colored_icon = color + icon + Style.RESET_ALL
            else:
                colored_icon = icon
                
            bar += colored_icon + '░' * (width - filled_length - 1)
        else:
            bar = '█' * width
            
        print(f"\r[{self.colors['success']}{bar}{Style.RESET_ALL}] {percent}% {suffix}", end='\r')
        if current == total:
            print()
    
    def _get_user_input(self, prompt: str, default: str = "") -> str:
        """Get input from the user with a prompt"""
        try:
            return input(self.colors['highlight'] + prompt + (f" [{default}]" if default else "") + ": " + Style.RESET_ALL) or default
        except EOFError:
            # Handle case when running in an environment that can't accept input
            print("\nInput not available. Using default value.")
            return default
    
    def _wait_for_key(self):
        """Wait for a key press"""
        try:
            print("\nPress any key to continue...")
            if os.name == 'nt':  # Windows
                import msvcrt
                msvcrt.getch()
            else:  # Unix/Linux/Mac
                import termios
                import tty
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            # If can't get interactive input, just continue
            pass
    
    def main_menu(self):
        """Display a simplified main menu"""
        self._clear_screen()
        
        # Simple header
        self._print_header("DAT FILTER AI - GAME COLLECTION CURATOR")
        
        # Show DAT info with safer data access
        if self.current_dat_file:
            basename = os.path.basename(self.current_dat_file)
            if len(basename) > 40:
                basename = basename[:37] + "..."
            
            self._print_data("Current DAT", basename)
            
            # Safe access to game_count with fallback
            game_count = "Unknown"
            if self.parsed_data and 'game_count' in self.parsed_data:
                game_count = str(self.parsed_data['game_count'])
            
            self._print_data("Game Count", game_count)
            
            if self.filtered_games:
                self._print_data("Filtered", f"{len(self.filtered_games)} games kept")
            else:
                self._print_info("Status: No filtering applied yet")
        else:
            self._print_info("No DAT file loaded")
        
        # Show engine info
        print()
        self._print_data("Engine", self.settings['provider'].upper())
        
        # Get Metacritic threshold from settings or default to 7.5
        metacritic_threshold = 7.5
        if 'criteria_thresholds' in self.settings and 'metacritic' in self.settings['criteria_thresholds']:
            metacritic_threshold = self.settings['criteria_thresholds']['metacritic']
        
        # Display filter mode and metacritic threshold (no global threshold anymore)
        self._print_data("Filter Mode", "Keep if ANY criteria matches")
        self._print_data("Metacritic Threshold", f"{metacritic_threshold:.2f}")
        
        # Menu options
        self._print_subheader("SYSTEM COMMANDS")
        
        menu_options = [
            ("1", "Load DAT File", False),
            ("2", "Apply Filters", not self.current_dat_file),
            ("3", "Export Results", not self.filtered_games),
            ("4", "Settings", False),
            ("5", "Batch Processing", False),
            ("6", f"Change AI Provider ({self.settings['provider'].upper()})", False),
            ("0", "Exit", False)
        ]
        
        for key, desc, disabled in menu_options:
            if disabled:
                status = self.colors['error'] + "[Need DAT File]" if desc == "Apply Filters" else self.colors['error'] + "[Need Filtered Games]"
                print(f"  [{key}] {desc} {status}" + Style.RESET_ALL)
            else:
                print(f"  [{key}] {desc}")
        
        print("-" * 50)
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self.load_dat_menu()
        elif choice == "2":
            if self.current_dat_file:
                self.apply_filters_menu()
            else:
                self._print_error("Please load a DAT file first")
                self._wait_for_key()
        elif choice == "3":
            if self.filtered_games:
                self.export_menu()
            else:
                self._print_error("Please apply filters first")
                self._wait_for_key()
        elif choice == "4":
            self.settings_menu()
        elif choice == "5":
            self.batch_processing_menu()
        elif choice == "6":
            self._change_provider()
        elif choice == "0":
            self.running = False
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
    
    def load_dat_menu(self):
        """Display the DAT file loading menu"""
        self._clear_screen()
        self._print_header("Load DAT File")
        
        # List available DAT files
        input_dir = self.settings['input_dir']
        dat_files = []
        
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                if file.endswith(".dat"):
                    dat_files.append(file)
        
        if not dat_files:
            self._print_error(f"No DAT files found in {input_dir}")
            self._wait_for_key()
            return
        
        self._print_subheader("Available DAT Files")
        
        # Display DAT files with size information
        for idx, file in enumerate(dat_files, 1):
            file_path = os.path.join(input_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            print(f"  [{idx}] {file} ({file_size:.1f} KB)")
        
        print(f"  [0] Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice (number)")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(dat_files):
                file_path = os.path.join(input_dir, dat_files[idx])
                self._load_dat_file(file_path)
            else:
                self._print_error("Invalid choice")
                self._wait_for_key()
        except ValueError:
            self._print_error("Please enter a number")
            self._wait_for_key()
    
    def _load_dat_file(self, file_path: str):
        """Load and parse a DAT file"""
        self._print_info(f"Loading DAT file: {file_path}...")
        
        try:
            # Parse the DAT file
            self.parsed_data = self.dat_parser.parse_file(file_path)
            self.current_dat_file = file_path
            
            # Reset filtered games
            self.filtered_games = []
            self.evaluations = []
            
            # Process the collection to identify special cases
            if 'games' in self.parsed_data:
                result = self.rule_engine.process_collection(self.parsed_data['games'])
                self.special_cases = result.get('special_cases', {}) if result else {}
            else:
                self._print_warning("No games found in DAT file")
                self.special_cases = {}
            
            # Safe access to game count
            game_count = self.parsed_data.get('game_count', 0)
            self._print_success(f"Successfully loaded DAT file with {game_count} games")
            self._wait_for_key()
            
        except Exception as e:
            logger.error(f"Error loading DAT file: {e}")
            self._print_error(f"Failed to load DAT file: {str(e)}")
            self._wait_for_key()
    
    def apply_filters_menu(self):
        """Display the filter application menu"""
        self._clear_screen()
        self._print_header("Apply Filters")
        
        # Show current criteria
        self._print_subheader("Current Filter Criteria")
        for idx, criterion in enumerate(self.settings['criteria'], 1):
            print(f"  {idx}. {criterion}")
        
        print()
        self._print_info(f"Current AI Provider: {self.settings['provider']}")
        self._print_info(f"Batch Size: {self.settings['batch_size']} games per API call")
        
        # Display filtering mode explanation
        self._print_info("Filter Mode: Keep if ANY criteria matches")
        self._print_info("Games are kept if they match at least one of the selected criteria.")
        
        # Display Metacritic threshold
        metacritic_threshold = 7.5
        if 'criteria_thresholds' in self.settings and 'metacritic' in self.settings['criteria_thresholds']:
            metacritic_threshold = self.settings['criteria_thresholds']['metacritic']
        
        self._print_info(f"Metacritic Threshold: {metacritic_threshold:.2f} (games with scores above this are kept)")
        
        print()
        self._print_option("A", "Apply filters with current settings")
        self._print_option("C", "Change filter criteria")
        self._print_option("P", "Change provider")
        self._print_option("B", "Change batch size")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice").upper()
        
        if choice == "A":
            self._apply_filters()
        elif choice == "C":
            self._change_criteria()
        elif choice == "P":
            self._change_provider()
        elif choice == "B":
            try:
                batch_size = int(self._get_user_input("Enter batch size (1-50)", str(self.settings['batch_size'])))
                if 1 <= batch_size <= 50:
                    self.settings['batch_size'] = batch_size
                    self._print_success(f"Batch size set to {batch_size}")
                else:
                    self._print_error("Batch size must be between 1 and 50")
                self._wait_for_key()
                self.apply_filters_menu()
            except ValueError:
                self._print_error("Please enter a valid number")
                self._wait_for_key()
                self.apply_filters_menu()
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.apply_filters_menu()
    
    def _change_criteria(self):
        """Change the filter criteria"""
        self._clear_screen()
        self._print_subheader("Change Filter Criteria")
        
        all_criteria = [
            ("metacritic", "Metacritic Scores & Critical Acclaim"),
            ("historical", "Historical Significance & Impact"),
            ("v_list", "Presence in V's Recommended Games List"),
            ("console_significance", "Console-specific Significance"),
            ("mods_hacks", "Notable Mods or Hacks")
        ]
        
        # Show current selected criteria
        for idx, (criterion_id, criterion_name) in enumerate(all_criteria, 1):
            selected = criterion_id in self.settings['criteria']
            print(f"  [{idx}] {criterion_name} {'✓' if selected else '✗'}")
        
        print()
        print("  [S] Save and return")
        print("  [0] Cancel")
        
        choice = self._get_user_input("Enter a number to toggle, or S to save").upper()
        
        if choice == "S":
            return
        elif choice == "0":
            self.apply_filters_menu()
            return
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(all_criteria):
                    criterion_id = all_criteria[idx][0]
                    if criterion_id in self.settings['criteria']:
                        self.settings['criteria'].remove(criterion_id)
                    else:
                        self.settings['criteria'].append(criterion_id)
                    self._change_criteria()
                else:
                    self._print_error("Invalid choice")
                    self._wait_for_key()
                    self._change_criteria()
            except ValueError:
                self._print_error("Please enter a valid number")
                self._wait_for_key()
                self._change_criteria()
    
    def _change_provider(self):
        """Change the AI provider"""
        self._clear_screen()
        self._print_subheader("Change AI Provider")
        
        # Get information about all available providers
        all_providers = get_available_providers()
        
        # Build the provider list with availability information
        providers_list = []
        
        # Random provider always comes first
        random_info = all_providers.get("random", {})
        status_text = self.colors['success'] + "[Available]" + Style.RESET_ALL
        providers_list.append(("random", f"Random (Testing mode only) {status_text}"))
        
        # Add Gemini with status
        gemini_info = all_providers.get("gemini", {})
        if gemini_info.get("available", False):
            status_text = self.colors['success'] + "[API Key Valid]" + Style.RESET_ALL
        elif gemini_info.get("has_valid_key", False):
            status_text = self.colors['warning'] + "[Package Missing]" + Style.RESET_ALL
        else:
            status_text = self.colors['error'] + "[API Key Required]" + Style.RESET_ALL
        providers_list.append(("gemini", f"Google Gemini (Fast, efficient) {status_text}"))
        
        # Display provider options
        for idx, (provider_id, provider_desc) in enumerate(providers_list, 1):
            selected = provider_id == self.settings['provider']
            print(f"  [{idx}] {provider_desc} {self.colors['success'] + '✓' + Style.RESET_ALL if selected else ''}")
        
        print()
        self._print_option("C", "Configure API Keys")
        print("  [0] Cancel")
        
        choice = self._get_user_input("Enter your choice").upper()
        
        if choice == "0":
            # Return to previous menu
            return
        elif choice == "C":
            # Configure API keys
            self._configure_api_keys()
            # Return to provider menu
            self._change_provider()
            return
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(providers_list):
                    # Store current provider for possible reversion
                    original_provider = self.settings['provider']
                    # Set the new provider
                    self.settings['provider'] = providers_list[idx][0]
                    
                    # Check if the provider is available with valid API key
                    available, reason, has_valid_key = check_provider_availability(self.settings['provider'])
                    
                    # Random provider always works
                    if self.settings['provider'] == 'random':
                        success = self._initialize_provider()
                        if success:
                            self._print_success(f"Provider changed to {self.settings['provider'].upper()}")
                        else:
                            self._print_error("Failed to initialize Random provider")
                        self._wait_for_key()
                        return
                        
                    # For Gemini, check availability and API key validity
                    if self.settings['provider'] == 'gemini':
                        if not available:
                            # Provider not available - show reason and options
                            self._print_error(f"{self.settings['provider'].upper()} provider is not available")
                            self._print_info(f"Reason: {reason}")
                            
                            # No API key found - need to request one
                            if not has_valid_key:
                                self._print_info(f"This provider requires a valid API key to function.")
                            
                            # Provide info on where to get the key
                            # Only Gemini is supported now
                            self._print_info("You can get a Gemini API key at https://ai.google.dev/")
                            self._print_info("Note: Gemini offers a free tier with generous quota limits.")
                            
                            # Ask for options
                            print("\nOptions:")
                            self._print_option("1", f"Enter a {self.settings['provider'].upper()} API key")
                            self._print_option("2", "Use Random provider for TESTING ONLY")
                            self._print_option("3", f"Cancel (keep {original_provider.upper()} provider)")
                            
                            next_step = self._get_user_input("Select an option")
                            
                            if next_step == "1":
                                # Get API key from user
                                api_key = request_api_key(self.settings['provider'])
                                
                                if api_key and set_api_key(self.settings['provider'], api_key):
                                    self._print_success(f"{self.settings['provider'].upper()} API key set")
                                    self._print_info(f"Testing {self.settings['provider'].upper()} API key (this may take a moment)...")
                                    
                                    # Test the key using our key checking utility
                                    success, message = check_api_key(self.settings['provider'])
                                    
                                    if success:
                                        self._print_success(f"API key validation successful: {message}")
                                        self._initialize_provider()
                                        self._print_success(f"Provider changed to {self.settings['provider'].upper()}")
                                    else:
                                        self._print_error(f"API key validation failed: {message}")
                                        self._print_warning("Please check your API key and try again.")
                                        
                                        # Offer to try again or revert
                                        print("\nOptions:")
                                        self._print_option("1", "Try a different API key")
                                        self._print_option("2", "Use Random provider for TESTING ONLY")
                                        self._print_option("3", f"Revert to {original_provider.upper()} provider")
                                        
                                        retry_choice = self._get_user_input("Select an option")
                                        
                                        if retry_choice == "1":
                                            # Try again with the same provider
                                            success, _ = check_and_request_api_key(self.settings['provider'])
                                            if success:
                                                self._initialize_provider()
                                                self._print_success(f"Provider changed to {self.settings['provider'].upper()}")
                                            else:
                                                self._print_error("API key setup failed")
                                                self.settings['provider'] = original_provider
                                                self._initialize_provider()
                                        elif retry_choice == "2":
                                            self._print_warning("Using Random provider for TESTING PURPOSES ONLY")
                                            self._print_warning("WARNING: Random provider is not suitable for actual curation")
                                            self.settings['provider'] = 'random'
                                            self._initialize_provider()
                                        else:
                                            self._print_info(f"Reverting to {original_provider.upper()} provider")
                                            self.settings['provider'] = original_provider
                                            self._initialize_provider()
                                else:
                                    # API key entry canceled
                                    self._print_info("API key entry cancelled")
                                    self._print_info(f"Reverting to {original_provider.upper()} provider")
                                    self.settings['provider'] = original_provider
                                    self._initialize_provider()
                            elif next_step == "2":
                                self._print_warning("Using Random provider for TESTING PURPOSES ONLY")
                                self._print_warning("WARNING: Random provider is not suitable for actual curation")
                                self.settings['provider'] = 'random'
                                self._initialize_provider()
                            else:
                                self._print_info(f"Keeping {original_provider.upper()} provider")
                                self.settings['provider'] = original_provider
                                self._initialize_provider()
                        else:
                            # Key exists, try to initialize
                            success = self._initialize_provider()
                            
                            if success:
                                self._print_success(f"Provider changed to {self.settings['provider'].upper()}")
                            else:
                                # Key exists but initialization failed - likely invalid
                                self._print_error(f"The {self.settings['provider'].upper()} API key appears to be invalid")
                                self._print_warning("The key may be invalid, expired, or have incorrect permissions")
                                
                                # Test the key again with explicit feedback
                                self._print_info(f"Testing {self.settings['provider'].upper()} API key...")
                                success, message = check_api_key(self.settings['provider'])
                                
                                if success:
                                    self._print_success(f"API key validation successful: {message}")
                                    self._print_error("However, provider initialization still failed")
                                    self._print_warning("This may be due to a temporary API issue")
                                else:
                                    self._print_error(f"API key validation failed: {message}")
                                
                                # Give options
                                print("\nOptions:")
                                self._print_option("1", "Configure a new API key")
                                self._print_option("2", "Use Random provider for TESTING ONLY")
                                self._print_option("3", f"Revert to {original_provider.upper()} provider")
                                
                                fix_choice = self._get_user_input("Select an option")
                                
                                if fix_choice == "1":
                                    # Use our advanced API key testing and request
                                    success, _ = check_and_request_api_key(self.settings['provider'])
                                    if success:
                                        self._initialize_provider()
                                        self._print_success(f"Provider changed to {self.settings['provider'].upper()}")
                                    else:
                                        self._print_error("API key setup failed")
                                        self.settings['provider'] = original_provider
                                        self._initialize_provider()
                                elif fix_choice == "2":
                                    self._print_warning("Using Random provider for TESTING PURPOSES ONLY")
                                    self._print_warning("WARNING: Random provider is not suitable for actual curation")
                                    self.settings['provider'] = 'random'
                                    self._initialize_provider()
                                else:
                                    self._print_info(f"Reverting to {original_provider.upper()} provider")
                                    self.settings['provider'] = original_provider
                                    self._initialize_provider()
                    
                    self._wait_for_key()
                    return
                else:
                    self._print_error("Invalid choice")
                    self._wait_for_key()
            except ValueError:
                self._print_error("Please enter a valid number")
                self._wait_for_key()
    
    def _apply_filters(self):
        """Apply filters to the loaded DAT file"""
        if not self.current_dat_file:
            self._print_error("No DAT file loaded")
            self._wait_for_key()
            return
        
        if not self.filter_engine:
            self._print_error("Filter engine not initialized")
            self._wait_for_key()
            return
        
        # Ensure the filter engine has the current threshold
        self._update_filter_engine_threshold()
        
        self._clear_screen()
        self._print_header("Applying Filters")
        
        # Show filtering details with safe access to data
        self._print_info(f"DAT File: {os.path.basename(self.current_dat_file)}")
        
        # Safe access to game count
        game_count = "Unknown"
        if self.parsed_data and 'game_count' in self.parsed_data:
            game_count = str(self.parsed_data['game_count'])
            
        self._print_info(f"Game Count: {game_count}")
        self._print_info(f"Provider: {self.settings['provider'].upper()}")
        self._print_info(f"Batch Size: {self.settings['batch_size']}")
        criteria_str = ", ".join(self.settings['criteria'])
        self._print_info(f"Criteria: {criteria_str}")
        print()
        
        # Start the filtering process
        try:
            start_time = time.time()
            
            # Define progress callback
            def progress_callback(current, total, batch_results=None):
                if self.settings['show_progress']:
                    # Calculate speed and ETA
                    elapsed = time.time() - start_time
                    games_per_sec = current / elapsed if elapsed > 0 else 0
                    remaining = (total - current) / games_per_sec if games_per_sec > 0 else 0
                    
                    # Format ETA
                    if remaining > 60:
                        eta = f"ETA: {int(remaining // 60)}m {int(remaining % 60)}s"
                    else:
                        eta = f"ETA: {int(remaining)}s"
                    
                    # Clear previous line and show progress
                    print("\r" + " " * 80, end="\r")  # Clear line
                    self._print_progress_bar(current, total, 40, f"{current}/{total} games - {games_per_sec:.1f} games/sec - {eta}")
                
                # Display detailed batch results if available
                if batch_results:
                    # Count stats
                    kept = len([g for g in batch_results if g.get('keep', False)])
                    removed = len(batch_results) - kept
                    
                    # The criteria mapping for display
                    criteria_display_names = {
                        "metacritic": "Metacritic Rating",
                        "historical": "Historical Significance",
                        "v_list": "V Recommendation",
                        "console_significance": "Console Significance",
                        "mods_hacks": "Mod Significance",
                        "hidden_gems": "Hidden Gem",
                        "criterion1": "Metacritic Rating",
                        "criterion2": "Historical Significance",
                        "criterion3": "V Recommendation",
                        "criterion4": "Console Significance",
                        "criterion5": "Mod Significance",
                        "criterion6": "Hidden Gem"
                    }
                    
                    # Show summary and game details with color coding
                    print("\n\nRecent games processed:")
                    print(f"  Last batch: {Fore.GREEN}{kept} kept{Style.RESET_ALL}, {Fore.RED}{removed} removed{Style.RESET_ALL}\n")
                    
                    # Display all games in the batch
                    for game in batch_results:
                        name = game.get('game_name', 'Unknown')
                        kept = game.get('keep', False)
                        score = game.get('quality_score', 0.0)
                        
                        # Green checkmark for kept, red X for removed
                        status = f"{Fore.GREEN}✓ KEEP{Style.RESET_ALL}" if kept else f"{Fore.RED}✗ REMOVE{Style.RESET_ALL}"
                        
                        # Display the game name and status on its own line
                        print(f"  {status} | {name}")
                        
                        # Get the evaluation object to display strengths and weaknesses
                        game_eval = game.get("evaluation", {})
                        analysis = game_eval.get("_criteria_analysis", {})
                        
                        # Display criteria insights on separate lines
                        if analysis:
                            # Display strengths and weaknesses
                            strongest = analysis.get("strongest_criteria", [])
                            weakest = analysis.get("weakest_criteria", [])
                            
                            # Add strengths on their own line with proper criterion names
                            if strongest:
                                strongest_names = []
                                for s in strongest:
                                    if s in criteria_display_names:
                                        strongest_names.append(criteria_display_names[s])
                                    else:
                                        strongest_names.append(s.replace("_", " ").title())
                                strongest_str = ", ".join(strongest_names)
                                print(f"    {Fore.GREEN}Strong:{Style.RESET_ALL} {strongest_str}")
                            
                            # Add weaknesses on their own line with proper criterion names
                            if weakest:
                                weakest_names = []
                                for w in weakest:
                                    if w in criteria_display_names:
                                        weakest_names.append(criteria_display_names[w])
                                    else:
                                        weakest_names.append(w.replace("_", " ").title())
                                weakest_str = ", ".join(weakest_names)
                                print(f"    {Fore.YELLOW}Weak:{Style.RESET_ALL} {weakest_str}")
                            
                            # Add low score exception tag if applicable
                            if kept and analysis.get("is_low_score_keeper", False):
                                print(f"    {Fore.YELLOW}[LOW SCORE EXCEPTION]{Style.RESET_ALL}")
                        
                        print("")  # Add spacing between games
                    
                    print("")  # Add spacing at the end
            
            # Apply the filters safely with fallback
            if not self.parsed_data or 'games' not in self.parsed_data:
                raise ValueError("No valid game data found. Please reload the DAT file.")
                
            if not self.filter_engine:
                raise ValueError("Filter engine not initialized properly")
                
            games_to_filter = self.parsed_data.get('games', [])
            result = self.filter_engine.filter_collection(
                games_to_filter,
                criteria=self.settings['criteria'],
                batch_size=self.settings['batch_size'],
                progress_callback=progress_callback
            )
            
            # Process result - handle both 3-item and 4-item tuples for backward compatibility
            if result and isinstance(result, tuple):
                try:
                    if len(result) == 4:
                        self.filtered_games, self.evaluations, provider_error, api_usage_data = result
                    elif len(result) == 3:
                        self.filtered_games, self.evaluations, provider_error = result
                        api_usage_data = None
                    elif len(result) == 2:
                        # Safe unpacking with explicit indexing to avoid type errors
                        self.filtered_games = result[0]  # First element is filtered_games
                        self.evaluations = result[1]     # Second element is evaluations
                        provider_error = None
                        api_usage_data = None
                    else:
                        raise ValueError(f"Unexpected result format from filter_engine: {result}")
                except Exception as e:
                    self._print_error(f"Error processing result: {str(e)}")
                    # Fallback to safe extraction
                    self.filtered_games = result[0] if len(result) > 0 else []
                    self.evaluations = result[1] if len(result) > 1 else []
                    provider_error = result[2] if len(result) > 2 else None
                    api_usage_data = result[3] if len(result) > 3 else None
            else:
                raise ValueError("Filter engine returned invalid result")
                
            # Display API usage information if available
            if api_usage_data:
                provider = api_usage_data.get("provider", "UNKNOWN").upper()
                today_tokens = api_usage_data.get("today_tokens", 0)
                month_tokens = api_usage_data.get("month_tokens", 0)
                total_requests = api_usage_data.get("total_requests", 0)
                
                # Get more accurate usage data directly from tracker
                if provider.lower() != "random":
                    from utils.api_usage_tracker import get_tracker
                    tracker = get_tracker()
                    
                    # Get today's tokens directly from daily usage
                    today = datetime.now().strftime('%Y-%m-%d')
                    provider_data = tracker.usage_data.get(provider.lower(), {})
                    
                    if "daily_usage" in provider_data and today in provider_data["daily_usage"]:
                        today_tokens = provider_data["daily_usage"][today].get("tokens", 0)
                    
                    # Get total requests directly from provider data
                    if provider.lower() in tracker.usage_data:
                        total_requests = tracker.usage_data[provider.lower()].get("total_requests", 0)
                
                print(f"\n{Fore.CYAN}API Usage Information:{Style.RESET_ALL}")
                print(f"Provider: {provider}")
                print(f"Today's usage: {today_tokens:,} tokens")
                print(f"30-day usage: {month_tokens:,} tokens")
                print(f"Total requests: {total_requests:,}")
                print()
            
            # Check for provider errors
            if provider_error:
                print("\n")  # Clear the progress bar line
                error_msg = 'Unknown provider error'
                if isinstance(provider_error, dict) and 'provider_error' in provider_error:
                    error_msg = provider_error['provider_error']
                self._print_error(f"Provider error: {error_msg}")
                
                # Provide helpful information about how to fix the issue
                if self.settings['provider'].lower() == 'gemini':
                    self._print_warning("The Gemini provider requires a valid API key to function.")
                    self._print_info("You can get a Gemini API key at https://ai.google.dev/")
                    self._print_info("Go to Settings → Configure API Keys to set your API key.")
                
                self._print_warning("The Random provider is only for testing and doesn't provide useful filtering.")
                self._print_warning("It will pass all games regardless of quality.")
                
                # Ask if user wants to switch to Random provider for testing only
                print()
                response = self._get_user_input("Do you want to switch to Random provider for TESTING ONLY? (y/n): ")
                
                if response.lower() == 'y':
                    # Switch to random provider but only temporarily
                    old_provider = self.settings['provider']
                    self.settings['provider'] = 'random'
                    self._initialize_provider()
                    
                    # Retry with random provider
                    self._print_info("Retrying with Random provider for TESTING ONLY...")
                    
                    # Check if filter engine is initialized
                    if not self.filter_engine:
                        self._print_error("Filter engine not properly initialized")
                        return
                        
                    # Safely get games with fallback
                    games_to_filter = self.parsed_data.get('games', []) if self.parsed_data else []
                    result = self.filter_engine.filter_collection(
                        games_to_filter,
                        criteria=self.settings['criteria'],
                        batch_size=self.settings['batch_size'],
                        progress_callback=progress_callback
                    )
                    
                    # Process result with safe handling of different return formats
                    if result and isinstance(result, tuple):
                        api_usage_data = None
                        
                        try:
                            if len(result) == 4:
                                self.filtered_games, self.evaluations, provider_error, api_usage_data = result
                            elif len(result) == 3:
                                self.filtered_games, self.evaluations, provider_error = result
                            elif len(result) == 2:
                                # Safe unpacking with explicit indexing to avoid type errors
                                self.filtered_games = result[0]  # First element is filtered_games
                                self.evaluations = result[1]     # Second element is evaluations
                                provider_error = None
                            else:
                                self._print_error(f"Unexpected result format from filter engine: {result}")
                                return
                        except Exception as e:
                            self._print_error(f"Error processing result: {str(e)}")
                            # Fallback to safe extraction
                            self.filtered_games = result[0] if len(result) > 0 else []
                            self.evaluations = result[1] if len(result) > 1 else []
                            provider_error = result[2] if len(result) > 2 else None
                            api_usage_data = result[3] if len(result) > 3 else None
                            
                        # Display API usage information if available
                        if api_usage_data:
                            provider = api_usage_data.get("provider", "UNKNOWN").upper()
                            today_tokens = api_usage_data.get("today_tokens", 0)
                            month_tokens = api_usage_data.get("month_tokens", 0)
                            total_requests = api_usage_data.get("total_requests", 0)
                            
                            # Get more accurate usage data directly from tracker
                            if provider.lower() != "random":
                                from utils.api_usage_tracker import get_tracker
                                tracker = get_tracker()
                                
                                # Get today's tokens directly from daily usage
                                today = datetime.now().strftime('%Y-%m-%d')
                                provider_data = tracker.usage_data.get(provider.lower(), {})
                                
                                if "daily_usage" in provider_data and today in provider_data["daily_usage"]:
                                    today_tokens = provider_data["daily_usage"][today].get("tokens", 0)
                                
                                # Get total requests directly from provider data
                                if provider.lower() in tracker.usage_data:
                                    total_requests = tracker.usage_data[provider.lower()].get("total_requests", 0)
                            
                            print(f"\n{Fore.CYAN}API Usage Information:{Style.RESET_ALL}")
                            print(f"Provider: {provider}")
                            print(f"Today's usage: {today_tokens:,} tokens")
                            print(f"30-day usage: {month_tokens:,} tokens")
                            print(f"Total requests: {total_requests:,}")
                            print()
                    else:
                        self._print_error("Filter engine returned invalid result")
                        return
                    
                    # If we still have an error, give up
                    if provider_error:
                        error_msg = 'Unknown error'
                        if isinstance(provider_error, dict) and 'provider_error' in provider_error:
                            error_msg = provider_error['provider_error']
                        self._print_error(f"Still having issues: {error_msg}")
                        return
                    
                    # Remind user they're in testing mode
                    self._print_warning("NOTE: You are using the Random provider which doesn't provide")
                    self._print_warning("      useful filtering. All games will likely pass.")
                    
                    # Reset the provider setting (but not the actual provider instance) after this run
                    self.settings['provider'] = old_provider
                else:
                    # User declined to use Random provider
                    self._print_info("Operation cancelled. Please configure your API key before trying again.")
                    self._wait_for_key()
                    return
            
            # Apply multi-disc rules
            if self.special_cases and 'multi_disc' in self.special_cases:
                print("\nApplying multi-disc rules...")
                rules_config = {"multi_disc": {"mode": "all_or_none", "prefer": "complete"}}
                self.filtered_games = self.rule_engine.apply_rules_to_filtered_games(self.filtered_games, rules_config)
            
            # Show final statistics with safe access to parsed_data
            original_count = self.parsed_data.get('game_count', 0) if self.parsed_data else 0
            filtered_count = len(self.filtered_games) if self.filtered_games else 0
            reduction = original_count - filtered_count
            reduction_pct = (reduction / original_count * 100) if original_count > 0 else 0
            
            print("\n" + "=" * 50)
            self._print_success(f"Filtering complete: {filtered_count} of {original_count} games kept")
            self._print_info(f"Reduction: {reduction} games ({reduction_pct:.1f}% of collection)")
            
            # Display criteria analysis instead of top games
            if filtered_count > 0:
                print("\n" + "-" * 50)
                self._print_subheader("Criteria Analysis:")
                
                # Count games by criteria
                criteria_counts = {}
                for criterion in self.settings['criteria']:
                    criteria_counts[criterion] = 0
                
                # Count low score keepers
                low_score_keepers = 0
                
                # Analyze criteria in filtered games
                for game in self.filtered_games:
                    if "_evaluation" in game and "_criteria_analysis" in game["_evaluation"]:
                        analysis = game["_evaluation"]["_criteria_analysis"]
                        
                        # Count by strongest criteria
                        for criterion in analysis.get("strongest_criteria", []):
                            if criterion in criteria_counts:
                                criteria_counts[criterion] += 1
                        
                        # Count low score keepers
                        if analysis.get("is_low_score_keeper", False):
                            low_score_keepers += 1
                
                # Display criteria counts
                for criterion in sorted(criteria_counts.keys(), key=lambda x: criteria_counts[x], reverse=True):
                    if criteria_counts[criterion] > 0:
                        pct = (criteria_counts[criterion] / filtered_count) * 100
                        criterion_name = criterion.replace('_', ' ').title()
                        self._print_info(f"- {criterion_name}: {criteria_counts[criterion]} games ({pct:.1f}%)")
                
                # Show low score keepers if any
                if low_score_keepers > 0:
                    pct = (low_score_keepers / filtered_count) * 100
                    print()
                    self._print_info(f"Low Score Exceptions: {low_score_keepers} games ({pct:.1f}%)")
                    self._print_info("These games were kept despite low scores due to other important criteria.")
                
                # Show warning if using Random provider
                if self.settings['provider'].lower() == 'random':
                    print()
                    self._print_warning("NOTE: You're using the Random provider which assigns random scores")
                    self._print_warning("      and doesn't provide meaningful filtering.")
                    self._print_warning("      Switch to Gemini for better results.")
            
            # Auto-save filtered DAT
            output_path = os.path.join(self.settings['output_dir'], f"filtered_{os.path.basename(self.current_dat_file)}")
            if not os.path.exists(self.settings['output_dir']):
                os.makedirs(self.settings['output_dir'])
                
            self.export_manager.export_dat_file(
                filtered_games=self.filtered_games,
                original_data=self.parsed_data,
                output_path=output_path
            )
            
            self._print_success(f"Automatically saved filtered DAT to: {output_path}")
            
            self._wait_for_key()
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            self._print_error(f"Failed to apply filters: {str(e)}")
            self._wait_for_key()
    
    def _update_filter_engine_threshold(self):
        """Update the filter engine with the current thresholds from settings"""
        if self.filter_engine:
            # Apply individual criteria thresholds if set
            if 'criteria_thresholds' in self.settings:
                thresholds = self.settings['criteria_thresholds']
                # Apply Metacritic threshold if set
                if 'metacritic' in thresholds:
                    self.filter_engine.set_threshold('metacritic', thresholds['metacritic'])
    
    def export_menu(self):
        """Display the export menu"""
        if not self.filtered_games:
            self._print_error("No filtered results to export")
            self._wait_for_key()
            return
        
        self._clear_screen()
        self._print_header("Export Results")
        
        self._print_option("1", "Export filtered DAT file")
        self._print_option("2", "Export JSON report")
        self._print_option("3", "Export text summary")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self._export_filtered_dat()
        elif choice == "2":
            self._export_json_report()
        elif choice == "3":
            self._export_text_summary()
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.export_menu()
    
    def _export_filtered_dat(self):
        """Export filtered games to a DAT file"""
        # Handle case when current_dat_file might be None
        basename = os.path.basename(self.current_dat_file) if self.current_dat_file else "filtered.dat"
        default_filename = f"filtered_{basename}"
        output_dir = self.settings['output_dir']
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, default_filename)
        custom_path = self._get_user_input("Output path (press Enter for default)", output_path)
        
        try:
            # Make sure we have valid data before proceeding
            if not self.filtered_games:
                raise ValueError("No filtered games to export")
                
            if not self.parsed_data:
                raise ValueError("No original data available for export")
                
            result = self.export_manager.export_dat_file(
                filtered_games=self.filtered_games,
                original_data=self.parsed_data, 
                output_path=custom_path
            )
            
            self._print_success(f"Successfully exported filtered DAT with {len(self.filtered_games)} games to {custom_path}")
            self._wait_for_key()
        except Exception as e:
            logger.error(f"Error exporting DAT file: {e}")
            self._print_error(f"Failed to export DAT file: {str(e)}")
            self._wait_for_key()
    
    def _export_json_report(self):
        """Export a JSON report of the filtering results"""
        # Handle case when current_dat_file might be None
        basename = "report.json"
        if self.current_dat_file:
            filename = os.path.basename(self.current_dat_file)
            basename = f"report_{os.path.splitext(filename)[0] if '.' in filename else filename}.json"
            
        output_dir = self.settings['output_dir']
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, basename)
        custom_path = self._get_user_input("Output path (press Enter for default)", output_path)
        
        try:
            # Make sure we have valid data before proceeding
            if not self.filtered_games:
                raise ValueError("No filtered games to export")
                
            if not self.evaluations:
                raise ValueError("No game evaluations available for export")
                
            result = self.export_manager.export_json_report(
                filtered_games=self.filtered_games,
                evaluations=self.evaluations,
                special_cases=self.special_cases or {},  # Provide empty dict as fallback
                output_path=custom_path
            )
            
            self._print_success(f"Successfully exported JSON report to {custom_path}")
            self._wait_for_key()
        except Exception as e:
            logger.error(f"Error exporting JSON report: {e}")
            self._print_error(f"Failed to export JSON report: {str(e)}")
            self._wait_for_key()
    
    def _export_text_summary(self):
        """Export a text summary of the filtering results"""
        # Handle case when current_dat_file might be None
        basename = "summary.txt"
        if self.current_dat_file:
            filename = os.path.basename(self.current_dat_file)
            basename = f"summary_{os.path.splitext(filename)[0] if '.' in filename else filename}.txt"
            
        output_dir = self.settings['output_dir']
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, basename)
        custom_path = self._get_user_input("Output path (press Enter for default)", output_path)
        
        try:
            # Safe access to game_count with fallback
            original_count = self.parsed_data.get('game_count', 0) if self.parsed_data else 0
            
            # Prepare metadata with original evaluations for near-miss analysis
            metadata = {
                "original_evaluations": self.evaluations if self.evaluations else [],
                "include_near_miss": True
            }
            
            result = self.export_manager.export_text_summary(
                filtered_games=self.filtered_games,
                original_count=original_count,
                filter_criteria=self.settings['criteria'],
                output_path=custom_path,
                provider_name=self.settings['provider'],
                metadata=metadata
            )
            
            self._print_success(f"Successfully exported text summary to {custom_path}")
            self._wait_for_key()
        except Exception as e:
            logger.error(f"Error exporting text summary: {e}")
            self._print_error(f"Failed to export text summary: {str(e)}")
            self._wait_for_key()
    
    def settings_menu(self):
        """Display the settings menu"""
        self._clear_screen()
        self._print_header("Settings")
        
        # Get current Metacritic threshold from the filter engine if available
        metacritic_threshold = "7.50"
        if hasattr(self, 'filter_engine') and self.filter_engine:
            metacritic_threshold = f"{self.filter_engine.threshold_scores.get('metacritic', 7.5):.2f}"
        
        self._print_subheader("FILTER SETTINGS")
        self._print_info("Filter Mode: Keep if ANY criteria matches")
        self._print_info("Games are kept if they match at least one of the selected criteria.")
        self._print_option("1", f"Metacritic Threshold: {metacritic_threshold} (games with higher scores are kept)")
        
        self._print_subheader("DIRECTORY SETTINGS")
        self._print_option("2", f"Input Directory: {self.settings['input_dir']}")
        self._print_option("3", f"Output Directory: {self.settings['output_dir']}")
        
        self._print_subheader("INTERFACE SETTINGS")
        self._print_option("4", f"Show Progress: {'Yes' if self.settings['show_progress'] else 'No'}")
        self._print_option("5", f"Color Output: {'Yes' if self.settings['color'] else 'No'}")
        self._print_option("6", "Configure API Keys")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self._change_metacritic_threshold()
        elif choice == "2":
            new_dir = self._get_user_input("Enter input directory", self.settings['input_dir'])
            self.settings['input_dir'] = new_dir
            self._print_success(f"Input directory set to {new_dir}")
            self._wait_for_key()
            self.settings_menu()
        elif choice == "3":
            new_dir = self._get_user_input("Enter output directory", self.settings['output_dir'])
            self.settings['output_dir'] = new_dir
            self._print_success(f"Output directory set to {new_dir}")
            self._wait_for_key()
            self.settings_menu()
        elif choice == "4":
            self.settings['show_progress'] = not self.settings['show_progress']
            self._print_success(f"Show progress: {'Yes' if self.settings['show_progress'] else 'No'}")
            self._wait_for_key()
            self.settings_menu()
        elif choice == "5":
            self.settings['color'] = not self.settings['color']
            self._print_success(f"Color output: {'Yes' if self.settings['color'] else 'No'}")
            self._wait_for_key()
            self.settings_menu()
        elif choice == "6":
            self._configure_api_keys()
            self.settings_menu()
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.settings_menu()
    
    # Global threshold method removed (deprecated)
            
    def _change_metacritic_threshold(self):
        """Change the Metacritic score threshold for filtering"""
        # Get current threshold from the filter engine if available
        current = 7.5
        if hasattr(self, 'filter_engine') and self.filter_engine:
            current = self.filter_engine.threshold_scores.get('metacritic', 7.5)
            
        try:
            self._print_info("This sets the minimum Metacritic score for games to be kept (scale: 0-10)")
            self._print_info("Games with a Metacritic score above this threshold will be kept")
            self._print_info("Default is 7.5 (good games)")
            
            new_threshold = float(self._get_user_input(
                f"Enter Metacritic threshold (current: {current:.2f})", 
                str(current)
            ))
            
            if 0.0 <= new_threshold <= 10.0:
                # Update the filter engine if available
                if hasattr(self, 'filter_engine') and self.filter_engine:
                    self.filter_engine.set_threshold('metacritic', new_threshold)
                    
                    # Save threshold in settings for persistence
                    if 'criteria_thresholds' not in self.settings:
                        self.settings['criteria_thresholds'] = {}
                    self.settings['criteria_thresholds']['metacritic'] = new_threshold
                    
                    self._print_success(f"Metacritic threshold set to {new_threshold:.2f}")
                    
                    # Give user feedback on what this means
                    if new_threshold <= 5.0:
                        self._print_info("This will keep most games (very lenient)")
                    elif new_threshold <= 6.5:
                        self._print_info("This will keep average and better games")
                    elif new_threshold <= 7.5:
                        self._print_info("This will keep good and great games (recommended)")
                    elif new_threshold <= 8.5:
                        self._print_info("This will only keep great games (strict)")
                    else:
                        self._print_info("This will only keep exceptional games (very strict)")
                else:
                    # Filter engine not initialized yet, just save for later
                    if 'criteria_thresholds' not in self.settings:
                        self.settings['criteria_thresholds'] = {}
                    self.settings['criteria_thresholds']['metacritic'] = new_threshold
                    self._print_success(f"Metacritic threshold set to {new_threshold:.2f}")
                    self._print_info("This will take effect when filters are applied.")
            else:
                self._print_error("Threshold must be between 0 and 10")
                
            self._wait_for_key()
            self.settings_menu()
        except ValueError:
            self._print_error("Please enter a valid number")
            self._wait_for_key()
            self.settings_menu()
    
    def _configure_api_keys(self):
        """Configure API keys for providers"""
        self._clear_screen()
        self._print_header("Configure API Keys")
        
        # Get information about available providers
        all_providers = get_available_providers()
        
        # Get Gemini status
        gemini_info = all_providers.get("gemini", {})
        
        gemini_status = "Not Set"
        
        # Determine status text and color for Gemini provider
        if gemini_info.get("available", False):
            gemini_status = self.colors['success'] + "[Valid]" + Style.RESET_ALL
        elif gemini_info.get("has_valid_key", False):
            gemini_status = self.colors['warning'] + "[Set but Untested]" + Style.RESET_ALL
        else:
            gemini_status = self.colors['error'] + "[Not Set]" + Style.RESET_ALL
        
        self._print_subheader("Available Providers")
        self._print_option("1", f"Google Gemini API Key {gemini_status}")
        self._print_option("2", "Test API Keys")
        self._print_option("0", "Back")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            gemini_key_set = bool(os.environ.get("GEMINI_API_KEY", ""))
            if gemini_key_set:
                self._print_info("Google Gemini API key is already set.")
                replace = self._get_user_input("Do you want to replace it? (y/n)", "n").lower() == "y"
                if not replace:
                    self._wait_for_key()
                    self._configure_api_keys()
                    return
            else:
                self._print_info("You need a Google Gemini API key to use the Gemini provider.")
                self._print_info("You can get an API key at https://ai.google.dev/")
                self._print_info("Gemini offers a free tier with generous quota limits.")
            
            key = self._get_user_input("Enter Google Gemini API Key (leave blank to keep current)")
            if key:
                os.environ["GEMINI_API_KEY"] = key
                self._print_success("Google Gemini API key set")
                
                # Optionally validate the key immediately
                validate = self._get_user_input("Would you like to validate this key now? (y/n)", "y").lower() == "y"
                if validate:
                    self._print_info("Testing Gemini API key (this may take a moment)...")
                    provider = get_provider("gemini")
                    if provider and provider.initialize():
                        self._print_success("Gemini API key is valid!")
                    else:
                        self._print_error("Failed to validate Gemini API key")
                        self._print_warning("The key may be invalid or there might be connection issues.")
                        self._print_info("You can try again later by selecting 'Test API Keys'")
            
            self._wait_for_key()
            self._configure_api_keys()
        elif choice == "2":
            # Test API keys with our enhanced validation system
            self._print_subheader("Testing API Keys")
            
            # Test Gemini provider
            self._print_info("Testing Gemini API key:")
            available, reason, has_valid_key = check_provider_availability("gemini")
            
            if has_valid_key:
                self._print_info("Gemini API key is present, testing connectivity...")
                # Perform an actual API test
                self._print_info("Testing Gemini API key (this may take a moment)...")
                success, message = check_api_key("gemini")
                if success:
                    self._print_success(f"Gemini API key is valid and working: {message}")
                else:
                    self._print_error(f"Gemini API key validation failed: {message}")
                    self._print_warning("The key may be invalid, expired, or have incorrect permissions")
                    self._print_info("You can get a Gemini API key at https://ai.google.dev/")
                    self._print_info("Note: Gemini offers a free tier with generous quota limits.")
            else:
                if "API key is not set" in reason:
                    self._print_warning("Gemini API key is not set")
                    self._print_info("You can set it by selecting option 2 from the API Keys menu")
                else:
                    self._print_error(f"Gemini provider issue: {reason}")
            
            self._wait_for_key()
            self._configure_api_keys()
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self._configure_api_keys()
    
    def batch_processing_menu(self):
        """Display the batch processing menu"""
        self._clear_screen()
        self._print_header("Batch Processing")
        
        self._print_info("Batch processing allows you to process multiple DAT files at once")
        print("All DAT files in the input directory will be processed with the current settings")
        print()
        
        self._print_option("1", "Run Batch Processing")
        self._print_option("2", "Run Quick Test (3 DAT files)")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self._run_batch_processing()
        elif choice == "2":
            self._run_batch_processing(test_mode=True)
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.batch_processing_menu()
    
    def _run_batch_processing(self, test_mode=False):
        """Run batch processing on multiple DAT files"""
        input_dir = self.settings['input_dir']
        output_dir = self.settings['output_dir']
        
        if not os.path.exists(input_dir):
            self._print_error(f"Input directory not found: {input_dir}")
            self._wait_for_key()
            return
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Find all DAT files
        dat_files = [f for f in os.listdir(input_dir) if f.endswith('.dat')]
        
        if not dat_files:
            self._print_error(f"No DAT files found in {input_dir}")
            self._wait_for_key()
            return
        
        # If test mode, limit to 3 files
        if test_mode:
            dat_files = dat_files[:3]
        
        self._clear_screen()
        self._print_header("Batch Processing")
        
        self._print_info(f"Found {len(dat_files)} DAT files to process")
        self._print_info(f"Provider: {self.settings['provider']}")
        self._print_info(f"Batch Size: {self.settings['batch_size']}")
        self._print_info(f"Threshold: {self.settings['global_threshold']}")
        print()
        
        # Start batch processing
        batch_start_time = time.time()
        results = []
        
        for idx, dat_file in enumerate(dat_files, 1):
            input_path = os.path.join(input_dir, dat_file)
            basename = os.path.splitext(dat_file)[0]
            
            self._print_subheader(f"Processing {dat_file} ({idx}/{len(dat_files)})")
            
            # Define output paths
            filtered_path = os.path.join(output_dir, f"{basename}_filtered.dat")
            report_path = os.path.join(output_dir, f"{basename}_report.json")
            summary_path = os.path.join(output_dir, f"{basename}_summary.txt")
            
            start_time = time.time()
            
            try:
                # Parse DAT file
                self._print_info("Parsing DAT file...")
                parsed_data = self.dat_parser.parse_file(input_path)
                game_count = parsed_data['game_count']
                self._print_info(f"Found {game_count} games")
                
                # Process special cases
                self._print_info("Identifying special cases...")
                special_cases = self.rule_engine.process_collection(parsed_data['games'])['special_cases']
                
                # Define progress callback with enhanced display
                def progress_callback(current, total, batch_results=None):
                    if self.settings['show_progress']:
                        elapsed = time.time() - start_time
                        games_per_sec = current / elapsed if elapsed > 0 else 0
                        
                        # Calculate ETA
                        if games_per_sec > 0:
                            remaining_games = total - current
                            eta_seconds = remaining_games / games_per_sec
                            if eta_seconds < 60:
                                eta_str = f"{eta_seconds:.0f}s"
                            else:
                                eta_str = f"{eta_seconds/60:.0f}m {eta_seconds%60:.0f}s"
                        else:
                            eta_str = "calculating..."
                        
                        # Print progress bar
                        self._print_progress_bar(current, total, 40, f"{current}/{total} games - {games_per_sec:.1f} games/sec - ETA: {eta_str}")
                        
                        # Display batch results if available
                        if batch_results:
                            # Count stats
                            kept_count = len([g for g in batch_results if g.get('keep', False)])
                            removed_count = len(batch_results) - kept_count
                            
                            # The criteria mapping for display
                            criteria_display_names = {
                                "metacritic": "Metacritic Rating",
                                "historical": "Historical Significance",
                                "v_list": "V Recommendation",
                                "console_significance": "Console Significance",
                                "mods_hacks": "Mod Significance",
                                "hidden_gems": "Hidden Gem",
                                "criterion1": "Metacritic Rating",
                                "criterion2": "Historical Significance",
                                "criterion3": "V Recommendation",
                                "criterion4": "Console Significance",
                                "criterion5": "Mod Significance",
                                "criterion6": "Hidden Gem"
                            }
                            
                            print("\nRecent games processed:")
                            print(f"  Last batch: {Fore.GREEN}{kept_count} kept{Style.RESET_ALL}, {Fore.RED}{removed_count} removed{Style.RESET_ALL}\n")
                            
                            # Display all games in the batch
                            for game in batch_results:
                                # Display keep/remove status with color coding
                                name = game.get('game_name', 'Unknown')
                                kept = game.get('keep', False)
                                score = game.get('quality_score', 0.0)
                                
                                # Green checkmark for kept, red X for removed
                                status = f"{Fore.GREEN}✓ KEEP{Style.RESET_ALL}" if kept else f"{Fore.RED}✗ REMOVE{Style.RESET_ALL}"
                                
                                # Display the game name and status on its own line
                                print(f"  {status} | {name}")
                                
                                # Get the evaluation object to display strengths and weaknesses
                                game_eval = game.get("evaluation", {})
                                analysis = game_eval.get("_criteria_analysis", {})
                                
                                # Display criteria insights on separate lines
                                if analysis:
                                    # Display strengths and weaknesses
                                    strongest = analysis.get("strongest_criteria", [])
                                    weakest = analysis.get("weakest_criteria", [])
                                    
                                    # Add strengths on their own line with proper criterion names
                                    if strongest:
                                        strongest_names = []
                                        for s in strongest:
                                            if s in criteria_display_names:
                                                strongest_names.append(criteria_display_names[s])
                                            else:
                                                strongest_names.append(s.replace("_", " ").title())
                                        strongest_str = ", ".join(strongest_names)
                                        print(f"    {Fore.GREEN}Strong:{Style.RESET_ALL} {strongest_str}")
                                    
                                    # Add weaknesses on their own line with proper criterion names
                                    if weakest:
                                        weakest_names = []
                                        for w in weakest:
                                            if w in criteria_display_names:
                                                weakest_names.append(criteria_display_names[w])
                                            else:
                                                weakest_names.append(w.replace("_", " ").title())
                                        weakest_str = ", ".join(weakest_names)
                                        print(f"    {Fore.YELLOW}Weak:{Style.RESET_ALL} {weakest_str}")
                                    
                                    # Add low score exception tag if applicable
                                    if kept and analysis.get("is_low_score_keeper", False):
                                        print(f"    {Fore.YELLOW}[LOW SCORE EXCEPTION]{Style.RESET_ALL}")
                                
                                print("")  # Add spacing between games
                
                # Apply filters
                self._print_info("Applying filters...")
                
                # Check if filter_engine is properly initialized
                if not self.filter_engine:
                    error_msg = "Filter engine not initialized"
                    self._print_error(error_msg)
                    
                    # Try to recover by initializing provider
                    self._print_info("Attempting to initialize provider...")
                    if not self._initialize_provider():
                        self._print_error("Failed to initialize provider. Check API keys.")
                        results.append({
                            'file': dat_file,
                            'error': "Filter engine not initialized and recovery failed"
                        })
                        continue
                    
                    if not self.filter_engine:
                        self._print_error("Still unable to initialize filter engine. Skipping file.")
                        results.append({
                            'file': dat_file,
                            'error': "Filter engine initialization failed"
                        })
                        continue
                
                # Now we can safely use the filter engine
                result = self.filter_engine.filter_collection(
                    parsed_data['games'],
                    criteria=self.settings['criteria'],
                    batch_size=self.settings['batch_size'],
                    progress_callback=progress_callback
                )
                
                # Process result - result is a tuple of (filtered_games, evaluations, provider_error, api_usage_data)
                if len(result) == 4:
                    filtered_games, evaluations, provider_error, api_usage_data = result
                    
                    # Display API usage information if available
                    if api_usage_data:
                        provider = api_usage_data.get("provider", "UNKNOWN").upper()
                        today_tokens = api_usage_data.get("today_tokens", 0)
                        month_tokens = api_usage_data.get("month_tokens", 0)
                        total_requests = api_usage_data.get("total_requests", 0)
                        
                        # Get more accurate usage data directly from tracker
                        if provider.lower() != "random":
                            from utils.api_usage_tracker import get_tracker
                            tracker = get_tracker()
                            
                            # Get today's tokens directly from daily usage
                            today = datetime.now().strftime('%Y-%m-%d')
                            provider_data = tracker.usage_data.get(provider.lower(), {})
                            
                            if "daily_usage" in provider_data and today in provider_data["daily_usage"]:
                                today_tokens = provider_data["daily_usage"][today].get("tokens", 0)
                            
                            # Get total requests directly from provider data
                            if provider.lower() in tracker.usage_data:
                                total_requests = tracker.usage_data[provider.lower()].get("total_requests", 0)
                        
                        print(f"\n{Fore.CYAN}API Usage Information:{Style.RESET_ALL}")
                        print(f"Provider: {provider}")
                        print(f"Today's usage: {today_tokens:,} tokens")
                        print(f"30-day usage: {month_tokens:,} tokens")
                        print(f"Total requests: {total_requests:,}")
                        print()
                else:
                    # For backward compatibility, handle different result lengths
                    if len(result) >= 3:
                        filtered_games, evaluations, provider_error = result
                    elif len(result) == 2:
                        filtered_games, evaluations = result
                        provider_error = None
                    else:
                        self._print_error(f"Unexpected result format: {result}")
                        filtered_games = []
                        evaluations = []
                        provider_error = {"provider_error": "Invalid result format from filter engine"}
                
                # Check if there was a provider error
                if provider_error:
                    error_msg = provider_error.get("provider_error", "Unknown provider error")
                    self._print_error(f"Provider error occurred: {error_msg}")
                    self._print_info("Please check your API keys and provider settings.")
                    return False
                
                # Apply multi-disc rules
                if special_cases and 'multi_disc' in special_cases:
                    self._print_info("Applying multi-disc rules...")
                    rules_config = {"multi_disc": {"mode": "all_or_none", "prefer": "complete"}}
                    filtered_games = self.rule_engine.apply_rules_to_filtered_games(filtered_games, rules_config)
                
                # Export results
                self._print_info(f"Exporting filtered DAT to: {filtered_path}")
                self.export_manager.export_dat_file(filtered_games, parsed_data, filtered_path)
                
                self._print_info(f"Exporting JSON report to: {report_path}")
                self.export_manager.export_json_report(
                    filtered_games=filtered_games,
                    evaluations=evaluations,
                    special_cases=special_cases,
                    output_path=report_path
                )
                
                self._print_info(f"Exporting text summary to: {summary_path}")
                # Prepare metadata with original evaluations for near-miss analysis
                metadata = {
                    "original_evaluations": evaluations,
                    "include_near_miss": True
                }
                
                self.export_manager.export_text_summary(
                    filtered_games=filtered_games,
                    original_count=game_count,
                    filter_criteria=self.settings['criteria'],
                    output_path=summary_path,
                    provider_name=self.settings['provider'],
                    metadata=metadata
                )
                
                # Calculate statistics
                kept_count = len(filtered_games)
                reduction = game_count - kept_count
                reduction_pct = (reduction / game_count * 100) if game_count > 0 else 0
                time_taken = time.time() - start_time
                
                self._print_success(f"Filtering complete: {kept_count} of {game_count} games kept ({reduction_pct:.1f}% reduction)")
                self._print_info(f"Time taken: {time_taken:.2f} seconds")
                print()
                
                # Store results
                results.append({
                    'file': dat_file,
                    'original_count': game_count,
                    'filtered_count': kept_count,
                    'reduction_pct': reduction_pct,
                    'time_taken': time_taken
                })
                
            except Exception as e:
                logger.error(f"Error processing {dat_file}: {e}")
                self._print_error(f"Failed to process {dat_file}: {str(e)}")
                results.append({
                    'file': dat_file,
                    'error': str(e)
                })
                print()
        
        # Show summary
        total_time = time.time() - batch_start_time
        self._print_header("Batch Processing Summary")
        
        self._print_info(f"Processed {len(dat_files)} DAT files in {total_time:.2f} seconds")
        print()
        
        for idx, result in enumerate(results, 1):
            if 'error' in result:
                self._print_error(f"{idx}. {result['file']}: Failed - {result['error']}")
            else:
                self._print_success(
                    f"{idx}. {result['file']}: {result['filtered_count']} of {result['original_count']} kept "
                    f"({result['reduction_pct']:.1f}% of collection) - {result['time_taken']:.2f}s"
                )
        
        # Export batch summary
        summary_path = os.path.join(output_dir, "batch_summary.txt")
        with open(summary_path, 'w') as f:
            f.write(f"DAT Filter AI - Batch Processing Summary\n")
            f.write(f"=====================================\n\n")
            f.write(f"Processed {len(dat_files)} DAT files in {total_time:.2f} seconds\n")
            f.write(f"Provider: {self.settings['provider']}\n")
            f.write(f"Threshold: {self.settings['global_threshold']}\n\n")
            
            for idx, result in enumerate(results, 1):
                if 'error' in result:
                    f.write(f"{idx}. {result['file']}: Failed - {result['error']}\n")
                else:
                    f.write(
                        f"{idx}. {result['file']}: {result['filtered_count']} of {result['original_count']} kept "
                        f"({result['reduction_pct']:.1f}% of collection) - {result['time_taken']:.2f}s\n"
                    )
        
        self._print_success(f"Batch summary exported to: {summary_path}")
        self._wait_for_key()
    
    # Provider comparison functionality has been removed as requested

def main():
    """Main entry point for the interactive menu"""
    menu = InteractiveMenu()
    
    while menu.running:
        try:
            menu.main_menu()
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            print(f"\nAn error occurred: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()