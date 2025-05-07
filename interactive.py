#!/usr/bin/env python
"""
DAT Filter AI - Interactive CLI Interface
A text-based menu interface for the DAT Filter AI tool that works
in environments without PyQt5 support.
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from typing import List, Dict, Any, Optional, Tuple
import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init(autoreset=True)

# Import core components
from core.dat_parser import DatParser
from core.filter_engine import FilterEngine
from core.rule_engine import RuleEngine
from core.export import ExportManager
from ai_providers import get_provider, BaseAIProvider
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger("interactive")

class InteractiveMenu:
    """Interactive text-based menu for DAT Filter AI"""
    
    def __init__(self):
        """Initialize the interactive menu"""
        self.running = True
        self.current_dat_file = None
        self.parsed_data = None
        self.filtered_games = []
        self.evaluations = []
        self.special_cases = {}
        
        # Initialize core components
        self.dat_parser = DatParser()
        self.ai_provider = None
        self.filter_engine = None
        self.rule_engine = RuleEngine()
        self.export_manager = ExportManager()
        
        # Application settings
        self.settings = {
            'provider': 'random',
            'batch_size': 10,
            'criteria': ['metacritic', 'historical', 'v_list', 'console_significance', 'mods_hacks'],
            'input_dir': 'ToFilter',
            'output_dir': 'Filtered',
            'theme': 'default',
            'multi_disc_mode': 'all_or_none',
        }
        
        # Available themes
        self.themes = {
            'default': {
                'header': Fore.CYAN + Style.BRIGHT,
                'option': Fore.GREEN,
                'highlight': Fore.YELLOW + Style.BRIGHT,
                'error': Fore.RED + Style.BRIGHT,
                'success': Fore.GREEN + Style.BRIGHT,
                'info': Fore.BLUE,
                'data': Fore.MAGENTA,
                'progress_bar': Fore.CYAN,
                'progress_fill': '█',
                'progress_empty': '░',
            },
            'retro': {
                'header': Fore.MAGENTA + Style.BRIGHT,
                'option': Fore.YELLOW,
                'highlight': Fore.CYAN + Style.BRIGHT,
                'error': Fore.RED + Style.BRIGHT,
                'success': Fore.GREEN + Style.BRIGHT,
                'info': Fore.BLUE,
                'data': Fore.WHITE,
                'progress_bar': Fore.YELLOW,
                'progress_fill': '🕹️',
                'progress_empty': ' ',
            },
        }
        
        self.current_theme = self.themes[self.settings['theme']]
        
        # Initialize the AI provider
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the AI provider based on current settings"""
        provider_name = self.settings['provider']
        
        try:
            self.ai_provider = get_provider(provider_name)
            self.ai_provider.initialize()
            self.filter_engine = FilterEngine(self.ai_provider)
            logger.info(f"Initialized {provider_name} provider")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {provider_name} provider: {e}")
            if provider_name != 'random':
                # Fallback to random provider
                try:
                    self.ai_provider = get_provider('random')
                    self.ai_provider.initialize()
                    self.filter_engine = FilterEngine(self.ai_provider)
                    logger.info("Initialized random provider as fallback")
                    self.settings['provider'] = 'random'
                    return False
                except:
                    logger.error("Failed to initialize even the random provider")
                    return False
            return False
    
    def _clear_screen(self):
        """Clear the terminal screen"""
        # Use platform-specific clear command
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _print_header(self, text: str):
        """Print a formatted header"""
        width = 70
        print(self.current_theme['header'] + "=" * width)
        print(self.current_theme['header'] + text.center(width))
        print(self.current_theme['header'] + "=" * width)
    
    def _print_subheader(self, text: str):
        """Print a formatted subheader"""
        width = 70
        print(self.current_theme['header'] + "-" * width)
        print(self.current_theme['header'] + text.center(width))
        print(self.current_theme['header'] + "-" * width)
    
    def _print_option(self, key: str, description: str, highlighted: bool = False):
        """Print a menu option"""
        theme = self.current_theme['highlight'] if highlighted else self.current_theme['option']
        print(f"{theme}[{key}] {description}")
    
    def _print_info(self, text: str):
        """Print info text"""
        print(self.current_theme['info'] + text)
    
    def _print_error(self, text: str):
        """Print error text"""
        print(self.current_theme['error'] + text)
    
    def _print_success(self, text: str):
        """Print success text"""
        print(self.current_theme['success'] + text)
    
    def _print_data(self, label: str, value: str):
        """Print a data item"""
        print(f"{self.current_theme['highlight']}{label}: {self.current_theme['data']}{value}")
    
    def _print_progress_bar(self, current: int, total: int, width: int = 50, suffix: str = ""):
        """Print a progress bar"""
        progress = current / total
        filled_length = int(width * progress)
        bar = (self.current_theme['progress_fill'] * filled_length) + (self.current_theme['progress_empty'] * (width - filled_length))
        percentage = int(100 * progress)
        
        # Add a small animation
        animation_chars = ['⬅️', '➡️', '⬆️', '⬇️', '🎮', '🕹️', '💥', '🔥']
        animation_idx = int(time.time() * 4) % len(animation_chars)
        
        if filled_length < width:
            # Insert animation character at the progress point
            bar = bar[:filled_length] + animation_chars[animation_idx] + bar[filled_length+1:]
        
        print(f"\r{self.current_theme['progress_bar']}[{bar}] {percentage}% {suffix}", end="\r")
        
        if current == total:
            print()
    
    def _get_user_input(self, prompt: str, default: str = "") -> str:
        """Get input from the user with a prompt"""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        try:
            return input(self.current_theme['highlight'] + prompt) or default
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return default
    
    def _wait_for_key(self):
        """Wait for a key press"""
        input(self.current_theme['info'] + "Press Enter to continue...")
    
    def main_menu(self):
        """Display the main menu"""
        while self.running:
            self._clear_screen()
            self._print_header("DAT Filter AI - Interactive CLI")
            
            # Print current status
            if self.current_dat_file:
                self._print_info(f"Current DAT file: {os.path.basename(self.current_dat_file)}")
                self._print_info(f"Game count: {self.parsed_data['game_count']}")
                if self.filtered_games:
                    self._print_info(f"Filtered games: {len(self.filtered_games)}")
            else:
                self._print_info("No DAT file loaded")
            
            self._print_info(f"AI Provider: {self.settings['provider']}")
            
            print()
            self._print_option("1", "Load DAT File")
            self._print_option("2", "Apply Filters" if self.current_dat_file else "Apply Filters (requires DAT file)")
            self._print_option("3", "Export Results" if self.filtered_games else "Export Results (requires filtering)")
            self._print_option("4", "Settings")
            self._print_option("5", "Batch Processing")
            self._print_option("6", "Compare Providers")
            self._print_option("0", "Exit")
            
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
                self.compare_providers_menu()
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
            self._print_option(str(idx), f"{file} ({file_size:.1f} KB)")
        
        self._print_option("0", "Back to Main Menu")
        
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
            result = self.rule_engine.process_collection(self.parsed_data['games'])
            self.special_cases = result['special_cases']
            
            self._print_success(f"Successfully loaded DAT file with {self.parsed_data['game_count']} games")
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
            self._print_option(str(idx), criterion)
        
        print()
        self._print_info(f"Current AI Provider: {self.settings['provider']}")
        self._print_info(f"Batch Size: {self.settings['batch_size']} games per API call")
        
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
            self._print_option(str(idx), f"{criterion_name} {'✓' if selected else '✗'}")
        
        print()
        self._print_option("S", "Save and return")
        self._print_option("0", "Cancel")
        
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
        
        providers = [
            ("random", "Random (Test mode, no API key needed)"),
            ("openai", "OpenAI (Most accurate, requires API key)"),
            ("gemini", "Google Gemini (Fast, efficient, requires API key)")
        ]
        
        for idx, (provider_id, provider_desc) in enumerate(providers, 1):
            selected = provider_id == self.settings['provider']
            self._print_option(str(idx), f"{provider_desc} {'✓' if selected else ''}")
        
        print()
        self._print_option("0", "Cancel")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "0":
            self.apply_filters_menu()
            return
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(providers):
                    self.settings['provider'] = providers[idx][0]
                    
                    # Try to initialize the provider
                    success = self._initialize_provider()
                    
                    if success:
                        self._print_success(f"Provider changed to {self.settings['provider']}")
                    else:
                        self._print_error(f"Failed to initialize {self.settings['provider']} provider")
                        
                        if self.settings['provider'] in ('openai', 'gemini'):
                            # Prompt for API key
                            api_key = self._get_user_input(f"Enter your {self.settings['provider'].title()} API key")
                            if api_key:
                                if self.settings['provider'] == 'openai':
                                    os.environ["OPENAI_API_KEY"] = api_key
                                elif self.settings['provider'] == 'gemini':
                                    os.environ["GEMINI_API_KEY"] = api_key
                                
                                # Try to initialize again
                                success = self._initialize_provider()
                                
                                if success:
                                    self._print_success(f"Provider changed to {self.settings['provider']}")
                                else:
                                    self._print_error(f"Failed to initialize {self.settings['provider']} provider with the provided API key")
                    
                    # Update batch size based on provider
                    if self.settings['provider'] == 'openai':
                        self.settings['batch_size'] = 5
                    elif self.settings['provider'] == 'gemini':
                        self.settings['batch_size'] = 10
                    else:
                        self.settings['batch_size'] = 20
                    
                    self._wait_for_key()
                    self.apply_filters_menu()
                else:
                    self._print_error("Invalid choice")
                    self._wait_for_key()
                    self._change_provider()
            except ValueError:
                self._print_error("Please enter a valid number")
                self._wait_for_key()
                self._change_provider()
    
    def _apply_filters(self):
        """Apply filters to the loaded DAT file"""
        if not self.current_dat_file:
            self._print_error("No DAT file loaded")
            self._wait_for_key()
            return
        
        if not self.settings['criteria']:
            self._print_error("No filter criteria selected")
            self._wait_for_key()
            return
        
        if not self.ai_provider or not self.ai_provider.is_available():
            self._print_error("AI provider not available")
            
            # Try to initialize it
            self._initialize_provider()
            
            if not self.ai_provider or not self.ai_provider.is_available():
                self._wait_for_key()
                return
        
        # Show progress UI
        self._clear_screen()
        self._print_header("Applying Filters")
        self._print_info(f"Using {self.settings['provider']} provider with batch size {self.settings['batch_size']}")
        self._print_info(f"Criteria: {', '.join(self.settings['criteria'])}")
        print()
        
        # Create rule config
        rule_config = {
            "multi_disc": {
                "mode": self.settings['multi_disc_mode'],
                "prefer": "complete"
            },
            "regional_variants": {
                "mode": "prefer_region",
                "preferred_regions": ["USA", "Europe", "World", "Japan"]
            },
            "mods_hacks": {
                "mode": "include_notable"
            }
        }
        
        try:
            # Define progress callback
            def progress_callback(current, total):
                percentage = int(100 * current / total) if total > 0 else 0
                self._print_progress_bar(current, total, 50, f"{current}/{total} games ({percentage}%)")
            
            # Apply filters
            self.filtered_games, self.evaluations = self.filter_engine.filter_collection(
                self.parsed_data['games'],
                self.settings['criteria'],
                self.settings['batch_size'],
                progress_callback
            )
            
            # Apply special case rules
            self.filtered_games = self.rule_engine.apply_rules_to_filtered_games(
                self.filtered_games,
                rule_config
            )
            
            print()
            self._print_success(f"Filtering complete: {len(self.filtered_games)} of {self.parsed_data['game_count']} games kept")
            
            # Show special cases
            if self.special_cases:
                print()
                self._print_subheader("Special Cases Detected")
                
                for case_type, cases in self.special_cases.items():
                    if cases:
                        if case_type == 'multi_disc':
                            self._print_info(f"Found {len(cases)} multi-disc game sets")
                        elif case_type == 'regional_variants':
                            self._print_info(f"Found {len(cases)} games with regional variants")
                        elif case_type == 'mods_hacks':
                            self._print_info(f"Found {len(cases)} game mods and hacks")
            
            # Show results summary
            print()
            self._print_subheader("Filter Results")
            original_count = self.parsed_data['game_count']
            filtered_count = len(self.filtered_games)
            reduction = original_count - filtered_count
            reduction_pct = (reduction / original_count) * 100 if original_count > 0 else 0
            
            self._print_data("Original game count", str(original_count))
            self._print_data("Filtered game count", str(filtered_count))
            self._print_data("Reduction", f"{reduction} games ({reduction_pct:.1f}%)")
            
            # Show top games (max 10)
            print()
            self._print_info("Top Filtered Games:")
            for i, game in enumerate(self.filtered_games[:10], 1):
                game_name = game.get('description', game.get('name', f"Game {i}"))
                self._print_info(f"{i}. {game_name}")
            
            if len(self.filtered_games) > 10:
                self._print_info(f"... and {len(self.filtered_games) - 10} more games")
            
            self._wait_for_key()
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            self._print_error(f"Failed to apply filters: {str(e)}")
            self._wait_for_key()
    
    def export_menu(self):
        """Display the export menu"""
        self._clear_screen()
        self._print_header("Export Results")
        
        if not self.filtered_games:
            self._print_error("No filtered games to export")
            self._wait_for_key()
            return
        
        self._print_option("1", "Export Filtered DAT")
        self._print_option("2", "Export JSON Report")
        self._print_option("3", "Export Text Summary")
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
        output_dir = self.settings['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(self.current_dat_file))[0]
        provider_name = self.settings['provider']
        default_file = f"{base_name}_{provider_name}_filtered.dat"
        default_path = os.path.join(output_dir, default_file)
        
        file_path = self._get_user_input(f"Output file path", default_path)
        
        # Get metadata for the export
        metadata = {
            "filtered_by": "DAT Filter AI",
            "filter_criteria": ", ".join(self.settings['criteria']),
            "original_count": str(self.parsed_data['game_count']),
            "filtered_count": str(len(self.filtered_games))
        }
        
        try:
            success, message = self.export_manager.export_dat_file(
                self.filtered_games,
                self.parsed_data,
                file_path,
                metadata
            )
            
            if success:
                self._print_success(message)
            else:
                self._print_error(message)
            
            self._wait_for_key()
            
        except Exception as e:
            logger.error(f"Error exporting DAT file: {e}")
            self._print_error(f"Failed to export DAT file: {str(e)}")
            self._wait_for_key()
    
    def _export_json_report(self):
        """Export a JSON report of the filtering results"""
        output_dir = self.settings['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(self.current_dat_file))[0]
        provider_name = self.settings['provider']
        default_file = f"report_{base_name}_{provider_name}.json"
        default_path = os.path.join(output_dir, default_file)
        
        file_path = self._get_user_input(f"Output file path", default_path)
        
        try:
            success, message = self.export_manager.export_json_report(
                self.filtered_games,
                self.evaluations,
                self.special_cases,
                file_path
            )
            
            if success:
                self._print_success(message)
            else:
                self._print_error(message)
            
            self._wait_for_key()
            
        except Exception as e:
            logger.error(f"Error exporting JSON report: {e}")
            self._print_error(f"Failed to export JSON report: {str(e)}")
            self._wait_for_key()
    
    def _export_text_summary(self):
        """Export a text summary of the filtering results"""
        output_dir = self.settings['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(self.current_dat_file))[0]
        provider_name = self.settings['provider']
        default_file = f"summary_{base_name}_{provider_name}.txt"
        default_path = os.path.join(output_dir, default_file)
        
        file_path = self._get_user_input(f"Output file path", default_path)
        
        try:
            success, message = self.export_manager.export_text_summary(
                self.filtered_games,
                self.parsed_data['game_count'],
                self.settings['criteria'],
                file_path
            )
            
            if success:
                self._print_success(message)
            else:
                self._print_error(message)
            
            self._wait_for_key()
            
        except Exception as e:
            logger.error(f"Error exporting text summary: {e}")
            self._print_error(f"Failed to export text summary: {str(e)}")
            self._wait_for_key()
    
    def settings_menu(self):
        """Display the settings menu"""
        self._clear_screen()
        self._print_header("Settings")
        
        # Display current settings
        self._print_subheader("Current Settings")
        self._print_data("AI Provider", self.settings['provider'])
        self._print_data("Batch Size", str(self.settings['batch_size']))
        self._print_data("Input Directory", self.settings['input_dir'])
        self._print_data("Output Directory", self.settings['output_dir'])
        self._print_data("Theme", self.settings['theme'])
        self._print_data("Multi-disc Mode", self.settings['multi_disc_mode'])
        
        print()
        self._print_option("1", "Change Provider")
        self._print_option("2", "Change Batch Size")
        self._print_option("3", "Change Input Directory")
        self._print_option("4", "Change Output Directory")
        self._print_option("5", "Change Theme")
        self._print_option("6", "Change Multi-disc Mode")
        self._print_option("7", "Configure API Keys")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self._change_provider()
        elif choice == "2":
            try:
                batch_size = int(self._get_user_input("Enter batch size (1-50)", str(self.settings['batch_size'])))
                if 1 <= batch_size <= 50:
                    self.settings['batch_size'] = batch_size
                    self._print_success(f"Batch size set to {batch_size}")
                else:
                    self._print_error("Batch size must be between 1 and 50")
                self._wait_for_key()
                self.settings_menu()
            except ValueError:
                self._print_error("Please enter a valid number")
                self._wait_for_key()
                self.settings_menu()
        elif choice == "3":
            dir_path = self._get_user_input("Enter input directory path", self.settings['input_dir'])
            if os.path.exists(dir_path):
                self.settings['input_dir'] = dir_path
                self._print_success(f"Input directory set to {dir_path}")
            else:
                create = self._get_user_input(f"Directory {dir_path} does not exist. Create it? (y/n)").lower()
                if create == 'y':
                    os.makedirs(dir_path, exist_ok=True)
                    self.settings['input_dir'] = dir_path
                    self._print_success(f"Created and set input directory to {dir_path}")
                else:
                    self._print_error("Directory not changed")
            self._wait_for_key()
            self.settings_menu()
        elif choice == "4":
            dir_path = self._get_user_input("Enter output directory path", self.settings['output_dir'])
            if os.path.exists(dir_path):
                self.settings['output_dir'] = dir_path
                self._print_success(f"Output directory set to {dir_path}")
            else:
                create = self._get_user_input(f"Directory {dir_path} does not exist. Create it? (y/n)").lower()
                if create == 'y':
                    os.makedirs(dir_path, exist_ok=True)
                    self.settings['output_dir'] = dir_path
                    self._print_success(f"Created and set output directory to {dir_path}")
                else:
                    self._print_error("Directory not changed")
            self._wait_for_key()
            self.settings_menu()
        elif choice == "5":
            self._change_theme()
        elif choice == "6":
            self._change_multi_disc_mode()
        elif choice == "7":
            self._configure_api_keys()
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.settings_menu()
    
    def _change_theme(self):
        """Change the application theme"""
        self._clear_screen()
        self._print_subheader("Change Theme")
        
        for idx, (theme_id, theme_data) in enumerate(self.themes.items(), 1):
            selected = theme_id == self.settings['theme']
            self._print_option(str(idx), f"{theme_id.title()} {'✓' if selected else ''}")
        
        print()
        self._print_option("0", "Cancel")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "0":
            self.settings_menu()
            return
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.themes):
                    theme_id = list(self.themes.keys())[idx]
                    self.settings['theme'] = theme_id
                    self.current_theme = self.themes[theme_id]
                    self._print_success(f"Theme changed to {theme_id}")
                    self._wait_for_key()
                    self.settings_menu()
                else:
                    self._print_error("Invalid choice")
                    self._wait_for_key()
                    self._change_theme()
            except ValueError:
                self._print_error("Please enter a valid number")
                self._wait_for_key()
                self._change_theme()
    
    def _change_multi_disc_mode(self):
        """Change the multi-disc handling mode"""
        self._clear_screen()
        self._print_subheader("Change Multi-disc Mode")
        
        modes = [
            ("all_or_none", "Include complete sets only (all or none)"),
            ("first_disc_only", "Keep first disc only")
        ]
        
        for idx, (mode_id, mode_desc) in enumerate(modes, 1):
            selected = mode_id == self.settings['multi_disc_mode']
            self._print_option(str(idx), f"{mode_desc} {'✓' if selected else ''}")
        
        print()
        self._print_option("0", "Cancel")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "0":
            self.settings_menu()
            return
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(modes):
                    self.settings['multi_disc_mode'] = modes[idx][0]
                    self._print_success(f"Multi-disc mode changed to {modes[idx][1]}")
                    self._wait_for_key()
                    self.settings_menu()
                else:
                    self._print_error("Invalid choice")
                    self._wait_for_key()
                    self._change_multi_disc_mode()
            except ValueError:
                self._print_error("Please enter a valid number")
                self._wait_for_key()
                self._change_multi_disc_mode()
    
    def _configure_api_keys(self):
        """Configure API keys for providers"""
        self._clear_screen()
        self._print_header("Configure API Keys")
        
        self._print_option("1", "Configure OpenAI API Key")
        self._print_option("2", "Configure Gemini API Key")
        self._print_option("0", "Back to Settings Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            current_key = os.environ.get("OPENAI_API_KEY", "")
            masked_key = "********" if current_key else ""
            api_key = self._get_user_input(f"Enter your OpenAI API key (leave empty to keep current key)", masked_key)
            
            if api_key and api_key != "********":
                os.environ["OPENAI_API_KEY"] = api_key
                self._print_success("OpenAI API key configured")
                
                # Reinitialize provider if currently using OpenAI
                if self.settings['provider'] == 'openai':
                    self._initialize_provider()
            
            self._wait_for_key()
            self._configure_api_keys()
            
        elif choice == "2":
            current_key = os.environ.get("GEMINI_API_KEY", "")
            masked_key = "********" if current_key else ""
            api_key = self._get_user_input(f"Enter your Gemini API key (leave empty to keep current key)", masked_key)
            
            if api_key and api_key != "********":
                os.environ["GEMINI_API_KEY"] = api_key
                self._print_success("Gemini API key configured")
                
                # Reinitialize provider if currently using Gemini
                if self.settings['provider'] == 'gemini':
                    self._initialize_provider()
            
            self._wait_for_key()
            self._configure_api_keys()
            
        elif choice == "0":
            self.settings_menu()
            return
            
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self._configure_api_keys()
    
    def batch_processing_menu(self):
        """Display the batch processing menu"""
        self._clear_screen()
        self._print_header("Batch Processing")
        
        self._print_info("This will process multiple DAT files in a batch")
        print()
        
        # Display current batch settings
        self._print_subheader("Current Settings")
        self._print_data("AI Provider", self.settings['provider'])
        self._print_data("Batch Size", str(self.settings['batch_size']))
        self._print_data("Input Directory", self.settings['input_dir'])
        self._print_data("Output Directory", self.settings['output_dir'])
        
        print()
        self._print_option("1", "Run Batch Processing with Current Settings")
        self._print_option("2", "Change Batch Settings")
        self._print_option("3", "Run Quick Test (Small Files Only)")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self._run_batch_processing()
        elif choice == "2":
            self.settings_menu()  # Reuse the settings menu
        elif choice == "3":
            self._run_batch_processing(test_mode=True)
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.batch_processing_menu()
    
    def _run_batch_processing(self, test_mode=False):
        """Run batch processing on multiple DAT files"""
        self._clear_screen()
        self._print_header("Running Batch Processing")
        
        # Build command for batch processing
        cmd = ["./batch_process.sh"]
        
        # Add provider
        if self.settings['provider'] == 'random':
            cmd.append("--random")
        elif self.settings['provider'] == 'openai':
            cmd.append("--openai")
        elif self.settings['provider'] == 'gemini':
            cmd.append("--gemini")
        
        # Add batch size
        cmd.extend(["--batch-size", str(self.settings['batch_size'])])
        
        # Add input/output dirs
        cmd.extend(["--input", self.settings['input_dir']])
        cmd.extend(["--output", self.settings['output_dir']])
        
        # Add test mode if specified
        if test_mode:
            cmd.append("--test")
        
        self._print_info(f"Running command: {' '.join(cmd)}")
        print()
        
        try:
            # Execute the batch processing script
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Display output in real-time
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self._print_success("Batch processing completed successfully")
            else:
                self._print_error(f"Batch processing failed with return code {return_code}")
            
            self._wait_for_key()
            
        except Exception as e:
            logger.error(f"Error running batch processing: {e}")
            self._print_error(f"Failed to run batch processing: {str(e)}")
            self._wait_for_key()
    
    def compare_providers_menu(self):
        """Display the provider comparison menu"""
        self._clear_screen()
        self._print_header("Compare Providers")
        
        self._print_info("This will compare results from different AI providers")
        print()
        
        self._print_option("1", "Compare All Providers on a Test File")
        self._print_option("2", "Run Multi-Evaluation Script")
        self._print_option("3", "View Provider Comparison Report")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self._run_provider_comparison()
        elif choice == "2":
            self._run_multi_eval()
        elif choice == "3":
            self._view_comparison_report()
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.compare_providers_menu()
    
    def _run_provider_comparison(self):
        """Run a comparison between providers on a test file"""
        self._clear_screen()
        self._print_header("Running Provider Comparison")
        
        # Find a small test file
        test_files = []
        input_dir = self.settings['input_dir']
        
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                if file.endswith(".dat") and ("test" in file.lower() or "sample" in file.lower()):
                    test_files.append(file)
        
        if not test_files:
            self._print_error(f"No test files found in {input_dir}")
            self._wait_for_key()
            return
        
        # Select a test file
        self._print_subheader("Available Test Files")
        
        for idx, file in enumerate(test_files, 1):
            file_path = os.path.join(input_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            self._print_option(str(idx), f"{file} ({file_size:.1f} KB)")
        
        print()
        self._print_option("0", "Cancel")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(test_files):
                test_file = os.path.join(input_dir, test_files[idx])
                
                # Build command for multi-eval
                cmd = ["./multieval.sh", test_file]
                
                self._print_info(f"Running comparison on {test_files[idx]} with all available providers")
                print()
                
                try:
                    # Execute the multi-eval script
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    # Display output in real-time
                    for line in iter(process.stdout.readline, ''):
                        print(line, end='')
                    
                    process.stdout.close()
                    return_code = process.wait()
                    
                    if return_code == 0:
                        self._print_success("Provider comparison completed successfully")
                    else:
                        self._print_error(f"Provider comparison failed with return code {return_code}")
                    
                    self._wait_for_key()
                    
                except Exception as e:
                    logger.error(f"Error running provider comparison: {e}")
                    self._print_error(f"Failed to run provider comparison: {str(e)}")
                    self._wait_for_key()
            else:
                self._print_error("Invalid choice")
                self._wait_for_key()
        except ValueError:
            self._print_error("Please enter a number")
            self._wait_for_key()
    
    def _run_multi_eval(self):
        """Run the multi-evaluation script"""
        self._clear_screen()
        self._print_header("Running Multi-Evaluation")
        
        # Find available DAT files
        dat_files = []
        input_dir = self.settings['input_dir']
        
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                if file.endswith(".dat"):
                    dat_files.append(file)
        
        if not dat_files:
            self._print_error(f"No DAT files found in {input_dir}")
            self._wait_for_key()
            return
        
        # Select a DAT file
        self._print_subheader("Available DAT Files")
        
        for idx, file in enumerate(dat_files, 1):
            file_path = os.path.join(input_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            self._print_option(str(idx), f"{file} ({file_size:.1f} KB)")
        
        print()
        self._print_option("0", "Cancel")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(dat_files):
                dat_file = os.path.join(input_dir, dat_files[idx])
                
                # Build command for multi-eval
                cmd = ["python", "multieval.py", "--input", dat_file]
                
                self._print_info(f"Running multi-evaluation on {dat_files[idx]}")
                print()
                
                try:
                    # Execute the multi-eval script
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    # Display output in real-time
                    for line in iter(process.stdout.readline, ''):
                        print(line, end='')
                    
                    process.stdout.close()
                    return_code = process.wait()
                    
                    if return_code == 0:
                        self._print_success("Multi-evaluation completed successfully")
                    else:
                        self._print_error(f"Multi-evaluation failed with return code {return_code}")
                    
                    self._wait_for_key()
                    
                except Exception as e:
                    logger.error(f"Error running multi-evaluation: {e}")
                    self._print_error(f"Failed to run multi-evaluation: {str(e)}")
                    self._wait_for_key()
            else:
                self._print_error("Invalid choice")
                self._wait_for_key()
        except ValueError:
            self._print_error("Please enter a number")
            self._wait_for_key()
    
    def _view_comparison_report(self):
        """View the provider comparison report"""
        self._clear_screen()
        self._print_header("Provider Comparison Report")
        
        # Check if comparison.txt exists
        if os.path.exists("comparison.txt"):
            try:
                with open("comparison.txt", "r") as f:
                    report = f.read()
                
                # Display the report
                print(report)
                
                self._wait_for_key()
                
            except Exception as e:
                logger.error(f"Error reading comparison report: {e}")
                self._print_error(f"Failed to read comparison report: {str(e)}")
                self._wait_for_key()
        elif os.path.exists("archive/comparison.txt"):
            try:
                with open("archive/comparison.txt", "r") as f:
                    report = f.read()
                
                # Display the report
                print(report)
                
                self._wait_for_key()
                
            except Exception as e:
                logger.error(f"Error reading comparison report: {e}")
                self._print_error(f"Failed to read comparison report: {str(e)}")
                self._wait_for_key()
        else:
            self._print_error("No comparison report found. Please run a provider comparison first.")
            self._wait_for_key()

def main():
    """Main entry point for the interactive menu"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="DAT Filter AI - Interactive CLI")
    parser.add_argument("--theme", help="UI theme (default, retro)", default="default")
    args = parser.parse_args()
    
    # Initialize the menu
    menu = InteractiveMenu()
    
    # Set theme if specified
    if args.theme in menu.themes:
        menu.settings['theme'] = args.theme
        menu.current_theme = menu.themes[args.theme]
    
    # Start the main menu
    try:
        menu.main_menu()
    except KeyboardInterrupt:
        print("\nExiting DAT Filter AI - Interactive CLI")
        sys.exit(0)

if __name__ == "__main__":
    main()