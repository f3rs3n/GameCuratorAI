#!/usr/bin/env python3
"""
Test script for precisely aligned borders and content
"""
import sys
import os
from colorama import Fore, Back, Style, init
init(autoreset=True)

def print_fixed_width_frame(width=65):
    """Create a perfectly aligned test frame"""
    # Constants and calculations
    padding = 2
    content_width = width - (padding * 2)
    
    # Top border with game console style
    print("\n" + "=" * width)
    print("+" + "-" * (width - 2) + "+")
    print("|" + " " * (width - 2) + "|")
    
    # Title - ASCII Art style (simplified for consistency)
    title = [
        "  _____    _  _____   ______ ___ _   _____ _____ ___  ",
        " |  __ \\  / \\|_   _| |  ____|_ _| | |_   _| ____|_ _| ",
        " | |  | |/ _ \\ | |   | |__   | || |   | | |  _|  | |  ",
        " | |  | / ___ \\| |   |  __|  | || |___| | | |___ | |  ",
        " | |__| / /  \\ \\ |_  | |    _| || |____| | |_____|_|  ",
        " |_____/_/    \\_\\__| |_|   |____|_____|_| |_____|___| "
    ]
    
    # Title width calculation
    title_width = len(title[0])
    display_width = min(title_width, width - 6)
    
    # Print title
    for line in title:
        if title_width > display_width:
            adjusted_line = line[:display_width]
        else:
            adjusted_line = line.ljust(display_width)
        
        # Exact spacing calculation
        spaces_left = (width - 2 - len(adjusted_line)) // 2
        spaces_right = width - 2 - spaces_left - len(adjusted_line)
        print("|" + " " * spaces_left + Fore.CYAN + adjusted_line + Style.RESET_ALL + " " * spaces_right + "|")
    
    # Subtitle - precise center alignment
    subtitle = "RETRO GAME COLLECTION CURATOR"
    spaces_left = (width - 2 - len(subtitle)) // 2
    spaces_right = width - 2 - spaces_left - len(subtitle)
    print("|" + " " * spaces_left + Fore.MAGENTA + Style.BRIGHT + subtitle + Style.RESET_ALL + " " * spaces_right + "|")
    print("|" + " " * (width - 2) + "|")
    
    # DAT info display - simplified border with perfect alignment
    monitor_width = 40
    spaces_left = (width - 2 - monitor_width - 2) // 2
    spaces_right = width - 2 - spaces_left - monitor_width - 2
    
    print("|" + " " * spaces_left + "+" + "-" * monitor_width + "+" + " " * spaces_right + "|")
    print("|" + " " * spaces_left + "|" + Fore.WHITE + Style.BRIGHT + " NO DAT FILE LOADED ".center(monitor_width) + Style.RESET_ALL + "|" + " " * spaces_right + "|")
    print("|" + " " * spaces_left + "|" + Fore.BLUE + " --- ".center(monitor_width) + Style.RESET_ALL + "|" + " " * spaces_right + "|")
    print("|" + " " * spaces_left + "+" + "-" * monitor_width + "+" + " " * spaces_right + "|")
    
    print("|" + " " * (width - 2) + "|")
    
    # Engine status display - precise center alignment
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
    
    # Menu options with fixed width display
    menu_options = [
        ("1", "🎮 LOAD DAT FILE", True),
        ("2", "🕹️ APPLY FILTERS", True),
        ("3", "💾 EXPORT RESULTS", True),
        ("4", "⚙️ SETTINGS", False),
        ("5", "📊 BATCH PROCESSING", False),
        ("6", "📈 COMPARE PROVIDERS", False),
        ("0", "🚪 EXIT", False)
    ]
    
    for key, desc, disabled in menu_options:
        if disabled:
            # Get width of the content part only
            prefix = f" [{key}] "
            unavailable_text = "[UNAVAILABLE]"
            
            # Calculate available space for description
            desc_width = width - 6 - len(prefix) - len(unavailable_text) - 1
            if len(desc) > desc_width:
                desc_text = desc[:desc_width-3] + "..."
            else:
                desc_text = desc
            
            # Pad to exact width
            total_content = prefix + desc_text + " " * (desc_width - len(desc_text)) + unavailable_text
            total_spaces = width - 6 - len(total_content)
            print("|  " + Fore.YELLOW + prefix + desc_text + " " * (desc_width - len(desc_text)) + Fore.RED + unavailable_text + Style.RESET_ALL + " " * total_spaces + "  |")
        else:
            option_text = f" [{key}] {desc}"
            spaces = width - 6 - len(option_text)
            print("|  " + Fore.YELLOW + option_text + Style.RESET_ALL + " " * spaces + "  |")
    
    # Bottom border
    print("|" + " " * (width - 2) + "|")
    print("|" + "_" * (width - 2) + "|")
    print("+" + "-" * (width - 2) + "+")
    print("=" * width + "\n")

if __name__ == "__main__":
    print_fixed_width_frame()