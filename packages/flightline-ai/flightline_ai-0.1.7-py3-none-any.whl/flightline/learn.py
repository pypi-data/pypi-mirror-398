"""Learn module - Analyzes input files to create a data profile."""

import json
import os
from pathlib import Path

import click
from dotenv import load_dotenv
from openai import OpenAI

from flightline.hud import (
    console,
    create_status_spinner,
    print_boot_sequence,
    print_complete,
    print_error,
    print_info,
    print_status,
    print_success,
    print_target,
    print_warning,
)

# Load .env file if present
load_dotenv()

# OpenRouter base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-3-flash-preview"

SYSTEM_PROMPT = """You are a data analyst expert. Analyze the provided data and create a data profile - a descriptive specification of this data structure.

Your profile must include:

1. **Schema**: The exact structure/shape of the data (fields, nesting, arrays)
2. **Data Types**: The type of each field (string, number, boolean, date, etc.)
3. **Business Logic**: Any implicit rules you can infer, such as:
   - Timestamps must be sequential
   - Certain fields are derived from others
   - Value ranges or constraints
   - Required vs optional fields
4. **PII Fields**: Identify any fields that appear to contain personally identifiable information (names, emails, phone numbers, addresses, SSNs, etc.)
5. **Patterns**: Any patterns in the data (date formats, ID formats, naming conventions)

Output your analysis as valid JSON with this structure:
{
    "schema": { ... field definitions ... },
    "data_types": { "field_name": "type", ... },
    "business_rules": [ "rule 1", "rule 2", ... ],
    "pii_fields": [ "field1", "field2", ... ],
    "patterns": { "field_name": "pattern description", ... },
    "example_formats": { "field_name": "format description or pattern", ... }
}

CRITICAL - PII PROTECTION:
- Do NOT copy any actual values from the input data into the profile
- For "example_formats", describe the FORMAT/PATTERN only (e.g., "email format: user@domain.com", "phone format: +1-555-XXX-XXXX")
- Never include real names, emails, addresses, phone numbers, or any identifiable information
- The profile must contain ZERO original data values - only structural descriptions

Be thorough but concise. The profile will be used to generate synthetic test data."""


def get_client() -> OpenAI:
    """Create an OpenRouter-compatible client."""
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )


def analyze_file(file_path: Path, model: str) -> dict:
    """Send file content to LLM for analysis and return the data profile."""
    client = get_client()

    content = file_path.read_text()

    # Truncate very large files to avoid token limits
    max_chars = 50000
    if len(content) > max_chars:
        content = content[:max_chars]
        print_warning(f"FILE TRUNCATED TO {max_chars} CHARACTERS")

    print_target("INPUT", file_path.name, wp_num=1)
    print_info(f"MODEL: {model}")

    with create_status_spinner("LEARNING DATA STRUCTURE"):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this data:\n\n{content}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

    profile_text = response.choices[0].message.content

    if not profile_text:
        print_error("MODEL RETURNED EMPTY RESPONSE")
        print_info("TRY A DIFFERENT MODEL OR CHECK YOUR API KEY CREDITS")
        raise SystemExit(1)

    # Strip markdown code fences if present
    profile_text = profile_text.strip()
    if profile_text.startswith("```"):
        # Remove opening fence (```json or ```)
        profile_text = profile_text.split("\n", 1)[1] if "\n" in profile_text else profile_text[3:]
        # Remove closing fence
        if profile_text.endswith("```"):
            profile_text = profile_text[:-3]
        profile_text = profile_text.strip()

    try:
        profile = json.loads(profile_text)
    except json.JSONDecodeError as e:
        print_error(f"FAILED TO PARSE MODEL RESPONSE: {e}")
        print_warning(f"RAW RESPONSE: {profile_text[:500]}...")
        raise SystemExit(1)

    return profile


def save_profile(profile: dict, output_dir: Path) -> Path:
    """Save the profile to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "profile.json"

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    return output_path


@click.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--model", "-m", type=str, default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="./flightline_output",
    help="Output directory for the profile",
)
def learn(file_path: Path, model: str, output: Path):
    """Learn data structure from a sample file.

    Analyzes FILE_PATH and extracts schema, patterns, and rules
    into a profile that can be used to generate synthetic data.

    \b
    Examples:
      flightline learn data.json
      flightline learn data.json -o ./output
    """
    # Display boot sequence
    print_boot_sequence("LEARN")

    # Check for API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        print_error("OPENROUTER_API_KEY NOT SET")
        print_info("GET YOUR API KEY AT HTTPS://OPENROUTER.AI/KEYS")
        raise SystemExit(1)

    print_status("STARTING", "RDY")
    console.print()

    # Analyze the file
    profile = analyze_file(file_path, model)

    # Save the profile
    output_path = save_profile(profile, output)

    print_success("LEARNING COMPLETE")

    # Summary
    print_complete(
        {
            "PROFILE": output_path.name,
            "OUTPUT": str(output),
            "FIELDS": len(profile.get("schema", {})),
            "PII FIELDS": len(profile.get("pii_fields", [])),
            "RULES": len(profile.get("business_rules", [])),
        }
    )

    console.print()
    print_info("NEXT: RUN [FLIGHTLINE GENERATE -N 100] TO CREATE SYNTHETIC DATA")


if __name__ == "__main__":
    learn()
