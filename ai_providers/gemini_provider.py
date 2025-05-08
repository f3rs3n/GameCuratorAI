"""
Gemini 2.0 implementation for the AI provider interface.
This module handles communication with Google's Gemini API for game evaluation.
"""

import json
import os
import logging
import time
from typing import Dict, Any, List, Optional

import google.generativeai as genai
from ai_providers.base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    """Gemini implementation of the AI provider interface"""
    
    def __init__(self, model: str = "gemini-1.5-flash"):
        """
        Initialize the Gemini provider
        
        Args:
            model: The Gemini model to use (default: gemini-1.5-flash)
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.api_key = None
        self.initialized = False
        
        # Rate limiting settings based on API limits (15 RPM, 1,000,000 TPM, 1,500 RPD)
        self.rate_limit_delay = 4.0  # 4 seconds between API calls (15 RPM = 1 call per 4 seconds)
        self.last_call_time = 0
        self.daily_call_count = 0
        self.daily_call_max = 1400  # Slightly below the 1,500 RPD limit for safety
        self.daily_reset_time = time.time()  # When we last reset the daily counter
        
        # Configuration for Gemini requests
        self.generation_config = {
            "temperature": 0.2,  # Lower temp for more consistent results
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 800,  # Reduced from 1024 to use fewer tokens
        }

    def initialize(self) -> bool:
        """
        Initialize the Gemini provider with API key
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            self.logger.error("Gemini API key not found in environment variables.")
            return False
        
        try:
            genai.configure(api_key=self.api_key)
            self.model_obj = genai.GenerativeModel(
                model_name=self.model,
                generation_config=self.generation_config
            )
            self.initialized = True
            self.logger.info("Gemini provider initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini provider: {e}")
            return False

    def is_available(self) -> bool:
        """
        Check if the Gemini provider is available for use
        
        Returns:
            bool: True if the provider is available, False otherwise
        """
        return self.initialized and self.api_key is not None

    def _respect_rate_limit(self):
        """
        Ensure we don't exceed rate limits by adding delays between API calls
        and checking daily limits
        """
        current_time = time.time()
        
        # Check if we should reset the daily counter (24 hours = 86400 seconds)
        if current_time - self.daily_reset_time > 86400:
            self.logger.info("Resetting daily API call counter")
            self.daily_call_count = 0
            self.daily_reset_time = current_time
        
        # Enforce per-minute rate limit
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            self.logger.debug(f"Rate limit: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Check daily call limit
        if self.daily_call_count >= self.daily_call_max:
            self.logger.warning(f"Daily API call limit reached ({self.daily_call_max})")
            # Sleep for a longer period before trying again
            self.logger.info("Sleeping for 5 minutes before retrying")
            time.sleep(300)  # 5 minutes
            
            # After sleep, check if day rolled over
            if time.time() - self.daily_reset_time > 86400:
                self.daily_call_count = 0
                self.daily_reset_time = time.time()
                self.logger.info("Daily counter reset after wait period")
        
        # Update tracking variables
        self.last_call_time = time.time()
        self.daily_call_count += 1
        
        # Log usage stats periodically
        if self.daily_call_count % 50 == 0:
            self.logger.info(f"API usage: {self.daily_call_count}/{self.daily_call_max} calls today")

    def evaluate_game(self, 
                     game_info: Dict[str, Any], 
                     criteria: List[str],
                     full_collection_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate a game based on the specified criteria using Gemini
        
        Args:
            game_info: Dictionary containing game information
            criteria: List of criteria to evaluate (e.g., "metacritic", "historical")
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            Dict containing evaluation results with scores and explanations
        """
        if not self.is_available():
            self.logger.error("Gemini provider is not available")
            return {"error": "Provider not available"}
        
        self._respect_rate_limit()
        
        # Construct prompt
        prompt = self._construct_evaluation_prompt(game_info, criteria, full_collection_context)
        
        try:
            # Format system prompt and user message
            response = self.model_obj.generate_content(
                prompt,
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                ]
            )
            
            # Parse the response
            response_text = response.text
            
            # Extract the JSON part from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse JSON from Gemini response")
                    
                    # Fallback: create a structured response from the text
                    fallback_response = {
                        "game_id": "unknown",
                        "game_name": game_info.get("name", "Unknown Game"),
                        "scores": {},
                        "explanations": {},
                        "error": "Failed to parse JSON, using text response"
                    }
                    
                    # Add basic scores
                    for criterion in criteria:
                        fallback_response["scores"][criterion] = 5.0  # Neutral score
                        fallback_response["explanations"][criterion] = f"Unable to evaluate {criterion} properly"
                    
                    return fallback_response
            else:
                self.logger.error("No JSON found in Gemini response")
                return {"error": "No JSON found in response", "raw_response": response_text}
            
        except Exception as e:
            self.logger.error(f"Error evaluating game with Gemini: {e}")
            return {"error": str(e)}

    def batch_evaluate_games(self, 
                           games_info: List[Dict[str, Any]], 
                           criteria: List[str],
                           full_collection_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evaluate multiple games in a batch operation for efficiency
        
        Args:
            games_info: List of dictionaries containing game information
            criteria: List of criteria to evaluate
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            List of dictionaries containing evaluation results
        """
        if not self.is_available():
            self.logger.error("Gemini provider is not available")
            return [{"error": "Provider not available"} for _ in games_info]
        
        self._respect_rate_limit()
        
        # Convert games to minimal format (only keep essential information)
        simplified_games = []
        for game in games_info:
            simplified_game = {
                "name": game.get("name", "Unknown Game"),
                "id": game.get("id", "unknown"),
            }
            # Only add other fields if they exist and are potentially useful
            if "year" in game and isinstance(game["year"], dict) and "text" in game["year"]:
                simplified_game["year"] = game["year"]["text"]
            if "manufacturer" in game and isinstance(game["manufacturer"], dict) and "text" in game["manufacturer"]:
                simplified_game["manufacturer"] = game["manufacturer"]["text"]
            
            simplified_games.append(simplified_game)
            
        # Process in small batches of up to 5 games to balance efficiency and reliability
        max_batch_size = 5
        all_results = []
        
        for i in range(0, len(simplified_games), max_batch_size):
            batch = simplified_games[i:i+max_batch_size]
            
            # Construct batch prompt
            prompt = self._construct_batch_evaluation_prompt(batch, criteria, full_collection_context)
            
            try:
                # Send batch to Gemini
                response = self.model_obj.generate_content(
                    prompt,
                    safety_settings=[
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                    ]
                )
                
                # Parse the response
                response_text = response.text
                
                # Extract the JSON part from the response
                # First try to detect standard JSON structure with brace matching
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    try:
                        batch_results = json.loads(json_str)
                        
                        # Ensure batch_results is a list or has a 'games' key with a list
                        if isinstance(batch_results, dict) and "games" in batch_results:
                            batch_results = batch_results["games"]
                        elif not isinstance(batch_results, list):
                            # If it's not a list or doesn't have a games key, something's wrong
                            raise ValueError(f"Unexpected result format: {type(batch_results)}")
                        
                        # Validate each result to ensure it has the expected structure
                        for i, result in enumerate(batch_results):
                            if not isinstance(result, dict):
                                self.logger.warning(f"Result {i} is not a dictionary: {result}")
                                continue
                                
                            # Ensure each result has required fields
                            if "game_name" not in result:
                                result["game_name"] = f"Unknown Game {i}"
                            
                            # Ensure scores and explanations are dictionaries
                            if "scores" not in result or not isinstance(result["scores"], dict):
                                result["scores"] = {c: 5.0 for c in criteria}
                            
                            if "explanations" not in result or not isinstance(result["explanations"], dict):
                                result["explanations"] = {c: "No explanation provided" for c in criteria}
                        
                        # Validate and ensure we have results for each game
                        if len(batch_results) != len(batch):
                            self.logger.warning(f"Batch returned {len(batch_results)} results for {len(batch)} games")
                            # Fill in missing games with placeholders
                            result_names = [result.get("game_name", "").strip() for result in batch_results]
                            
                            # Add any missing games
                            for game in batch:
                                if game["name"] not in result_names:
                                    self.logger.warning(f"Game {game['name']} missing from results, adding placeholder")
                                    placeholder = {
                                        "game_id": game.get("id", "unknown"),
                                        "game_name": game["name"],
                                        "scores": {c: 5.0 for c in criteria},
                                        "explanations": {c: f"No evaluation provided for {c}" for c in criteria},
                                        "error": "Game missing from batch results"
                                    }
                                    batch_results.append(placeholder)
                            
                        all_results.extend(batch_results)
                        
                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse JSON from Gemini batch response: {json_str}")
                        
                        # Generate individual fallbacks for each game in the batch
                        for game in batch:
                            fallback = {
                                "game_id": game.get("id", "unknown"),
                                "game_name": game["name"],
                                "scores": {c: 5.0 for c in criteria},
                                "explanations": {c: f"Failed to parse batch results for {c}" for c in criteria},
                                "error": "Failed to parse JSON from batch response"
                            }
                            all_results.append(fallback)
                else:
                    self.logger.error("No JSON found in Gemini batch response")
                    for game in batch:
                        fallback = {
                            "game_id": game.get("id", "unknown"),
                            "game_name": game["name"],
                            "scores": {c: 5.0 for c in criteria},
                            "explanations": {c: f"No batch results found for {c}" for c in criteria},
                            "error": "No JSON found in batch response"
                        }
                        all_results.append(fallback)
                        
            except Exception as e:
                self.logger.error(f"Error in batch evaluation: {e}")
                # Add fallback results for this batch
                for game in batch:
                    fallback = {
                        "game_id": game.get("id", "unknown"),
                        "game_name": game["name"],
                        "scores": {c: 5.0 for c in criteria},
                        "explanations": {c: f"Batch processing error for {c}" for c in criteria},
                        "error": str(e)
                    }
                    all_results.append(fallback)
            
            # Respect API rate limits between batches
            if i + max_batch_size < len(simplified_games):
                self._respect_rate_limit()
        
        # Ensure we have the same number of results as input games
        if len(all_results) != len(games_info):
            self.logger.error(f"Result count mismatch: {len(all_results)} results for {len(games_info)} games")
            # Fill missing entries with error results
            while len(all_results) < len(games_info):
                missing_index = len(all_results)
                if missing_index < len(games_info):
                    game = games_info[missing_index]
                    fallback = {
                        "game_id": game.get("id", "unknown"),
                        "game_name": game.get("name", "Unknown Game"),
                        "scores": {c: 5.0 for c in criteria},
                        "explanations": {c: "Missing result" for c in criteria},
                        "error": "Game missing from batch processing results"
                    }
                    all_results.append(fallback)
                else:
                    break
                    
        return all_results

    def identify_special_cases(self,
                             games_info: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify special cases like multi-disc games, regional variants, etc.
        
        Args:
            games_info: List of dictionaries containing game information
            
        Returns:
            Dictionary mapping special case types to lists of affected games
        """
        if not self.is_available():
            self.logger.error("Gemini provider is not available")
            return {"error": [{"message": "Provider not available"}]}
        
        self._respect_rate_limit()
        
        # Extract game names for compact analysis
        game_names = [game.get("name", "") for game in games_info]
        
        try:
            prompt = (
                "Analyze the following list of video game titles and identify special cases like: "
                "1. Multi-disc games (games with Disc 1, CD 2, etc. in the title) "
                "2. Regional variants (US, Europe, Japan versions of the same game) "
                "3. Console-specific naming patterns "
                "4. Special editions, collections, or compilations "
                "\n\nGame titles:\n" + "\n".join(game_names) + "\n\n"
                "Group the titles by special case type. Return the results as a JSON object with the following format: "
                "{\n"
                '  "multi_disc": ["Game A (Disc 1)", "Game A (Disc 2)"], \n'
                '  "regional_variants": ["Game B (USA)", "Game B (Europe)"], \n'
                '  "console_specific": ["Nintendo GameCube title pattern examples"], \n'
                '  "special_editions": ["Game C Collector\'s Edition", "Game D Complete Collection"] \n'
                "}"
            )
            
            response = self.model_obj.generate_content(prompt)
            response_text = response.text
            
            # Extract the JSON part from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Map back to the original game_info dictionaries
                mapped_results = {}
                for category, titles in result.items():
                    mapped_results[category] = []
                    for title in titles:
                        for game in games_info:
                            if game.get("name", "") == title:
                                mapped_results[category].append(game)
                                break
                
                return mapped_results
            else:
                self.logger.error("No JSON found in Gemini response")
                return {"error": [{"message": "No JSON found in response"}]}
            
        except Exception as e:
            self.logger.error(f"Error identifying special cases with Gemini: {e}")
            return {"error": [{"message": str(e)}]}

    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider
        
        Returns:
            str: Provider name
        """
        return "Gemini"

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the AI provider
        
        Returns:
            Dict containing provider information like version, capabilities, etc.
        """
        return {
            "name": "Gemini",
            "model": self.model,
            "initialized": self.initialized,
            "capabilities": [
                "metacritic_evaluation",
                "historical_significance",
                "cultural_impact",
                "special_case_detection",
                "regional_variant_analysis"
            ]
        }

    def _construct_evaluation_prompt(self, 
                                   game_info: Dict[str, Any], 
                                   criteria: List[str],
                                   full_collection_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Construct a prompt for evaluating a single game
        
        Args:
            game_info: Dictionary containing game information
            criteria: List of criteria to evaluate
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            str: Constructed prompt
        """
        game_name = game_info.get("name", "Unknown Game")
        
        # Use a more minimal game description to reduce token usage
        simplified_game = {
            "name": game_name,
            "id": game_info.get("id", "unknown"),
        }
        
        # Only add other fields if they exist and are potentially useful
        if "year" in game_info and isinstance(game_info["year"], dict) and "text" in game_info["year"]:
            simplified_game["year"] = game_info["year"]["text"]
        if "manufacturer" in game_info and isinstance(game_info["manufacturer"], dict) and "text" in game_info["manufacturer"]:
            simplified_game["manufacturer"] = game_info["manufacturer"]["text"]
            
        game_description = json.dumps(simplified_game, indent=2)
        
        criteria_descriptions = {
            "metacritic": "Evaluate the game based on its Metacritic score and critical acclaim",
            "historical": "Evaluate the game's historical significance and impact on the gaming industry",
            "v_list": "Determine if this game is likely on V's recommended games list",
            "console_significance": "Evaluate this game's significance for its specific console",
            "mods_hacks": "Identify if this is a notable mod or hack worth preserving"
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
        
        prompt = f"""You are an expert video game historian and curator. Your task is to evaluate a video game based on specific criteria and determine if it should be included in a curated collection. Provide detailed reasoning for your evaluation.

Evaluate the following video game:

Game Name: {game_name}

Game Information:
{game_description}

Evaluate this game based on these criteria:
{criteria_text}
{context_text}

For each criterion, assign a score from 0 to 10 and provide a brief explanation.
Then give an overall recommendation of whether to include this game in a curated collection.

Return your evaluation as a JSON object with this structure:
{{
  "game_name": "{game_name}",
  "scores": {{
    "criterion1": score1,
    "criterion2": score2,
    ...
  }},
  "explanations": {{
    "criterion1": "brief explanation",
    "criterion2": "brief explanation",
    ...
  }},
  "overall_recommendation": {{
    "include": true/false,
    "reason": "brief explanation"
  }}
}}

Keep explanations concise and specific. Make sure your response is valid JSON.
"""
        return prompt
        
    def _construct_batch_evaluation_prompt(self, 
                                       games_info: List[Dict[str, Any]], 
                                       criteria: List[str],
                                       full_collection_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Construct a prompt for evaluating multiple games in a batch
        
        Args:
            games_info: List of dictionaries containing game information
            criteria: List of criteria to evaluate
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            str: Constructed batch prompt
        """
        games_json = json.dumps(games_info, indent=2)
        
        criteria_descriptions = {
            "metacritic": "Evaluate the game based on its Metacritic score and critical acclaim",
            "historical": "Evaluate the game's historical significance and impact on the gaming industry",
            "v_list": "Determine if this game is likely on V's recommended games list",
            "console_significance": "Evaluate this game's significance for its specific console",
            "mods_hacks": "Identify if this is a notable mod or hack worth preserving"
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
        
        prompt = f"""You are an expert video game historian and curator. Your task is to evaluate multiple video games based on specific criteria and determine if each should be included in a curated collection.

Games to evaluate:
{games_json}

Evaluate each game based on these criteria:
{criteria_text}
{context_text}

For each criterion, assign a score from 0 to 10 and provide a brief explanation.

Return your evaluations as a JSON array where each object follows this structure:
{{
  "game_name": "Name of Game",
  "scores": {{
    "criterion1": score1,
    "criterion2": score2,
    ...
  }},
  "explanations": {{
    "criterion1": "brief explanation",
    "criterion2": "brief explanation",
    ...
  }}
}}

Keep explanations concise and specific. Your response must be valid JSON.
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