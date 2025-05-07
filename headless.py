#!/usr/bin/env python3
"""
DAT Filter AI - Headless version for testing the core functionality
without requiring PyQt5 GUI components.
"""

import os
import sys
import logging
import argparse
import json
from typing import Dict, Any, List

from utils.logging_config import setup_logging
from utils.config import load_config
from core.dat_parser import DatParser
from core.filter_engine import FilterEngine
from core.rule_engine import RuleEngine
from core.export import ExportManager
from ai_providers import get_provider, AVAILABLE_PROVIDERS

def main():
    """Main entry point for the headless application."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="DAT Filter AI - Headless Mode")
    parser.add_argument("--input", "-i", help="Input DAT file path", required=True)
    parser.add_argument("--output", "-o", help="Output DAT file path")
    parser.add_argument("--provider", "-p", help=f"AI provider to use {list(AVAILABLE_PROVIDERS.keys())}", default="random")
    parser.add_argument("--criteria", "-c", help="Comma-separated list of criteria to evaluate", 
                       default="metacritic,historical,v_list,console_significance,mods_hacks")
    parser.add_argument("--batch-size", "-b", help="Batch size for processing", type=int, default=10)
    parser.add_argument("--report", "-r", help="Generate JSON report file path")
    parser.add_argument("--summary", "-s", help="Generate text summary file path")
    parser.add_argument("--debug", "-d", help="Enable debug logging", action="store_true")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting DAT Filter AI in headless mode")
    
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
            if args.provider != "random":
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
        # Parse the DAT file
        logger.info(f"Parsing DAT file: {args.input}")
        parsed_data = dat_parser.parse_file(args.input)
        
        # Get list of criteria
        criteria = args.criteria.split(",")
        
        # Apply filters
        logger.info(f"Filtering collection with criteria: {criteria}")
        
        def progress_callback(current, total):
            """Simple progress reporting callback"""
            percentage = int(100 * current / total) if total > 0 else 0
            logger.info(f"Processing: {current}/{total} games ({percentage}%)")
        
        filtered_games, evaluations = filter_engine.filter_collection(
            parsed_data['games'],
            criteria,
            args.batch_size,
            progress_callback
        )
        
        # Process the collection to identify special cases
        logger.info("Identifying special cases...")
        result = rule_engine.process_collection(parsed_data['games'])
        special_cases = result['special_cases']
        
        # Print summary
        logger.info(f"Filtering complete: {len(filtered_games)} of {parsed_data['game_count']} games kept")
        
        # Export filtered DAT if requested
        if args.output:
            logger.info(f"Exporting filtered DAT to: {args.output}")
            success, message = export_manager.export_dat_file(
                filtered_games,
                parsed_data,
                args.output,
                {"filter_criteria": criteria}
            )
            if success:
                logger.info(f"Successfully exported filtered DAT: {message}")
            else:
                logger.error(f"Failed to export filtered DAT: {message}")
        
        # Export JSON report if requested
        if args.report:
            logger.info(f"Exporting JSON report to: {args.report}")
            success, message = export_manager.export_json_report(
                filtered_games,
                evaluations,
                special_cases,
                args.report
            )
            if success:
                logger.info(f"Successfully exported JSON report: {message}")
            else:
                logger.error(f"Failed to export JSON report: {message}")
        
        # Export text summary if requested
        if args.summary:
            logger.info(f"Exporting text summary to: {args.summary}")
            success, message = export_manager.export_text_summary(
                filtered_games,
                parsed_data['game_count'],
                criteria,
                args.summary
            )
            if success:
                logger.info(f"Successfully exported text summary: {message}")
            else:
                logger.error(f"Failed to export text summary: {message}")
        
    except Exception as e:
        logger.error(f"Error processing DAT file: {e}", exc_info=True)
        return 1
    
    logger.info("DAT Filter AI processing completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())