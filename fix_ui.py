#!/usr/bin/env python3
"""
Test script for fixing the UI border alignment issues
"""
import os
import sys
from colorama import Fore, Back, Style, init
init(autoreset=True)

def show_test_ui():
    """Show a test UI with fixed border alignment"""
    # Constants for UI
    width = 70
    padding = 2
    content_width = width - (padding * 2)
    
    # Top border with game console style
    print("\n" + "=" * width)
    print("┌" + "─" * (width - 2) + "┐")
    print("│" + " " * (width - 2) + "│")
    
    # Title - ASCII Art style (simplified for test)
    title = [
        "██████╗  █████╗ ████████╗    ███████╗██╗██╗  ████████╗███████╗██████╗ ",
        "██╔══██╗██╔══██╗╚══██╔══╝    ██╔════╝██║██║  ╚══██╔══╝██╔════╝██╔══██╗"
    ]
    
    title_width = len(title[0])
    # Fix title width if wider than the frame
    display_width = min(title_width, width - 4)
    
    for line in title:
        # Center the title consistently with proper padding for borders
        if title_width > display_width:
            # Truncate if title too long
            adjusted_line = line[:display_width]
        else:
            # Pad if title shorter than display width
            adjusted_line = line
        
        space = (width - display_width - 2) // 2
        print("│" + " " * space + Fore.CYAN + adjusted_line + Style.RESET_ALL + " " * (width - space - display_width - 2) + "│")
    
    # Subtitle with proper centering
    subtitle = "RETRO GAME COLLECTION CURATOR"
    space = (width - len(subtitle) - 2) // 2
    if space < 0: space = 0
    print("│" + " " * space + Fore.MAGENTA + Style.BRIGHT + subtitle + Style.RESET_ALL + " " * (width - space - len(subtitle) - 2) + "│")
    print("│" + " " * (width - 2) + "│")
    
    # Monitor display for DAT info
    dat_info = " NO DAT FILE LOADED "
    filtered_info = " --- "
    
    # Calculate monitor width with proper alignment
    monitor_width = min(max(len(dat_info), len(filtered_info)) + 6, content_width)
    # Ensure even width for better visual symmetry
    if monitor_width % 2 != 0:
        monitor_width += 1
    # Ensure it's not wider than the frame
    monitor_width = min(monitor_width, width - 6)
    
    # Calculate left space to center the monitor
    space_left = (width - monitor_width - 2) // 2
    
    # Draw monitor with perfectly aligned borders
    print("│" + " " * space_left + "╔" + "═" * monitor_width + "╗" + " " * (width - space_left - monitor_width - 3) + "│")
    print("│" + " " * space_left + "║" + Fore.WHITE + Style.BRIGHT + dat_info.center(monitor_width) + Style.RESET_ALL + "║" + " " * (width - space_left - monitor_width - 3) + "│")
    print("│" + " " * space_left + "║" + Fore.BLUE + filtered_info.center(monitor_width) + Style.RESET_ALL + "║" + " " * (width - space_left - monitor_width - 3) + "│")
    print("│" + " " * space_left + "╚" + "═" * monitor_width + "╝" + " " * (width - space_left - monitor_width - 3) + "│")
    
    print("│" + " " * (width - 2) + "│")
    
    # Settings bar
    engine_status = " ENGINE: RANDOM │ THRESHOLD: 1.00 "
    space_left = (width - len(engine_status) - 2) // 2
    print("│" + " " * space_left + Fore.GREEN + engine_status + Style.RESET_ALL + " " * (width - space_left - len(engine_status) - 2) + "│")
    
    print("│" + " " * (width - 2) + "│")
    
    # Menu options with retro gaming icons
    menu_divider = "=" * (width - 4)
    menu_header = " SYSTEM COMMANDS "
    menu_header_padding = (width - 4 - len(menu_header)) // 2
    menu_header_display = "=" * menu_header_padding + menu_header + "=" * menu_header_padding
    # Adjust if odd length
    if len(menu_header_display) < width - 4:
        menu_header_display += "="
    
    print("│  " + menu_divider + "  │")
    print("│  " + Fore.MAGENTA + Style.BRIGHT + menu_header_display + Style.RESET_ALL + "  │")
    print("│  " + menu_divider + "  │")
    
    # Menu options
    menu_options = [
        ("1", "🎮 LOAD DAT FILE", True),
        ("2", "🕹️ APPLY FILTERS", True),
        ("3", "💾 EXPORT RESULTS", True),
        ("4", "⚙️ SETTINGS", False),
        ("5", "📊 BATCH PROCESSING", False),
        ("0", "🚪 EXIT", False)
    ]
    
    for key, desc, disabled in menu_options:
        if disabled:
            option_text = f" [{key}] {desc} " + Fore.RED + "[UNAVAILABLE]" + Style.RESET_ALL
        else:
            option_text = f" [{key}] {desc}"
        
        print("│  " + Fore.YELLOW + option_text.ljust(width - 6) + Style.RESET_ALL + "  │")
    
    # Bottom of the console - ensure proper alignment
    print("│" + " " * (width - 2) + "│")
    print("│" + "_" * (width - 2) + "│")
    print("└" + "─" * (width - 2) + "┘")
    print("=" * width)

if __name__ == "__main__":
    show_test_ui()