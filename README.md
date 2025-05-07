# DAT Filter AI

An application that uses AI to intelligently filter and curate video game collections from XML-formatted .dat files with text-based visualization, advanced filtering capabilities, and flexible data processing.

## Features

- AI-powered evaluation of video games based on multiple criteria
- Support for XML .dat file processing
- Text-based visualization with colored output and progress tracking
- Rich multi-provider support (Random, OpenAI, and Google Gemini)
- Special case detection and rule enforcement for multi-disc games, regional variants, etc.
- Detailed interactive game evaluation inspection
- Comprehensive reports, comparisons, and summaries

## Installation

### Prerequisites

- Python 3.10 or higher
- Required Python packages (install via `pip`):
  - PyQt5 (for GUI mode)
  - openai (for OpenAI integration)
  - google-generativeai (for Gemini integration)
  - xml.etree (included in Python standard library)

### Setup

1. Clone the repository
2. Install the required Python packages
3. Set up API keys (optional):
   ```
   # For OpenAI provider
   export OPENAI_API_KEY=your_openai_api_key_here
   
   # For Gemini provider
   export GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

### Main Mode (Text-based UI)

The primary way to use DAT Filter AI is through its text-based interface:

```
python headless.py --input path/to/input.dat --output path/to/output.dat [options]
```

This provides rich text visualization with progress tracking, colored output, and detailed evaluation information.

### Legacy GUI Mode

A GUI mode is available but may have compatibility issues in some environments:

```
python main.py
```

Note: The text-based interface (headless.py) is now the recommended way to use DAT Filter AI.

Options:
- `--provider`: AI provider to use (random, openai, or gemini, default: random)
- `--criteria`: Comma-separated list of criteria to evaluate (default: metacritic,historical,v_list,console_significance,mods_hacks)
- `--batch-size`: Batch size for processing (default: 10)
- `--report`: Generate JSON report file path
- `--summary`: Generate text summary file path
- `--debug`: Enable debug logging

### Batch Processing

Process multiple DAT files:

```
python batch_process.py [options]
```

Options:
- `--limit`: Limit number of files to process
- `--test`: Process only small test files
- `--provider`: AI provider to use (random, openai, gemini, both, or all, default: random)
- `--sample`: Process only the sample.dat file

#### Shell Script

For convenience, you can use the shell script:

```
./batch_process.sh [options]
```

Options:
- `-h, --help`: Show this help message
- `-t, --test`: Process only test files
- `-s, --sample`: Process only the sample.dat file
- `-l, --limit N`: Limit processing to N files
- `-r, --random`: Use random provider (default)
- `-o, --openai`: Use OpenAI provider
- `-g, --gemini`: Use Gemini provider
- `-b, --both`: Use both OpenAI and random providers
- `-a, --all`: Use all providers (random, OpenAI, and Gemini)

Examples:
- `./batch_process.sh --test --random`: Process test files with random provider
- `./batch_process.sh --sample --gemini`: Process sample.dat with Gemini provider
- `./batch_process.sh --sample --both`: Process sample.dat with OpenAI and random providers
- `./batch_process.sh --limit 5`: Process first 5 DAT files with random provider
- `./batch_process.sh --sample --all`: Process sample.dat with all providers

## AI Providers

### Random Provider

The random provider generates random evaluation scores without requiring an API key. It's useful for testing the application's functionality without needing an API key.

### OpenAI Provider

The OpenAI provider uses the OpenAI API to evaluate games. It requires an OpenAI API key to function and provides more intelligent evaluations based on OpenAI's GPT-4o model.

### Gemini Provider

The Gemini provider uses Google's Gemini 2.0 API to evaluate games. It requires a Gemini API key to function and provides detailed evaluations with a focus on historical significance and cultural impact. The Gemini provider offers an alternative to OpenAI with different evaluation strengths and styles.

## Multi-Provider Comparison

One of the powerful features of DAT Filter AI is the ability to run evaluations using multiple AI providers and compare their results. This can provide greater insight into game evaluations and help identify edge cases where different AI systems may disagree.

To run evaluations with multiple providers:

```bash
# Process with all available providers
./batch_process.sh --sample --all

# Compare output files
ls -la filtered_sample_*.dat
ls -la summary_*.txt
```

This will generate separate output files for each provider (random, OpenAI, and Gemini) with the provider name included in the filename. You can then compare the evaluation results to see how different AI systems rate the same games.

### Provider Comparison Tools

DAT Filter AI includes dedicated tools for comparing results from different providers. There are two main ways to use this functionality:

> For a comprehensive guide on provider comparisons, see [docs/provider_comparison.md](docs/provider_comparison.md)

#### 1. Multi-Provider Evaluation Script

For the most streamlined experience, use the multi-provider evaluation tools which handle everything automatically:

```bash
# Using the convenient shell script (recommended)
./multieval.sh -s                           # Process sample.dat with default providers
./multieval.sh -i sample.dat -a             # Process with all available providers
./multieval.sh -i sample.dat -p random gemini openai  # Process with specific providers
./multieval.sh -i sample.dat -d test_output # Specify output directory

