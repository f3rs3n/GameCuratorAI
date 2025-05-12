#!/usr/bin/env python3

"""Show a real prompt and response from Gemini API."""

import json
import sys
import os
import logging
import google.generativeai as genai
from core.dat_parser import DatParser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a smaller sample size to keep the output manageable
SAMPLE_SIZE = 5

def main():
    """Main function"""
    # Configure the Gemini API
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("GEMINI_API_KEY environment variable not set.")
        return
        
    print("Initializing Gemini API...")
    genai.configure(api_key=gemini_api_key)
    model_obj = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
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
    # Use a subset for demonstration (just 5 games)
    for game in parsed_data['games'][:SAMPLE_SIZE]:
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
    print("\n=== NINTENDO DS DATA SENT TO AI MODEL (SAMPLE) ===\n")
    print(json.dumps(sample_games, indent=2))
    
    # Use a subset of criteria
    criteria = ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"]
    
    # Construct the prompt
    prompt = construct_batch_evaluation_prompt(
        sample_games, 
        criteria,
        full_collection_context={"console": "Nintendo DS"}
    )
    
    print("\n=== PROMPT SENT TO AI MODEL ===\n")
    print(prompt)
    
    # Send to Gemini API and get response
    print("\n=== SENDING REQUEST TO GEMINI API ===\n")
    try:
        response = model_obj.generate_content(
            prompt,
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
            ],
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4096,
            }
        )
        print("\n=== RESPONSE FROM GEMINI API ===\n")
        print(response.text)
        
        # Try to extract and format JSON for better readability
        try:
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response.text[json_start:json_end]
                result = json.loads(json_str)
                
                print("\n=== FORMATTED JSON RESULT ===\n")
                print(json.dumps(result, indent=2))
                
                # Print a summary of which games were kept/removed
                if "games" in result:
                    print("\n=== DECISION SUMMARY ===\n")
                    for game in result["games"]:
                        decisions = game.get("criteria_decisions", {})
                        keep_criteria = [c for c, v in decisions.items() if v]
                        
                        if any(decisions.values()):
                            print(f"✓ KEEP | {game['game_name']}")
                            print(f"   Criteria met: {', '.join(keep_criteria)}")
                        else:
                            print(f"✗ REMOVE | {game['game_name']}")
                            print(f"   No criteria met")
        except json.JSONDecodeError:
            print("\nCould not parse response as JSON. Showing raw response only.")
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")

def construct_batch_evaluation_prompt(
    games_info, 
    criteria,
    full_collection_context=None
) -> str:
    """
    Construct a prompt for evaluating multiple games in a batch with binary decisions
    
    Args:
        games_info: List of dictionaries containing game information
        criteria: List of criteria to evaluate
        full_collection_context: Optional additional context from the full collection
        
    Returns:
        str: Constructed batch prompt
    """
    games_json = json.dumps(games_info, indent=2)
    
    criteria_descriptions = {
        "metacritic": "Evaluate if the game would have a Metacritic score of 7.5/10 or higher. Keep if it meets this threshold.",
        "historical": "Evaluate if the game has significant historical importance or impact on the gaming industry. Keep if historically significant.",
        "v_list": "Determine if this game is likely on V's recommended games list. Keep if likely on the list.",
        "console_significance": "Evaluate if this game is significant for its specific console. Keep if it's an important title for the platform.",
        "mods_hacks": "Identify if this is a notable mod, hack, or unofficial translation. Keep only if very significant.",
        "hidden_gems": "Evaluate if this game is considered a 'hidden gem' with a devoted community following. Keep if it's a hidden gem."
    }
    
    criteria_prompts = [criteria_descriptions.get(c, f"Evaluate based on {c}") for c in criteria]
    criteria_text = "\n".join([f"- {p}" for p in criteria_prompts])
    
    context_text = ""
    if full_collection_context:
        # Simplify context to just essential information
        simplified_context = {
            "console": full_collection_context.get("console", ""),
            "genre_distribution": full_collection_context.get("genre_distribution", {})
        }
        context_text = "\nAdditional context from the collection:\n" + json.dumps(simplified_context, indent=2)
    
    # Get proper criterion names for the prompt
    criterion_names = {
        "metacritic": "metacritic",
        "historical": "historical",
        "v_list": "v_list",
        "console_significance": "console_significance",
        "mods_hacks": "mods_hacks",
        "hidden_gems": "hidden_gems"
    }
    
    # Create a comma-separated string of criterion names for the example
    criterion_names_list = ", ".join([f'"{name}"' for name in [c for c in criteria]])
    
    prompt = f"""You are an expert video game historian and curator evaluating games for a collection.
Your task is to provide binary KEEP or DISCARD decisions for each criterion for multiple games.

Games to evaluate:
{games_json}

For each criterion, determine if the game should be KEPT based on:
{criteria_text}
{context_text}

For EACH game and EACH criterion, provide a binary "keep" decision (true or false).
Games that match ANY criterion with "keep: true" will be included in the collection.

Return your evaluations as a JSON array where each object follows this structure:
{{
  "game_name": "Name of Game",
  "criteria_decisions": {{
    "metacritic": true/false,
    "historical": true/false,
    "v_list": true/false,
    "console_significance": true/false,
    "mods_hacks": true/false,
    ...
  }},
  "minimal_notes": {{
    "metacritic": "1-2 word justification",
    "historical": "1-2 word justification",
    "v_list": "1-2 word justification",
    "console_significance": "1-2 word justification",
    "mods_hacks": "1-2 word justification",
    ...
  }}
}}

Important: Use EXACTLY these criterion keys in your response: {criterion_names_list}
Do not use generic names like criterion1, criterion2, etc.

Keep any notes extremely brief - just 1-2 words per criterion.
Your response MUST be valid JSON and MUST include all the criteria asked for.

Wrap your entire response in a single JSON object containing a "games" array:
{{
  "games": [
    {{game1 evaluation}},
    {{game2 evaluation}},
    ...
  ]
}}
"""
    return prompt

if __name__ == "__main__":
    main()