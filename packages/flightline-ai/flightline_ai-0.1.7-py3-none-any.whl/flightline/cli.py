"""Flightline CLI - AI testing and synthetic data generation tool."""

import click

from flightline import __version__
from flightline.discover_cmd import discover
from flightline.generate import generate
from flightline.learn import learn
from flightline.scaffold import scaffold


@click.group()
@click.version_option(version=__version__, prog_name="flightline")
def cli():
    """Flightline - AI testing and synthetic data generation.

    Discover AI operations, learn from sample data, and generate
    realistic synthetic records for testing.

    \b
    Quick start:
      flightline discover              # Find AI operations in your codebase
      flightline learn samples/data.json
      flightline generate -n 100
    """
    pass


# Register commands
cli.add_command(discover)
cli.add_command(learn)
cli.add_command(generate)
cli.add_command(scaffold)

# Add 'gen' as an alias for 'generate'
cli.add_command(generate, name="gen")

# Add 'scan' as an alias for 'discover'
cli.add_command(discover, name="scan")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
