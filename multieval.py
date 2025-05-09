#!/usr/bin/env python3
"""
Multi-provider evaluation script for DAT Filter AI.
This script processes a single DAT file with multiple AI providers
and automatically generates a comparison report.
"""

import argparse
import logging
import os
import sys
import time
import subprocess
from typing import List, Dict, Any, Set
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def get_available_providers() -> Set[str]:
    """
    Detect available AI providers based on environment variables
    
    Returns:
        Set of available provider names
    """
    available = {"random"}  # Random provider is always available
    
    # Import our API key checking utilities
    try:
        from utils.check_api_keys import check_api_key
        import test_api_keys
        
        # Check for OpenAI API key
        openai_exists, _ = check_api_key("openai")
        if openai_exists:
            # Perform actual validation
            print("Testing OpenAI API key...")
            success, message = test_api_keys.test_api_key("openai")
            if success:
                available.add("openai")
                print(f"✓ OpenAI API key validation successful: {message}")
            else:
                print(f"✗ OpenAI API key validation failed: {message}")
        
        # Check for Gemini API key
        gemini_exists, _ = check_api_key("gemini")
        if gemini_exists:
            # Perform actual validation
            print("Testing Gemini API key...")
            success, message = test_api_keys.test_api_key("gemini")
            if success:
                available.add("gemini")
                print(f"✓ Gemini API key validation successful: {message}")
            else:
                print(f"✗ Gemini API key validation failed: {message}")
    except Exception as e:
        # Fallback to the old method if there's an issue with the new utilities
        logger.warning(f"Error using API key validation utilities: {e}")
        logger.info("Falling back to basic environment variable check")
        
        # Check for OpenAI API key
        if os.environ.get("OPENAI_API_KEY"):
            available.add("openai")
        
        # Check for Gemini API key
        if os.environ.get("GEMINI_API_KEY"):
            available.add("gemini")
    
    logger.info(f"Detected available providers: {', '.join(sorted(available))}")
    return available

def run_provider_evaluation(input_file: str, provider: str, output_dir: str = ".", allow_random_fallback: bool = False) -> Dict[str, str]:
    """
    Run evaluation with a specific provider
    
    Args:
        input_file: Path to input DAT file
        provider: Provider name to use
        output_dir: Directory for output files
        allow_random_fallback: Whether to allow fallback to Random provider
        
    Returns:
        Dict with paths to output files
    """
    # Create base filename from input file
    base_name = os.path.basename(input_file).replace(".dat", "")
    
    # Define output filenames
    filtered_dat = os.path.join(output_dir, f"filtered_{base_name}_{provider}.dat")
    report_json = os.path.join(output_dir, f"report_{provider}.json")
    summary_txt = os.path.join(output_dir, f"summary_{provider}.txt")
    
    # Build command
    cmd = [
        "python", "headless.py",
        "--input", input_file,
        "--output", filtered_dat,
        "--provider", provider,
        "--report", report_json,
        "--summary", summary_txt
    ]
    
    # Add random fallback option if requested
    if allow_random_fallback:
        cmd.append("--allow-random-fallback")
        logger.warning(f"Using --allow-random-fallback option for {provider} (for testing only, not for actual curation)")
    
    logger.info(f"Running evaluation with provider: {provider}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    # Run command
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Successfully completed evaluation with provider: {provider}")
        return {
            "filtered_dat": filtered_dat,
            "report_json": report_json,
            "summary_txt": summary_txt
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run evaluation with provider {provider}: {e}")
        return {}

def run_comparison(reports: List[str], output_file: str = "comparison.txt", json_output: str = "provider_comparison.json") -> bool:
    """
    Run comparison between provider reports
    
    Args:
        reports: List of report files to compare
        output_file: Output filename for comparison text
        json_output: Output filename for comparison JSON
        
    Returns:
        True if comparison was successful, False otherwise
    """
    # Build command
    cmd = [
        "python", "compare_providers.py",
        "--reports", *reports,
        "--output", output_file,
        "--json-output", json_output
    ]
    
    logger.info(f"Running comparison with reports: {', '.join(reports)}")
    
    # Run command
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Successfully generated comparison report: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate comparison report: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Multi-provider evaluation tool for DAT Filter AI")
    parser.add_argument("--input", required=True, help="Input DAT file to process")
    parser.add_argument("--providers", nargs="+", default=None, 
                        help="AI providers to use (default: all available providers)")
    parser.add_argument("--output-dir", default=".", help="Directory for output files")
    parser.add_argument("--comparison", default="comparison.txt",
                        help="Output filename for comparison text")
    parser.add_argument("--json-comparison", default="provider_comparison.json",
                        help="Output filename for comparison JSON")
    parser.add_argument("--all", action="store_true", help="Use all available providers")
    parser.add_argument("--allow-random-fallback", action="store_true",
                        help="Allow fallback to Random provider if API key is missing/invalid (for testing only)")
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input):
        logger.error(f"Input file does not exist: {args.input}")
        return 1
    
    # Create output directory if it doesn't exist
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)
    
    # Detect available providers
    available_providers = get_available_providers()
    
    # Determine which providers to use
    if args.all or args.providers is None:
        providers = list(sorted(available_providers))
    else:
        providers = []
        for provider in args.providers:
            if provider in available_providers:
                providers.append(provider)
            else:
                logger.warning(f"Provider '{provider}' is not available and will be skipped")
    
    if not providers:
        logger.error("No available providers match the requested providers")
        return 1
    
    logger.info(f"Using providers: {', '.join(providers)}")
    
    # Run evaluations for each provider
    start_time = time.time()
    report_files = []
    
    for provider in providers:
        result = run_provider_evaluation(args.input, provider, args.output_dir, args.allow_random_fallback)
        if result and "report_json" in result:
            report_files.append(result["report_json"])
    
    # Run comparison if we have multiple reports
    if len(report_files) > 1:
        comparison_path = os.path.join(args.output_dir, args.comparison)
        json_comparison_path = os.path.join(args.output_dir, args.json_comparison)
        
        success = run_comparison(report_files, comparison_path, json_comparison_path)
        if success:
            # Display summary info
            elapsed_time = time.time() - start_time
            logger.info(f"Multi-provider evaluation completed in {elapsed_time:.2f} seconds")
            logger.info(f"Processed file: {args.input}")
            logger.info(f"Providers used: {', '.join(providers)}")
            logger.info(f"Comparison report: {comparison_path}")
            logger.info(f"JSON comparison: {json_comparison_path}")
            
            # Print a preview of the comparison report
            if os.path.isfile(comparison_path):
                print("\nPreview of comparison report:")
                print("-----------------------------")
                with open(comparison_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines[:15]:
                        print(line.rstrip())
                print("... (See full report for details)")
        else:
            logger.error("Failed to generate comparison report")
            return 1
    else:
        logger.warning("Not enough reports to generate comparison (need at least 2)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())