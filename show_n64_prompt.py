#!/usr/bin/env python3
"""Quick script to show a sample Nintendo 64 DAT query."""

import os
import sys
import json
from pathlib import Path
from ai_providers.gemini_provider import GeminiProvider

def main():
    print("Loading Nintendo 64 DAT file...")
    
    dat_file = "ToFilter/Nintendo - Nintendo 64 (BigEndian) (20250208-050759) (Retool 2025-03-21 11-58-44) (348) (-ny) [-aABbcdkMmpPv].dat"
    
    # Create a simple provider
    provider = GeminiProvider()
    
    # Mock N64 games
    n64_games = [
        {
            "name": "Super Mario 64 (USA)",
            "description": "The first 3D Mario game and a revolutionary platformer.",
            "language": "en",
            "region": "USA",
            "platform": "Nintendo 64",
            "year": "1996",
            "genre": "Platformer"
        },
        {
            "name": "GoldenEye 007 (USA)",
            "description": "A groundbreaking first-person shooter based on the James Bond film.",
            "language": "en",
            "region": "USA",
            "platform": "Nintendo 64",
            "year": "1997",
            "genre": "First-Person Shooter"
        },
        {
            "name": "The Legend of Zelda - Ocarina of Time (USA)",
            "description": "One of the most acclaimed games of all time and the first 3D Zelda.",
            "language": "en",
            "region": "USA",
            "platform": "Nintendo 64",
            "year": "1998",
            "genre": "Action-Adventure"
        },
        {
            "name": "Mario Kart 64 (USA)",
            "description": "Popular kart racing game and sequel to Super Mario Kart.",
            "language": "en",
            "region": "USA",
            "platform": "Nintendo 64",
            "year": "1997",
            "genre": "Racing"
        },
        {
            "name": "Banjo-Kazooie (USA)",
            "description": "A platformer developed by Rare featuring a bear and bird duo.",
            "language": "en",
            "region": "USA",
            "platform": "Nintendo 64",
            "year": "1998",
            "genre": "Platformer"
        }
    ]
    
    # Criteria to use for evaluation
    criteria = ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"]
    
    # Collection context
    context = {
        "console": "Nintendo 64",
        "genre_distribution": {
            "Platformer": 25,
            "Racing": 15,
            "First-Person Shooter": 10,
            "Action-Adventure": 20,
            "Sports": 12,
            "Fighting": 8,
            "Puzzle": 5,
            "Other": 5
        }
    }
    
    # Get the prompt for this batch
    prompt = provider._construct_batch_evaluation_prompt(n64_games, criteria, context)
    
    # Print the prompt
    print("\n=== NINTENDO 64 PROMPT EXAMPLE ===\n")
    print(prompt)
    print("\n=== END OF PROMPT ===\n")

if __name__ == "__main__":
    main()