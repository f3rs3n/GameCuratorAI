"""
Text-based visualization for the headless mode.
This module provides terminal-friendly text visualization for filtering results.
"""

import os
import sys
import textwrap
from typing import Dict, List, Any, Tuple
from colorama import init, Fore, Style, Back

# Initialize colorama for cross-platform color support
init()

class TextVisualizer:
    """Text-based visualization for DAT Filter AI results."""
    
    def __init__(self, use_color: bool = True):
        """
        Initialize the text visualizer
        
        Args:
            use_color: Whether to use colored output (default: True)
        """
        self.use_color = use_color
        self.terminal_width = self._get_terminal_width()
    
    def _get_terminal_width(self) -> int:
        """
        Get the terminal width, with fallback for non-terminal environments
        
        Returns:
            int: Terminal width
        """
        try:
            return os.get_terminal_size().columns
        except (AttributeError, OSError):
            return 80
    
    def _format_text(self, text: str, color: str = "", style: str = "", max_width: int = 0) -> str:
        """
        Format text with color and style
        
        Args:
            text: Text to format
            color: Color to use (from colorama.Fore)
            style: Style to use (from colorama.Style)
            max_width: Maximum width for text wrapping
            
        Returns:
            Formatted text
        """
        if max_width:
            text = textwrap.fill(text, width=max_width)
            
        if not self.use_color:
            return text
            
        formatted = ""
        if color:
            formatted += getattr(Fore, color.upper())
        if style:
            formatted += getattr(Style, style.upper())
            
        formatted += text + Style.RESET_ALL
        return formatted
    
    def print_header(self, text: str, width: int = 0):
        """
        Print a header with decoration
        
        Args:
            text: Header text
            width: Width for the header (default: terminal width)
        """
        if width == 0:
            width = self.terminal_width
        
        print()
        if self.use_color:
            print(Back.BLUE + Fore.WHITE + text.center(width) + Style.RESET_ALL)
        else:
            print(text.center(width))
            print("=" * width)
        print()
    
    def print_section(self, title: str, width: int = 0):
        """
        Print a section title
        
        Args:
            title: Section title
            width: Width for the section (default: terminal width)
        """
        if width == 0:
            width = self.terminal_width
        
        print()
        if self.use_color:
            print(Fore.CYAN + Style.BRIGHT + title + Style.RESET_ALL)
            print(Fore.CYAN + "-" * len(title) + Style.RESET_ALL)
        else:
            print(title)
            print("-" * len(title))
    
    def display_filtering_results(self, 
                               filtered_games: List[Dict[str, Any]], 
                               total_games: int,
                               criteria: List[str]):
        """
        Display filtering results summary
        
        Args:
            filtered_games: List of games that passed the filter
            total_games: Total number of games processed
            criteria: Criteria used for filtering
        """
        self.print_header("DAT Filter AI - Filtering Results")
        
        # Summary statistics
        reduction = total_games - len(filtered_games)
        reduction_pct = (reduction / total_games) * 100 if total_games > 0 else 0
        
        print(self._format_text(f"Original game count: {total_games}", "WHITE", "BRIGHT"))
        print(self._format_text(f"Filtered game count: {len(filtered_games)}", "WHITE", "BRIGHT"))
        
        if reduction > 0:
            status_color = "GREEN"
        else:
            status_color = "YELLOW"
            
        print(self._format_text(
            f"Reduction: {reduction} games ({reduction_pct:.1f}%)", 
            status_color,
            "BRIGHT"
        ))
        
        # Criteria used
        self.print_section("Filter Criteria")
        for criterion in criteria:
            print(f"- {criterion}")
        
        # Display filtered games
        self.print_section("Filtered Games")
        display_count = min(25, len(filtered_games))
        
        for i, game in enumerate(filtered_games[:display_count]):
            game_name = game.get("name", "Unknown")
            print(f"{i+1}. {game_name}")
            
        if len(filtered_games) > display_count:
            print(f"... and {len(filtered_games) - display_count} more games")
    
    def display_special_cases(self, special_cases: Dict[str, Any]):
        """
        Display special cases detected in the collection
        
        Args:
            special_cases: Special cases dictionary from RuleEngine
        """
        if not special_cases:
            return
            
        self.print_header("Special Cases Detected")
        
        # Display multi-disc games
        if "multi_disc" in special_cases and special_cases["multi_disc"]["count"] > 0:
            self.print_section("Multi-Disc Games")
            print(f"Detected {special_cases['multi_disc']['count']} multi-disc game sets")
            
            display_count = min(10, special_cases["multi_disc"]["count"])
            for i, group in enumerate(special_cases["multi_disc"]["groups"][:display_count]):
                base_name = group[0].get("name", "Unknown").split("(")[0].strip()
                print(self._format_text(f"\nGame Set {i+1}: {base_name}", "YELLOW"))
                for disc in group:
                    print(f"  - {disc.get('name', 'Unknown')}")
            
            if special_cases["multi_disc"]["count"] > display_count:
                remaining = special_cases["multi_disc"]["count"] - display_count
                print(f"\n... and {remaining} more multi-disc game sets")
        
        # Display regional variants
        if "regional_variants" in special_cases and special_cases["regional_variants"]["count"] > 0:
            self.print_section("Regional Variants")
            print(f"Detected {special_cases['regional_variants']['count']} games with regional variants")
            
            display_count = min(10, special_cases["regional_variants"]["count"])
            for i, group in enumerate(special_cases["regional_variants"]["groups"][:display_count]):
                base_name = group[0].get("name", "Unknown").split("(")[0].strip()
                print(self._format_text(f"\nGame {i+1}: {base_name}", "YELLOW"))
                for variant in group:
                    print(f"  - {variant.get('name', 'Unknown')}")
            
            if special_cases["regional_variants"]["count"] > display_count:
                remaining = special_cases["regional_variants"]["count"] - display_count
                print(f"\n... and {remaining} more games with regional variants")
                
        # Display mods and hacks
        if "mods_hacks" in special_cases and special_cases["mods_hacks"]["count"] > 0:
            self.print_section("Mods and Hacks")
            print(f"Detected {special_cases['mods_hacks']['count']} game mods and hacks")
            
            display_count = min(10, len(special_cases["mods_hacks"].get("games", [])))
            for i, game in enumerate(special_cases["mods_hacks"].get("games", [])[:display_count]):
                print(f"{i+1}. {game.get('name', 'Unknown')}")
            
            if len(special_cases["mods_hacks"].get("games", [])) > display_count:
                remaining = len(special_cases["mods_hacks"].get("games", [])) - display_count
                print(f"... and {remaining} more mods/hacks")
    
    def display_game_evaluation(self, game: Dict[str, Any], evaluation: Dict[str, Any]):
        """
        Display detailed evaluation for a single game
        
        Args:
            game: Game information dictionary
            evaluation: Evaluation results for the game
        """
        game_name = game.get("name", "Unknown")
        self.print_header(f"Evaluation: {game_name}")
        
        # Game information
        self.print_section("Game Info")
        print(f"Name: {game_name}")
        
        if "description" in game and isinstance(game["description"], dict):
            print(f"Description: {game['description'].get('text', '')}")
            
        if "year" in game and isinstance(game["year"], dict):
            print(f"Year: {game['year'].get('text', '')}")
            
        if "manufacturer" in game and isinstance(game["manufacturer"], dict):
            print(f"Manufacturer: {game['manufacturer'].get('text', '')}")
            
        if "category" in game and isinstance(game["category"], dict):
            print(f"Category: {game['category'].get('text', '')}")
        
        # Evaluation scores
        if "scores" in evaluation:
            self.print_section("Evaluation Scores")
            for criterion, score in evaluation["scores"].items():
                if score > 7:
                    color = "GREEN"
                elif score > 5:
                    color = "YELLOW"
                else:
                    color = "RED"
                    
                print(f"{criterion}: {self._format_text(str(score), color)}")
        
        # Explanations
        if "explanations" in evaluation:
            self.print_section("Explanations")
            for criterion, explanation in evaluation["explanations"].items():
                print(self._format_text(f"{criterion}:", "CYAN"))
                print(self._format_text(explanation, max_width=self.terminal_width - 4))
                print()
        
        # Overall recommendation
        if "overall_recommendation" in evaluation:
            self.print_section("Overall Recommendation")
            
            include = evaluation["overall_recommendation"].get("include", False)
            reason = evaluation["overall_recommendation"].get("reason", "")
            
            if include:
                status = self._format_text("INCLUDE", "GREEN", "BRIGHT")
            else:
                status = self._format_text("EXCLUDE", "RED", "BRIGHT")
                
            print(f"Decision: {status}")
            print(f"Reason: {reason}")