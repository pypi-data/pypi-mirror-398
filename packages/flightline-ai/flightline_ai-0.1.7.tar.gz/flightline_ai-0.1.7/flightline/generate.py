"""Generate module - Creates synthetic data from a learned profile."""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv
from openai import OpenAI

from flightline.hud import (
    MFDProgress,
    console,
    print_boot_sequence,
    print_complete,
    print_error,
    print_info,
    print_status,
    print_success,
    print_target,
)

# Load .env file if present
load_dotenv()

# OpenRouter base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-3-flash-preview"
BATCH_SIZE = 10  # Records per API call


def get_client() -> OpenAI:
    """Create an OpenRouter-compatible client."""
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )


SYSTEM_PROMPT = """You are a synthetic data generator. You generate realistic fake data based on a learned data profile.

RULES:
1. Match the EXACT schema structure - same fields, nesting, and data types
2. Follow ALL business rules from the profile
3. Generate realistic but FAKE values for PII (names, emails, phones, addresses)
4. Make each record UNIQUE with varied values
5. Output valid JSON only - a JSON object with a "records" array"""


def load_profile(profile_path: Path) -> dict:
    """Load the data profile from file."""
    with open(profile_path) as f:
        return json.load(f)


def generate_batch(client: OpenAI, profile: dict, count: int, model: str) -> list:
    """Generate a single batch of records."""
    profile_text = json.dumps(profile, indent=2)

    user_prompt = f"""Generate exactly {count} synthetic data records based on this profile.

PROFILE:
{profile_text}

IMPORTANT:
- Generate {count} COMPLETE records matching the schema
- Each record must have ALL fields from the schema
- Follow all business_rules (calculations must be correct!)
- Use fake but realistic PII values
- Make each record unique

Output as: {{"records": [... {count} complete records ...]}}"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
        response_format={"type": "json_object"},
        temperature=0.8,
    )

    result_text = response.choices[0].message.content
    result = json.loads(result_text)

    # Extract records from response
    if isinstance(result, dict):
        if "records" in result and isinstance(result["records"], list):
            return result["records"]
        for key, value in result.items():
            if isinstance(value, list) and len(value) > 0:
                return value
        return [result]
    elif isinstance(result, list):
        return result

    return [result]


def generate_records_parallel(profile: dict, count: int, model: str, progress: MFDProgress) -> list:
    """Generate records in parallel batches with progress updates."""
    client = get_client()

    # Calculate batch sizes
    total_batches = progress.total_batches
    batch_sizes = []
    remaining = count
    for _ in range(total_batches):
        batch_count = min(BATCH_SIZE, remaining)
        batch_sizes.append(batch_count)
        remaining -= batch_count

    # Mark all batches as active
    progress.start_all()

    # Results storage (indexed by batch)
    results: list[list] = [[] for _ in range(total_batches)]

    def generate_one_batch(batch_idx: int) -> tuple[int, list]:
        """Generate a single batch and return (index, records)."""
        batch_count = batch_sizes[batch_idx]
        records = generate_batch(client, profile, batch_count, model)
        return batch_idx, records

    # Execute all batches in parallel
    with ThreadPoolExecutor(max_workers=total_batches) as executor:
        futures = {executor.submit(generate_one_batch, i): i for i in range(total_batches)}

        for future in as_completed(futures):
            batch_idx, records = future.result()
            results[batch_idx] = records
            progress.complete_batch(batch_idx, len(records))

    # Flatten results in order
    all_records = []
    for batch_records in results:
        all_records.extend(batch_records)

    return all_records


def save_output(records: list, output_dir: Path) -> Path:
    """Save the synthetic data to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use timestamp to avoid overwriting previous runs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"synthetic_{timestamp}.json"

    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    return output_path


@click.command()
@click.option("--count", "-n", type=int, default=10, help="Number of records to generate")
@click.option("--model", "-m", type=str, default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
@click.option(
    "--profile",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default="./flightline_output/profile.json",
    help="Path to the learned profile",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="./flightline_output",
    help="Output directory for generated data",
)
def generate(count: int, model: str, profile: Path, output: Path):
    """Generate synthetic data from a learned profile.

    Uses the profile created by 'flightline learn' to generate
    realistic synthetic records.

    \b
    Examples:
      flightline generate -n 100
      flightline gen -n 50 -p custom_profile.json
    """
    # Display boot sequence
    print_boot_sequence("GENERATE")

    # Check for API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        print_error("OPENROUTER_API_KEY NOT SET")
        print_info("GET YOUR API KEY AT HTTPS://OPENROUTER.AI/KEYS")
        raise SystemExit(1)

    # Check profile exists
    if not profile.exists():
        print_error(f"PROFILE NOT FOUND: {profile}")
        print_info("RUN [FLIGHTLINE LEARN <FILE>] FIRST")
        raise SystemExit(1)

    print_status("STARTING", "RDY")
    console.print()

    print_target("PROFILE", str(profile), wp_num=1)
    print_target("OUTPUT", str(output), wp_num=2)
    print_info(f"MODEL: {model}")
    print_info(f"COUNT: {count}")
    console.print()

    print_status("LOADING PROFILE", "ACT")
    profile_data = load_profile(profile)
    print_success("PROFILE LOADED")

    console.print()

    # Generate with MFD progress panel (parallel batches)
    with MFDProgress(total_records=count, batch_size=BATCH_SIZE) as progress:
        records = generate_records_parallel(profile_data, count, model, progress)

    console.print()
    print_success(f"GENERATED {len(records)} RECORDS")

    # Save the results
    console.print()
    print_status("WRITING OUTPUT", "ACT")
    output_path = save_output(records, output)
    print_success("SAVED")

    # Summary
    print_complete(
        {
            "RECORDS": len(records),
            "FILE": output_path.name,
            "OUTPUT": str(output),
        }
    )


if __name__ == "__main__":
    generate()
