#!/usr/bin/env python3
"""
Batch processing script for DAT Filter AI.
This script processes all DAT files in the test_input directory,
generating filtered DAT files, reports, and summaries.
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"batch_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_dat_file(input_file, output_dir="test_output", provider="random"):
    """
    Process a single DAT file using the headless application
    
    Args:
        input_file: Path to input DAT file
        output_dir: Directory for output files
        provider: AI provider to use ('random' or 'openai')
    
    Returns:
        Tuple of (success, time_taken)
    """
    file_name = os.path.basename(input_file)
    base_name = os.path.splitext(file_name)[0]
    
    # Create output paths with provider suffix
    provider_suffix = f"_{provider}"
    output_file = os.path.join(output_dir, f"{base_name}{provider_suffix}_filtered.dat")
    report_file = os.path.join(output_dir, f"{base_name}{provider_suffix}_report.json")
    summary_file = os.path.join(output_dir, f"{base_name}{provider_suffix}_summary.txt")
    
    # Construct command
    cmd = [
        "python", "headless.py",
        "--input", input_file,
        "--output", output_file,
        "--provider", provider,
        "--report", report_file,
        "--summary", summary_file
    ]
    
    try:
        logger.info(f"Processing {file_name}...")
        start_time = time.time()
        
        # Run command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            timeout=1800  # 30-minute timeout
        )
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        # Check result
        if result.returncode == 0:
            logger.info(f"Successfully processed {file_name} in {time_taken:.2f} seconds")
            return True, time_taken
        else:
            logger.error(f"Failed to process {file_name}: {result.stderr}")
            # Save error output
            error_file = os.path.join(output_dir, f"{base_name}_{provider}_error.txt")
            with open(error_file, "w") as f:
                f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            return False, time_taken
    
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout processing {file_name} (exceeded 30 minutes)")
        return False, 1800
    
    except Exception as e:
        logger.error(f"Error processing {file_name}: {e}")
        return False, 0

def main():
    """Main entry point for batch processing"""
    # Process arguments
    import argparse
    parser = argparse.ArgumentParser(description="Batch process DAT files")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument("--test", action="store_true", help="Process only small test files")
    parser.add_argument("--provider", "-p", help="AI provider to use (random, openai, or both)", default="random")
    parser.add_argument("--sample", "-s", help="Process only the sample.dat file", action="store_true")
    args = parser.parse_args()
    
    # Check test_input directory exists
    if not os.path.exists("test_input"):
        logger.error("test_input directory not found")
        return 1
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get list of DAT files
    dat_files = []
    
    if args.sample:
        # Just process the sample file
        if os.path.exists("sample.dat"):
            dat_files.append("sample.dat")
        else:
            logger.error("sample.dat file not found")
            return 1
    elif args.test:
        # Just process the test files
        test_files = ["neo_geo_cd_test.dat", "commodore_c64_test.dat"]
        for file in test_files:
            file_path = os.path.join("test_input", file)
            if os.path.exists(file_path):
                dat_files.append(file_path)
    else:
        # Process all files
        for file in os.listdir("test_input"):
            if file.endswith(".dat"):
                dat_files.append(os.path.join("test_input", file))
        
        # Apply limit if specified
        if args.limit and args.limit > 0:
            dat_files = dat_files[:args.limit]
    
    logger.info(f"Found {len(dat_files)} DAT files to process")
    
    # Determine which providers to use
    providers = []
    if args.provider.lower() == "all":
        providers = ["random", "openai", "gemini"]
    elif args.provider.lower() == "both":
        providers = ["random", "openai"]
    else:
        providers = [args.provider.lower()]
    
    logger.info(f"Using AI providers: {providers}")
    
    # Process each file with each provider
    # Use a more explicit approach with individual variables instead of a dictionary to avoid type issues
    success_count = 0
    failure_count = 0
    total_time = 0.0
    
    for provider in providers:
        logger.info(f"Processing with provider: {provider}")
        provider_success = 0
        provider_failures = 0
        provider_time = 0.0
        
        for input_file in dat_files:
            success, time_taken = process_dat_file(input_file, output_dir, provider)
            if success:
                success_count += 1
                provider_success += 1
            else:
                failure_count += 1
                provider_failures += 1
            total_time += time_taken
            provider_time += time_taken  # This can be a float
        
        logger.info(f"Provider {provider} completed: {provider_success} successes, {provider_failures} failures, {provider_time:.2f} seconds")
    
    # Generate summary
    logger.info("=" * 50)
    logger.info("Batch Processing Summary")
    logger.info("=" * 50)
    logger.info(f"Total files: {len(dat_files)}")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed: {failure_count}")
    logger.info(f"Total processing time: {total_time:.2f} seconds")
    avg_time = total_time / len(dat_files) if len(dat_files) > 0 else 0
    logger.info(f"Average processing time: {avg_time:.2f} seconds per file")
    logger.info("=" * 50)
    
    # Save summary to file
    summary_path = os.path.join(output_dir, "batch_summary.txt")
    with open(summary_path, "w") as f:
        f.write("DAT Filter AI - Batch Processing Summary\n")
        f.write("=====================================\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total files: {len(dat_files)}\n")
        f.write(f"Successfully processed: {success_count}\n")
        f.write(f"Failed: {failure_count}\n")
        f.write(f"Total processing time: {total_time:.2f} seconds\n")
        avg_time = total_time / len(dat_files) if len(dat_files) > 0 else 0
        f.write(f"Average processing time: {avg_time:.2f} seconds per file\n\n")
        
        f.write("File Processing Results:\n")
        f.write("------------------------\n")
        for provider in providers:
            f.write(f"\nProvider: {provider}\n")
            for input_file in dat_files:
                file_name = os.path.basename(input_file)
                base_name = os.path.splitext(file_name)[0]
                output_file = os.path.join(output_dir, f"{base_name}_{provider}_filtered.dat")
                success = os.path.exists(output_file)
                status = "SUCCESS" if success else "FAILED"
                f.write(f"  {file_name}: {status}\n")
    
    logger.info(f"Batch summary saved to {summary_path}")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())