"""
Configuration management for DAT Filter AI application.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Default application configuration
DEFAULT_CONFIG = {
    "ai_provider": "gemini",
    "default_thresholds": {
        "metacritic": 7.0,
        "historical": 6.0,
        "v_list": 5.0,
        "console_significance": 7.0,
        "mods_hacks": 6.0
    },
    "default_criteria_weights": {
        "metacritic": 0.35,
        "historical": 0.25,
        "v_list": 0.15,
        "console_significance": 0.15,
        "mods_hacks": 0.10
    },
    "default_rule_config": {
        "multi_disc": {
            "mode": "all_or_none",
            "prefer": "complete"
        },
        "regional_variants": {
            "mode": "prefer_region",
            "preferred_regions": ["USA", "Europe", "World", "Japan"]
        },
        "mods_hacks": {
            "mode": "include_notable"
        }
    },
    "ui": {
        "theme": "light",
        "default_batch_size": 10,
        "table_rows_per_page": 100
    }
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load application configuration from file or use defaults
    
    Args:
        config_path: Path to configuration file (optional)
        
    Returns:
        Dictionary containing application configuration
    """
    logger = logging.getLogger(__name__)
    config = DEFAULT_CONFIG.copy()
    
    # If no config path specified, look in standard locations
    if not config_path:
        # Look in current directory
        if os.path.exists("config.json"):
            config_path = "config.json"
        # Look in user home directory
        else:
            home_config = os.path.join(os.path.expanduser("~"), ".config", "datfilterai", "config.json")
            if os.path.exists(home_config):
                config_path = home_config
    
    # Load from file if exists
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            
            # Update config with user values
            _update_config_recursive(config, user_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Falling back to default configuration")
    else:
        logger.info("Using default configuration")
    
    return config

def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    Save application configuration to file
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration file
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        return False

def _update_config_recursive(target: Dict[str, Any], source: Dict[str, Any]):
    """
    Recursively update a nested dictionary with values from another dictionary
    
    Args:
        target: Target dictionary to update
        source: Source dictionary with values to update
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # Recursively update nested dictionaries
            _update_config_recursive(target[key], value)
        else:
            # Update or add value
            target[key] = value

def get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration
    
    Returns:
        Dictionary containing default configuration
    """
    return DEFAULT_CONFIG.copy()
