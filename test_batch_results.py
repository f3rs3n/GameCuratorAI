#!/usr/bin/env python3
"""
Test script to verify the batch results structure from filter_engine.
"""

import os
import sys
import json
import logging
from core.dat_parser import DatParser
from core.filter_engine import FilterEngine
from ai_providers import get_provider

def main():
    """Test the batch results structure"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_batch_results")
    
    # Initialize components
    dat_parser = DatParser()
    provider = get_provider("random")
    filter_engine = FilterEngine(ai_provider=provider)
    
    # Use a small file for testing
    input_file = "ToFilter/Sega - 32X (20250126-142831) (Retool 2025-03-21 11-59-44) (33) (-ny) [-aABbcdkMmpPv].dat"
    
    # Parse DAT file
    logger.info(f"Parsing DAT file: {input_file}")
    parsed_data = dat_parser.parse_file(input_file)
    
    # Define a custom progress callback that logs batch results
    def progress_callback(current, total, batch_results=None):
        if batch_results:
            logger.info("Batch Results Structure:")
            # Log the structure of the first result
            if batch_results:
                logger.info(f"Sample batch result: {json.dumps(batch_results[0], indent=2)}")
                logger.info(f"Keys in batch result: {list(batch_results[0].keys())}")
    
    # Apply filters
    criteria = ["metacritic", "historical", "v_list", "console_significance", "mods_hacks"]
    batch_size = 3  # Small batch for testing
    
    logger.info(f"Starting filtering with batch size {batch_size}")
    filter_engine.filter_collection(
        parsed_data["games"],
        criteria=criteria,
        batch_size=batch_size,
        progress_callback=progress_callback
    )
    
    logger.info("Test completed")

if __name__ == "__main__":
    main()