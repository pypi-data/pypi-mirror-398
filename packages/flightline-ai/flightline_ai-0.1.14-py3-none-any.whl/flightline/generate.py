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
    MFDProgress,
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
@click.option(
    "--engine",
    type=click.Choice(["backend", "openrouter"]),
    default="backend",
    show_default=True,
    help="Where to run generation. Backend is recommended; OpenRouter is a fallback.",
)
@click.option(
    "--backend-url",
    default=lambda: os.getenv("FLIGHTLINE_BACKEND_URL", "https://be.flightlinehq.com"),
    show_default=True,
    help="Backend base URL used when --engine=backend (no trailing /api/v1 required).",
)
def generate(profile: Path, count: int, output: str, model: str, batch_size: int, engine: str, backend_url: str):
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

    if engine == "backend":
        # Backend request schema currently caps batch_size at 100.
        batch_size = max(1, min(int(batch_size), 100))

        # Split into batches so we can display progress and avoid long single-request timeouts.
        total_batches = (count + batch_size - 1) // batch_size
        results: List[List[Dict]] = [[] for _ in range(total_batches)]

        def call_backend_batch(batch_idx: int, n: int) -> Tuple[int, List[Dict]]:
            """Call backend to generate n records for one batch."""
            attempts = 0
            last_err: Exception | None = None
            while attempts < 3:
                attempts += 1
                try:
                    with httpx.Client(timeout=120.0) as client:
                        resp = client.post(
                            f"{backend_url.rstrip('/')}/api/v1/generate",
                            json={
                                "profile": profile_data,
                                "count": n,
                                # Force backend to do a single batch for this request.
                                "batch_size": n,
                                "model": model,
                                "profile_id": profile_data.get("cloud_id"),
                                "tool_version": __version__,
                            },
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        records = data.get("records", [])
                        if isinstance(records, list):
                            # Ensure dict records only
                            return batch_idx, [r for r in records if isinstance(r, dict)]
                        return batch_idx, []
                except Exception as e:
                    last_err = e
            raise last_err or RuntimeError("Backend generate failed")

        try:
            print_info(f"GENERATING {count} RECORDS VIA BACKEND IN {total_batches} BATCHES...")
            with MFDProgress(total_records=count, batch_size=batch_size) as progress:
                # Keep concurrency conservative (backend will call OpenRouter under the hood).
                max_workers = min(3, total_batches)
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_idx = {}
                    for i in range(total_batches):
                        n = min(batch_size, count - (i * batch_size))
                        progress.start_batch(i)
                        future_to_idx[executor.submit(call_backend_batch, i, n)] = i

                    for future in as_completed(future_to_idx):
                        idx, batch_records = future.result()
                        results[idx] = batch_records
                        progress.complete_batch(idx, len(batch_records))
        except Exception as e:
            print_error(f"BACKEND GENERATE FAILED: {e}")
            print_info("TIP: Use --engine openrouter to run locally, or check FLIGHTLINE_BACKEND_URL.")
            return

        # Save to file
        records = [rec for batch in results for rec in batch][:count]
        with open(output, "w") as f:
            json.dump(records, f, indent=2)

        # print_complete expects a dict; it will also accept a string for backwards compatibility.
        print_complete({"success": True, "records": len(records), "output": output})
        return

    # Legacy (direct-to-OpenRouter/OpenAI compatible) path
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

    # print_complete expects a dict; it will also accept a string for backwards compatibility.
    print_complete({"success": True, "records": len(all_records), "output": output})

    # Sync metadata to cloud if profile contains cloud ID
    if "cloud_id" in profile_data:
        sync_dataset_to_cloud(profile_data["cloud_id"], len(all_records), all_records)
