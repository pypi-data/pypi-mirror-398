"""Learn module - Analyzes input files to create a data profile."""

import json
import os
from pathlib import Path
from typing import Optional

import click
import httpx
from dotenv import load_dotenv
from openai import OpenAI

from flightline import __version__
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
from flightline.learn.pydantic_parser import parse_pydantic_model
from flightline.learn.typescript_parser import parse_typescript_interface

# Load .env file if present
load_dotenv()

# OpenRouter base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-3-flash-preview"

# Profile format constants
FORMAT_DATA_SAMPLE = "data_sample"
FORMAT_TYPESCRIPT = "typescript"
FORMAT_PYDANTIC = "pydantic"

# Profile role constants
ROLE_INPUT = "input"
ROLE_OUTPUT = "output"

SYSTEM_PROMPT = """You are a data analyst expert. Analyze the provided data and create a data profile -
a descriptive specification of this data structure.

Your profile must include:

1. **Schema**: The exact structure/shape of the data (fields, nesting, arrays)
2. **Data Types**: The type of each field (string, number, boolean, date, etc.)
3. **Business Logic**: Any implicit rules you can infer, such as:
   - Timestamps must be sequential
   - Certain fields are derived from others
   - Value ranges or constraints
   - Required vs optional fields
4. **PII Fields**: Identify any fields that appear to contain personally identifiable information
   (names, emails, phone numbers, addresses, SSNs, etc.)
5. **Patterns**: Any patterns in the data (date formats, ID formats, naming conventions)

Output your analysis as valid JSON with this structure:
{
    "schema": { ... field definitions ... },
    "data_types": { "field_name": "type", ... },
    "business_rules": [ "rule 1", "rule 2", ... ],
    "pii_fields": [ "field1", "field2", ... ],
    "patterns": { "field_name": "pattern description", ... },
    "example_formats": { "field_name": "format description or pattern", ... },
    "required_fields": [ "field1", "field2", ... ]
}

CRITICAL - PII PROTECTION:
- Do NOT copy any actual values from the input data into the profile
- For "example_formats", describe the FORMAT/PATTERN only (e.g., "email format: user@domain.com",
  "phone format: +1-555-XXX-XXXX")
- Never include real names, emails, addresses, phone numbers, or any identifiable information
- The profile must contain ZERO original data values - only structural descriptions

Be thorough but concise. The profile will be used to generate synthetic test data."""


def get_client() -> OpenAI:
    """Create an OpenRouter-compatible client."""
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )


def detect_file_type(file_path: Path) -> str:
    """Detect the type of file based on extension.

    Returns one of: 'typescript', 'pydantic', 'data_sample'
    """
    suffix = file_path.suffix.lower()

    # TypeScript interfaces
    if suffix in (".ts", ".tsx", ".d.ts"):
        return FORMAT_TYPESCRIPT

    # Python files (potentially Pydantic)
    if suffix == ".py":
        return FORMAT_PYDANTIC

    # Data files that need LLM analysis
    if suffix in (".json", ".csv", ".jsonl", ".yaml", ".yml"):
        return FORMAT_DATA_SAMPLE

    # Default to data sample for unknown types
    return FORMAT_DATA_SAMPLE


def analyze_typescript(file_path: Path) -> tuple[dict, str]:
    """Parse TypeScript file into a profile.

    Returns (profile, raw_content)
    """
    content = file_path.read_text()
    print_target("INPUT", file_path.name, wp_num=1)
    print_info("FORMAT: TypeScript Interface")

    with create_status_spinner("PARSING TYPESCRIPT"):
        profile = parse_typescript_interface(content)

    return profile, content


def analyze_pydantic(file_path: Path) -> tuple[dict, str]:
    """Parse Python/Pydantic file into a profile.

    Returns (profile, raw_content)
    """
    content = file_path.read_text()
    print_target("INPUT", file_path.name, wp_num=1)
    print_info("FORMAT: Pydantic Model")

    with create_status_spinner("PARSING PYDANTIC"):
        profile = parse_pydantic_model(content)

    return profile, content


def analyze_data_file(file_path: Path, model: str) -> tuple[dict, None]:
    """Send data file content to LLM for analysis.

    Returns (profile, None) - no raw content for LLM-analyzed files
    """
    client = get_client()

    content = file_path.read_text()

    # Truncate very large files to avoid token limits
    max_chars = 50000
    if len(content) > max_chars:
        content = content[:max_chars]
        print_warning(f"FILE TRUNCATED TO {max_chars} CHARACTERS")

    print_target("INPUT", file_path.name, wp_num=1)
    print_info(f"FORMAT: Data Sample (using {model})")

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

    # Normalize schema key
    if "schema" in profile and "schema_data" not in profile:
        profile["schema_data"] = profile.pop("schema")

    return profile, None


