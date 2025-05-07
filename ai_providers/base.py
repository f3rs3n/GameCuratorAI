"""
Base class for AI providers that will be used for game evaluation.
This provides a common interface for different AI services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAIProvider(ABC):
    """Abstract base class defining the interface for AI providers"""

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the AI provider with necessary credentials and setup
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the AI provider is available for use
        
        Returns:
            bool: True if the provider is available, False otherwise
        """
        pass

    @abstractmethod
    def evaluate_game(self, 
                      game_info: Dict[str, Any], 
                      criteria: List[str],
                      full_collection_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate a game based on the specified criteria
        
        Args:
            game_info: Dictionary containing game information
            criteria: List of criteria to evaluate (e.g., "metacritic", "historical")
            full_collection_context: Optional additional context from the full collection
            
        Returns:
            Dict containing evaluation results with scores and explanations
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def identify_special_cases(self,
                              games_info: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify special cases like multi-disc games, regional variants, etc.
        
        Args:
            games_info: List of dictionaries containing game information
            
        Returns:
            Dictionary mapping special case types to lists of affected games
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider
        
        Returns:
            str: Provider name
        """
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the AI provider
        
        Returns:
            Dict containing provider information like version, capabilities, etc.
        """
        pass
