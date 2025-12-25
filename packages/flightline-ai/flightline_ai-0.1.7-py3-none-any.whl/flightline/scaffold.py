"""Flightline Scaffold command - Generate flightline.yaml from discovery."""

from pathlib import Path

import click

from flightline.discover.ingest import (
    enumerate_files,
)
from flightline.discover.interpret import interpret_all
from flightline.discover.observe import observe_all
from flightline.hud import (
    console,
    create_status_spinner,
    print_boot_sequence,
    print_complete,
    print_info,
    print_status,
    print_success,
    print_warning,
)


def _generate_yaml_config(nodes: list) -> str:
    """Generate a commented flightline.yaml from discovery nodes."""
    yaml = [
        "# 🛩️ Flightline Configuration",
        "# This file defines your AI operations and testing rubrics.",
        "",
        'project_name: "flightline-project"',
        "",
        "monitoring:",
        "  # Fail CI if regressions are found in these tiers",
        '  fail_on: "critical"',
        "  # Directories to scan for AI operations",
        "  scan_paths:",
        '    - "./src"',
        '    - "./app"',
        "  # Patterns to ignore",
        "  ignore:",
        '    - "**/node_modules/**"',
        '    - "**/tests/**"',
        '    - "**/dist/**"',
        "",
        "operations:",
    ]

    for node in nodes:
        func_name = node.location.function or "module"
        tier = node.interpretation.risk_tier.value if node.interpretation else "medium"

        yaml.append(f'  - id: "{node.id}"')
        yaml.append(f'    name: "{func_name}"')
        yaml.append(f'    path: "{node.location.file}"')
        yaml.append(f'    risk_tier: "{tier}"')
        yaml.append('    # custom_rubric: "./rubrics/default.md"')
        yaml.append("")

    return "\n".join(yaml)


@click.command()
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path),
    default=".",
)
@click.option(
    "--out",
    "-o",
    type=click.Path(path_type=Path),
    default="flightline.yaml",
    help="Output config file path",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing config",
)
def scaffold(path: Path, out: Path, force: bool):
    """Automatically generate flightline.yaml based on codebase discovery.

    This is the first step in setting up Flightline in a new repository.
    It scans your code for AI operations and proposes a flight plan.
    """
    if out.exists() and not force:
        print_warning(f"CONFIG FILE ALREADY EXISTS: {out}")
        print_info("USE --force TO OVERWRITE")
        return

    print_boot_sequence("SCAFFOLD")
    print_status("ANALYZING REPOSITORY", "RDY")
    console.print()

    root = path.resolve()

    # Run a quick discovery
    with create_status_spinner("INDEXING FILES"):
        file_index = enumerate_files(root, max_files=5000)

    if not file_index.files:
        print_warning("NO SUPPORTED FILES FOUND")
        return

    with create_status_spinner("SCANNING FOR AI OPERATIONS"):
        observations = observe_all(file_index)
        observations = interpret_all(observations)

    if not observations:
        print_warning("NO AI OPERATIONS DETECTED")
        print_info("CREATING BOILERPLATE CONFIG INSTEAD")
    else:
        print_success(f"MAPPED {len(observations)} AI OPERATIONS")

    # Generate YAML
    config_yaml = _generate_yaml_config(observations)

    # Write to file
    with open(out, "w", encoding="utf-8") as f:
        f.write(config_yaml)

    print_complete(
        {
            "CONFIG CREATED": str(out),
            "OPERATIONS MAPPED": len(observations),
        }
    )

    console.print()
    print_info("NEXT: Review flightline.yaml and merge to enable CI monitoring")
