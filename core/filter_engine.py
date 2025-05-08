"""
Filter Engine module for evaluating and filtering games based on AI analysis.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple

from ai_providers.base import BaseAIProvider
from utils.api_usage_tracker import get_tracker

class FilterEngine:
    """Engine for filtering games based on AI evaluations and rule criteria."""
    
    def __init__(self, ai_provider: BaseAIProvider):
        """
        Initialize the filter engine with an AI provider
        
        Args:
            ai_provider: Instance of an AI provider
        """
        self.logger = logging.getLogger(__name__)
        self.ai_provider = ai_provider
        # Base threshold scores for each criterion
        self.threshold_scores = {
            "metacritic": 7.0,
            "historical": 6.0,
            "v_list": 5.0,
            "console_significance": 7.0,
            "mods_hacks": 6.0
        }
        # Global threshold modifier applied to all criteria
        self.global_threshold = 1.0  # 1.0 is neutral, lower is more lenient, higher is stricter
        self.criteria_weights = {
            "metacritic": 0.30,
            "historical": 0.20,
            "v_list": 0.30,  # Double weight for V's recommended list
            "console_significance": 0.12,
            "mods_hacks": 0.08
        }
    
    def set_threshold(self, criterion: str, value: float):
        """
        Set the threshold score for a criterion
        
        Args:
            criterion: The criterion to set the threshold for
            value: The threshold value (0.0 to 10.0)
        """
        if criterion in self.threshold_scores:
            self.threshold_scores[criterion] = max(0.0, min(10.0, value))
            self.logger.debug(f"Set threshold for {criterion} to {value}")
        else:
            self.logger.warning(f"Unknown criterion: {criterion}")
    
    def set_global_threshold(self, value: float):
        """
        Set the global threshold modifier
        
        Args:
            value: The global threshold modifier (0.5 to 1.5)
                  Lower values (< 1.0) make filtering more lenient
                  Higher values (> 1.0) make filtering more strict
                  1.0 is neutral (no modification)
        """
        # Limit range to 0.5 - 1.5 to prevent extreme values
        self.global_threshold = max(0.5, min(1.5, value))
        self.logger.debug(f"Set global threshold modifier to {self.global_threshold}")
        
    def set_weight(self, criterion: str, value: float):
        """
        Set the weight for a criterion
        
        Args:
            criterion: The criterion to set the weight for
            value: The weight value (0.0 to 1.0)
        """
        if criterion in self.criteria_weights:
            # Normalize weight to ensure sum of weights equals 1.0
            total_weight = sum(w for c, w in self.criteria_weights.items() if c != criterion)
            max_allowed = 1.0 - total_weight
            new_weight = max(0.0, min(max_allowed, value))
            
            self.criteria_weights[criterion] = new_weight
            self.logger.debug(f"Set weight for {criterion} to {new_weight}")
            
            # Renormalize other weights if needed
            self._normalize_weights()
        else:
            self.logger.warning(f"Unknown criterion: {criterion}")
    
    def _normalize_weights(self):
        """
        Normalize weights to ensure they sum to 1.0
        """
        total = sum(self.criteria_weights.values())
        if total == 0:
            # Equal weights if all are zero
            for c in self.criteria_weights:
                self.criteria_weights[c] = 1.0 / len(self.criteria_weights)
        elif total != 1.0:
            # Scale proportionally
            factor = 1.0 / total
            for c in self.criteria_weights:
                self.criteria_weights[c] *= factor
    
    def evaluate_game(self, 
                     game_info: Dict[str, Any], 
                     criteria: List[str],
                     collection_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate a single game using the AI provider
        
        Args:
            game_info: Dictionary containing game information
            criteria: List of criteria to evaluate
            collection_context: Optional context about the collection
            
        Returns:
            Dictionary with evaluation results
        """
        start_time = time.time()
        
        # Validate criteria
        valid_criteria = [c for c in criteria if c in self.threshold_scores]
        if len(valid_criteria) < len(criteria):
            unknown = set(criteria) - set(valid_criteria)
            self.logger.warning(f"Unknown criteria ignored: {unknown}")
        
        # If no valid criteria, use all available criteria
        if not valid_criteria:
            valid_criteria = list(self.threshold_scores.keys())
        
        # Evaluate using AI provider
        result = self.ai_provider.evaluate_game(game_info, valid_criteria, collection_context)
        
        # Add additional metadata
        result["_evaluation_time"] = time.time() - start_time
        result["_criteria_used"] = valid_criteria
        result["_thresholds_used"] = {c: self.threshold_scores[c] for c in valid_criteria}
        result["_weights_used"] = {c: self.criteria_weights[c] for c in valid_criteria}
        
        return result
    
    def filter_collection(self, 
                         collection: List[Dict[str, Any]], 
                         criteria: List[str],
                         batch_size: int = 10,
                         progress_callback=None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Filter a collection of games based on the specified criteria
        
        Args:
            collection: List of game dictionaries to filter
            criteria: List of criteria to use for filtering
            batch_size: Number of games to process in each batch
            progress_callback: Optional callback function for progress updates
                              Can receive a third parameter with the current batch results
            
        Returns:
            Tuple of (filtered_games, evaluation_results, provider_error, api_usage_data)
            provider_error is None if no error occurred, otherwise contains error information
            api_usage_data contains information about the API usage (tokens used, etc.)
        """
        self.logger.info(f"Starting to filter collection of {len(collection)} games")
        
        # Extract collection context for better AI evaluation
        collection_context = self._extract_collection_context(collection)
        
        # Process games in batches
        filtered_games = []
        all_evaluations = []
        
        total_games = len(collection)
        processed = 0
        
        # Process in batches
        for i in range(0, total_games, batch_size):
            batch = collection[i:i+batch_size]
            current_batch_results = []
            
            # Update progress
            if progress_callback:
                progress_callback(processed, total_games)
            
            self.logger.debug(f"Processing batch {i//batch_size + 1} ({len(batch)} games)")
            
            # Evaluate batch
            for game in batch:
                evaluation = self.evaluate_game(game, criteria, collection_context)
                
                # Check if there was an error with the provider
                if "error" in evaluation and "Provider not available" in evaluation["error"]:
                    self.logger.error(f"Provider error: {evaluation['error']} - stopping processing")
                    # Return early with a provider error flag
                    api_usage_data = {
                        "provider": self.ai_provider.get_provider_name().upper(),
                        "today_tokens": 0,
                        "month_tokens": 0,
                        "total_requests": 0,
                        "error": evaluation["error"]
                    }
                    return ([], all_evaluations, {"provider_error": evaluation["error"]}, api_usage_data)
                
                # Add evaluation to game and to results list
                game["_evaluation"] = evaluation
                all_evaluations.append(evaluation)
                
                # Check if game meets criteria
                meets_criteria = self._meets_criteria(evaluation, criteria)
                if meets_criteria:
                    filtered_games.append(game)
                
                # Store result for batch display
                # Extract overall score - check for different key formats from different providers
                overall_score = 0.0
                if "overall_score" in evaluation:
                    overall_score = evaluation["overall_score"]
                elif "quality_score" in evaluation:
                    overall_score = evaluation["quality_score"]
                elif "score" in evaluation:
                    overall_score = evaluation["score"]
                # Fallback method: average the scores if available
                elif "scores" in evaluation and evaluation["scores"]:
                    score_values = [float(score) for score in evaluation["scores"].values() if str(score).replace('.', '', 1).isdigit()]
                    if score_values:
                        overall_score = sum(score_values) / len(score_values)
                
                current_batch_results.append({
                    "game_name": game.get("name", "Unknown Game"),
                    "keep": meets_criteria,
                    "quality_score": overall_score,
                    "reason": evaluation.get("reason", "")
                })
                
                processed += 1
                
                # Update progress more frequently
                if progress_callback and processed % max(1, batch_size // 2) == 0:
                    progress_callback(processed, total_games, current_batch_results)
            
            # Show batch results at the end of batch
            if progress_callback and current_batch_results:
                progress_callback(processed, total_games, current_batch_results)
        
        # Final progress update
        if progress_callback:
            progress_callback(total_games, total_games)
        
        self.logger.info(f"Filtering complete. {len(filtered_games)} of {len(collection)} games passed filters.")
        
        # Get and log API usage information
        api_usage_data = None
        provider_name = self.ai_provider.get_provider_name().lower()
        
        if provider_name.lower() == "random":
            provider_name = "RANDOM TEST PROVIDER"  # More descriptive name for logs
            self.logger.info(f"API Usage for {provider_name}: 0 tokens used today")
            api_usage_data = {
                "provider": provider_name,
                "today_tokens": 0,
                "month_tokens": 0,
                "total_requests": 0
            }
        else:
            try:
                usage_tracker = get_tracker()
                
                # Get both 1-day and 30-day reports
                usage_report = usage_tracker.get_usage_report(provider_name)
                
                # Calculate tokens used today
                today_tokens = 0
                month_tokens = 0
                total_requests = 0
                
                if usage_report and provider_name in usage_report:
                    provider_data = usage_report[provider_name]
                    today_tokens = provider_data.get("current_day_tokens", 0)
                    month_tokens = provider_data.get("last_30_days_tokens", 0)
                    total_requests = provider_data.get("total_requests", 0)
                
                # Create API usage data dictionary
                api_usage_data = {
                    "provider": provider_name.upper(),
                    "today_tokens": today_tokens,
                    "month_tokens": month_tokens,
                    "total_requests": total_requests
                }
                
                # Log basic usage info
                self.logger.info(f"API Usage for {provider_name.upper()}: {today_tokens} tokens used today")
            except Exception as e:
                self.logger.warning(f"Failed to report API usage: {e}")
                api_usage_data = {
                    "provider": provider_name.upper(),
                    "today_tokens": 0,
                    "month_tokens": 0,
                    "total_requests": 0,
                    "error": str(e)
                }
                
        return filtered_games, all_evaluations, None, api_usage_data
    
    def _extract_collection_context(self, collection: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract context information from the collection to help the AI make better evaluations
        
        Args:
            collection: List of game dictionaries
            
        Returns:
            Dictionary with collection context
        """
        # Get a sample of game names for context
        sample_size = min(50, len(collection))
        game_names = [game.get("name", "Unknown") for game in collection[:sample_size]]
        
        # Extract console information if available
        consoles = set()
        
        # First try to get console name from the first game's header info (if present)
        if collection and "_header" in collection[0]:
            header = collection[0]["_header"]
            if header:
                for key in ["name", "description"]:
                    if key in header and header[key]:
                        # Extract console name from header (usually in format "Brand - Console Name")
                        header_value = header[key]
                        if " - " in header_value:
                            # Extract just the console name part
                            brand, console = header_value.split(" - ", 1)
                            # Remove any parenthetical text
                            if "(" in console:
                                console = console.split("(", 1)[0].strip()
                            consoles.add(console.strip())
                        else:
                            consoles.add(header_value)
        
        # Also check for console info in game entries
        for game in collection:
            for key in ["console", "platform", "system"]:
                if key in game and isinstance(game[key], dict) and game[key].get("text"):
                    consoles.add(game[key]["text"])
        
        # Get the primary console if available, otherwise join all detected consoles
        primary_console = ""
        if consoles:
            # Try to find the most specific console name
            if len(consoles) == 1:
                primary_console = list(consoles)[0]
            else:
                # If multiple consoles, use the most specific one (usually the longest name)
                primary_console = max(consoles, key=len)
        
        return {
            "collection_size": len(collection),
            "sample_games": game_names,
            "consoles": list(consoles),
            "console": primary_console,  # Add single primary console for the AI provider
            "evaluation_criteria": list(self.threshold_scores.keys()),
            "threshold_scores": self.threshold_scores,
            "criteria_weights": self.criteria_weights,
            "global_threshold": self.global_threshold
        }
    
    def _meets_criteria(self, evaluation: Dict[str, Any], criteria: List[str]) -> bool:
        """
        Check if a game's evaluation meets the threshold criteria
        
        Args:
            evaluation: Game evaluation results
            criteria: List of criteria to check
            
        Returns:
            True if the game meets the criteria, False otherwise
        """
        # If there was an error in evaluation, fail
        if "error" in evaluation:
            return False
        
        # If the AI explicitly recommends inclusion/exclusion
        if "overall_recommendation" in evaluation and "include" in evaluation["overall_recommendation"]:
            return evaluation["overall_recommendation"]["include"]
        
        # Check individual criteria
        if "evaluations" in evaluation:
            evals = evaluation["evaluations"]
            
            # Calculate weighted score
            weighted_score = 0.0
            total_weight = 0.0
            
            for criterion in criteria:
                if criterion in evals and "score" in evals[criterion]:
                    score = float(evals[criterion]["score"])
                    weight = self.criteria_weights.get(criterion, 0.1)
                    
                    weighted_score += score * weight
                    total_weight += weight
            
            # If we have weights, check against thresholds
            if total_weight > 0:
                normalized_score = weighted_score / total_weight
                
                # Calculate base threshold (before applying global modifier)
                base_threshold = sum(self.threshold_scores.get(c, 5.0) * self.criteria_weights.get(c, 0.1) 
                                   for c in criteria) / total_weight
                
                # Apply global threshold modifier
                adjusted_threshold = base_threshold * self.global_threshold
                
                self.logger.debug(f"Game evaluation: score={normalized_score:.2f}, " +
                                f"threshold={base_threshold:.2f}, " +
                                f"adjusted={adjusted_threshold:.2f}, " +
                                f"modifier={self.global_threshold:.2f}")
                
                return normalized_score >= adjusted_threshold
        
        # Default to conservative inclusion
        return True
    
    def save_evaluations(self, evaluations: List[Dict[str, Any]], file_path: str) -> bool:
        """
        Save evaluation results to a JSON file
        
        Args:
            evaluations: List of evaluation results
            file_path: Path to save the evaluations
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(evaluations, f, indent=2)
            self.logger.info(f"Saved {len(evaluations)} evaluations to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving evaluations: {e}")
            return False
    
    def load_evaluations(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load evaluation results from a JSON file
        
        Args:
            file_path: Path to load the evaluations from
            
        Returns:
            List of evaluation results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                evaluations = json.load(f)
            self.logger.info(f"Loaded {len(evaluations)} evaluations from {file_path}")
            return evaluations
        except Exception as e:
            self.logger.error(f"Error loading evaluations: {e}")
            return []
