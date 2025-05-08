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
    parser.add_argument("--allow-random-fallback", help="Allow fallback to Random provider if API key is missing/invalid", action="store_true")
    
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
        
        # Verify that the requested provider can be initialized
        ai_provider_initialized = ai_provider.initialize()
        
        if not ai_provider_initialized:
            # Check if it's an API key issue
            if args.provider.lower() in ['openai', 'gemini']:
                key_name = "OPENAI_API_KEY" if args.provider.lower() == 'openai' else "GEMINI_API_KEY"
                
                if not os.environ.get(key_name):
                    # Show helpful message about missing API key
                    print(f"ERROR: {args.provider.upper()} API key not found.")
                    if args.provider.lower() == 'openai':
                        print("You need an OpenAI API key to use this provider.")
                        print("You can get an API key at https://platform.openai.com/")
                    elif args.provider.lower() == 'gemini':
                        print("You need a Google Gemini API key to use this provider.")
                        print("You can get an API key at https://ai.google.dev/")
                    
                    # Exit or fallback based on the allow_random_fallback flag
                    if args.allow_random_fallback:
                        logger.warning(f"API key for '{args.provider}' not found, falling back to random provider as requested")
                        print("Falling back to random provider (for testing only)")
                        print("NOTE: Random provider is not suitable for actual curation")
                        print("      as it will pass all games regardless of quality.")
                        ai_provider = get_provider("random")
                        ai_provider.initialize()
                    else:
                        print("\nTo use Random provider for testing, rerun with the --allow-random-fallback flag")
                        print("Example: python headless.py --input your_file.dat --provider openai --allow-random-fallback")
                        sys.exit(1)
                else:
                    # API key exists but failed to initialize - likely invalid
                    print(f"ERROR: Failed to initialize {args.provider.upper()} provider with the provided API key")
                    print("The API key may be invalid, expired, or have incorrect permissions")
                    
                    # Exit or fallback based on the allow_random_fallback flag
                    if args.allow_random_fallback:
                        logger.warning(f"'{args.provider}' provider failed to initialize, falling back to random provider as requested")
                        print("Falling back to random provider (for testing only)")
                        print("NOTE: Random provider is not suitable for actual curation")
                        ai_provider = get_provider("random")
                        ai_provider.initialize()
                    else:
                        print("\nTo use Random provider for testing, rerun with the --allow-random-fallback flag")
                        print("Example: python headless.py --input your_file.dat --provider openai --allow-random-fallback")
                        sys.exit(1)
            else:
                # For other providers - generic error
                logger.error(f"Provider '{args.provider}' failed to initialize")
                print(f"ERROR: Provider '{args.provider}' failed to initialize")
                sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize AI provider: {e}")
        print(f"ERROR: Failed to initialize {args.provider} provider: {e}")
        sys.exit(1)
    
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
        last_batch_results = []
        
        def progress_callback(current, total, batch_results=None):
            """Progress reporting with game-themed visual feedback"""
            nonlocal last_batch_results
            percentage = int(100 * current / total) if total > 0 else 0
            
            elapsed = time.time() - start_time
            games_per_sec = current / elapsed if elapsed > 0 else 0
            
            # Calculate ETA
            if games_per_sec > 0 and current < total:
                eta = (total - current) / games_per_sec
                eta_str = f"ETA: {int(eta//60)}m {int(eta%60)}s"
            else:
                eta_str = "ETA: calculating..."
            
            # Save batch results if provided
            if batch_results:
                last_batch_results = batch_results

            # Use the game-themed progress display
            progress_display = visualizer.display_game_themed_progress(
                current, total, games_per_sec, eta_str
            )
            
            # Clear line and display progress
            sys.stdout.write("\r" + " " * 100 + "\r")  # Clear line
            sys.stdout.write(f"{progress_display}")

            # Show batch results if available
            if last_batch_results and current < total:
                # Count stats
                kept_count = len([g for g in last_batch_results if g.get('keep', False)])
                removed_count = len(last_batch_results) - kept_count
                
                # Show recent game evaluations with color coding
                sys.stdout.write("\n\nRecent games processed:")
                
                # Display batch summary
                sys.stdout.write(f"\n  Last batch: {visualizer.get_color('success')}{kept_count} kept{visualizer.get_color('reset')}, ")
                sys.stdout.write(f"{visualizer.get_color('error')}{removed_count} removed{visualizer.get_color('reset')}\n")
                
                for idx, result in enumerate(last_batch_results[-5:]):  # Show up to 5 recent games
                    game_name = result.get("game_name", "Unknown Game")
                    keep = result.get("keep", False)
                    quality = result.get("quality_score", 0)
                    
                    status = "✓ KEEP" if keep else "✗ REMOVE"
                    color = visualizer.get_color('success') if keep else visualizer.get_color('error')
                    
                    # Display with color
                    sys.stdout.write(f"\n  {color}{status}{visualizer.get_color('reset')} | ")
                    sys.stdout.write(f"{game_name} (Score: {quality:.2f})")
                    
                    # Access the game's stored evaluation if available
                    analysis = {}
                    
                    # First try to get game's full evaluation data
                    if "_evaluation" in result:
                        analysis = result.get("_evaluation", {}).get("_criteria_analysis", {})
                    
                    # If not found, and we're just displaying batch results, we don't have access
                    # to the _evaluation data yet since it's still being processed
                    
                    # Display criteria insights
                    if analysis:
                        # Display strengths and weaknesses
                        strongest = analysis.get("strongest_criteria", [])
                        weakest = analysis.get("weakest_criteria", [])
                        
                        if strongest:
                            strongest_str = ", ".join([s.replace("_", " ").title() for s in strongest])
                            sys.stdout.write(f" {visualizer.get_color('success')}Strong:{visualizer.get_color('reset')} {strongest_str}")
                        
                        if weakest:
                            weakest_str = ", ".join([w.replace("_", " ").title() for w in weakest])
                            sys.stdout.write(f" {visualizer.get_color('warning')}Weak:{visualizer.get_color('reset')} {weakest_str}")
                        
                        # Special handling for low score keepers
                        if keep and analysis.get("is_low_score_keeper", False):
                            sys.stdout.write(f" {visualizer.get_color('warning')}[LOW SCORE EXCEPTION]{visualizer.get_color('reset')}")
                
                sys.stdout.write("\n")  # Add spacing
            
            sys.stdout.flush()
            
            logger.info(f"Processing: {current}/{total} games ({percentage}%)")
        
        result = filter_engine.filter_collection(
            parsed_data['games'],
            criteria,
            args.batch_size,
            progress_callback
        )
        
        # Handle both 3-item and 4-item return values for compatibility
        if len(result) == 4:
            filtered_games, evaluations, provider_error, api_usage_data = result
        else:
            filtered_games, evaluations, provider_error = result
            api_usage_data = None
        
        # Check for provider errors
        if provider_error:
            error_msg = provider_error.get('provider_error', 'Unknown provider error')
            print(f"\nProvider Error: {error_msg}")
            logger.error(f"Provider error: {provider_error}")
            
            # Provide more helpful information about API keys
            if args.provider.lower() == 'openai':
                print("\nThe OpenAI provider requires a valid API key to function.")
                print("You can get an OpenAI API key at https://platform.openai.com/")
                print("Set the API key as the OPENAI_API_KEY environment variable.")
                
                # Add information about options
                print("\nOptions:")
                print("1. Set OPENAI_API_KEY environment variable and try again")
                print("2. Use --allow-random-fallback flag for testing only")
                print("3. Use --provider random for testing only")
                
            elif args.provider.lower() == 'gemini':
                print("\nThe Gemini provider requires a valid API key to function.")
                print("You can get a Gemini API key at https://ai.google.dev/")
                print("Set the API key as the GEMINI_API_KEY environment variable.")
                
                # Add information about options
                print("\nOptions:")
                print("1. Set GEMINI_API_KEY environment variable and try again")
                print("2. Use --allow-random-fallback flag for testing only")
                print("3. Use --provider random for testing only")
                
            # Add note about using Random provider if not already using it
            if args.provider.lower() != 'random':
                print("\nWARNING: The Random provider is NOT suitable for actual curation")
                print("         as it will pass all games regardless of quality.")
                
                if not args.allow_random_fallback:
                    print("\nTo use Random provider for testing, you can:")
                    print("1. Rerun with the --allow-random-fallback flag")
                    print("   Example: python headless.py --input your_file.dat --provider openai --allow-random-fallback")
                    print("2. Or specify Random provider directly")
                    print("   Example: python headless.py --input your_file.dat --provider random")
                
            # Exit with error
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
        
        # Display API usage information if available
        if api_usage_data:
            provider = api_usage_data.get("provider", "UNKNOWN")
            today_tokens = api_usage_data.get("today_tokens", 0)
            month_tokens = api_usage_data.get("month_tokens", 0)
            total_requests = api_usage_data.get("total_requests", 0)
            
            if provider.lower() == "random test provider":
                print(f"API Usage for {provider}: No API tokens used (Random provider)")
                logger.info(f"API Usage for {provider}: No API tokens used (Random provider)")
            else:
                print(f"API Usage for {provider}: {today_tokens:,} tokens used today")
                logger.info(f"API Usage for {provider}: {today_tokens:,} tokens used today")
        
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
                summary_path,
                provider_name=ai_provider.get_provider_name()
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