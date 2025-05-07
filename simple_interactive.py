#!/usr/bin/env python3
"""
DAT Filter AI - Simple Interactive CLI Interface
A text-based menu interface for the DAT Filter AI tool with minimal formatting.
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Tuple, Optional, Callable
from colorama import init, Fore, Style, Back

# Import core modules
from core.dat_parser import DatParser
from core.filter_engine import FilterEngine
from core.rule_engine import RuleEngine
from core.export import ExportManager
from ai_providers import get_provider
from utils.logging_config import setup_logging

# Initialize colorama for cross-platform color support
init()

# Set up logging
logger = logging.getLogger('datfilterai')

class SimpleInteractiveMenu:
    """Simple text-based menu for DAT Filter AI without fancy formatting"""
    
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
        
        # Default settings
        self.settings = {
            'provider': 'random',
            'criteria': ['metacritic', 'historical', 'v_list', 'console_significance', 'mods_hacks'],
            'batch_size': 10,
            'global_threshold': 1.0,
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
            provider = get_provider(self.settings['provider'])
            if provider:
                self.filter_engine = FilterEngine(provider)
                self.filter_engine.set_global_threshold(self.settings['global_threshold'])
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to initialize provider: {e}")
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
        """Print a simple progress bar"""
        filled_length = int(width * current // total)
        bar = '█' * filled_length + '░' * (width - filled_length)
        percent = f"{100 * current / total:.1f}"
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
        
        # Show DAT info
        if self.current_dat_file:
            basename = os.path.basename(self.current_dat_file)
            if len(basename) > 40:
                basename = basename[:37] + "..."
            
            self._print_data("Current DAT", basename)
            self._print_data("Game Count", str(self.parsed_data['game_count']))
            if self.filtered_games:
                self._print_data("Filtered", f"{len(self.filtered_games)} games kept")
            else:
                self._print_info("Status: No filtering applied yet")
        else:
            self._print_info("No DAT file loaded")
        
        # Show engine info
        print()
        self._print_data("Engine", self.settings['provider'].upper())
        self._print_data("Threshold", f"{self.settings['global_threshold']:.2f}")
        
        # Menu options
        self._print_subheader("SYSTEM COMMANDS")
        
        menu_options = [
            ("1", "Load DAT File", False),
            ("2", "Apply Filters", not self.current_dat_file),
            ("3", "Export Results", not self.filtered_games),
            ("4", "Settings", False),
            ("5", "Batch Processing", False),
            ("6", "Compare Providers", False),
            ("7", f"Change AI Provider ({self.settings['provider'].upper()})", False),
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
            self.compare_providers_menu()
        elif choice == "7":
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
            print(f"  {idx}. {criterion}")
        
        print()
        self._print_info(f"Current AI Provider: {self.settings['provider']}")
        self._print_info(f"Batch Size: {self.settings['batch_size']} games per API call")
        
        # Display threshold with description
        threshold = self.settings['global_threshold']
        threshold_desc = "Neutral"
        if threshold < 1.0:
            threshold_desc = "More Lenient"
        elif threshold > 1.0:
            threshold_desc = "More Strict"
        self._print_info(f"Global Threshold: {threshold:.2f} ({threshold_desc})")
        
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
        
        providers = [
            ("random", "Random (Test mode, no API key needed)"),
            ("openai", "OpenAI (Most accurate, requires API key)"),
            ("gemini", "Google Gemini (Fast, efficient, requires API key)")
        ]
        
        for idx, (provider_id, provider_desc) in enumerate(providers, 1):
            selected = provider_id == self.settings['provider']
            print(f"  [{idx}] {provider_desc} {'✓' if selected else ''}")
        
        print()
        print("  [0] Cancel")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "0":
            # Check where we came from - this will determine where to return
            # If we came from the main menu (filter engine is not active yet),
            # return to main menu instead
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
                                    self._print_error(f"Failed to initialize {self.settings['provider']} provider")
                    
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
        
        # Show filtering details
        self._print_info(f"DAT File: {os.path.basename(self.current_dat_file)}")
        self._print_info(f"Game Count: {self.parsed_data['game_count']}")
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
                    
                    # Show progress
                    self._print_progress_bar(current, total, 40, f"{current}/{total} games - {games_per_sec:.1f} games/sec - {eta}")
                
                # Display intermediate results if available
                if batch_results and current % 5 == 0:
                    print("\nIntermediate results:")
                    kept = len([g for g in batch_results if g.get('keep', False)])
                    removed = len(batch_results) - kept
                    self._print_info(f"Last batch: {kept} kept, {removed} removed")
            
            # Apply the filters
            result = self.filter_engine.filter_collection(
                self.parsed_data['games'],
                criteria=self.settings['criteria'],
                batch_size=self.settings['batch_size'],
                progress_callback=progress_callback
            )
            
            # Process result
            self.filtered_games = result['filtered_games']
            self.evaluations = result['evaluations']
            
            # Apply multi-disc rules
            if self.special_cases and 'multi_disc' in self.special_cases:
                print("\nApplying multi-disc rules...")
                rules_config = {"multi_disc": {"mode": "all_or_none", "prefer": "complete"}}
                self.filtered_games = self.rule_engine.apply_special_case_rules(self.filtered_games, rules_config)
            
            # Show final statistics
            original_count = self.parsed_data['game_count']
            filtered_count = len(self.filtered_games)
            reduction = original_count - filtered_count
            reduction_pct = (reduction / original_count * 100) if original_count > 0 else 0
            
            print("\n" + "=" * 50)
            self._print_success(f"Filtering complete: {filtered_count} of {original_count} games kept")
            self._print_info(f"Reduction: {reduction} games ({reduction_pct:.1f}%)")
            
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
        """Update the filter engine with the current global threshold"""
        if self.filter_engine:
            self.filter_engine.set_global_threshold(self.settings['global_threshold'])
    
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
        default_filename = f"filtered_{os.path.basename(self.current_dat_file)}"
        output_dir = self.settings['output_dir']
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, default_filename)
        custom_path = self._get_user_input("Output path (press Enter for default)", output_path)
        
        try:
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
        default_filename = f"report_{os.path.splitext(os.path.basename(self.current_dat_file))[0]}.json"
        output_dir = self.settings['output_dir']
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, default_filename)
        custom_path = self._get_user_input("Output path (press Enter for default)", output_path)
        
        try:
            result = self.export_manager.export_json_report(
                filtered_games=self.filtered_games,
                evaluations=self.evaluations,
                special_cases=self.special_cases,
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
        default_filename = f"summary_{os.path.splitext(os.path.basename(self.current_dat_file))[0]}.txt"
        output_dir = self.settings['output_dir']
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, default_filename)
        custom_path = self._get_user_input("Output path (press Enter for default)", output_path)
        
        try:
            result = self.export_manager.export_text_summary(
                filtered_games=self.filtered_games,
                original_count=self.parsed_data['game_count'],
                filter_criteria=self.settings['criteria'],
                output_path=custom_path
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
        
        self._print_option("1", f"Global Threshold: {self.settings['global_threshold']:.2f}")
        self._print_option("2", f"Input Directory: {self.settings['input_dir']}")
        self._print_option("3", f"Output Directory: {self.settings['output_dir']}")
        self._print_option("4", f"Show Progress: {'Yes' if self.settings['show_progress'] else 'No'}")
        self._print_option("5", f"Color Output: {'Yes' if self.settings['color'] else 'No'}")
        self._print_option("6", "Configure API Keys")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            self._change_global_threshold()
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
        elif choice == "0":
            return
        else:
            self._print_error("Invalid choice")
            self._wait_for_key()
            self.settings_menu()
    
    def _change_global_threshold(self):
        """Change the global threshold modifier for filtering"""
        current = self.settings['global_threshold']
        try:
            new_threshold = float(self._get_user_input(
                f"Enter threshold value (current: {current:.2f})", 
                str(current)
            ))
            
            if 0.1 <= new_threshold <= 2.0:
                self.settings['global_threshold'] = new_threshold
                self._update_filter_engine_threshold()
                
                threshold_desc = "neutral"
                if new_threshold < 1.0:
                    threshold_desc = "more lenient (keeps more games)"
                elif new_threshold > 1.0:
                    threshold_desc = "more strict (keeps fewer games)"
                    
                self._print_success(f"Threshold set to {new_threshold:.2f} - {threshold_desc}")
            else:
                self._print_error("Threshold must be between 0.1 and 2.0")
                
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
        
        self._print_subheader("Available Providers")
        self._print_option("1", "OpenAI API Key")
        self._print_option("2", "Google Gemini API Key")
        self._print_option("0", "Back to Settings")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
            key = self._get_user_input("Enter OpenAI API Key (leave blank to keep current)")
            if key:
                os.environ["OPENAI_API_KEY"] = key
                self._print_success("OpenAI API key updated")
                
            self._wait_for_key()
            self._configure_api_keys()
        elif choice == "2":
            key = self._get_user_input("Enter Google Gemini API Key (leave blank to keep current)")
            if key:
                os.environ["GEMINI_API_KEY"] = key
                self._print_success("Google Gemini API key updated")
                
            self._wait_for_key()
            self._configure_api_keys()
        elif choice == "0":
            self.settings_menu()
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
                
                # Define progress callback
                def progress_callback(current, total):
                    if self.settings['show_progress']:
                        elapsed = time.time() - start_time
                        games_per_sec = current / elapsed if elapsed > 0 else 0
                        self._print_progress_bar(current, total, 40, f"{current}/{total} games ({games_per_sec:.1f} games/sec)")
                
                # Apply filters
                self._print_info("Applying filters...")
                result = self.filter_engine.filter_collection(
                    parsed_data['games'],
                    criteria=self.settings['criteria'],
                    batch_size=self.settings['batch_size'],
                    progress_callback=progress_callback
                )
                
                filtered_games = result['filtered_games']
                evaluations = result['evaluations']
                
                # Apply multi-disc rules
                if special_cases and 'multi_disc' in special_cases:
                    self._print_info("Applying multi-disc rules...")
                    rules_config = {"multi_disc": {"mode": "all_or_none", "prefer": "complete"}}
                    filtered_games = self.rule_engine.apply_special_case_rules(filtered_games, rules_config)
                
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
                self.export_manager.export_text_summary(
                    filtered_games=filtered_games,
                    original_count=game_count,
                    filter_criteria=self.settings['criteria'],
                    output_path=summary_path
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
                    f"({result['reduction_pct']:.1f}% reduction) - {result['time_taken']:.2f}s"
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
                        f"({result['reduction_pct']:.1f}% reduction) - {result['time_taken']:.2f}s\n"
                    )
        
        self._print_success(f"Batch summary exported to: {summary_path}")
        self._wait_for_key()
    
    def compare_providers_menu(self):
        """Display the provider comparison menu"""
        self._clear_screen()
        self._print_header("Compare Providers")
        
        self._print_info("This feature allows you to compare the filtering results from different AI providers")
        print("A test DAT file will be processed by each provider and the results will be compared")
        print()
        
        self._print_option("1", "Run Provider Comparison")
        self._print_option("2", "Run Multi-Provider Evaluation")
        self._print_option("3", "View Comparison Report")
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
        self._print_header("Provider Comparison")
        
        input_dir = self.settings['input_dir']
        
        # Choose a test file
        test_files = [f for f in os.listdir(input_dir) if f.endswith('.dat') and 'test' in f.lower()]
        if not test_files:
            test_files = [f for f in os.listdir(input_dir) if f.endswith('.dat')]
            
        if not test_files:
            self._print_error(f"No DAT files found in {input_dir}")
            self._wait_for_key()
            return
        
        self._print_subheader("Select a test file")
        for idx, file in enumerate(test_files, 1):
            file_path = os.path.join(input_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            self._print_option(str(idx), f"{file} ({file_size:.1f} KB)")
        
        print()
        choice = self._get_user_input("Enter file number (or 0 to cancel)")
        
        if choice == "0":
            return
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(test_files):
                test_file = test_files[idx]
                input_path = os.path.join(input_dir, test_file)
                
                # Execute Python script
                script_path = os.path.join(os.getcwd(), "compare_providers.py")
                if not os.path.exists(script_path):
                    self._print_error(f"Script not found: {script_path}")
                    self._wait_for_key()
                    return
                
                cmd = f"python {script_path} -i {input_path}"
                
                self._print_info(f"Running comparison with {test_file}...")
                self._print_info(f"Command: {cmd}")
                print()
                
                os.system(cmd)
                
                self._print_success("Comparison complete")
                self._wait_for_key()
            else:
                self._print_error("Invalid choice")
                self._wait_for_key()
        except ValueError:
            self._print_error("Please enter a valid number")
            self._wait_for_key()
    
    def _run_multi_eval(self):
        """Run the multi-evaluation script"""
        self._clear_screen()
        self._print_header("Multi-Provider Evaluation")
        
        input_dir = self.settings['input_dir']
        
        # Choose a test file
        test_files = [f for f in os.listdir(input_dir) if f.endswith('.dat') and 'test' in f.lower()]
        if not test_files:
            test_files = [f for f in os.listdir(input_dir) if f.endswith('.dat')]
            
        if not test_files:
            self._print_error(f"No DAT files found in {input_dir}")
            self._wait_for_key()
            return
        
        self._print_subheader("Select a test file")
        for idx, file in enumerate(test_files, 1):
            file_path = os.path.join(input_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            self._print_option(str(idx), f"{file} ({file_size:.1f} KB)")
        
        print()
        choice = self._get_user_input("Enter file number (or 0 to cancel)")
        
        if choice == "0":
            return
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(test_files):
                test_file = test_files[idx]
                input_path = os.path.join(input_dir, test_file)
                
                # Execute Python script
                script_path = os.path.join(os.getcwd(), "multieval.py")
                if not os.path.exists(script_path):
                    self._print_error(f"Script not found: {script_path}")
                    self._wait_for_key()
                    return
                
                cmd = f"python {script_path} -i {input_path}"
                
                self._print_info(f"Running multi-evaluation with {test_file}...")
                self._print_info(f"Command: {cmd}")
                print()
                
                os.system(cmd)
                
                self._print_success("Multi-evaluation complete")
                self._wait_for_key()
            else:
                self._print_error("Invalid choice")
                self._wait_for_key()
        except ValueError:
            self._print_error("Please enter a valid number")
            self._wait_for_key()
    
    def _view_comparison_report(self):
        """View the provider comparison report"""
        report_file = "comparison.txt"
        
        if not os.path.exists(report_file):
            # Try to find in archive directory
            archive_file = os.path.join("archive", report_file)
            if os.path.exists(archive_file):
                report_file = archive_file
            else:
                self._print_error(f"Comparison report not found: {report_file}")
                self._wait_for_key()
                return
        
        self._clear_screen()
        self._print_header("Provider Comparison Report")
        
        # Display report
        with open(report_file, 'r') as f:
            content = f.read()
            print(content)
        
        self._wait_for_key()

def main():
    """Main entry point for the simple interactive menu"""
    menu = SimpleInteractiveMenu()
    
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