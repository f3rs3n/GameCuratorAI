# DAT Filter AI: Provider Comparison Guide

This document explains how to use the provider comparison tools in DAT Filter AI to evaluate games with multiple AI systems and compare their results.

## Why Compare Providers?

Different AI models have different strengths, biases, and evaluation styles. Comparing multiple providers can help:

1. **Identify Agreement**: When multiple AI systems agree on a game's importance, you can be more confident in the evaluation.

2. **Spot Edge Cases**: Games where AI systems disagree may require more manual review or indicate unusual properties.

3. **Understand AI Biases**: Each AI system may have different knowledge or biases about certain game genres, eras, or platforms.

4. **Find the Best Provider for Your Collection**: Some AI providers may align better with your curation goals.

## Available Providers

DAT Filter AI currently supports these providers:

- **Random**: A test provider that generates random scores (useful for testing without API keys)
- **Gemini**: Google's Gemini 2.0 AI with strong knowledge of gaming history and cultural impact

## Quick Start

The easiest way to get started with provider comparisons is to use the `multieval.sh` script:

```bash
# Process the sample file with all available providers
./multieval.sh -s

# Process your own DAT file with all available providers
./multieval.sh -i your_collection.dat -a
```

This will:
1. Automatically detect which AI providers are available (based on API keys)
2. Process the file with each available provider
3. Generate a side-by-side comparison report

## Reading Comparison Reports

The comparison report includes:

### 1. Score Comparisons

For each game, you'll see how each provider scored it across different criteria:

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
```

### 2. Recommendation Reasoning

You'll also see each provider's recommendation with their reasoning:

```
Overall Recommendation
---------------------
  random: Include
    Reason: No reason provided
  gemini: Include
    Reason: While Disc 2 doesn't stand alone in terms of review scores 
    or modding, its historical significance as an integral part of the 
    groundbreaking Final Fantasy VII and its importance in showcasing 
    the technological constraints of its era warrant its inclusion.
```

## Advanced Usage

### Selecting Specific Providers

You can specify which providers to use:

```bash
./multieval.sh -i sample.dat -p random gemini
```

### Custom Output Directory

Save the results in a specific directory:

```bash
./multieval.sh -i sample.dat -d results/comparison1
```

### Comparing Existing Reports

If you have already generated reports separately, you can compare them:

```bash
./compare.sh -r report_random.json report_gemini.json
```

## API Keys

To use the AI providers, you'll need API keys:

- **Gemini**: Set the `GEMINI_API_KEY` environment variable

The random provider works without any API keys.

## Performance Considerations

- The random provider is the fastest (instant)
- Gemini will take longer due to API calls (seconds to minutes per file)
- Processing large DAT files with multiple providers can take significant time