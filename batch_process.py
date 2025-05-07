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

def process_dat_file(input_file, output_dir="test_output", provider="random", batch_size=5):
    """
    Process a single DAT file using the headless application
    
    Args:
        input_file: Path to input DAT file
        output_dir: Directory for output files
        provider: AI provider to use ('random', 'openai', or 'gemini')
        batch_size: Number of games to process in one batch (for API efficiency)
    
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
        "--summary", summary_file,
        "--batch-size", str(batch_size)
    ]
    
    # Add debugging flag for easier troubleshooting
    # cmd.append("--debug")
    
    try:
        logger.info(f"Processing {file_name} with {provider} provider (batch size: {batch_size})...")
        start_time = time.time()
        
        # Run command with increased timeout for larger collections
        timeout = 3600  # 60-minute timeout (increased from 30 minutes)
        
        # Run command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        # Check result
        if result.returncode == 0:
            logger.info(f"Successfully processed {file_name} in {time_taken:.2f} seconds")
            
            # Calculate processing rate
            try:
                # Try to parse the game count from the summary file
                with open(summary_file, "r") as f:
                    summary_content = f.read()
                    import re
                    match = re.search(r"Original game count: (\d+)", summary_content)
                    if match:
                        game_count = int(match.group(1))
                        rate = game_count / time_taken
                        logger.info(f"Processing rate: {rate:.2f} games/second")
            except:
                pass  # Skip if we can't calculate the rate
                
            return True, time_taken
        else:
            logger.error(f"Failed to process {file_name}: {result.stderr}")
            # Save error output
            error_file = os.path.join(output_dir, f"{base_name}_{provider}_error.txt")
            with open(error_file, "w") as f:
                f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            return False, time_taken
    
    except subprocess.TimeoutExpired as e:
        logger.error(f"Timeout processing {file_name} (exceeded {e.timeout} seconds)")
        return False, e.timeout
    
    except Exception as e:
        logger.error(f"Error processing {file_name}: {e}")
        return False, 0

def main():
    """Main entry point for batch processing"""
    # Process arguments
    import argparse
    parser = argparse.ArgumentParser(description="Batch process DAT files")
    parser.add_argument("--input-dir", "-i", help="Directory containing DAT files", default="test_input")
    parser.add_argument("--output-dir", "-o", help="Directory for output files", default="test_output")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument("--test", action="store_true", help="Process only small test files")
    parser.add_argument("--provider", "-p", help="AI provider to use (random, openai, gemini, or all)", default="random")
    parser.add_argument("--sample", "-s", help="Process only the sample.dat file", action="store_true")
    parser.add_argument("--batch-size", "-b", type=int, help="Batch size for processing games", default=5)
    parser.add_argument("--continue", "-c", dest="continue_processing", action="store_true", 
                        help="Continue processing from previous run (skip already processed files)")
    parser.add_argument("--rate-limit", "-r", type=float, 
                        help="Delay between files in seconds for API rate limiting", default=0)
    parser.add_argument("--sort", help="Sort order for processing files (name, size, none)", default="size")
    args = parser.parse_args()
    
    # Check input directory exists
    input_dir = args.input_dir
    if not os.path.exists(input_dir):
        logger.error(f"Input directory '{input_dir}' not found")
        return 1
    
    # Create output directory
    output_dir = args.output_dir
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
            file_path = os.path.join(input_dir, file)
            if os.path.exists(file_path):
                dat_files.append(file_path)
    else:
        # Process all files
        for file in os.listdir(input_dir):
            if file.endswith(".dat"):
                dat_files.append(os.path.join(input_dir, file))
    
    # Sort the files if specified
    if args.sort == "name":
        dat_files.sort()  # Sort by filename
        logger.info("Sorting files by name")
    elif args.sort == "size":
        # Process smaller files first (for quicker feedback)
        dat_files.sort(key=lambda x: os.path.getsize(x))
        logger.info("Sorting files by size (smallest first)")
    
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
    
    # Create a command line to pass the batch size
    base_cmd = ["python", "headless.py", "--batch-size", str(args.batch_size)]
    
    # Process each file with each provider
    success_count = 0
    failure_count = 0
    total_time = 0.0
    processed_files = []
    skipped_files = []
    
    for provider in providers:
        logger.info(f"Processing with provider: {provider}")
        provider_success = 0
        provider_failures = 0
        provider_time = 0.0
        
        # Show progress information
        total_files = len(dat_files)
        current_file = 0
        
        for input_file in dat_files:
            current_file += 1
            file_name = os.path.basename(input_file)
            base_name = os.path.splitext(file_name)[0]
            
            # Check if this file was already processed
            output_file = os.path.join(output_dir, f"{base_name}_{provider}_filtered.dat")
            if args.continue_processing and os.path.exists(output_file):
                logger.info(f"Skipping already processed file: {file_name} ({current_file}/{total_files})")
                skipped_files.append(input_file)
                continue
            
            # Show progress
            progress_pct = int(100 * current_file / total_files)
            logger.info(f"Processing file {current_file}/{total_files} ({progress_pct}%): {file_name}")
            
            # Process the file
            success, time_taken = process_dat_file(input_file, output_dir, provider, args.batch_size)
            
            if success:
                success_count += 1
                provider_success += 1
                processed_files.append(input_file)
                logger.info(f"✓ Successfully processed: {file_name} in {time_taken:.2f} seconds")
            else:
                failure_count += 1
                provider_failures += 1
                logger.error(f"✗ Failed to process: {file_name}")
                
            total_time += time_taken
            provider_time += time_taken
            
            # Estimate remaining time
            if current_file < total_files:
                avg_time_per_file = provider_time / current_file
                remaining_files = total_files - current_file
                eta_seconds = avg_time_per_file * remaining_files
                eta_str = f"{int(eta_seconds // 3600)}h {int((eta_seconds % 3600) // 60)}m {int(eta_seconds % 60)}s"
                logger.info(f"Estimated time remaining: {eta_str} ({avg_time_per_file:.2f} seconds/file)")
            
            # Respect rate limits between files
            if args.rate_limit > 0 and current_file < total_files:
                logger.info(f"Rate limiting: waiting {args.rate_limit} seconds before next file")
                time.sleep(args.rate_limit)
        
        logger.info(f"Provider {provider} completed: {provider_success} successes, {provider_failures} failures, {provider_time:.2f} seconds")
    
    # Generate summary
    logger.info("=" * 50)
    logger.info("Batch Processing Summary")
    logger.info("=" * 50)
    logger.info(f"Total files: {len(dat_files)}")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed: {failure_count}")
    logger.info(f"Skipped: {len(skipped_files)}")
    logger.info(f"Total processing time: {total_time:.2f} seconds")
    
    processed_count = success_count + failure_count
    if processed_count > 0:
        avg_time = total_time / processed_count
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
        f.write(f"Skipped: {len(skipped_files)}\n")
        f.write(f"Total processing time: {total_time:.2f} seconds\n")
        
        if processed_count > 0:
            avg_time = total_time / processed_count
            f.write(f"Average processing time: {avg_time:.2f} seconds per file\n\n")
        
        f.write("File Processing Results:\n")
        f.write("------------------------\n")
        for provider in providers:
            f.write(f"\nProvider: {provider}\n")
            for input_file in dat_files:
                file_name = os.path.basename(input_file)
                base_name = os.path.splitext(file_name)[0]
                output_file = os.path.join(output_dir, f"{base_name}_{provider}_filtered.dat")
                if input_file in skipped_files:
                    status = "SKIPPED"
                else:
                    status = "SUCCESS" if os.path.exists(output_file) else "FAILED"
                f.write(f"  {file_name}: {status}\n")
    
    logger.info(f"Batch summary saved to {summary_path}")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())