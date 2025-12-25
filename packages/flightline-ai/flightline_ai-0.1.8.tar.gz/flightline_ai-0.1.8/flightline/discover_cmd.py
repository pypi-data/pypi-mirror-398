"""Flightline Discover command - AI operation discovery."""

from __future__ import annotations

import os
import subprocess
from contextlib import nullcontext
from pathlib import Path
from typing import Dict, List, Optional, Set

import click
import httpx

from flightline import __version__
from flightline.discover.diff import compare_discoveries
from flightline.discover.ingest import (
    build_repo_metadata,
    detect_project_signals,
    enumerate_files,
)
from flightline.discover.interpret import interpret_all, sort_by_risk
from flightline.discover.observe import observe_all
from flightline.discover.schema import (
    Artifact,
    DiscoveryOutput,
    RiskTier,
    SourceType,
)
from flightline.hud import (
    console,
    create_status_spinner,
    print_boot_sequence,
    print_info,
    print_warning,
)


def _get_repo_commit(path: Path) -> Optional[str]:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def print_discovery_summary(output: DiscoveryOutput):
    """Print a high-level summary of the discovery results."""
    from flightline.discover.schema import DetectionMethod

    # Check for baseline diffs
    has_diff = hasattr(output, "_diff") and output._diff

    # ... existing counts logic ...
    provider_counts: Dict[str, int] = {}
    for node in output.nodes:
        provider = node.provider.value
        provider_counts[provider] = provider_counts.get(provider, 0) + 1

    # Count by detection method
    method_counts: Dict[str, int] = {
        DetectionMethod.SDK_VERIFIED: 0,
        DetectionMethod.HEURISTIC: 0,
    }
    for node in output.nodes:
        method_counts[node.detection_method] = method_counts.get(node.detection_method, 0) + 1

    # Count input sources
    source_counts: Dict[str, int] = {}
    for node in output.nodes:
        if node.inputs.system_prompt:
            src = node.inputs.system_prompt.source_type.value
            source_counts[src] = source_counts.get(src, 0) + 1
        for cv in node.inputs.context_variables:
            src = cv.source_type.value
            source_counts[src] = source_counts.get(src, 0) + 1

    # Diff summary line
    if has_diff:
        diff = output._diff
        diff_parts = []
        if diff["new"]:
            diff_parts.append(f"[green]+{len(diff['new'])} NEW[/green]")
        if diff["risk_changes"]:
            diff_parts.append(f"[yellow]!{len(diff['risk_changes'])} CHANGED RISK[/yellow]")
        if diff["removed"]:
            diff_parts.append(f"[red]-{len(diff['removed'])} REMOVED[/red]")

        if diff_parts:
            print_info("CHANGES FROM BASELINE: " + " | ".join(diff_parts))

    print_info(f"FOUND {len(output.nodes)} AI OPERATIONS:")
    for provider, count in sorted(provider_counts.items(), key=lambda x: -x[1]):
        print_info(f"  • {provider.upper()}: {count}")

    if method_counts[DetectionMethod.HEURISTIC] > 0:
        print_info(f"  • CUSTOM/HEURISTIC: {method_counts[DetectionMethod.HEURISTIC]}")

    # Top Risks Display
    top_nodes = sort_by_risk(output.nodes)[:5]
    if top_nodes:
        from rich.text import Text

        print_info("TOP RISK ANALYSIS:")

        # Box dimensions
        inner_width = 74
        box_width = inner_width + 6

        text = Text()
        text.append("┌" + "─" * (box_width - 2) + "┐", style="hud.frame")
        text.append("\n")

        for i, node in enumerate(top_nodes):
            risk = node.interpretation.risk_tier if node.interpretation else RiskTier.LOW

            # Risk Header
            risk_label = f"[{risk.value.upper()}]"
            header = f"  {risk_label} {node.location.file}:{node.location.line}"
            text.append("│  ", style="hud.frame")
            text.append(header.ljust(inner_width))
            text.append("  │\n", style="hud.frame")

            # Observations
            if node.interpretation and node.interpretation.observations_summary:
                for obs in node.interpretation.observations_summary[:2]:
                    obs_line = f"   └─ {obs}"
                    text.append("│  ", style="hud.frame")
                    text.append(obs_line.ljust(inner_width))
                    text.append("  │\n", style="hud.frame")

            # Sinks
            if node.usage.sinks:
                sinks_text = "   └─ Sinks: " + " | ".join([s.value.upper() for s in node.usage.sinks])
                text.append("│  ", style="hud.frame")
                text.append(sinks_text.ljust(inner_width))
                text.append("  │\n", style="hud.frame")

            # Blank line between nodes
            if i < len(top_nodes) - 1:
                text.append("│  " + " " * inner_width + "│\n", style="hud.frame")

        text.append("└" + "─" * (box_width - 2) + "┘", style="hud.frame")

        console.print(text)
        console.print()

    # Input sources summary
    if source_counts:
        external_sources = {k: v for k, v in source_counts.items() if k in {"api", "database", "user_input", "config"}}

        if external_sources:
            print_info("INPUT SOURCES DETECTED:")
            for src, count in sorted(external_sources.items(), key=lambda x: -x[1]):
                source_label = {
                    "api": "from external APIs",
                    "database": "from database",
                    "user_input": "from user input",
                    "config": "from configuration/env",
                }.get(src, f"from {src}")
                print_info(f"  • {count} data point(s) {source_label}")

    # Next steps
    if output.nodes:
        print_info("NEXT: Review discovery.json and run [flightline learn] on input sources")


