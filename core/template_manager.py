"""
Template manager for DAT Filter AI.
This module handles saving, loading, and management of filtering templates.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"))

class TemplateManager:
    """Manager for filtering templates"""
    
    def __init__(self, templates_dir: str = TEMPLATES_DIR):
        """
        Initialize the template manager
        
        Args:
            templates_dir: Directory where templates are stored
        """
        self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)
        logger.info(f"Template manager initialized with directory: {self.templates_dir}")
    
    def get_available_templates(self) -> List[str]:
        """
        Get a list of available template names
        
        Returns:
            List of template names (without extension)
        """
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                templates.append(filename[:-5])  # Remove .json extension
        return templates
    
    def save_template(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Save a template configuration
        
        Args:
            name: Template name
            config: Template configuration dictionary
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Ensure the template name is valid
            if not name or not all(c.isalnum() or c in ['-', '_'] for c in name):
                logger.error(f"Invalid template name: {name}")
                return False
            
            filepath = os.path.join(self.templates_dir, f"{name}.json")
            
            # Add metadata to the config
            config['_template_name'] = name
            config['_template_version'] = '1.0'
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Template saved: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save template '{name}': {e}")
            return False
    
    def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a template configuration
        
        Args:
            name: Template name
            
        Returns:
            Template configuration or None if not found
        """
        try:
            filepath = os.path.join(self.templates_dir, f"{name}.json")
            if not os.path.exists(filepath):
                logger.error(f"Template not found: {name}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"Template loaded: {name}")
            return config
        except Exception as e:
            logger.error(f"Failed to load template '{name}': {e}")
            return None
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template
        
        Args:
            name: Template name
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            filepath = os.path.join(self.templates_dir, f"{name}.json")
            if not os.path.exists(filepath):
                logger.error(f"Template not found: {name}")
                return False
            
            os.remove(filepath)
            logger.info(f"Template deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete template '{name}': {e}")
            return False
    
    def create_default_templates(self) -> None:
        """Create default templates if they don't exist"""
        # Essentials template - focuses on historically significant games
        essentials = {
            "name": "Essentials",
            "description": "Keep only the most essential, historically significant games",
            "criteria": ["metacritic", "historical", "console_significance"],
            "thresholds": {
                "metacritic": 8.0,
                "historical": 7.0,
                "v_list": 0.0,  # Not used
                "console_significance": 7.0,
                "mods_hacks": 0.0  # Not used
            },
            "provider": "openai",  # Recommended provider for best results
            "batch_size": 5
        }
        
        # Complete template - keeps most games
        complete = {
            "name": "Complete",
            "description": "Keep a complete collection with more lenient filtering",
            "criteria": ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"],
            "thresholds": {
                "metacritic": 5.0,
                "historical": 4.0,
                "v_list": 4.0,
                "console_significance": 4.0,
                "mods_hacks": 4.0
            },
            "provider": "openai",
            "batch_size": 10
        }
        
        # Balanced template - moderate filtering
        balanced = {
            "name": "Balanced",
            "description": "Balanced filtering keeping games of moderate to high significance",
            "criteria": ["metacritic", "historical", "v_list", "console_significance"],
            "thresholds": {
                "metacritic": 6.0,
                "historical": 6.0,
                "v_list": 5.0,
                "console_significance": 6.0,
                "mods_hacks": 0.0  # Not used
            },
            "provider": "openai",
            "batch_size": 5
        }
        
        # Testing template - uses random provider for quick testing
        testing = {
            "name": "Testing",
            "description": "Quick testing template using random provider",
            "criteria": ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"],
            "thresholds": {
                "metacritic": 7.0,
                "historical": 6.0,
                "v_list": 5.0,
                "console_significance": 7.0,
                "mods_hacks": 6.0
            },
            "provider": "random",
            "batch_size": 20
        }
        
        # Save the default templates
        if "Essentials" not in self.get_available_templates():
            self.save_template("Essentials", essentials)
        
        if "Complete" not in self.get_available_templates():
            self.save_template("Complete", complete)
        
        if "Balanced" not in self.get_available_templates():
            self.save_template("Balanced", balanced)
        
        if "Testing" not in self.get_available_templates():
            self.save_template("Testing", testing)