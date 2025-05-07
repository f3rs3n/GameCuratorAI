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
        self.rate_limit_delay = 1.0  # 1 second between API calls to avoid rate limits
        self.last_call_time = 0
        self.generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 1024,
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
        """
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_call)
        
        self.last_call_time = time.time()

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
        results = []
        
        # Process games individually for now
        # In a production environment, this could be optimized further
        for game_info in games_info:
            results.append(self.evaluate_game(game_info, criteria, full_collection_context))
        
        return results

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
        Construct a prompt for game evaluation
        
        Args:
            game_info: Dictionary containing game information
            criteria: List of criteria to evaluate
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            str: Constructed prompt
        """
        game_name = game_info.get("name", "Unknown Game")
        game_description = json.dumps(game_info, indent=2)
        
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
            context_text = "\nAdditional context from the collection:\n" + json.dumps(full_collection_context, indent=2)
        
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

Make sure your response is valid JSON.
"""
        return prompt