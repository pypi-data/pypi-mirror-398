"""Generate module - Creates synthetic data from a learned profile."""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

import click
import httpx
from dotenv import load_dotenv
from openai import OpenAI

from flightline import __version__
from flightline.hud import (
    create_status_spinner,
    print_boot_sequence,
    print_complete,
    print_error,
    print_info,
)

load_dotenv()

# OpenRouter base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-3-flash-preview"


def get_client() -> OpenAI:
    """Initialize OpenAI client with OpenRouter base URL if available."""
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY.")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )


def sync_dataset_to_cloud(profile_id: str, record_count: int, sample_records: List[Dict]):
    """Sync metadata about the generated dataset to the cloud."""
    token = os.getenv("FLIGHTLINE_API_KEY")
    api_url = os.getenv("FLIGHTLINE_API_URL", "https://api.flightline.ai")

    if not token:
        return

    payload = {
        "profile_id": profile_id,
        "record_count": record_count,
        "sample_records": sample_records[:5],  # Only sync a small sample for visibility
        "tool_version": __version__,
        "model_used": DEFAULT_MODEL,
    }

    try:
        headers = {"X-API-Key": token}
        with httpx.Client(timeout=10.0) as client:
            client.post(f"{api_url}/api/v1/profiles/datasets", json=payload, headers=headers)
    except Exception:
        # Silently fail for background sync
        pass


@click.command()
@click.option(
    "--profile",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default="data_profile.json",
    help="Path to learned data profile",
)
@click.option("--count", "-n", type=int, default=10, help="Number of records to generate")
@click.option("--output", "-o", type=str, default="synthetic_data.json", help="Output file path")
@click.option("--model", "-m", type=str, default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
@click.option("--batch-size", "-b", type=int, default=10, help="Batch size for generation")
def generate(profile: Path, count: int, output: str, model: str, batch_size: int):
    """Generate realistic synthetic data from a learned profile."""
    print_boot_sequence("GENERATE", __version__)

    if not profile.exists():
        print_error(f"Profile not found: {profile}")
        return

    # Load profile
    try:
        profile_data = json.loads(profile.read_text())
    except Exception as e:
        print_error(f"Failed to read profile: {e}")
        return

    client = get_client()

    # Calculate batches
    total_batches = (count + batch_size - 1) // batch_size
    records_generated = 0

    # Results storage (indexed by batch)
    results: List[List] = [[] for _ in range(total_batches)]

    def generate_one_batch(batch_idx: int) -> Tuple[int, List]:
        """Generate a single batch of records."""
        current_batch_size = min(batch_size, count - (batch_idx * batch_size))

        prompt = f"""Generate {current_batch_size} realistic synthetic records based on this data profile:

{json.dumps(profile_data, indent=2)}

CRITICAL:
- Output valid JSON only
- Output an ARRAY of records
- Do NOT include any real PII from the profile (if any)
- Ensure data is varied and realistic
- Follow all business rules and patterns in the profile
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a synthetic data generation engine. Output only raw JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        try:
            content = response.choices[0].message.content
            # Handle potential wrapping object from LLM
            data = json.loads(content)
            if isinstance(data, dict):
                # Try to find the array in the object
                for val in data.values():
                    if isinstance(val, list):
                        return batch_idx, val[:current_batch_size]
            return batch_idx, data if isinstance(data, list) else []
        except Exception:
            return batch_idx, []

    # Run batches in parallel
    print_info(f"GENERATING {count} RECORDS IN {total_batches} BATCHES...")

    with create_status_spinner("GENERATING BATCHES") as spinner:
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_batch = {executor.submit(generate_one_batch, i): i for i in range(total_batches)}

            for future in as_completed(future_to_batch):
                idx, batch_results = future.result()
                results[idx] = batch_results
                records_generated += len(batch_results)
                spinner.update(f"GENERATED {records_generated}/{count} RECORDS")

    # Flatten results
    all_records = [rec for batch in results for rec in batch]

    # Save to file
    with open(output, "w") as f:
        json.dump(all_records, f, indent=2)

    print_complete(f"SUCCESS: {len(all_records)} records saved to {output}")

    # Sync metadata to cloud if profile contains cloud ID
    if "cloud_id" in profile_data:
        sync_dataset_to_cloud(profile_data["cloud_id"], len(all_records), all_records)
