#!/bin/bash
# Shell script to run the batch processor with different configurations

show_help() {
    echo "DAT Filter AI - Batch Processing Script"
    echo "Usage: ./batch_process.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -t, --test       Process only test files"
    echo "  -s, --sample     Process only the sample.dat file"
    echo "  -l, --limit N    Limit processing to N files"
    echo "  -r, --random     Use random provider (default)"
    echo "  -o, --openai     Use OpenAI provider"
    echo "  -g, --gemini     Use Gemini provider"
    echo "  -b, --both       Use both OpenAI and random providers"
    echo "  -a, --all        Use all providers (random, OpenAI, and Gemini)"
    echo ""
    echo "Examples:"
    echo "  ./batch_process.sh --test --random   # Process test files with random provider"
    echo "  ./batch_process.sh --sample --both   # Process sample.dat with both random and OpenAI"
    echo "  ./batch_process.sh --sample --gemini # Process sample.dat with Gemini provider"
    echo "  ./batch_process.sh --limit 5         # Process first 5 DAT files with random provider"
    echo "  ./batch_process.sh --sample --all    # Process sample.dat with all providers"
}

ARGS=""
PROVIDER="random"

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
        -r|--random)
            PROVIDER="random"
            shift
            ;;
        -o|--openai)
            PROVIDER="openai"
            shift
            ;;
        -b|--both)
            PROVIDER="both"
            shift
            ;;
        -g|--gemini)
            PROVIDER="gemini"
            shift
            ;;
        -a|--all)
            PROVIDER="all"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "Running batch processor with provider: $PROVIDER"
echo "Additional arguments: $ARGS"
echo ""

python batch_process.py --provider $PROVIDER $ARGS