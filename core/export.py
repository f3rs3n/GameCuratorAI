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
                           output_path: str) -> Tuple[bool, str]:
        """
        Export a human-readable text summary of the filtering results
        
        Args:
            filtered_games: List of filtered game entries
            original_count: Number of games in the original collection
            filter_criteria: List of filtering criteria used
            output_path: Path to save the text summary
            
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
            
            # Get top games (highest scores)
            top_games = []
            near_miss_games = []
            worst_games = []
            
            # Sort games by quality score if available
            games_with_scores = []
            for game in filtered_games:
                score = 0
                eval_data = game.get('_evaluation', {})
                if eval_data and 'overall_score' in eval_data:
                    score = float(eval_data['overall_score'])
                games_with_scores.append((game, score))
            
            # Sort by score descending
            games_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Get top games
            top_games = [game for game, score in games_with_scores[:display_count]]
            
            # Get games that were excluded
            excluded_count = original_count - len(filtered_games)
            
            summary.extend([
                "",
                f"Top {len(top_games)} Games (Highest Quality Scores):",
                "----------------------------------------"
            ])
            
            # Add top games
            for i, game in enumerate(top_games):
                score = 0
                eval_data = game.get('_evaluation', {})
                if eval_data and 'overall_score' in eval_data:
                    score = float(eval_data['overall_score'])
                
                summary.append(f"{i+1}. {game.get('name', 'Unknown')} - Score: {score:.2f}/10")
            
            # Only show worst games if we have excluded games
            if excluded_count > 0:
                summary.extend([
                    "",
                    f"Removed Games Preview (Lowest Scores):",
                    "----------------------------------------",
                    f"These games didn't make the cut and were removed from the filtered collection:"
                ])
                
                # Since we don't have the removed games list directly, we'll include a note
                summary.append(f"Total games removed: {excluded_count}")
                summary.append("")
                summary.append("Note: To see the complete list of removed games, compare the original DAT")
                summary.append("      file with the filtered output using a comparison tool.")
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary))
            
            self.logger.info(f"Successfully exported text summary to {output_path}")
            return True, f"Successfully exported summary to {output_path}"
            
        except Exception as e:
            error_msg = f"Error exporting text summary: {e}"
            self.logger.error(error_msg)
            return False, error_msg