# Or using the Python script directly
./multieval.py --input sample.dat --providers random gemini
./multieval.py --input sample.dat --providers random gemini openai --output-dir test_output
```

This script will:
1. Process the input file with each specified provider
2. Generate filtered DAT files and reports for each provider
3. Automatically run the comparison tool to create a side-by-side report

#### 2. Manual Comparison

You can also perform the steps individually for more control:

```bash
# First process the same file with different providers
python headless.py --input sample.dat --output filtered_sample_random.dat --provider random --report report_random.json
python headless.py --input sample.dat --output filtered_sample_gemini.dat --provider gemini --report report_gemini.json

# Then run the comparison tool directly
python compare_providers.py --reports report_random.json report_gemini.json --output comparison.txt

# Or use the convenient shell script
./compare.sh                              # Compare all available report files
./compare.sh -r report_random.json report_gemini.json   # Compare specific reports
./compare.sh -o custom_comparison.txt     # Specify custom output filename
```

The comparison tool generates:
1. A text report with side-by-side score comparisons for each game and criterion
2. A JSON file containing structured comparison data for programmatic use

This makes it easy to identify differences in how providers evaluate games and understand the strengths and biases of each AI model.

Sample comparison output:
```
Game: Final Fantasy VII (Disc 2)
--------------------------------
Criterion                random         gemini         
-------------------------------------------------------
console_significance     3.8            8.0            
historical               6.8            8.0            
metacritic               1.7            0.0            
mods_hacks               3.5            0.0            
v_list                   8.2            7.0            

Overall Recommendation
---------------------
  random: Include
    Reason: No reason provided
  gemini: Include
    Reason: While Disc 2 doesn't stand alone in terms of review scores 
    or modding, its historical significance as an integral part of the 
    groundbreaking Final Fantasy VII and its importance in showcasing 
    the technological constraints of its era warrant its inclusion in 
    the curated collection.
```

## Project Structure

```
.
├── ai_providers/             # AI provider modules
│   ├── __init__.py           # Provider factory
│   ├── base.py               # Base provider class
│   ├── openai_provider.py    # OpenAI implementation
│   ├── gemini_provider.py    # Google Gemini implementation
│   └── random_provider.py    # Random test provider
├── assets/                   # Application assets
│   ├── app_icon.svg          # Application icon
│   └── style.qss             # Application style
├── core/                     # Core functionality
│   ├── __init__.py
│   ├── dat_parser.py         # XML DAT file parser
│   ├── export.py             # Export functionality
│   ├── filter_engine.py      # Filtering engine
│   └── rule_engine.py        # Rule processing engine
├── docs/                     # Documentation
│   └── provider_comparison.md # Provider comparison guide
├── logs/                     # Log files
├── test_input/               # Test input DAT files
├── test_output/              # Test output files
├── ui/                       # GUI components
│   ├── __init__.py
│   ├── file_selector.py      # File selection dialog
│   ├── filter_panel.py       # Filtering options panel
│   ├── main_window.py        # Main application window
│   ├── results_view.py       # Results display
│   └── theme.py              # UI theme settings
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── config.py             # Configuration handling
│   └── logging_config.py     # Logging setup
├── batch_process.py          # Batch processing script
├── batch_process.sh          # Shell script for batch processing
├── compare.sh                # Comparison helper script
├── compare_providers.py      # Provider comparison tool
├── headless.py               # Headless application
├── main.py                   # Main GUI application
├── multieval.py              # Multi-provider evaluation script
├── multieval.sh              # Multi-provider evaluation shell script
├── README.md                 # This documentation
├── pyproject.toml            # Project configuration
├── sample.dat                # Sample DAT file
├── test_gemini.py            # Gemini provider single-game test
└── test_providers.py         # Test script for all providers
```

## Output Files

### Filtered DAT File

Contains the filtered games, maintaining the original XML structure while adding metadata about the filtering process.

### JSON Report

Contains detailed information about the filtering process, including:
- Game evaluations
- Special cases (multi-disc games, regional variants, etc.)
- Filtering statistics

### Text Summary

Contains a human-readable summary of the filtering process, including:
- Number of games processed
- Number of games kept
- Filtering criteria used
- Special cases detected

## License

This project is licensed under the MIT License - see the LICENSE file for details.