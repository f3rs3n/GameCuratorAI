#!/usr/bin/env python
"""
DAT Filter AI - Simple Interactive CLI Interface
A minimalist text-based menu interface for the DAT Filter AI tool
that works with minimal dependencies.
"""

import os
import sys
import time
import subprocess
from typing import List, Dict, Any

# Check for colorama
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # Define dummy color classes
    class DummyFore:
        CYAN = ''
        GREEN = ''
        YELLOW = ''
        RED = ''
        BLUE = ''
        MAGENTA = ''
        WHITE = ''
    
    class DummyStyle:
        BRIGHT = ''
        NORMAL = ''
    
    Fore = DummyFore()
    Style = DummyStyle()

class SimpleInteractiveMenu:
    """Simplified interactive text-based menu for DAT Filter AI"""
    
    def __init__(self):
        """Initialize the interactive menu"""
        self.running = True
        
        # Application settings
        self.settings = {
            'provider': 'random',
            'batch_size': 10,
            'criteria': ['metacritic', 'historical', 'v_list', 'console_significance', 'mods_hacks'],
            'input_dir': 'test_input',
            'output_dir': 'test_output',
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
            },
            'retro': {
                'header': Fore.MAGENTA + Style.BRIGHT,
                'option': Fore.YELLOW,
                'highlight': Fore.CYAN + Style.BRIGHT,
                'error': Fore.RED + Style.BRIGHT,
                'success': Fore.GREEN + Style.BRIGHT,
                'info': Fore.BLUE,
                'data': Fore.WHITE,
            },
        }
        
        self.current_theme = self.themes[self.settings['theme']]
    
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
            self._print_header("DAT Filter AI - Simple Interactive CLI")
            
            # Print current status
            self._print_info("Simple mode - Limited functionality")
            self._print_info("Install required dependencies for full features")
            
            print()
            self._print_option("1", "Check Dependencies")
            self._print_option("2", "Install Dependencies")
            self._print_option("3", "Run Interactive Mode")
            self._print_option("4", "Run GUI Mode")
            self._print_option("5", "Run Headless Mode")
            self._print_option("6", "Settings")
            self._print_option("0", "Exit")
            
            choice = self._get_user_input("Enter your choice")
            
            if choice == "1":
                self.check_dependencies()
            elif choice == "2":
                self.install_dependencies()
            elif choice == "3":
                self.run_interactive()
            elif choice == "4":
                self.run_gui()
            elif choice == "5":
                self.run_headless()
            elif choice == "6":
                self.settings_menu()
            elif choice == "0":
                self.running = False
            else:
                self._print_error("Invalid choice")
                self._wait_for_key()
    
    def check_dependencies(self):
        """Check dependencies"""
        self._clear_screen()
        self._print_header("Checking Dependencies")
        
        # Required modules
        required_modules = [
            "colorama",
            "openai", 
            "google.generativeai"
        ]
        
        # Optional modules
        optional_modules = [
            "PyQt5.QtWidgets"
        ]
        
        # Check required modules
        self._print_subheader("Required Modules")
        all_required_installed = True
        
        for module_name in required_modules:
            try:
                __import__(module_name.split('.')[0])
                self._print_success(f"{module_name}: Installed")
            except ImportError:
                all_required_installed = False
                self._print_error(f"{module_name}: Not installed")
        
        # Check optional modules
        self._print_subheader("Optional Modules")
        all_optional_installed = True
        
        for module_name in optional_modules:
            try:
                __import__(module_name.split('.')[0])
                self._print_success(f"{module_name}: Installed")
            except ImportError:
                all_optional_installed = False
                self._print_error(f"{module_name}: Not installed")
        
        print()
        if all_required_installed:
            self._print_success("All required dependencies are installed!")
        else:
            self._print_error("Some required dependencies are missing.")
            self._print_info("You can install them with option 2 from the main menu.")
        
        if not all_optional_installed:
            self._print_info("Some optional dependencies are missing.")
            self._print_info("The GUI will not work without PyQt5.")
        
        self._wait_for_key()
    
    def install_dependencies(self):
        """Install dependencies"""
        self._clear_screen()
        self._print_header("Install Dependencies")
        
        # Ask which dependencies to install
        self._print_subheader("Available Packages")
        self._print_option("1", "Required dependencies (colorama, openai, google-generativeai)")
        self._print_option("2", "GUI dependencies (PyQt5)")
        self._print_option("3", "All dependencies")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "0":
            return
        
        # Build pip command
        packages = []
        
        if choice in ("1", "3"):
            packages.extend(["colorama", "openai", "google-generativeai"])
        
        if choice in ("2", "3"):
            packages.append("PyQt5")
        
        if not packages:
            self._print_error("Invalid choice")
            self._wait_for_key()
            return
        
        # Run pip install
        self._print_info(f"Installing packages: {', '.join(packages)}")
        print()
        
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + packages
            subprocess.check_call(cmd)
            self._print_success("Packages installed successfully!")
        except subprocess.CalledProcessError as e:
            self._print_error(f"Error installing packages: {e}")
        
        self._wait_for_key()
    
    def run_interactive(self):
        """Run interactive mode"""
        self._clear_screen()
        self._print_header("Run Interactive Mode")
        
        self._print_info("Starting interactive mode...")
        print()
        
        try:
            cmd = [sys.executable, "interactive.py"]
            subprocess.call(cmd)
        except Exception as e:
            self._print_error(f"Error running interactive mode: {e}")
        
        self._print_info("Returned to simple menu")
        self._wait_for_key()
    
    def run_gui(self):
        """Run GUI mode"""
        self._clear_screen()
        self._print_header("Run GUI Mode")
        
        # Check if PyQt5 is installed
        try:
            __import__("PyQt5.QtWidgets")
        except ImportError:
            self._print_error("PyQt5 is not installed")
            self._print_info("Please install it first from the 'Install Dependencies' menu")
            self._wait_for_key()
            return
        
        self._print_info("Starting GUI mode...")
        print()
        
        try:
            cmd = [sys.executable, "main.py"]
            subprocess.call(cmd)
        except Exception as e:
            self._print_error(f"Error running GUI mode: {e}")
        
        self._print_info("Returned to simple menu")
        self._wait_for_key()
    
    def run_headless(self):
        """Run headless mode"""
        self._clear_screen()
        self._print_header("Run Headless Mode")
        
        # Check if required dependencies are installed
        try:
            __import__("colorama")
        except ImportError:
            self._print_error("Colorama is not installed")
            self._print_info("Please install it first from the 'Install Dependencies' menu")
            self._wait_for_key()
            return
        
        # Input file selection
        self._print_subheader("Select Input File")
        
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
                input_file = os.path.join(input_dir, dat_files[idx])
                
                # Output file
                output_file = self._get_user_input("Output file name", f"filtered_{dat_files[idx]}")
                output_path = os.path.join(self.settings['output_dir'], output_file)
                
                # Provider selection
                self._print_subheader("Select AI Provider")
                self._print_option("1", "Random (no API key needed)")
                self._print_option("2", "OpenAI (requires API key)")
                self._print_option("3", "Gemini (requires API key)")
                
                provider_choice = self._get_user_input("Enter your choice", "1")
                
                if provider_choice == "1":
                    provider = "random"
                elif provider_choice == "2":
                    provider = "openai"
                elif provider_choice == "3":
                    provider = "gemini"
                else:
                    provider = "random"
                
                # Batch size
                batch_size = self._get_user_input("Batch size (1-50)", str(self.settings['batch_size']))
                try:
                    batch_size = int(batch_size)
                    if batch_size < 1 or batch_size > 50:
                        batch_size = 10
                except ValueError:
                    batch_size = 10
                
                # Run headless.py
                self._print_info(f"Running headless mode with {provider} provider...")
                print()
                
                # Report file
                report_file = self._get_user_input("Report file name", f"report_{os.path.splitext(output_file)[0]}.json")
                report_path = os.path.join(self.settings['output_dir'], report_file)
                
                # Summary file
                summary_file = self._get_user_input("Summary file name", f"summary_{os.path.splitext(output_file)[0]}.txt")
                summary_path = os.path.join(self.settings['output_dir'], summary_file)
                
                try:
                    cmd = [
                        sys.executable, 
                        "headless.py",
                        "--input", input_file,
                        "--output", output_path,
                        "--provider", provider,
                        "--report", report_path,
                        "--summary", summary_path,
                        "--batch-size", str(batch_size)
                    ]
                    subprocess.call(cmd)
                except Exception as e:
                    self._print_error(f"Error running headless mode: {e}")
            else:
                self._print_error("Invalid choice")
        except ValueError:
            self._print_error("Please enter a number")
        
        self._wait_for_key()
    
    def settings_menu(self):
        """Display the settings menu"""
        self._clear_screen()
        self._print_header("Settings")
        
        # Display current settings
        self._print_subheader("Current Settings")
        self._print_data("Input Directory", self.settings['input_dir'])
        self._print_data("Output Directory", self.settings['output_dir'])
        self._print_data("Theme", self.settings['theme'])
        
        print()
        self._print_option("1", "Change Input Directory")
        self._print_option("2", "Change Output Directory")
        self._print_option("3", "Change Theme")
        self._print_option("0", "Back to Main Menu")
        
        choice = self._get_user_input("Enter your choice")
        
        if choice == "1":
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
        elif choice == "2":
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
        elif choice == "3":
            self._change_theme()
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


def main():
    """Main entry point for the simple interactive menu"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="DAT Filter AI - Simple Interactive CLI")
    parser.add_argument("--theme", help="UI theme (default, retro)", default="default")
    args = parser.parse_args()
    
    # Initialize the menu
    menu = SimpleInteractiveMenu()
    
    # Set theme if specified
    if args.theme in menu.themes:
        menu.settings['theme'] = args.theme
        menu.current_theme = menu.themes[args.theme]
    
    # Start the main menu
    try:
        menu.main_menu()
    except KeyboardInterrupt:
        print("\nExiting DAT Filter AI - Simple Interactive CLI")
        sys.exit(0)


if __name__ == "__main__":
    main()