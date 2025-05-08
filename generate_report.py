#!/usr/bin/env python3
"""
Script to generate reports and summaries for already filtered DAT files.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List

from core.dat_parser import DatParser
from core.export import ExportManager
from utils.text_visualizer import TextVisualizer
from utils.logging_config import setup_logging
import logging

def main():
    """Generate reports and summaries for already filtered DAT files."""
    parser = argparse.ArgumentParser(description="Generate reports for filtered DAT files")
    parser.add_argument("--input", "-i", help="Filtered DAT file path", required=True)
    parser.add_argument("--report", "-r", help="Output JSON report file path")
    parser.add_argument("--summary", "-s", help="Output text summary file path")
    parser.add_argument("--no-color", help="Disable colored output", action="store_true")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize components
    dat_parser = DatParser()
    export_manager = ExportManager()
    visualizer = TextVisualizer(use_color=not args.no_color)
    
    # Process the filtered DAT file
    try:
        # Parse the DAT file
        print(f"Parsing filtered DAT file: {args.input}...")
        parsed_data = dat_parser.parse_file(args.input)
        games = parsed_data['games']
        total_games = parsed_data.get('original_games_count', parsed_data['game_count'])
        print(f"Successfully parsed with {len(games)} games.")
        
        # Create dummy evaluations for the report
        evaluations = []
        for game in games:
            evaluations.append({
                "game_name": game["name"],
                "kept": True,
                "score": 7.0,  # Assign a default score
                "reasons": {
                    "metacritic": "Passed filter",
                    "historical": "Passed filter",
                    "v_list": "Passed filter",
                    "console_significance": "Passed filter",
                    "mods_hacks": "Not applicable"
                }
            })
        
        # Create dummy special cases for the report
        special_cases = {
            "multi_disc": [],
            "regional_variants": [],
            "console_families": [],
            "mods_hacks": []
        }
        
        # Print summary
        print(f"Filtered DAT contains {len(games)} of {total_games} games")
        
        # Export JSON report if requested
        if args.report:
            print(f"Exporting JSON report to: {args.report}")
            logger.info(f"Exporting JSON report to: {args.report}")
            success, message = export_manager.export_json_report(
                games,
                evaluations,
                special_cases,
                args.report
            )
            if success:
                print(f"Successfully exported JSON report to {args.report}")
                logger.info(f"Successfully exported JSON report: {message}")
            else:
                print(f"Failed to export JSON report: {message}")
                logger.error(f"Failed to export JSON report: {message}")
        
        # Export text summary if requested
        if args.summary:
            print(f"Exporting text summary to: {args.summary}")
            logger.info(f"Exporting text summary to: {args.summary}")
            
            # Generate proportional lists of games for top/worst/near-miss categories
            top_percentage = 0.1  # Top 10%
            
            # Calculate how many games to show in each category
            top_count = min(10, max(3, int(len(games) * top_percentage)))
            
            # Create a list of game names sorted by "score" (since we don't have real scores, just use alphabetical)
            sorted_games = sorted([g["name"] for g in games])
            top_games = sorted_games[:top_count]
            
            # Add evaluations to filtered games
            for game in games:
                # Create a simple evaluation object with default score
                game['_evaluation'] = {
                    'overall_score': 7.0,  # Default reasonable score
                    'kept': True,
                    'criteria': {
                        'metacritic': 'Passed filter',
                        'historical': 'Passed filter',
                        'v_list': 'Passed filter',
                        'console_significance': 'Passed filter',
                        'mods_hacks': 'Not applicable'
                    }
                }
            
            success, message = export_manager.export_text_summary(
                games,
                total_games,
                ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"],
                args.summary
            )
            if success:
                print(f"Successfully exported text summary to {args.summary}")
                logger.info(f"Successfully exported text summary: {message}")
            else:
                print(f"Failed to export text summary: {message}")
                logger.error(f"Failed to export text summary: {message}")
            
    except Exception as e:
        logger.error(f"Error processing filtered DAT file: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()