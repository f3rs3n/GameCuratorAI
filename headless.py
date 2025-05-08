#!/usr/bin/env python3
"""
DAT Filter AI - Headless version with text-based UI.
Primary interface for filtering and curating video game collections from XML-formatted .dat files.
Features rich text visualization, detailed evaluations, and rule enforcement for proper handling
of multi-disc games and other special cases.
"""

import os
import sys
import logging
import argparse
import json
import time
from typing import Dict, Any, List

from utils.logging_config import setup_logging
from utils.config import load_config
from utils.text_visualizer import TextVisualizer
from core.dat_parser import DatParser
from core.filter_engine import FilterEngine
from core.rule_engine import RuleEngine
from core.export import ExportManager
from ai_providers import get_provider, AVAILABLE_PROVIDERS

def main():
    """Main entry point for the DAT Filter AI application."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="DAT Filter AI - Video Game Collection Curator")
    parser.add_argument("--input", "-i", help="Input DAT file path", required=True)
    parser.add_argument("--output", "-o", help="Output DAT file path")
    parser.add_argument("--provider", "-p", help=f"AI provider to use {list(AVAILABLE_PROVIDERS.keys())}", default="gemini")
    parser.add_argument("--criteria", "-c", help="Comma-separated list of criteria to evaluate", 
                       default="metacritic,historical,v_list,console_significance,mods_hacks")
    parser.add_argument("--batch-size", "-b", help="Batch size for processing", type=int, default=10)
    parser.add_argument("--report", "-r", help="Generate JSON report file path")
    parser.add_argument("--summary", "-s", help="Generate text summary file path")
    parser.add_argument("--no-color", help="Disable colored output", action="store_true")
    parser.add_argument("--game-detail", "-g", help="Show detailed evaluation for a specific game (by name)")
    parser.add_argument("--debug", "-d", help="Enable debug logging", action="store_true")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting DAT Filter AI application")
    
    # Initialize text visualizer
    visualizer = TextVisualizer(use_color=not args.no_color)
    
    # Load configuration
    config = load_config()
    logger.debug("Configuration loaded")
    
    # Initialize components
    dat_parser = DatParser()
    
    # Initialize AI provider
    try:
        ai_provider = get_provider(args.provider)
        ai_provider_initialized = ai_provider.initialize()
        if not ai_provider_initialized:
            logger.warning(f"AI provider '{args.provider}' failed to initialize")
            logger.info("Falling back to random provider")
            ai_provider = get_provider("random")
            ai_provider.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize AI provider: {e}")
        logger.info("Falling back to random provider")
        ai_provider = get_provider("random")
        ai_provider.initialize()
    
    filter_engine = FilterEngine(ai_provider)
    rule_engine = RuleEngine()
    export_manager = ExportManager()
    
    # Process the DAT file
    try:
        # Use the correct input directory (ToFilter) if not already specified
        input_path = args.input
        if not os.path.exists(input_path) and os.path.exists(os.path.join("ToFilter", os.path.basename(input_path))):
            input_path = os.path.join("ToFilter", os.path.basename(input_path))
            logger.info(f"Using path from ToFilter directory: {input_path}")
            
        # Parse the DAT file
        print(f"Parsing DAT file: {input_path}...")
        logger.info(f"Parsing DAT file: {input_path}")
        parsed_data = dat_parser.parse_file(input_path)
        print(f"Successfully parsed with {parsed_data['game_count']} games.")
        
        # Get list of criteria
        criteria = args.criteria.split(",")
        
        # Apply filters
        print(f"Filtering collection with criteria: {', '.join(criteria)}...")
        logger.info(f"Filtering collection with criteria: {criteria}")
        
        # Progress bar setup
        start_time = time.time()
        
        def progress_callback(current, total):
            """Progress reporting with game-themed visual feedback"""
            percentage = int(100 * current / total) if total > 0 else 0
            
            elapsed = time.time() - start_time
            games_per_sec = current / elapsed if elapsed > 0 else 0
            
            # Calculate ETA
            if games_per_sec > 0 and current < total:
                eta = (total - current) / games_per_sec
                eta_str = f"ETA: {int(eta//60)}m {int(eta%60)}s"
            else:
                eta_str = "ETA: calculating..."
            
            # Use the game-themed progress display
            progress_display = visualizer.display_game_themed_progress(
                current, total, games_per_sec, eta_str
            )
            
            sys.stdout.write(f"\r{progress_display}")
            sys.stdout.flush()
            
            logger.info(f"Processing: {current}/{total} games ({percentage}%)")
        
        filtered_games, evaluations, provider_error = filter_engine.filter_collection(
            parsed_data['games'],
            criteria,
            args.batch_size,
            progress_callback
        )
        
        # Check for provider errors
        if provider_error:
            print(f"\nError: {provider_error.get('provider_error', 'Unknown provider error')}")
            logger.error(f"Provider error: {provider_error}")
            sys.exit(1)
        
        # Finish progress bar
        print("\n")
        
        # Process the collection to identify special cases
        print("Identifying special cases...")
        logger.info("Identifying special cases...")
        result = rule_engine.process_collection(parsed_data['games'])
        special_cases = result['special_cases']
        
        # Apply the multi-disc rule to ensure proper grouping
        multi_disc_rule_config = {
            "multi_disc": {
                "mode": "all_or_none",
                "prefer": "complete"
            }
        }
        
        # Apply rules to filtered games
        print("Applying multi-disc rules...")
        filtered_games = rule_engine.apply_rules_to_filtered_games(
            filtered_games,
            multi_disc_rule_config
        )
        
        # Print summary
        print(f"Filtering complete: {len(filtered_games)} of {parsed_data['game_count']} games kept")
        logger.info(f"Filtering complete: {len(filtered_games)} of {parsed_data['game_count']} games kept")
        
        # Show filtering results
        visualizer.display_filtering_results(
            filtered_games,
            parsed_data['game_count'],
            criteria
        )
        
        # Show special cases
        visualizer.display_special_cases(special_cases)
        
        # Show detailed evaluation for a specific game if requested
        if args.game_detail:
            found = False
            for game in parsed_data['games']:
                if args.game_detail.lower() in game.get("name", "").lower():
                    # Find the evaluation for this game
                    game_evaluation = None
                    game_id = game.get("id", game.get("name", ""))
                    
                    for eval_data in evaluations:
                        if eval_data.get("game_name", "") == game.get("name", ""):
                            game_evaluation = eval_data
                            break
                    
                    if game_evaluation:
                        visualizer.display_game_evaluation(game, game_evaluation)
                        found = True
                        break
            
            if not found:
                print(f"Game not found: {args.game_detail}")
        
        # Export filtered DAT if requested
        if args.output:
            # Use Filtered directory if not already specified
            output_path = args.output
            if not "/" in output_path and not "\\" in output_path:
                output_path = os.path.join("Filtered", output_path)
                logger.info(f"Using output path in Filtered directory: {output_path}")
                
            print(f"Exporting filtered DAT to: {output_path}")
            logger.info(f"Exporting filtered DAT to: {output_path}")
            success, message = export_manager.export_dat_file(
                filtered_games,
                parsed_data,
                output_path,
                {"filter_criteria": criteria}
            )
            if success:
                print(f"Successfully exported filtered DAT with {len(filtered_games)} games to {output_path}")
                logger.info(f"Successfully exported filtered DAT: {message}")
            else:
                print(f"Failed to export filtered DAT: {message}")
                logger.error(f"Failed to export filtered DAT: {message}")
        
        # Export JSON report if requested
        if args.report:
            # Use Filtered directory if not already specified
            report_path = args.report
            if not "/" in report_path and not "\\" in report_path:
                report_path = os.path.join("Filtered", report_path)
                logger.info(f"Using report path in Filtered directory: {report_path}")
                
            print(f"Exporting JSON report to: {report_path}")
            logger.info(f"Exporting JSON report to: {report_path}")
            success, message = export_manager.export_json_report(
                filtered_games,
                evaluations,
                special_cases,
                report_path
            )
            if success:
                print(f"Successfully exported JSON report to {report_path}")
                logger.info(f"Successfully exported JSON report: {message}")
            else:
                print(f"Failed to export JSON report: {message}")
                logger.error(f"Failed to export JSON report: {message}")
        
        # Export text summary if requested
        if args.summary:
            # Use Filtered directory if not already specified
            summary_path = args.summary
            if not "/" in summary_path and not "\\" in summary_path:
                summary_path = os.path.join("Filtered", summary_path)
                logger.info(f"Using summary path in Filtered directory: {summary_path}")
                
            print(f"Exporting text summary to: {summary_path}")
            logger.info(f"Exporting text summary to: {summary_path}")
            success, message = export_manager.export_text_summary(
                filtered_games,
                parsed_data['game_count'],
                criteria,
                summary_path
            )
            if success:
                print(f"Successfully exported text summary to {summary_path}")
                logger.info(f"Successfully exported text summary: {message}")
            else:
                print(f"Failed to export text summary: {message}")
                logger.error(f"Failed to export text summary: {message}")
        
    except Exception as e:
        logger.error(f"Error processing DAT file: {e}", exc_info=True)
        print(f"Error processing DAT file: {e}")
        return 1
    
    print("\nDAT Filter AI processing completed successfully")
    logger.info("DAT Filter AI processing completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())