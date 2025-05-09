#!/bin/bash
# Shell script to run the batch processor with different configurations
# Enhanced with Gemini API optimization options

show_help() {
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║               DAT Filter AI - Batch Processing                ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo "Usage: ./batch_process.sh [options]"
    echo ""
    echo "Basic Options:"
    echo "  -h, --help           Show this help message"
    echo "  -t, --test           Process only test files"
    echo "  -s, --sample         Process only the sample.dat file"
    echo "  -l, --limit N        Limit processing to N files"
    echo "  -i, --input DIR      Input directory (default: test_input)"
    echo "  -o, --output DIR     Output directory (default: test_output)"
    echo ""
    echo "Provider Options:"
    echo "  -r, --random         Use random provider (for testing only)"
    echo "  -g, --gemini         Use Gemini provider (default)"
    echo ""
    echo "API Optimization Options:"
    echo "  -b, --batch-size N   Number of games to process in each batch (default: 20)"
    echo "  -d, --delay N        Delay between files in seconds for rate limiting (default: 0)"
    echo "  -c, --continue       Continue processing from previous run"
    echo "  -z, --sort TYPE      Sort order for files (name, size, none) (default: size)"
    echo ""
    echo "Examples:"
    echo "  ./batch_process.sh --test --random"
    echo "      Process test files with random provider"
    echo ""
    echo "  ./batch_process.sh --gemini --batch-size 10 --delay 5"
    echo "      Process all DAT files with Gemini, 10 games per batch, 5s delay between files"
    echo ""
    echo "  ./batch_process.sh --gemini --continue"
    echo "      Continue processing with Gemini from where it left off"
    echo ""
    echo "  ./batch_process.sh --gemini --input myfolder --output results"
    echo "      Process DAT files from myfolder with results in results folder"
}

ARGS=""
PROVIDER="gemini"
BATCH_SIZE=20
RATE_LIMIT=0
INPUT_DIR="test_input"
OUTPUT_DIR="test_output"
SORT="size"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--test)
            ARGS="$ARGS --test"
            shift
            ;;
        -s|--sample)
            ARGS="$ARGS --sample"
            shift
            ;;
        -l|--limit)
            ARGS="$ARGS --limit $2"
            shift 2
            ;;
        -i|--input)
            INPUT_DIR="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -b|--batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        -d|--delay)
            RATE_LIMIT="$2"
            shift 2
            ;;
        -c|--continue)
            ARGS="$ARGS --continue"
            shift
            ;;
        -z|--sort)
            SORT="$2"
            shift 2
            ;;
        -r|--random)
            PROVIDER="random"
            shift
            ;;
        -g|--gemini)
            PROVIDER="gemini"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Create nice box around output
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║               DAT Filter AI - Batch Processing                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo "• Provider:           $PROVIDER"
echo "• Input directory:    $INPUT_DIR"
echo "• Output directory:   $OUTPUT_DIR"
echo "• Batch size:         $BATCH_SIZE games per API call"
echo "• Rate limit:         $RATE_LIMIT seconds between files"
echo "• Sort order:         $SORT"
echo "• Additional args:    $ARGS"

# Construct the full command
CMD="python batch_process.py --provider $PROVIDER --input-dir $INPUT_DIR --output-dir $OUTPUT_DIR --batch-size $BATCH_SIZE --rate-limit $RATE_LIMIT --sort $SORT $ARGS"

echo ""
echo "Command: $CMD"
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Starting Processing                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Execute the command
eval $CMD

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  Batch Processing Complete                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"