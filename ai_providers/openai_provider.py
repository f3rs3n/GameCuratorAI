"""
OpenAI implementation for the AI provider interface.
This module handles communication with OpenAI's API for game evaluation.
"""

import json
import os
import logging
import time
from typing import Dict, Any, List, Optional

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI
from ai_providers.base import BaseAIProvider
from utils.api_usage_tracker import get_tracker

class OpenAIProvider(BaseAIProvider):
    """OpenAI implementation of the AI provider interface"""
    
    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize the OpenAI provider
        
        Args:
            model: The OpenAI model to use (default: gpt-4o)
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.client = None
        self.api_key = None
        self.initialized = False
        self.rate_limit_delay = 1.0  # 1 second between API calls to avoid rate limits
        self.last_call_time = 0

    def initialize(self) -> bool:
        """
        Initialize the OpenAI provider with API key and verify it works
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        self.api_key = os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            self.logger.error("OpenAI API key not found in environment variables.")
            return False
        
        try:
            # Create the client
            self.client = OpenAI(api_key=self.api_key)
            
            # Test the API key with a minimal request to verify it works
            test_prompt = "Respond with the word 'success' if you can read this."
            self.logger.info("Testing OpenAI API key with a simple request...")
            
            try:
                # Make a minimal API call to verify the key works
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10  # Keep it very small to minimize token usage
                )
                
                # Track API usage
                token_usage = 0
                if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                    token_usage = response.usage.total_tokens
                
                # Record the request in usage tracker
                usage_tracker = get_tracker()
                usage_tracker.record_request("openai", token_usage)
                
                if not response or not hasattr(response, 'choices') or len(response.choices) == 0:
                    self.logger.error("API test failed: No valid response received")
                    return False
                
                # Log a snippet of the response - safely with checks
                response_text = ""
                if response and hasattr(response, 'choices') and len(response.choices) > 0:
                    if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                        response_text = response.choices[0].message.content
                
                self.logger.info(f"API test response: {response_text[:50] if response_text else 'No content'}...")
                
                # If we got here, the API key is valid
                self.initialized = True
                self.logger.info("OpenAI provider initialized successfully with verified API key")
                return True
                
            except Exception as test_error:
                self.logger.error(f"API key validation failed: {test_error}")
                # Clear out the client since it doesn't work
                self.client = None
                self.initialized = False
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI provider: {e}")
            self.initialized = False
            return False

    def is_available(self) -> bool:
        """
        Check if the OpenAI provider is available for use
        
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
        Evaluate a game based on the specified criteria using OpenAI
        
        Args:
            game_info: Dictionary containing game information
            criteria: List of criteria to evaluate (e.g., "metacritic", "historical")
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            Dict containing evaluation results with scores and explanations
        """
        if not self.is_available():
            self.logger.error("OpenAI provider is not available")
            return {"error": "Provider not available"}
        
        self._respect_rate_limit()
        
        # Construct prompt
        prompt = self._construct_evaluation_prompt(game_info, criteria, full_collection_context)
        
        try:
            # Check if client is properly initialized
            if not self.client:
                self.logger.error("OpenAI client is not initialized")
                return {"error": "Provider client not initialized"}
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert video game historian and curator. "
                            "Your task is to evaluate a video game based on specific criteria "
                            "and determine if it should be included in a curated collection. "
                            "Provide detailed reasoning for your evaluation."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2  # Lower temperature for more consistent results
            )
            
            # Track API usage
            token_usage = 0
            if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                token_usage = response.usage.total_tokens
            
            # Record the request in usage tracker
            usage_tracker = get_tracker()
            usage_tracker.record_request("openai", token_usage)
            
            # Parse the response with safety checks
            if not response or not hasattr(response, 'choices') or len(response.choices) == 0:
                self.logger.error("No valid response from OpenAI API")
                return {"error": "No valid response received"}
                
            content = response.choices[0].message.content
            if not content:
                self.logger.error("Empty content in response")
                return {"error": "Empty response content"}
                
            # Parse the JSON response safely
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as je:
            self.logger.error(f"JSON parsing error: {je}")
            return {"error": f"Failed to parse response as JSON: {str(je)}"}
        except Exception as e:
            self.logger.error(f"Error evaluating game with OpenAI: {e}")
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
            self.logger.error("OpenAI provider is not available")
            # Create a properly typed error response matching Dict[str, List[Dict[str, Any]]]
            return {"error": [{"reason": "Provider not available"}]}
        
        self._respect_rate_limit()
        
        # Extract game names for compact analysis
        game_names = [game.get("name", "") for game in games_info]
        
        try:
            # Check if client is properly initialized
            if not self.client:
                self.logger.error("OpenAI client is not initialized")
                return {"error": [{"reason": "Provider client not initialized"}]}
                
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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in video game cataloging and organization. "
                            "Your task is to identify special cases within a game collection."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            # Track API usage
            token_usage = 0
            if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                token_usage = response.usage.total_tokens
            
            # Record the request in usage tracker
            usage_tracker = get_tracker()
            usage_tracker.record_request("openai", token_usage)
            
            # Safe parsing of the response with validation
            if not response or not hasattr(response, 'choices') or len(response.choices) == 0:
                self.logger.error("No valid response from OpenAI API for special cases")
                return {"error": [{"reason": "No valid response received"}]}
                
            content = response.choices[0].message.content
            if not content:
                self.logger.error("Empty content in special cases response")
                return {"error": [{"reason": "Empty response content"}]}
                
            # Parse the JSON response safely
            result = json.loads(content)
            
            # Map back to the original game_info dictionaries
            mapped_results = {}
            
            if not isinstance(result, dict):
                self.logger.error(f"Expected dict result but got {type(result)}")
                return {"error": [{"reason": "Invalid response format received"}]}
                
            for category, titles in result.items():
                if not isinstance(titles, list):
                    self.logger.warning(f"Expected list for {category} but got {type(titles)}")
                    continue
                    
                mapped_results[category] = []
                for title in titles:
                    for game in games_info:
                        if game.get("name", "") == title:
                            mapped_results[category].append(game)
                            break
            
            return mapped_results
            
        except json.JSONDecodeError as je:
            self.logger.error(f"JSON parsing error in special cases: {je}")
            return {"error": [{"reason": f"Failed to parse response as JSON: {str(je)}"}]}
        except Exception as e:
            self.logger.error(f"Error identifying special cases with OpenAI: {e}")
            return {"error": [{"reason": str(e)}]}

    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider
        
        Returns:
            str: Provider name
        """
        return "OpenAI"

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the AI provider
        
        Returns:
            Dict containing provider information like version, capabilities, etc.
        """
        return {
            "name": "OpenAI",
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
            "metacritic": "Evaluate the game based on its Metacritic score and critical acclaim. Games scoring 7.5/10 or higher should be kept.",
            "historical": "Evaluate the game's historical significance and impact on the gaming industry",
            "v_list": "Determine if this game is likely on V's recommended games list",
            "console_significance": "Evaluate this game's significance for its specific console",
            "mods_hacks": "Identify if this is a notable mod, hack, or unofficial translation worth preserving",
            "hidden_gems": "Evaluate if this game is considered a 'hidden gem' based on Reddit discussions and specialized gaming forums"
        }
        
        criteria_prompts = [criteria_descriptions.get(c, f"Evaluate based on {c}") for c in criteria]
        criteria_text = "\n".join([f"- {p}" for p in criteria_prompts])
        
        context_text = ""
        if full_collection_context:
            context_text = "\nAdditional context from the collection:\n" + json.dumps(full_collection_context, indent=2)
        
        prompt = f"""
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
  "evaluations": {{
    "criterion_name": {{
      "score": numeric_score,
      "explanation": "brief explanation"
    }},
    ...
  }},
  "overall_recommendation": {{
    "include": true/false,
    "reason": "brief explanation"
  }}
}}
"""
        return prompt
