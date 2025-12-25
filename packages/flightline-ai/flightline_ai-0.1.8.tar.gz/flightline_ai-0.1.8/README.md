# Flightline

Synthetic data generation from sample files.

## The Problem

You can't download real production files to test locally due to security/compliance constraints. **Flightline** solves this by analyzing a sample file and generating N valid synthetic variations.

## How It Works

1. **Learn** - Analyze a sample file to create a profile describing the schema, data types, business logic, and PII fields
2. **Generate** - Use the profile to generate N realistic synthetic records

## Installation

```bash
pip install flightline-ai
```

For development:

```bash
# Clone the repo and install in editable mode
pip install -e .
```

## Usage

### Step 1: Learn from a sample file

```bash
flightline learn path/to/sample.json
```

This analyzes your file and creates a profile at `./flightline_output/profile.json`.

### Step 2: Generate synthetic data

```bash
flightline generate -n 10
```

This generates 10 synthetic records based on the profile, saved to `./flightline_output/synthetic_<timestamp>.json`.

You can also use the shorthand:

```bash
flightline gen -n 10
```

### Choosing a Model

Both commands support a `--model` flag to choose any model available on OpenRouter:

```bash
# Use Gemini (default)
flightline learn sample.json --model google/gemini-3-flash-preview

# Use a specific model for generation
flightline gen -n 100 --model google/gemini-3-flash-preview
```

See [OpenRouter Models](https://openrouter.ai/models) for all available models.

## Environment Variables

- `OPENROUTER_API_KEY` - Your OpenRouter API key (required). Get one at https://openrouter.ai/keys

## Output

All generated files are saved to `./flightline_output/`:
- `profile.json` - The learned schema and rules
- `synthetic_<timestamp>.json` - The generated synthetic records
