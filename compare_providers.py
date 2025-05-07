#!/usr/bin/env python3
"""
Comparison tool for DAT Filter AI provider results.
This script compares the evaluation results from different providers
and generates a comparison report.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def load_report(report_path: str) -> Dict[str, Any]:
    """
    Load a JSON report file
    
    Args:
        report_path: Path to the report file
        
    Returns:
        Dict containing the report data
    """
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load report file {report_path}: {e}")
        return {}

def extract_game_evaluations(report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract game evaluations from a report
    
    Args:
        report: Report data
        
    Returns:
        Dict mapping game names to their evaluations
    """
    game_evals = {}
    
    # Process evaluations that are at the top level
    if "evaluations" in report:
        for game_data in report["evaluations"]:
            if "_evaluation" in game_data:
                eval_data = game_data["_evaluation"]
                game_name = eval_data.get("game_name", "Unknown")
                game_evals[game_name] = eval_data
    
    # Process nested evaluations within special cases
    if "special_cases" in report:
        for case_type, case_group in report["special_cases"].items():
            if "groups" in case_group:
                for group in case_group["groups"]:
                    for game_data in group:
                        if "_evaluation" in game_data:
                            eval_data = game_data["_evaluation"]
                            game_name = eval_data.get("game_name", "Unknown")
                            game_evals[game_name] = eval_data
    
    return game_evals

def compare_providers(reports: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Compare evaluations from different providers
    
    Args:
        reports: Dict mapping provider names to their report data
        
    Returns:
        Tuple of (comparison_data, all_game_names)
    """
    # Extract game evaluations from all reports
    provider_evals = {}
    all_games = set()
    
    for provider, report in reports.items():
        evals = extract_game_evaluations(report)
        provider_evals[provider] = evals
        all_games.update(evals.keys())
    
    all_game_names = sorted(list(all_games))
    
    # Build comparison data
    comparison = {}
    for game in all_game_names:
        comparison[game] = {}
        for provider, evals in provider_evals.items():
            if game in evals:
                comparison[game][provider] = {
                    "scores": evals[game].get("scores", {}),
                    "overall_recommendation": evals[game].get("overall_recommendation", {})
                }
    
    return comparison, all_game_names

def generate_text_comparison(comparison: Dict[str, Dict[str, Any]], 
                           game_names: List[str], 
                           providers: List[str]) -> str:
    """
    Generate a text comparison report
    
    Args:
        comparison: Comparison data
        game_names: List of game names
        providers: List of provider names
        
    Returns:
        str: Formatted comparison report
    """
    report = []
    report.append("DAT Filter AI - Provider Comparison Report")
    report.append("========================================")
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Comparing providers: {', '.join(providers)}")
    report.append("")
    
    for game in game_names:
        report.append(f"Game: {game}")
        report.append("-" * (len(game) + 6))
        
        # Build a table for each criterion
        criteria = set()
        for provider in providers:
            if provider in comparison[game]:
                criteria.update(comparison[game][provider].get("scores", {}).keys())
        
        criteria = sorted(list(criteria))
        
        # Header row
        header = "Criterion".ljust(25)
        for provider in providers:
            header += provider.ljust(15)
        report.append(header)
        report.append("-" * len(header))
        
        # Criteria rows
        for criterion in criteria:
            row = criterion.ljust(25)
            for provider in providers:
                if provider in comparison[game] and criterion in comparison[game][provider].get("scores", {}):
                    score = comparison[game][provider]["scores"][criterion]
                    row += f"{score:<15.1f}" if isinstance(score, (int, float)) else f"{score:<15}"
                else:
                    row += "N/A".ljust(15)
            report.append(row)
        
        # Overall recommendation
        report.append("")
        report.append("Overall Recommendation")
        report.append("---------------------")
        for provider in providers:
            if provider in comparison[game]:
                recommendation = comparison[game][provider].get("overall_recommendation", {})
                include = recommendation.get("include", "Unknown")
                reason = recommendation.get("reason", "No reason provided")
                report.append(f"  {provider}: {'Include' if include else 'Exclude'}")
                report.append(f"    Reason: {reason}")
        
        report.append("")
        report.append("=" * 80)
        report.append("")
    
    return "\n".join(report)

def generate_json_comparison(comparison: Dict[str, Dict[str, Any]],
                           all_providers: List[str]) -> Dict[str, Any]:
    """
    Generate a JSON comparison report
    
    Args:
        comparison: Comparison data
        all_providers: List of all provider names
        
    Returns:
        Dict: Structured comparison data for JSON output
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "providers": all_providers,
        "comparisons": comparison
    }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Compare DAT Filter AI provider results")
    parser.add_argument("--reports", nargs="+", required=True, 
                        help="Paths to JSON report files (e.g., report_random.json report_openai.json)")
    parser.add_argument("--output", default="provider_comparison.txt", 
                        help="Output file for text comparison (default: provider_comparison.txt)")
    parser.add_argument("--json-output", default="provider_comparison.json",
                        help="Output file for JSON comparison (default: provider_comparison.json)")
    args = parser.parse_args()
    
    # Load reports
    reports = {}
    for report_path in args.reports:
        provider_name = os.path.basename(report_path).replace("report_", "").replace(".json", "")
        report_data = load_report(report_path)
        if report_data:
            reports[provider_name] = report_data
            logger.info(f"Loaded report for provider: {provider_name}")
    
    if not reports:
        logger.error("No valid reports loaded")
        return 1
    
    # Compare providers
    logger.info(f"Comparing providers: {', '.join(reports.keys())}")
    comparison, all_game_names = compare_providers(reports)
    
    # Generate text comparison
    text_comparison = generate_text_comparison(comparison, all_game_names, list(reports.keys()))
    with open(args.output, "w") as f:
        f.write(text_comparison)
    logger.info(f"Text comparison saved to {args.output}")
    
    # Generate JSON comparison
    json_comparison = generate_json_comparison(comparison, list(reports.keys()))
    with open(args.json_output, "w") as f:
        json.dump(json_comparison, f, indent=2)
    logger.info(f"JSON comparison saved to {args.json_output}")
    
    logger.info("Comparison completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())