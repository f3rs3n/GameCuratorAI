"""
Export module for saving filtered game collections and results.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom
from utils.api_usage_tracker import get_tracker

class ExportManager:
    """Manager for exporting filtered game collections and results."""
    
    def __init__(self):
        """Initialize the export manager."""
        self.logger = logging.getLogger(__name__)
    
    def export_dat_file(self, 
                       filtered_games: List[Dict[str, Any]], 
                       original_data: Dict[str, Any],
                       output_path: str,
                       metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Export filtered games as a DAT file, preserving the original XML structure
        
        Args:
            filtered_games: List of filtered game entries
            original_data: Original parsed DAT file data
            output_path: Path to save the filtered DAT file
            metadata: Optional metadata to include in the header
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract original structure
            original_structure = original_data.get('original_structure', {})
            
            if not original_structure:
                return False, "Original DAT structure not available"
            
            # Create a new root element
            root_tag = original_structure.get('root_tag', 'datafile')
            root_attrib = original_structure.get('root_attrib', {})
            
            root = ET.Element(root_tag, attrib=root_attrib)
            
            # Recreate header
            if 'header' in original_structure and original_structure['header']:
                header_element = ET.SubElement(root, 'header')
                
                # Update header with filtering metadata
                header_data = original_structure['header'].copy()
                
                # Add filtering metadata
                if metadata:
                    header_data.update(metadata)
                
                # Add timestamp and filter info
                now = datetime.datetime.now()
                header_data['filtered_date'] = now.strftime('%Y-%m-%d')
                header_data['filtered_time'] = now.strftime('%H:%M:%S')
                header_data['filtered_games_count'] = str(len(filtered_games))
                header_data['original_games_count'] = str(original_data.get('game_count', 0))
                
                for key, value in header_data.items():
                    if value is not None:
                        header_child = ET.SubElement(header_element, key)
                        header_child.text = str(value)
            
            # Find parent tag for games
            games_parent_tag = original_structure.get('games_parent_tag', 'datafile')
            
            # If games are not direct children of root, create parent element
            if games_parent_tag != root_tag:
                games_parent = ET.SubElement(root, games_parent_tag)
            else:
                games_parent = root
            
            # Add filtered games to the structure
            for game in filtered_games:
                if '_xml' in game:
                    # Parse the stored XML representation
                    game_element = ET.fromstring(game['_xml'])
                    games_parent.append(game_element)
                else:
                    # If for some reason we don't have the original XML, 
                    # try to reconstruct the element
                    self._reconstruct_game_element(game, games_parent)
            
            # Convert to string with proper formatting
            rough_string = ET.tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Remove empty lines within elements
            pretty_xml = self._clean_xml_output(pretty_xml)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            self.logger.info(f"Successfully exported filtered DAT with {len(filtered_games)} games to {output_path}")
            return True, f"Successfully exported {len(filtered_games)} games to {output_path}"
            
        except Exception as e:
            error_msg = f"Error exporting filtered DAT file: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _clean_xml_output(self, xml_string: str) -> str:
        """
        Clean XML output to remove empty lines and excessive whitespace within elements
        
        Args:
            xml_string: XML string to clean
            
        Returns:
            Cleaned XML string
        """
        import re
        
        # First pass: Use a more aggressive regex to remove all empty lines between tags
        # This pattern matches any amount of whitespace and newlines between tags
        pattern = r'>\s*\n+\s*<'
        replacement = '>\n<'
        xml_string = re.sub(pattern, replacement, xml_string)
        
        # Handle specific patterns for game elements
        xml_string = re.sub(r'<game([^>]*)>\s*\n+\s*', r'<game\1>\n  ', xml_string)
        xml_string = re.sub(r'</rom>\s*\n+\s*</game>', r'</rom>\n</game>', xml_string)
        
        # Second pass: Process line by line for more control
        lines = xml_string.splitlines()
        cleaned_lines = []
        in_game_element = False
        prev_line_empty = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Track when we're inside a game element
            if '<game ' in stripped:
                in_game_element = True
                prev_line_empty = False
            elif '</game>' in stripped:
                in_game_element = False
                prev_line_empty = False
            
            # Handle empty lines
            if not stripped:
                # Only keep empty lines outside of game elements
                # or if they're structural (not consecutive)
                if not in_game_element and not prev_line_empty:
                    cleaned_lines.append(line)
                    prev_line_empty = True
                continue
            
            # Reset empty line tracker on non-empty lines
            prev_line_empty = False
            
            # Always add non-empty lines
            cleaned_lines.append(line)
        
        # Final pass: Do another regex cleanup on the joined result
        # to catch any remaining issues
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'(<game[^>]*>)\s*\n+\s*', r'\1\n  ', result)
        result = re.sub(r'\n\s*\n+\s*(<[^/])', r'\n\1', result)
        
        return result
    
    def _reconstruct_game_element(self, game: Dict[str, Any], parent: ET.Element):
        """
        Reconstruct a game element from a dictionary when original XML is not available
        
        Args:
            game: Game dictionary
            parent: Parent element to attach the reconstructed game element
        """
        game_tag = game.get('tag', 'game')
        game_attrib = game.get('attrib', {})
        
        game_element = ET.SubElement(parent, game_tag, attrib=game_attrib)
        
        # Add known fields
        for key, value in game.items():
            # Skip metadata and special fields
            if key.startswith('_') or key in ['tag', 'attrib']:
                continue
            
            # Handle dictionary values (complex elements)
            if isinstance(value, dict):
                if 'text' in value or 'attrib' in value:
                    child = ET.SubElement(game_element, key, attrib=value.get('attrib', {}))
                    if 'text' in value and value['text'] is not None:
                        child.text = value['text']
                    
                    # Handle nested children
                    if 'children' in value and isinstance(value['children'], list):
                        for subchild_data in value['children']:
                            if 'tag' in subchild_data:
                                subchild = ET.SubElement(child, subchild_data['tag'], 
                                                      attrib=subchild_data.get('attrib', {}))
                                if 'text' in subchild_data and subchild_data['text'] is not None:
                                    subchild.text = subchild_data['text']
                else:
                    # Handle other dictionary values
                    child = ET.SubElement(game_element, key)
                    child.text = json.dumps(value)
            else:
                # Handle simple values
                child = ET.SubElement(game_element, key)
                child.text = str(value)
    
    def export_json_report(self, 
                          filtered_games: List[Dict[str, Any]], 
                          evaluations: List[Dict[str, Any]],
                          special_cases: Dict[str, Any],
                          output_path: str) -> Tuple[bool, str]:
        """
        Export a detailed JSON report of the filtering process
        
        Args:
            filtered_games: List of filtered game entries
            evaluations: List of game evaluations
            special_cases: Dictionary of detected special cases
            output_path: Path to save the JSON report
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create report structure
            report = {
                "timestamp": datetime.datetime.now().isoformat(),
                "filtered_games_count": len(filtered_games),
                "evaluations_count": len(evaluations),
                "special_cases": special_cases,
                "filtered_games": [
                    {
                        "name": game.get("name", "Unknown"),
                        "id": game.get("id", game.get("name", "Unknown")),
                        "evaluation": game.get("_evaluation", {})
                    }
                    for game in filtered_games
                ]
            }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Successfully exported JSON report to {output_path}")
            return True, f"Successfully exported report to {output_path}"
            
        except Exception as e:
            error_msg = f"Error exporting JSON report: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def export_text_summary(self, 
                           filtered_games: List[Dict[str, Any]], 
                           original_count: int,
                           filter_criteria: List[str],
                           output_path: str,
                           provider_name: str = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Export a human-readable text summary of the filtering results
        
        Args:
            filtered_games: List of filtered game entries
            original_count: Number of games in the original collection
            filter_criteria: List of filtering criteria used
            output_path: Path to save the text summary
            provider_name: Name of the AI provider used
            metadata: Optional metadata containing original evaluations for near-miss games
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create summary text
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            summary = [
                "DAT Filter AI - Filtering Summary",
                "==============================",
                f"Date: {now}",
                f"Original game count: {original_count}",
                f"Filtered game count: {len(filtered_games)}",
                f"Reduction: {original_count - len(filtered_games)} games ({100 * (original_count - len(filtered_games)) / original_count:.1f}% of collection)",
                "",
                "Filter Criteria:",
                "---------------"
            ]
            
            for criterion in filter_criteria:
                summary.append(f"- {criterion}")
            
            # Calculate proportional display size - show 10% of the collection size but min 5, max 30 games
            display_count = max(5, min(30, int(len(filtered_games) * 0.1)))
            
            # Collect near-miss games (those that didn't make the cut but were close)
            near_miss_games = []
            excluded_games_with_scores = []
            
            # Try to get info about games that didn't make the cut
            # These are typically excluded games that were close to qualifying
            # This involves fetching data from the original game evaluations
            if metadata is not None and 'original_evaluations' in metadata and metadata['original_evaluations']:
                # Extract all games that were evaluated but not included
                original_evals = metadata['original_evaluations']
                
                # List of all included game names for fast lookup
                included_names = {game.get('name', '').strip() for game in filtered_games}
                
                # Find near-miss games - games that were evaluated but didn't make the cut
                for eval_data in original_evals:
                    if 'name' in eval_data and eval_data['name'].strip() not in included_names:
                        score = 0
                        if 'overall_score' in eval_data:
                            try:
                                score = float(eval_data['overall_score'])
                            except (ValueError, TypeError):
                                continue
                        
                        # Create a simpler game object with just the evaluation data
                        near_miss_game = {
                            'name': eval_data['name'],
                            '_evaluation': eval_data
                        }
                        excluded_games_with_scores.append((near_miss_game, score))
                
                # Sort excluded games by score descending to get "near miss" games first
                excluded_games_with_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Take top N excluded games as "near miss" games
                near_miss_count = min(display_count, len(excluded_games_with_scores))
                near_miss_games = [game for game, score in excluded_games_with_scores[:near_miss_count]]
            
            # Get games that were excluded
            excluded_count = original_count - len(filtered_games)
            
            # Analyze criteria strength/weakness for the top games
            strengths_count = {}
            weaknesses_count = {}
            low_score_keepers = 0
            
            # Initialize counters using the filter_criteria argument
            for criterion in filter_criteria:
                strengths_count[criterion] = 0
                weaknesses_count[criterion] = 0
            
            # Analyze criteria in the filtered games
            for game in filtered_games:
                if "_evaluation" in game and "_criteria_analysis" in game["_evaluation"]:
                    analysis = game["_evaluation"]["_criteria_analysis"]
                    
                    # Count strengths
                    for criterion in analysis.get("strongest_criteria", []):
                        if criterion in strengths_count:
                            strengths_count[criterion] += 1
                    
                    # Count weaknesses
                    for criterion in analysis.get("weakest_criteria", []):
                        if criterion in weaknesses_count:
                            weaknesses_count[criterion] += 1
                    
                    # Count low score keepers
                    if analysis.get("is_low_score_keeper", False):
                        low_score_keepers += 1
            
            # Add criteria analysis section
            if any(strengths_count.values()):
                summary.extend([
                    "",
                    "Criteria Analysis:",
                    "-----------------"
                ])
                
                # Show criteria strengths
                summary.append("Strongest criteria in the collection:")
                for criterion in sorted(strengths_count.keys(), key=lambda x: strengths_count[x], reverse=True):
                    if strengths_count[criterion] > 0:
                        pct = (strengths_count[criterion] / len(filtered_games)) * 100
                        summary.append(f"- {criterion.replace('_', ' ').title()}: {strengths_count[criterion]} games ({pct:.1f}%)")
                
                # Show criteria weaknesses
                summary.append("\nWeakest criteria in the collection:")
                for criterion in sorted(weaknesses_count.keys(), key=lambda x: weaknesses_count[x], reverse=True):
                    if weaknesses_count[criterion] > 0:
                        pct = (weaknesses_count[criterion] / len(filtered_games)) * 100
                        summary.append(f"- {criterion.replace('_', ' ').title()}: {weaknesses_count[criterion]} games ({pct:.1f}%)")
                
                # Show low score keepers if any
                if low_score_keepers > 0:
                    pct = (low_score_keepers / len(filtered_games)) * 100
                    summary.append(f"\nLow Score Exceptions: {low_score_keepers} games ({pct:.1f}%)")
                    summary.append("These are games kept despite low scores due to other important factors.")
            
            # This section previously contained the "Highest Scoring Games" listing
            # It has been removed as it's no longer relevant with the new filtering approach
            # that keeps games that match ANY criterion, rather than based on overall scores
            
            # Add Near Miss Games Section - these are games that just missed the cut
            if near_miss_games:
                summary.extend([
                    "",
                    f"Near Miss Games ({len(near_miss_games)}):",
                    "----------------------------------------",
                    "These games were close to making the cut but fell just short:"
                ])
                
                # Add near miss games with their scores and analysis
                for i, game in enumerate(near_miss_games):
                    score = 0
                    eval_data = game.get('_evaluation', {})
                    if eval_data and 'overall_score' in eval_data:
                        score = float(eval_data['overall_score'])
                    
                    game_line = f"{i+1}. {game.get('name', 'Unknown')} - Score: {score:.2f}/10"
                    
                    # Add strengths/weaknesses if available in the evaluation data
                    if eval_data and '_criteria_analysis' in eval_data:
                        analysis = eval_data['_criteria_analysis']
                        strengths = analysis.get('strongest_criteria', [])
                        weaknesses = analysis.get('weakest_criteria', [])
                        
                        if strengths:
                            strengths_str = ", ".join([s.replace("_", " ").title() for s in strengths])
                            game_line += f" - Strong: {strengths_str}"
                        
                        if weaknesses:
                            weaknesses_str = ", ".join([w.replace("_", " ").title() for w in weaknesses])
                            game_line += f" - Weak: {weaknesses_str}"
                    
                    summary.append(game_line)
            
            # Only show removed games section if we have excluded games
            if excluded_count > 0:
                summary.extend([
                    "",
                    f"Removed Games Summary:",
                    "----------------------------------------",
                    f"These games didn't make the cut and were removed from the filtered collection:"
                ])
                
                # Since we don't have the full removed games list directly, we'll include a note
                summary.append(f"Total games removed: {excluded_count}")
                summary.append("")
                summary.append("Note: To see the complete list of removed games, compare the original DAT")
                summary.append("      file with the filtered output using a comparison tool.")
            
            # Add API usage information for all providers
            try:
                # Include API usage section for all providers (even random)
                summary.extend([
                    "",
                    "API Usage Information:",
                    "----------------------",
                    f"Provider: {provider_name.upper() if provider_name else 'UNKNOWN'}"
                ])
                
                # Add specific provider information
                if provider_name and provider_name.lower() == "random":
                    summary.extend([
                        "Random provider does not use external API tokens.",
                        "It's recommended only for testing purposes only.",
                        "Total requests: 0 (No API calls needed)"
                    ])
                elif provider_name:
                    provider_name_lower = provider_name.lower()
                    usage_tracker = get_tracker()
                    usage_report = usage_tracker.get_usage_report(provider_name_lower, days=30)
                    
                    # Calculate tokens for today and last 30 days
                    today_tokens = 0
                    month_tokens = 0
                    total_requests = 0
                    
                    # Access provider data directly to get today's usage
                    today = datetime.datetime.now().strftime('%Y-%m-%d')
                    provider_data = usage_tracker.usage_data.get(provider_name_lower, {})
                    
                    # Get today's tokens from daily usage
                    if "daily_usage" in provider_data and today in provider_data["daily_usage"]:
                        today_tokens = provider_data["daily_usage"][today].get("tokens", 0)
                    
                    # Get monthly tokens from the report
                    if provider_name_lower in usage_report:
                        month_tokens = usage_report[provider_name_lower].get("last_30_days_tokens", 0)
                        total_requests = usage_report[provider_name_lower].get("total_requests", 0)
                    
                    summary.extend([
                        f"Today's usage: {today_tokens:,} tokens",
                        f"30-day usage: {month_tokens:,} tokens",
                        f"Total requests: {total_requests:,}"
                    ])
            except Exception as e:
                self.logger.warning(f"Failed to add API usage information: {e}")
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary))
            
            self.logger.info(f"Successfully exported text summary to {output_path}")
            return True, f"Successfully exported summary to {output_path}"
            
        except Exception as e:
            error_msg = f"Error exporting text summary: {e}"
            self.logger.error(error_msg)
            return False, error_msg