def save_profile(profile: dict, output_dir: Path, name: str) -> Path:
    """Save the profile to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{name}_profile.json"

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    return output_path


def sync_profile_to_cloud(
    profile: dict,
    name: str,
    source_file: str,
    api_url: str,
    role: str,
    file_format: str,
    raw_type_definition: Optional[str] = None,
    repository: Optional[str] = None,
) -> Optional[str]:
    """Sync a profile to the Flightline cloud backend.

    Returns the profile ID if successful, None otherwise.
    """
    payload = {
        "name": name,
        "source_type": "learned",
        "role": role,
        "format": file_format,
        "source_file": source_file,
        "raw_type_definition": raw_type_definition,
        "schema_data": profile.get("schema_data", profile.get("schema", {})),
        "data_types": profile.get("data_types", {}),
        "business_rules": profile.get("business_rules", []),
        "pii_fields": profile.get("pii_fields", []),
        "patterns": profile.get("patterns", {}),
        "example_formats": profile.get("example_formats", {}),
        "required_fields": profile.get("required_fields", []),
        "value_constraints": profile.get("value_constraints", {}),
        "tool_version": __version__,
    }

    # If we have a repository context, look up the repository_id
    repository_id = None
    if repository:
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{api_url.rstrip('/')}/api/v1/repos/lookup",
                    json={"full_name": repository},
                )
                if resp.status_code == 200:
                    repository_id = resp.json().get("id")
        except httpx.HTTPError:
            # Fall back to no repository association
            pass

    if repository_id:
        payload["repository_id"] = repository_id

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{api_url.rstrip('/')}/api/v1/profiles",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("id")
    except httpx.HTTPError as e:
        print_error(f"SYNC FAILED: {e}")
        return None


@click.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--model",
    "-m",
    type=str,
    default=DEFAULT_MODEL,
    help=f"Model to use for data files (default: {DEFAULT_MODEL})",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="./flightline_output",
    help="Output directory for the profile",
)
@click.option(
    "--name",
    "-n",
    type=str,
    default=None,
    help="Profile name (default: derived from filename)",
)
@click.option(
    "--role",
    "-r",
    type=click.Choice(["input", "output"]),
    default="input",
    help="Profile role: input (data going IN to AI) or output (data coming OUT)",
)
@click.option(
    "--sync",
    is_flag=True,
    help="Sync profile to Flightline cloud",
)
@click.option(
    "--api-url",
    default=lambda: os.getenv("FLIGHTLINE_API_URL", "https://api.flightlinehq.com"),
    help="Flightline API URL",
)
@click.option(
    "--repository",
    default=lambda: os.getenv("GITHUB_REPOSITORY"),
    help="GitHub repository (org/repo). Auto-detected in CI.",
)
def learn(
    file_path: Path,
    model: str,
    output: Path,
    name: Optional[str],
    role: str,
    sync: bool,
    api_url: str,
    repository: Optional[str],
):
    """Learn data structure from a sample file.

    Analyzes FILE_PATH and extracts schema, patterns, and rules
    into a profile that can be used for testing.

    Supports multiple file types:
    - .json, .csv, .yaml: LLM-analyzed data samples
    - .ts, .d.ts: TypeScript interfaces (parsed directly)
    - .py: Pydantic models (parsed directly)

    Use --role to specify if this describes INPUT or OUTPUT data.

    \b
    Examples:
      # Learn from data sample (input profile)
      flightline learn customer_data.json

      # Learn from TypeScript interface (output profile)
      flightline learn AIResponse.ts --role output

      # Learn from Pydantic model and sync to cloud
      flightline learn models.py --sync
    """
    # Display boot sequence
    print_boot_sequence("LEARN")

    # Detect file type
    file_format = detect_file_type(file_path)
    raw_type_definition: Optional[str] = None

    # Parse based on file type
    if file_format == FORMAT_TYPESCRIPT:
        profile, raw_type_definition = analyze_typescript(file_path)
    elif file_format == FORMAT_PYDANTIC:
        profile, raw_type_definition = analyze_pydantic(file_path)
    else:
        # Data files need LLM - check for API key
        if not os.environ.get("OPENROUTER_API_KEY"):
            print_error("OPENROUTER_API_KEY NOT SET")
            print_info("GET YOUR API KEY AT HTTPS://OPENROUTER.AI/KEYS")
            print_info("(TypeScript and Pydantic files don't require an API key)")
            raise SystemExit(1)
        profile, _ = analyze_data_file(file_path, model)

    print_status("LEARNING COMPLETE", "OK")

    # Check if we got any useful data
    schema_data = profile.get("schema_data", profile.get("schema", {}))
    if not schema_data:
        print_warning("NO SCHEMA DETECTED - FILE MAY NOT CONTAIN STRUCTURED DATA")
        if file_format == FORMAT_PYDANTIC:
            print_info("ENSURE FILE CONTAINS PYDANTIC MODELS (CLASSES INHERITING FROM BASEMODEL)")
        elif file_format == FORMAT_TYPESCRIPT:
            print_info("ENSURE FILE CONTAINS TYPESCRIPT INTERFACES")

    # Derive profile name
    profile_name = name or file_path.stem

    # Save the profile locally
    output_path = save_profile(profile, output, profile_name)

    print_success(f"PROFILE SAVED: {output_path}")

    # Sync to cloud if requested
    profile_id = None
    if sync:
        print_status("SYNCING TO CLOUD", "ACT")
        profile_id = sync_profile_to_cloud(
            profile=profile,
            name=profile_name,
            source_file=str(file_path),
            api_url=api_url,
            role=role,
            file_format=file_format,
            raw_type_definition=raw_type_definition,
            repository=repository,
        )
        if profile_id:
            print_success(f"SYNCED: {profile_id}")
        else:
            print_warning("SYNC FAILED - PROFILE SAVED LOCALLY ONLY")

    # Summary
    summary = {
        "PROFILE": output_path.name,
        "OUTPUT": str(output),
        "FORMAT": file_format.upper(),
        "ROLE": role.upper(),
        "FIELDS": len(schema_data),
        "PII FIELDS": len(profile.get("pii_fields", [])),
        "REQUIRED": len(profile.get("required_fields", [])),
    }
    if profile_id:
        summary["CLOUD ID"] = profile_id

    print_complete(summary)

    console.print()
    if role == "input":
        print_info("NEXT: RUN [FLIGHTLINE GENERATE] TO CREATE SYNTHETIC TEST DATA")
    else:
        print_info("OUTPUT PROFILE READY FOR VALIDATION TESTING")


if __name__ == "__main__":
    learn()
