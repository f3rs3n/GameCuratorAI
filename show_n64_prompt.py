#!/usr/bin/env python3
"""Quick script to show a sample Nintendo 64 DAT query with real data."""

import os
import sys
import json
import xml.etree.ElementTree as ET
from core.dat_parser import DatParser

def main():
    print("Loading real Nintendo 64 DAT file data...")
    
    dat_file_path = "ToFilter/Nintendo - Nintendo 64 (BigEndian) (20250208-050759) (Retool 2025-03-21 11-58-44) (348) (-ny) [-aABbcdkMmpPv].dat"
    
    # Parse the actual DAT file
    parser = DatParser()
    parsed_data = parser.parse_file(dat_file_path)
    
    # Show total number of games
    game_count = len(parsed_data['games'])
    print(f"Total Nintendo 64 games in DAT: {game_count}")
    
    # Display the first 10 games with their actual data
    print("\n=== NINTENDO 64 ACTUAL GAME DATA (First 10 Games) ===\n")
    
    for i, game in enumerate(parsed_data['games'][:10]):
        print(f"Game {i+1}: {game.get('name', 'Unknown')}")
        print(f"  Description: {game.get('description', 'N/A')}")
        
        # Print year if available
        if 'year' in game and isinstance(game['year'], dict) and 'text' in game['year']:
            print(f"  Year: {game['year']['text']}")
        
        # Print manufacturer if available
        if 'manufacturer' in game and isinstance(game['manufacturer'], dict) and 'text' in game['manufacturer']:
            print(f"  Manufacturer: {game['manufacturer']['text']}")
        
        # Print ROM info if available
        if 'rom' in game:
            if isinstance(game['rom'], dict):
                print(f"  ROM: {game['rom'].get('name', 'Unknown')} (Size: {game['rom'].get('size', 'Unknown')})")
            elif isinstance(game['rom'], list):
                print(f"  ROM(s): {len(game['rom'])}")
                for idx, rom in enumerate(game['rom'][:3]):  # Show first 3 ROMs if multiple
                    print(f"    - {rom.get('name', 'Unknown')} (Size: {rom.get('size', 'Unknown')})")
                if len(game['rom']) > 3:
                    print(f"    ... and {len(game['rom']) - 3} more ROMs")
                    
        print()  # Blank line between games
        
    # Show a sample of what goes into the AI model
    print("\n=== NINTENDO 64 DATA SENT TO AI MODEL ===\n")
    
    # Create simplified game objects like what's sent to the AI
    sample_games = []
    for game in parsed_data['games'][:5]:  # First 5 games
        simplified_game = {
            "name": game.get("name", "Unknown Game"),
        }
        
        # Only add other fields if they exist and are potentially useful
        if "year" in game and isinstance(game["year"], dict) and "text" in game["year"]:
            simplified_game["year"] = game["year"]["text"]
        if "manufacturer" in game and isinstance(game["manufacturer"], dict) and "text" in game["manufacturer"]:
            simplified_game["manufacturer"] = game["manufacturer"]["text"]
        
        sample_games.append(simplified_game)
    
    # Print the simplified games that would be sent to the AI
    print(json.dumps(sample_games, indent=2))

if __name__ == "__main__":
    main()