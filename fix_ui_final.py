#!/usr/bin/env python3
"""
Final test script for perfectly aligned borders and content
"""
import sys
import os
from colorama import Fore, Back, Style, init
init(autoreset=True)

def print_fixed_width_frame(width=65):
    """Create a perfectly aligned test frame"""
    # Constants and calculations
    
    # Top border
    print("\n" + "=" * width)
    print("+" + "-" * (width - 2) + "+")
    print("|" + " " * (width - 2) + "|")
    
    # Title - ASCII Art style
    title = [
        "  _____    _  _____   ______ ___ _   _____ _____ ___  ",
        " |  __ \\  / \\|_   _| |  ____|_ _| | |_   _| ____|_ _| ",
        " | |  | |/ _ \\ | |   | |__   | || |   | | |  _|  | |  ",
        " | |  | / ___ \\| |   |  __|  | || |___| | | |___ | |  ",
        " | |__| / /  \\ \\ |_  | |    _| || |____| | |_____|_|  ",
        " |_____/_/    \\_\\__| |_|   |____|_____|_| |_____|___| "
    ]
    
    # Title display with perfect centering
    for line in title:
        spaces_left = (width - 2 - len(line)) // 2
        spaces_right = width - 2 - spaces_left - len(line)
        print("|" + " " * spaces_left + Fore.CYAN + line + Style.RESET_ALL + " " * spaces_right + "|")
    
    # Subtitle with perfect centering
    subtitle = "RETRO GAME COLLECTION CURATOR"
    spaces_left = (width - 2 - len(subtitle)) // 2
    spaces_right = width - 2 - spaces_left - len(subtitle)
    print("|" + " " * spaces_left + Fore.MAGENTA + Style.BRIGHT + subtitle + Style.RESET_ALL + " " * spaces_right + "|")
    print("|" + " " * (width - 2) + "|")
    
    # DAT info display
    monitor_width = 40
    spaces_left = (width - 2 - monitor_width - 2) // 2
    spaces_right = width - 2 - spaces_left - monitor_width - 2
    
    print("|" + " " * spaces_left + "+" + "-" * monitor_width + "+" + " " * spaces_right + "|")
    print("|" + " " * spaces_left + "|" + Fore.WHITE + Style.BRIGHT + " NO DAT FILE LOADED ".center(monitor_width) + Style.RESET_ALL + "|" + " " * spaces_right + "|")
    print("|" + " " * spaces_left + "|" + Fore.BLUE + " --- ".center(monitor_width) + Style.RESET_ALL + "|" + " " * spaces_right + "|")
    print("|" + " " * spaces_left + "+" + "-" * monitor_width + "+" + " " * spaces_right + "|")
    
    print("|" + " " * (width - 2) + "|")
    
    # Engine status display
    engine_status = " ENGINE: RANDOM | THRESHOLD: 1.00 "
    spaces_left = (width - 2 - len(engine_status)) // 2
    spaces_right = width - 2 - spaces_left - len(engine_status)
    print("|" + " " * spaces_left + Fore.GREEN + engine_status + Style.RESET_ALL + " " * spaces_right + "|")
    
    print("|" + " " * (width - 2) + "|")
    
    # Menu separator
    header_text = "SYSTEM COMMANDS"
    divider_char = "="
    inner_width = width - 6
    divider = divider_char * inner_width
    header_spaces = (inner_width - len(header_text)) // 2
    
    header_line = (divider_char * header_spaces) + header_text + (divider_char * (inner_width - header_spaces - len(header_text)))
    print("|  " + divider + "  |")
    print("|  " + Fore.MAGENTA + Style.BRIGHT + header_line + Style.RESET_ALL + "  |")
    print("|  " + divider + "  |")
    
    # Test perfect menu alignments with specific positioning for [UNAVAILABLE]
    menu_options = [
        ("1", "🎮 LOAD DAT FILE", True),
        ("2", "🕹️ APPLY FILTERS", True),
        ("3", "💾 EXPORT RESULTS", True),
        ("4", "⚙️ SETTINGS", False),
        ("5", "📊 BATCH PROCESSING", False),
        ("6", "📈 COMPARE PROVIDERS", False),
        ("0", "🚪 EXIT", False)
    ]
    
    # Find longest menu option for consistent spacing
    max_width = max(len(option[1]) for option in menu_options)
    unavailable_text = "[UNAVAILABLE]"
    
    for key, desc, disabled in menu_options:
        prefix = f" [{key}] "
        
        if disabled:
            # Calculate a fixed position for the [UNAVAILABLE] text
            unavailable_position = width - len(unavailable_text) - 5  # 5 spaces from right border
            desc_spaces = unavailable_position - len(prefix) - 2  # -2 for buffer space
            
            # Create the line with exact positioning
            line = prefix + desc.ljust(desc_spaces) + unavailable_text
            spaces_right = width - 6 - len(line)
            
            print("|  " + Fore.YELLOW + prefix + desc.ljust(desc_spaces) + Fore.RED + unavailable_text + Style.RESET_ALL + " " * spaces_right + "  |")
        else:
            # Regular menu items aligned to match the position of unavailable items
            spaces = width - 6 - len(prefix) - len(desc)
            print("|  " + Fore.YELLOW + prefix + desc + Style.RESET_ALL + " " * spaces + "  |")
    
    # Bottom border
    print("|" + " " * (width - 2) + "|")
    print("|" + "_" * (width - 2) + "|")
    print("+" + "-" * (width - 2) + "+")
    print("=" * width + "\n")

if __name__ == "__main__":
    print_fixed_width_frame()