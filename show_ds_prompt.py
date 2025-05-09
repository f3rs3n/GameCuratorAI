#!/usr/bin/env python3

"""Show Nintendo DS prompt with the first 20 games."""

import json
import sys
import os
from core.dat_parser import DatParser
from ai_providers.gemini_provider import GeminiProvider

def main():
    """Main function"""
    print("Loading Nintendo DS DAT file data...")
    try:
        parser = DatParser()
        parsed_data = parser.parse_file("ToFilter/Nintendo - Nintendo DS (Decrypted) (20250319-094434) (Retool 2025-03-21 11-58-53) (2,177) (-ny) [-aABbcdkMmpPv].dat")
        print(f"Total Nintendo DS games in DAT: {len(parsed_data['games'])}")
    except Exception as e:
        print(f"Error loading DAT file: {e}")
        return
    
    # Create simplified game objects like what's sent to the AI
    sample_games = []
    for game in parsed_data['games'][:20]:  # First 20 games
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
    print("\n=== NINTENDO DS DATA SENT TO AI MODEL (FIRST 20 GAMES) ===\n")
    print(json.dumps(sample_games, indent=2))
    
    # Create a provider to generate the prompt
    provider = GeminiProvider()
    
    # Use a subset of criteria
    criteria = ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"]
    
    # Generate the actual prompt that would be sent
    prompt = provider._construct_batch_evaluation_prompt(
        sample_games, 
        criteria,
        full_collection_context={"console": "Nintendo DS"}
    )
    
    print("\n=== PROMPT SENT TO AI MODEL ===\n")
    print(prompt)

if __name__ == "__main__":
    main()