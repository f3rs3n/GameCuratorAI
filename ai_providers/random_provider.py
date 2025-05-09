"""
Random score AI provider for testing purposes.
This provider generates random evaluations without requiring an API key.
"""

import random
import logging
from typing import Dict, List, Any, Optional
from ai_providers.base import BaseAIProvider

logger = logging.getLogger(__name__)

class RandomProvider(BaseAIProvider):
    """Random implementation of the AI provider interface for testing"""

    def __init__(self):
        """Initialize the Random provider"""
        self.initialized = False
        self.criteria_descriptions = {
            "metacritic": "Critical acclaim and review scores (7.5/10 or higher)",
            "historical": "Historical significance and innovation",
            "v_list": "Inclusion in V's recommended games list",
            "console_significance": "Significance to the console's identity",
            "mods_hacks": "Notable mods, hacks, or unofficial translations",
            "hidden_gems": "Community-recognized hidden gems from forums and Reddit"
        }

    def initialize(self) -> bool:
        """
        Initialize the Random provider
        
        Returns:
            bool: True if initialization was successful
        """
        self.initialized = True
        logger.info("RandomProvider initialized successfully")
        return True

    def is_available(self) -> bool:
        """
        Check if the Random provider is available for use
        
        Returns:
            bool: True if the provider is available
        """
        return self.initialized

    def evaluate_game(self, 
                     game_info: Dict[str, Any], 
                     criteria: List[str],
                     full_collection_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate a game with random scores for testing purposes
        
        Args:
            game_info: Dictionary containing game information
            criteria: List of criteria to evaluate
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            Dict containing evaluation results with scores and explanations
        """
        logger.info(f"Generating random evaluation for game: {game_info.get('name', 'Unknown')}")
        
        # Create a structure that matches what the filter engine expects
        evaluation = {
            "game_id": game_info.get("id", "unknown"),
            "game_name": game_info.get("name", "Unknown Game"),
            "scores": {},
            "explanations": {},
            "evaluations": {},  # This is the new format expected by filter_engine
            "overall_score": 0.0,
            "confidence": round(random.uniform(0.65, 0.95), 2)
        }
        
        total_score = 0.0
        criterion_evaluations = {}
        
        for criterion in criteria:
            # Generate a random score between 1.0 and 10.0
            score = round(random.uniform(1.0, 10.0), 1)
            total_score += score
            
            # Store the score in the old format (for backward compatibility)
            evaluation["scores"][criterion] = score
            
            # Generate a random explanation
            explanation = self._generate_random_explanation(criterion, score, game_info)
            evaluation["explanations"][criterion] = explanation
            
            # Add to the new evaluations format
            criterion_evaluations[criterion] = {
                "score": score,
                "explanation": explanation,
                "confidence": round(random.uniform(0.6, 0.9), 2)
            }
        
        # Add the evaluations in the expected format
        evaluation["evaluations"] = criterion_evaluations
        
        # Calculate overall score (average of all criteria scores)
        if criteria:
            evaluation["overall_score"] = round(total_score / len(criteria), 1)
        
        # Add an overall recommendation
        if criteria and evaluation["overall_score"] >= 5.0:
            evaluation["overall_recommendation"] = {
                "include": True,
                "reason": "This game scored well across the evaluation criteria."
            }
        else:
            evaluation["overall_recommendation"] = {
                "include": False,
                "reason": "This game did not score well enough across the evaluation criteria."
            }
        
        # Add low score exception for about 10% of games
        if random.random() < 0.1:
            # Adjust the score to be below 3.0 but still decide to keep it
            evaluation["overall_score"] = round(random.uniform(1.0, 2.9), 1)
            evaluation["overall_recommendation"] = {
                "include": True,
                "reason": "Despite low overall score, this game has historical importance or collector value."
            }
        
        return evaluation

    def batch_evaluate_games(self, 
                           games_info: List[Dict[str, Any]], 
                           criteria: List[str],
                           full_collection_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evaluate multiple games with random scores
        
        Args:
            games_info: List of dictionaries containing game information
            criteria: List of criteria to evaluate
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            List of dictionaries containing evaluation results
        """
        logger.info(f"Batch evaluating {len(games_info)} games with RandomProvider")
        
        results = []
        for game_info in games_info:
            evaluation = self.evaluate_game(game_info, criteria, full_collection_context)
            results.append(evaluation)
            
            # Simulate some processing time to make it feel realistic
            # Use a very short delay since this is just test data
            # random.uniform(0.05, 0.2)  # Uncomment in real implementation if needed
            
        return results

    def identify_special_cases(self,
                             games_info: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify special cases with randomized detection
        
        Args:
            games_info: List of dictionaries containing game information
            
        Returns:
            Dictionary mapping special case types to lists of affected games
        """
        special_cases = {
            "multi_disc": [],
            "regional_variants": [],
            "series": [],
            "collections": [],
            "unusual_naming": []
        }
        
        # Randomly assign some games to special cases
        for game in games_info:
            # Approximately 5% chance for each special case category
            for case_type in special_cases.keys():
                if random.random() < 0.05:
                    special_cases[case_type].append(game)
        
        return special_cases

    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider
        
        Returns:
            str: Provider name
        """
        return "Random Test Provider"

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the AI provider
        
        Returns:
            Dict containing provider information
        """
        return {
            "name": "Random Test Provider",
            "version": "1.0.0",
            "description": "Generates random evaluation scores for testing purposes",
            "capabilities": {
                "batch_processing": True,
                "special_case_detection": True
            },
            "cost": "Free (test provider)"
        }
        
    def _generate_random_explanation(self, criterion: str, score: float, game_info: Dict[str, Any]) -> str:
        """
        Generate a random explanation for a given criterion and score
        
        Args:
            criterion: The evaluation criterion
            score: The assigned score
            game_info: Game information
            
        Returns:
            str: A randomly generated explanation
        """
        game_name = game_info.get("name", "This game")
        
        # Get description for this criterion
        criterion_desc = self.criteria_descriptions.get(criterion, criterion)
        
        # Score ranges
        if score >= 8.0:
            quality = random.choice(["excellent", "outstanding", "exceptional", "remarkable", "impressive"])
            sentences = [
                f"{game_name} scores highly on {criterion_desc}.",
                f"For {criterion_desc}, {game_name} is {quality}.",
                f"This title shows {quality} qualities regarding {criterion_desc}.",
                f"Based on random evaluation, {game_name} receives top marks for {criterion_desc}."
            ]
        elif score >= 5.0:
            quality = random.choice(["good", "solid", "decent", "adequate", "reasonable"])
            sentences = [
                f"{game_name} has {quality} standing in terms of {criterion_desc}.",
                f"For {criterion_desc}, {game_name} performs at a {quality} level.",
                f"This title shows {quality} qualities for {criterion_desc}.",
                f"Based on random evaluation, {game_name} has {quality} marks for {criterion_desc}."
            ]
        else:
            quality = random.choice(["limited", "modest", "minimal", "below average", "questionable"])
            sentences = [
                f"{game_name} has {quality} significance in terms of {criterion_desc}.",
                f"For {criterion_desc}, {game_name} shows {quality} qualities.",
                f"This title demonstrates {quality} standing regarding {criterion_desc}.",
                f"Based on random evaluation, {game_name} receives {quality} marks for {criterion_desc}."
            ]
            
        return random.choice(sentences)