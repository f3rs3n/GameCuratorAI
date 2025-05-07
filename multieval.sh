#!/bin/bash
# Shell script to run the multi-provider evaluation tool with different configurations

show_help() {
    echo "DAT Filter AI - Multi-Provider Evaluation Script"
    echo "Usage: ./multieval.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -i, --input      Input DAT file to process (required)"
    echo "  -p, --providers  Providers to use (default: random gemini)"
    echo "  -d, --dir        Output directory (default: current directory)"
    echo "  -a, --all        Use all available providers"
    echo "  -s, --sample     Use the sample.dat file as input"
    echo ""
    echo "Examples:"
    echo "  ./multieval.sh -i sample.dat                   # Process with default providers"
    echo "  ./multieval.sh -s                              # Process sample.dat with default providers"
    echo "  ./multieval.sh -i sample.dat -p random openai  # Process with specific providers"
    echo "  ./multieval.sh -i sample.dat -a                # Process with all available providers"
    echo "  ./multieval.sh -i sample.dat -d test_output    # Specify output directory"
}

# Default values
INPUT=""
PROVIDERS="random gemini"
OUTPUT_DIR="."
USE_ALL_PROVIDERS=false
USE_SAMPLE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--input)
            INPUT="$2"
            shift 2
            ;;
        -p|--providers)
            shift
            PROVIDERS=""
            while [[ $# -gt 0 && ! $1 =~ ^- ]]; do
                PROVIDERS="$PROVIDERS $1"
                shift
            done
            PROVIDERS=$(echo $PROVIDERS | xargs)  # Trim whitespace
            ;;
        -d|--dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -a|--all)
            USE_ALL_PROVIDERS=true
            shift
            ;;
        -s|--sample)
            USE_SAMPLE=true
            INPUT="sample.dat"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if input file is provided
if [ -z "$INPUT" ]; then
    echo "Error: Input file is required"
    show_help
    exit 1
fi

# Check if input file exists
if [ ! -f "$INPUT" ]; then
    echo "Error: Input file does not exist: $INPUT"
    exit 1
fi

# Detect available providers
AVAILABLE_PROVIDERS="random"
if [ -n "$OPENAI_API_KEY" ]; then
    AVAILABLE_PROVIDERS="$AVAILABLE_PROVIDERS openai"
fi
if [ -n "$GEMINI_API_KEY" ]; then
    AVAILABLE_PROVIDERS="$AVAILABLE_PROVIDERS gemini"
fi

echo "Available providers: $AVAILABLE_PROVIDERS"

# Use all providers if requested
if [ "$USE_ALL_PROVIDERS" = true ]; then
    PROVIDERS="$AVAILABLE_PROVIDERS"
fi

# If no providers specified, use all available
if [ -z "$PROVIDERS" ]; then
    PROVIDERS="$AVAILABLE_PROVIDERS"
fi

# Create output directory if it doesn't exist
if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

echo "DAT Filter AI - Multi-Provider Evaluation"
echo "========================================"
echo "Input file: $INPUT"
echo "Providers: $PROVIDERS"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Run multi-provider evaluation
if [ "$USE_ALL_PROVIDERS" = true ]; then
    python multieval.py --input "$INPUT" --all --output-dir "$OUTPUT_DIR"
else
    python multieval.py --input "$INPUT" --providers $PROVIDERS --output-dir "$OUTPUT_DIR"
fi

# Check if evaluation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Multi-provider evaluation completed successfully!"
    echo "The results are available in the $OUTPUT_DIR directory."
    
    # List generated files
    echo ""
    echo "Generated files:"
    find "$OUTPUT_DIR" -name "filtered_$(basename $INPUT .dat)*" -o -name "report_*" -o -name "summary_*" -o -name "comparison.txt" -o -name "provider_comparison.json" | sort
else
    echo ""
    echo "Multi-provider evaluation failed."
    exit 1
fi