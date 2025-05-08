#!/usr/bin/env python3
"""
Test script to verify the enhanced progress display in headless mode.
"""

import os
import sys
import subprocess

def main():
    """Test the enhanced progress display"""
    # Use the Atari 5200 DAT file as it's relatively small
    input_file = "ToFilter/Atari - Atari 5200 (20250316-080333) (Retool 2025-03-21 11-57-31) (77) (-ny) [-aABbcdkMmpPv].dat"
    output_file = "test_output_display.dat"
    report_file = "test_report_display.json"
    summary_file = "test_summary_display.txt"
    
    # Use a small batch size to see more updates
    batch_size = 5
    
    # Use random provider for testing
    provider = "random"
    
    # Build command
    cmd = [
        "python", "headless.py",
        "--input", input_file,
        "--output", output_file,
        "--report", report_file,
        "--summary", summary_file,
        "--provider", provider,
        "--batch-size", str(batch_size)
    ]
    
    print(f"Running test: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    # Clean up test files
    for file in [output_file, report_file, summary_file]:
        if os.path.exists(file):
            os.remove(file)
        
        # Also check in Filtered directory
        filtered_path = os.path.join("Filtered", file)
        if os.path.exists(filtered_path):
            os.remove(filtered_path)
    
    print("Test completed")

if __name__ == "__main__":
    main()