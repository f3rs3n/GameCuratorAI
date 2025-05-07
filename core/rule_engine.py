"""
Rule engine for handling special cases in game data such as multi-disc games,
regional variants, console naming patterns, etc.
"""

import logging
import re
from typing import Dict, List, Any, Callable, Tuple

class RuleEngine:
    """Rule engine for handling special cases in game data."""
    
    def __init__(self):
        """Initialize the rule engine."""
        self.logger = logging.getLogger(__name__)
        self.rules = {}
        self.special_cases = {}
        
        # Register default rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register the default set of rules for special cases."""
        # Multi-disc game detection
        self.register_rule(
            "multi_disc", 
            self._detect_multi_disc_games,
            "Detect multi-disc games and group them together"
        )
        
        # Regional variant detection
        self.register_rule(
            "regional_variants",
            self._detect_regional_variants,
            "Detect regional variants of the same game"
        )
        
        # Console naming pattern detection
        self.register_rule(
            "console_naming",
            self._detect_console_naming_patterns,
            "Detect and normalize console-specific naming patterns"
        )
        
        # Mods and hacks detection
        self.register_rule(
            "mods_hacks",
            self._detect_mods_and_hacks,
            "Identify game mods and hacks"
        )
    
    def register_rule(self, rule_id: str, rule_func: Callable, description: str):
        """
        Register a new rule for handling special cases
        
        Args:
            rule_id: Unique identifier for the rule
            rule_func: Function that implements the rule
            description: Description of what the rule does
        """
        self.rules[rule_id] = {
            "func": rule_func,
            "description": description,
            "enabled": True
        }
        self.logger.debug(f"Registered rule: {rule_id} - {description}")
    
    def enable_rule(self, rule_id: str, enabled: bool = True):
        """
        Enable or disable a rule
        
        Args:
            rule_id: ID of the rule to enable/disable
            enabled: True to enable, False to disable
        """
        if rule_id in self.rules:
            self.rules[rule_id]["enabled"] = enabled
            self.logger.debug(f"Rule {rule_id} {'enabled' if enabled else 'disabled'}")
        else:
            self.logger.warning(f"Unknown rule: {rule_id}")
    
    def process_collection(self, collection: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a collection of games to identify special cases
        
        Args:
            collection: List of game dictionaries
            
        Returns:
            Dictionary with special cases and processed collection
        """
        self.logger.info(f"Processing collection of {len(collection)} games for special cases")
        
        # Reset special cases
        self.special_cases = {}
        
        # Apply each enabled rule
        for rule_id, rule in self.rules.items():
            if rule["enabled"]:
                self.logger.debug(f"Applying rule: {rule_id}")
                rule["func"](collection)
        
        return {
            "special_cases": self.special_cases,
            "processed_collection": collection
        }
    
    def get_special_cases(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the identified special cases
        
        Returns:
            Dictionary mapping special case types to lists of affected games
        """
        return self.special_cases
    
    def get_groups(self, group_type: str) -> List[List[Dict[str, Any]]]:
        """
        Get groups of related games by type
        
        Args:
            group_type: Type of grouping (e.g., "multi_disc", "regional_variants")
            
        Returns:
            List of game groups, where each group is a list of related games
        """
        return self.special_cases.get(group_type, {}).get("groups", [])
    
    def _detect_multi_disc_games(self, collection: List[Dict[str, Any]]):
        """
        Detect multi-disc games in the collection
        
        Args:
            collection: List of game dictionaries
        """
        # Common patterns for multi-disc games
        disc_patterns = [
            r'\(Disc (\d+)(.*)\)',
            r'\(CD (\d+)(.*)\)',
            r'- (Disc|CD) (\d+)(.*)',
            r'_(Disc|CD)(\d+)(.*)',
            r' (Disc|CD)(\d+)(.*)'
        ]
        
        # Combine patterns into a single regex
        combined_pattern = '|'.join(f'({pattern})' for pattern in disc_patterns)
        regex = re.compile(combined_pattern, re.IGNORECASE)
        
        # Group games by base name (without disc information)
        base_names = {}
        multi_disc_games = []
        
        for game in collection:
            name = game.get("name", "")
            if not name:
                continue
            
            match = regex.search(name)
            if match:
                # Extract base name by removing disc information
                base_name = name.split(match.group(0))[0].strip()
                
                if base_name not in base_names:
                    base_names[base_name] = []
                
                base_names[base_name].append(game)
        
        # Filter for actual multi-disc games (more than one disc)
        for base_name, games in base_names.items():
            if len(games) > 1:
                multi_disc_games.append(games)
        
        # Store results
        self.special_cases["multi_disc"] = {
            "count": len(multi_disc_games),
            "groups": multi_disc_games
        }
        
        self.logger.info(f"Detected {len(multi_disc_games)} multi-disc game sets")
    
    def _detect_regional_variants(self, collection: List[Dict[str, Any]]):
        """
        Detect regional variants of games
        
        Args:
            collection: List of game dictionaries
        """
        # Common patterns for regional variants
        region_patterns = {
            "USA": [r'\(USA\)', r'\(US\)', r'\(U\)', r'\(America\)'],
            "Europe": [r'\(Europe\)', r'\(EU\)', r'\(E\)', r'\(PAL\)'],
            "Japan": [r'\(Japan\)', r'\(J\)', r'\(JP\)', r'\(NTSC-J\)'],
            "World": [r'\(World\)', r'\(W\)', r'\(International\)']
        }
        
        # Create regex patterns for each region
        region_regex = {}
        for region, patterns in region_patterns.items():
            region_regex[region] = re.compile('|'.join(f'({pattern})' for pattern in patterns), re.IGNORECASE)
        
        # Group games by base name (without region information)
        base_names = {}
        
        for game in collection:
            name = game.get("name", "")
            if not name:
                continue
            
            # Detect region
            detected_region = None
            region_match = None
            
            for region, regex in region_regex.items():
                match = regex.search(name)
                if match:
                    detected_region = region
                    region_match = match.group(0)
                    break
            
            if detected_region and region_match:
                # Extract base name by removing region information
                base_name = name.replace(region_match, "").strip()
                # Clean up parentheses and extra spaces
                base_name = re.sub(r'\(\s*\)', '', base_name).strip()
                
                if base_name not in base_names:
                    base_names[base_name] = []
                
                base_names[base_name].append({
                    "game": game,
                    "region": detected_region
                })
        
        # Filter for actual regional variants (more than one region)
        regional_variants = []
        
        for base_name, variants in base_names.items():
            if len(variants) > 1 and len(set(v["region"] for v in variants)) > 1:
                regional_variants.append([v["game"] for v in variants])
        
        # Store results
        self.special_cases["regional_variants"] = {
            "count": len(regional_variants),
            "groups": regional_variants
        }
        
        self.logger.info(f"Detected {len(regional_variants)} games with regional variants")
    
    def _detect_console_naming_patterns(self, collection: List[Dict[str, Any]]):
        """
        Detect console-specific naming patterns
        
        Args:
            collection: List of game dictionaries
        """
        # Common console naming patterns
        console_patterns = {
            "Nintendo": [
                r'Nintendo (.*) - (.*)',
                r'\(Nintendo (.*)\)'
            ],
            "Sony": [
                r'(PlayStation|PS1|PS2|PS3|PS4|PS5|PSP|PS Vita) - (.*)',
                r'\((PlayStation|PS1|PS2|PS3|PS4|PS5|PSP|PS Vita)\)'
            ],
            "Microsoft": [
                r'(Xbox|Xbox 360|Xbox One|Xbox Series X) - (.*)',
                r'\((Xbox|Xbox 360|Xbox One|Xbox Series X)\)'
            ],
            "Sega": [
                r'(Sega|Genesis|Mega Drive|Dreamcast|Saturn|Master System) - (.*)',
                r'\((Sega|Genesis|Mega Drive|Dreamcast|Saturn|Master System)\)'
            ]
        }
        
        # Create regex patterns for each console family
        console_regex = {}
        for console, patterns in console_patterns.items():
            console_regex[console] = re.compile('|'.join(f'({pattern})' for pattern in patterns), re.IGNORECASE)
        
        # Group games by console naming pattern
        console_groups = {}
        
        for console, regex in console_regex.items():
            matches = []
            
            for game in collection:
                name = game.get("name", "")
                if not name:
                    continue
                
                if regex.search(name):
                    matches.append(game)
            
            if matches:
                console_groups[console] = matches
        
        # Store results
        self.special_cases["console_naming"] = {
            "count": sum(len(games) for games in console_groups.values()),
            "by_console": {console: len(games) for console, games in console_groups.items()},
            "groups": [games for games in console_groups.values()]
        }
        
        self.logger.info(f"Detected console naming patterns for {len(console_groups)} console families")
    
    def _detect_mods_and_hacks(self, collection: List[Dict[str, Any]]):
        """
        Detect game mods and hacks
        
        Args:
            collection: List of game dictionaries
        """
        # Common patterns for mods and hacks
        mod_patterns = [
            r'\b(hack|mod|modified|modded)\b',
            r'\b(translation|translated|fan translation)\b',
            r'\b(enhancement|enhanced|improvement|improved)\b',
            r'\b(patch|patched|fix|fixed)\b',
            r'\b(rebalance|rebalanced|overhaul)\b'
        ]
        
        # Combine patterns into a single regex
        regex = re.compile('|'.join(f'({pattern})' for pattern in mod_patterns), re.IGNORECASE)
        
        # Find games that match mod patterns
        mods_and_hacks = []
        
        for game in collection:
            name = game.get("name", "")
            description = ""
            
            # Check description field if available
            if "description" in game and isinstance(game["description"], dict):
                description = game["description"].get("text", "")
            
            if regex.search(name) or (description and regex.search(description)):
                mods_and_hacks.append(game)
        
        # Store results
        self.special_cases["mods_hacks"] = {
            "count": len(mods_and_hacks),
            "games": mods_and_hacks
        }
        
        self.logger.info(f"Detected {len(mods_and_hacks)} game mods and hacks")
    
    def apply_rules_to_filtered_games(self, 
                                    filtered_games: List[Dict[str, Any]], 
                                    rules_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply special case rules to a list of filtered games
        
        Args:
            filtered_games: List of games that passed the initial filtering
            rules_config: Configuration for how to handle special cases
            
        Returns:
            Updated list of filtered games
        """
        result = filtered_games.copy()
        
        # Apply multi-disc rule if configured
        if "multi_disc" in rules_config and "multi_disc" in self.special_cases:
            result = self._apply_multi_disc_rule(result, rules_config["multi_disc"])
        
        # Apply regional variants rule if configured
        if "regional_variants" in rules_config and "regional_variants" in self.special_cases:
            result = self._apply_regional_variants_rule(result, rules_config["regional_variants"])
        
        # Apply mods/hacks rule if configured
        if "mods_hacks" in rules_config and "mods_hacks" in self.special_cases:
            result = self._apply_mods_hacks_rule(result, rules_config["mods_hacks"])
        
        return result
    
    def _apply_multi_disc_rule(self, 
                              filtered_games: List[Dict[str, Any]], 
                              rule_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply the multi-disc rule to filtered games
        
        Args:
            filtered_games: List of games that passed the initial filtering
            rule_config: Configuration for how to handle multi-disc cases
            
        Returns:
            Updated list of filtered games
        """
        mode = rule_config.get("mode", "all_or_none")
        
        if mode == "all_or_none":
            # Either include all discs or none
            multi_disc_groups = self.special_cases["multi_disc"]["groups"]
            
            for group in multi_disc_groups:
                # Get game IDs for this group
                group_ids = [g.get("id", g.get("name", "")) for g in group]
                
                # Check if any game in this group is in the filtered list
                filtered_group_games = [g for g in filtered_games if g.get("id", g.get("name", "")) in group_ids]
                
                if 0 < len(filtered_group_games) < len(group):
                    # Some but not all discs are in the filtered list
                    if rule_config.get("prefer", "complete") == "complete":
                        # Add missing discs
                        for game in group:
                            game_id = game.get("id", game.get("name", ""))
                            if game_id not in [g.get("id", g.get("name", "")) for g in filtered_games]:
                                filtered_games.append(game)
                                self.logger.debug(f"Added missing disc: {game.get('name', '')}")
                    else:
                        # Remove partial set
                        filtered_games = [g for g in filtered_games if g.get("id", g.get("name", "")) not in group_ids]
                        self.logger.debug(f"Removed partial multi-disc set: {group[0].get('name', '').split('(')[0]}")
        
        elif mode == "first_disc_only":
            # Only include the first disc of each set
            multi_disc_groups = self.special_cases["multi_disc"]["groups"]
            
            for group in multi_disc_groups:
                # Sort by disc number (simple alphanumeric sort should work for most cases)
                sorted_group = sorted(group, key=lambda g: g.get("name", ""))
                
                # Keep only the first disc if multiple are in the filtered list
                group_ids = [g.get("id", g.get("name", "")) for g in sorted_group]
                
                # Check how many of this group are in the filtered list
                filtered_group_games = [g for g in filtered_games if g.get("id", g.get("name", "")) in group_ids]
                
                if len(filtered_group_games) > 1:
                    # Remove all but the first disc
                    first_disc_id = sorted_group[0].get("id", sorted_group[0].get("name", ""))
                    filtered_games = [g for g in filtered_games if 
                                    g.get("id", g.get("name", "")) not in group_ids or 
                                    g.get("id", g.get("name", "")) == first_disc_id]
                    
                    self.logger.debug(f"Kept only first disc for set: {sorted_group[0].get('name', '')}")
        
        return filtered_games
    
    def _apply_regional_variants_rule(self, 
                                    filtered_games: List[Dict[str, Any]], 
                                    rule_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply the regional variants rule to filtered games
        
        Args:
            filtered_games: List of games that passed the initial filtering
            rule_config: Configuration for how to handle regional variants
            
        Returns:
            Updated list of filtered games
        """
        mode = rule_config.get("mode", "prefer_region")
        preferred_regions = rule_config.get("preferred_regions", ["USA", "Europe", "World", "Japan"])
        
        if mode == "prefer_region":
            regional_groups = self.special_cases["regional_variants"]["groups"]
            
            for group in regional_groups:
                # Get game IDs for this group
                group_ids = [g.get("id", g.get("name", "")) for g in group]
                
                # Check which games in this group are in the filtered list
                filtered_group_games = [g for g in filtered_games if g.get("id", g.get("name", "")) in group_ids]
                
                if len(filtered_group_games) > 1:
                    # Multiple regional variants are in the filtered list
                    # Keep only the preferred one based on order of preferred_regions
                    
                    # First, detect the region of each game
                    games_with_regions = []
                    for game in filtered_group_games:
                        name = game.get("name", "")
                        detected_region = None
                        
                        for region in preferred_regions:
                            if re.search(f'\\({region}\\)', name, re.IGNORECASE):
                                detected_region = region
                                break
                        
                        games_with_regions.append((game, detected_region))
                    
                    # Find the game with the most preferred region
                    selected_game = None
                    
                    for region in preferred_regions:
                        for game, game_region in games_with_regions:
                            if game_region == region:
                                selected_game = game
                                break
                        
                        if selected_game:
                            break
                    
                    # If no preferred region found, just keep the first one
                    if not selected_game and games_with_regions:
                        selected_game = games_with_regions[0][0]
                    
                    if selected_game:
                        # Remove all other variants
                        selected_id = selected_game.get("id", selected_game.get("name", ""))
                        filtered_games = [g for g in filtered_games if 
                                        g.get("id", g.get("name", "")) not in group_ids or 
                                        g.get("id", g.get("name", "")) == selected_id]
                        
                        self.logger.debug(f"Kept preferred region for: {selected_game.get('name', '')}")
        
        return filtered_games
    
    def _apply_mods_hacks_rule(self, 
                              filtered_games: List[Dict[str, Any]], 
                              rule_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply the mods/hacks rule to filtered games
        
        Args:
            filtered_games: List of games that passed the initial filtering
            rule_config: Configuration for how to handle mods and hacks
            
        Returns:
            Updated list of filtered games
        """
        mode = rule_config.get("mode", "include_notable")
        
        if mode == "exclude_all":
            # Remove all detected mods and hacks
            if "mods_hacks" in self.special_cases and "games" in self.special_cases["mods_hacks"]:
                mod_ids = [g.get("id", g.get("name", "")) for g in self.special_cases["mods_hacks"]["games"]]
                filtered_games = [g for g in filtered_games if g.get("id", g.get("name", "")) not in mod_ids]
                
                self.logger.debug(f"Excluded {len(mod_ids)} mods and hacks")
        
        # For "include_notable" mode, we rely on the AI evaluation to determine
        # which mods/hacks are notable, so no additional filtering is needed here
        
        return filtered_games
