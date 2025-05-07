#!/bin/bash
# Shell script to run provider comparisons with different configurations

show_help() {
    echo "DAT Filter AI - Provider Comparison Script"
    echo "Usage: ./compare.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -r, --reports    List of report files to compare (default: all report_*.json files)"
    echo "  -o, --output     Output filename for text report (default: comparison.txt)"
    echo "  -j, --json       Output filename for JSON data (default: provider_comparison.json)"
    echo ""
    echo "Examples:"
    echo "  ./compare.sh                              # Compare all available report files"
    echo "  ./compare.sh -r report_random.json report_gemini.json   # Compare specific reports"
    echo "  ./compare.sh -o custom_comparison.txt     # Specify custom output filename"
}

REPORTS=""
OUTPUT="comparison.txt"
JSON_OUTPUT="provider_comparison.json"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -r|--reports)
            shift
            REPORTS=()
            while [[ $# -gt 0 && ! $1 =~ ^- ]]; do
                REPORTS+=("$1")
                shift
            done
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -j|--json)
            JSON_OUTPUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# If no reports specified, find all report files
if [ -z "$REPORTS" ]; then
    REPORTS=(report_*.json)
    # Check if we found any reports
    if [ ${#REPORTS[@]} -eq 0 ]; then
        echo "No report files found matching pattern report_*.json"
        echo "Please run evaluations with different providers first or specify report files with -r option"
        exit 1
    fi
fi

echo "Comparing the following reports: ${REPORTS[@]}"
echo "Saving text output to: $OUTPUT"
echo "Saving JSON output to: $JSON_OUTPUT"
echo ""

python compare_providers.py --reports "${REPORTS[@]}" --output "$OUTPUT" --json-output "$JSON_OUTPUT"

# Check if comparison was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Comparison completed successfully!"
    echo "Text comparison: $OUTPUT"
    echo "JSON comparison: $JSON_OUTPUT"
    
    # Show a preview of the comparison
    echo ""
    echo "Preview of comparison report:"
    echo "-----------------------------"
    head -n 15 "$OUTPUT"
    echo "... (See full report in $OUTPUT)"
fi