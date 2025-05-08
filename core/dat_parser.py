"""
Module for parsing XML-formatted .dat files containing video game information.
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from xml.dom import minidom

class DatParser:
    """Parser for XML-formatted .dat files containing video game information."""
    
    def __init__(self):
        """Initialize the DAT parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a .dat file and extract its structure and game information
        
        Args:
            file_path: Path to the .dat file
            
        Returns:
            Dictionary containing the parsed file structure and game data
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a valid XML file
        """
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract header information (metadata about the DAT file)
            header = self._extract_header(root)
            
            # Extract game entries
            games = self._extract_games(root)
            
            # Save original XML structure for later reconstruction
            original_structure = {
                'root_tag': root.tag,
                'root_attrib': dict(root.attrib),
                'header': header,
                'games_parent_tag': self._find_games_parent_tag(root)
            }
            
            result = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'original_structure': original_structure,
                'header': header,
                'games': games,
                'game_count': len(games),
                'consoles': self._extract_consoles(games, header)
            }
            
            self.logger.info(f"Successfully parsed DAT file: {file_path} with {len(games)} games")
            return result
            
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error in file {file_path}: {e}")
            raise ValueError(f"Invalid XML format in .dat file: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing file {file_path}: {e}")
            raise
    
    def _extract_header(self, root: ET.Element) -> Dict[str, Any]:
        """
        Extract header information from the DAT file
        
        Args:
            root: Root element of the XML tree
            
        Returns:
            Dictionary containing header information
        """
        header = {}
        
        # Common header elements in different DAT formats
        header_elements = ['header', 'datafile', 'clrmamepro', 'romcenter']
        
        for element_name in header_elements:
            element = root.find(f'.//{element_name}')
            if element is not None:
                for child in element:
                    header[child.tag] = child.text
        
        # If no structured header is found, try to get basic attributes
        if not header and root.attrib:
            header.update(root.attrib)
        
        return header
    
    def _find_games_parent_tag(self, root: ET.Element) -> str:
        """
        Find the parent tag containing game entries
        
        Args:
            root: Root element of the XML tree
            
        Returns:
            Tag name of the games parent element
        """
        # Common parent tags for game entries
        game_parent_tags = {
            'game': ['datafile', 'dat', 'games', 'root'],
            'machine': ['mame', 'softwarelist'],
            'software': ['softwarelist']
        }
        
        for game_tag, parent_tags in game_parent_tags.items():
            for parent_tag in parent_tags:
                games = root.findall(f'.//{parent_tag}/{game_tag}')
                if games:
                    return parent_tag
                
                # Direct children of root
                games = root.findall(f'./{game_tag}')
                if games:
                    return root.tag
        
        # Default to root if no specific parent found
        return root.tag
    
    def _extract_games(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract game entries from the DAT file
        
        Args:
            root: Root element of the XML tree
            
        Returns:
            List of dictionaries containing game information
        """
        games = []
        
        # Extract header first (so we can add it to every game)
        header = self._extract_header(root)
        
        # Common game entry tag names in different DAT formats
        game_tags = ['game', 'machine', 'software', 'rom']
        
        for tag in game_tags:
            entries = root.findall(f'.//{tag}')
            
            if entries:
                for entry in entries:
                    game_data = {'tag': tag, 'attrib': dict(entry.attrib)}
                    
                    # Add header information to every game for context
                    game_data['_header'] = header
                    
                    # Extract the name (handles different formats)
                    if 'name' in entry.attrib:
                        game_data['name'] = entry.attrib['name']
                    else:
                        name_element = entry.find('./name')
                        if name_element is not None:
                            game_data['name'] = name_element.text
                        else:
                            description = entry.find('./description')
                            if description is not None:
                                game_data['name'] = description.text
                    
                    # Extract all child elements
                    for child in entry:
                        if child.tag not in game_data:
                            # Handle elements with children
                            if len(child) > 0:
                                game_data[child.tag] = {
                                    'text': child.text,
                                    'attrib': dict(child.attrib),
                                    'children': [
                                        {
                                            'tag': subchild.tag,
                                            'text': subchild.text,
                                            'attrib': dict(subchild.attrib)
                                        }
                                        for subchild in child
                                    ]
                                }
                            else:
                                # Simple elements
                                game_data[child.tag] = {
                                    'text': child.text,
                                    'attrib': dict(child.attrib)
                                }
                    
                    # Store XML representation for later reconstruction
                    game_data['_xml'] = ET.tostring(entry, encoding='unicode')
                    
                    games.append(game_data)
                
                # If we found games with one tag, no need to check others
                if games:
                    break
        
        return games
    
    def _extract_consoles(self, games: List[Dict[str, Any]], header: Dict[str, Any]) -> List[str]:
        """
        Extract console names from game entries and header information
        
        Args:
            games: List of game entries
            header: Header information
            
        Returns:
            List of detected console names
        """
        consoles = set()
        
        # Try to extract from header
        for key in ['name', 'description']:
            if key in header and header[key]:
                consoles.add(header[key])
        
        # Look for console information in game entries
        for game in games:
            for key in ['console', 'platform', 'system']:
                if key in game and isinstance(game[key], dict) and game[key].get('text'):
                    consoles.add(game[key]['text'])
            
            # Check attribute values
            for key, value in game.get('attrib', {}).items():
                if key in ['console', 'platform', 'system']:
                    consoles.add(value)
        
        return sorted(list(consoles))
    
    def export_filtered_dat(self, 
                           original_data: Dict[str, Any], 
                           filtered_games: List[Dict[str, Any]], 
                           output_path: str,
                           metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Export filtered games back to a DAT file, maintaining original structure
        
        Args:
            original_data: Original parsed DAT data
            filtered_games: List of filtered game entries to include
            output_path: Path to save the filtered DAT file
            metadata: Optional metadata to include in the header
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract original structure
            original_structure = original_data['original_structure']
            
            # Create a new root element
            root = ET.Element(original_structure['root_tag'], attrib=original_structure['root_attrib'])
            
            # Recreate header
            if 'header' in original_structure and original_structure['header']:
                header_element = ET.SubElement(root, 'header')
                
                # Update header with filtering metadata if provided
                header_data = original_structure['header'].copy()
                if metadata:
                    header_data.update(metadata)
                
                for key, value in header_data.items():
                    if value is not None:
                        header_child = ET.SubElement(header_element, key)
                        header_child.text = str(value)
            
            # Find parent tag for games
            games_parent_tag = original_structure.get('games_parent_tag', 'datafile')
            
            # If games are not direct children of root, create parent element
            if games_parent_tag != original_structure['root_tag']:
                games_parent = ET.SubElement(root, games_parent_tag)
            else:
                games_parent = root
            
            # Add filtered games to the structure
            game_tag = filtered_games[0]['tag'] if filtered_games else 'game'
            
            for game in filtered_games:
                # Parse the original XML representation
                game_element = ET.fromstring(game['_xml'])
                games_parent.append(game_element)
            
            # Convert to string with proper formatting
            rough_string = ET.tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            self.logger.info(f"Successfully exported filtered DAT file to {output_path} with {len(filtered_games)} games")
            return True, f"Successfully exported {len(filtered_games)} games to {output_path}"
            
        except Exception as e:
            error_msg = f"Error exporting filtered DAT file: {e}"
            self.logger.error(error_msg)
            return False, error_msg