def _sync_to_cloud(
    output: DiscoveryOutput,
    repository: Optional[str],
    pr_number: Optional[int],
    branch: Optional[str],
    commit_sha: Optional[str],
):
    """Upload discovery results to Flightline Mission Control."""
    token = os.getenv("FLIGHTLINE_API_KEY")
    api_url = os.getenv("FLIGHTLINE_API_URL", "https://api.flightline.ai")

    if not token:
        return

    # Prepare payload
    payload = {
        "repository": repository,
        "branch": branch,
        "pr_number": pr_number,
        "commit_sha": commit_sha,
        "tool_version": output.tool_version,
        "nodes": [],
    }

    for node in output.nodes:
        node_data = {
            "id": node.id,
            "file_path": node.location.file,
            "line_number": node.location.line,
            "function_name": node.location.function,
            "provider": node.provider.value,
            "call_type": node.call_type.value,
            "risk_tier": node.interpretation.risk_tier.value if node.interpretation else "low",
            "observations": node.interpretation.observations_summary if node.interpretation else [],
            "extraction": {
                "prompt_confidence": node.extraction.prompt_confidence.value,
                "input_schema_confidence": node.extraction.input_schema_confidence.value,
                "output_schema_confidence": node.extraction.output_schema_confidence.value,
                "prompt_preview": node.extraction.prompt_preview,
                "input_type_name": node.extraction.input_type_name,
                "output_type_name": node.extraction.output_type_name,
            },
        }
        payload["nodes"].append(node_data)

    try:
        headers = {"X-API-Key": token}
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{api_url}/api/v1/discoveries", json=payload, headers=headers)
            if response.status_code == 200:
                print_info("Cloud sync complete: PR report updated.")
            else:
                print_warning(f"Cloud sync failed (HTTP {response.status_code})")
    except Exception as e:
        print_warning(f"Cloud sync unavailable: {str(e)}")


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--output", "-o", type=str, default="flightline.discovery.json", help="Output JSON file")
@click.option("--languages", "-l", type=str, help="Comma-separated languages to scan (python,javascript,typescript)")
@click.option("--sync", is_flag=True, help="Sync results to Flightline Mission Control (requires FLIGHTLINE_API_KEY)")
@click.option("--repository", envvar="GITHUB_REPOSITORY", help="Repository full name (owner/repo)")
@click.option("--pr-number", type=int, envvar="GITHUB_PR_NUMBER", help="PR number for cloud sync")
@click.option("--branch", envvar="GITHUB_REF_NAME", help="Current branch name")
@click.option("--commit-sha", envvar="GITHUB_SHA", help="Current commit SHA")
@click.option("--baseline", type=click.Path(exists=True, path_type=Path), help="Baseline discovery file to compare")
@click.option("--quiet", "quiet_mode", is_flag=True, help="Reduce output verbosity")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON (legacy compatibility)")
def discover(
    path: Path,
    output: str,
    languages: Optional[str],
    sync: bool,
    repository: Optional[str],
    pr_number: Optional[int],
    branch: Optional[str],
    commit_sha: Optional[str],
    baseline: Optional[Path] = None,
    quiet_mode: bool = False,
    json_output: bool = False,
):
    """Discover AI operations in your codebase."""
    # If JSON output is requested, suppress HUD output
    if json_output:
        quiet_mode = True

    if not quiet_mode:
        print_boot_sequence("DISCOVER", __version__)

    root = path.absolute()
    lang_set = set(languages.split(",")) if languages else None

    # 1. Index files
    with create_status_spinner("INDEXING FILES") if not quiet_mode else nullcontext():
        file_index = enumerate_files(root, languages=lang_set)

    # 2. Extract metadata
    repo_meta = build_repo_metadata(file_index)
    signals = detect_project_signals(file_index)

    # 3. Detect and observe
    with create_status_spinner("DETECTING PROJECT TYPE") if not quiet_mode else nullcontext():
        # Signals were already built, just status feedback
        pass

    with create_status_spinner("SCANNING FOR AI OPERATIONS") if not quiet_mode else nullcontext():
        observations = observe_all(file_index)

    # 4. Interpret
    with create_status_spinner("ANALYZING RISK") if not quiet_mode else nullcontext():
        interpreted = interpret_all(observations)

    # 5. Build output
    output_data = DiscoveryOutput(
        repo=repo_meta,
        project_signals=signals,
        nodes=interpreted,
        tool_version=__version__,
        repo_commit=_get_repo_commit(root),
    )

    # Collect artifacts (prompt sources, etc.)
    artifacts: List[Artifact] = []
    seen_sources: Set[str] = set()

    for obs in observations:
        if obs.inputs.system_prompt and obs.inputs.system_prompt.source_hint:
            hint = obs.inputs.system_prompt.source_hint
            if hint not in seen_sources and obs.inputs.system_prompt.source_type == SourceType.API:
                seen_sources.add(hint)
                artifacts.append(
                    Artifact(
                        type="prompt_source",
                        reference=hint,
                        used_by=[obs.id],
                    )
                )

    output_data.artifacts = artifacts

    # 6. Compare with baseline if provided
    if baseline:
        try:
            baseline_data = DiscoveryOutput.parse_file(baseline)
            diff = compare_discoveries(output_data, baseline_data)
            output_data._diff = diff
        except Exception as e:
            print_warning(f"Could not load baseline: {str(e)}")

    # 7. Write results
    json_str = output_data.model_dump_json(indent=2)
    with open(output, "w", encoding="utf-8") as f:
        f.write(json_str)

    if json_output:
        # Print JSON to stdout for programmatic consumption
        click.echo(json_str)
    elif not quiet_mode:
        print_discovery_summary(output_data)
        print_info(f"✓ Discovery saved to {output}")

    # 8. Sync to cloud
    if sync:
        _sync_to_cloud(output_data, repository, pr_number, branch, commit_sha)
