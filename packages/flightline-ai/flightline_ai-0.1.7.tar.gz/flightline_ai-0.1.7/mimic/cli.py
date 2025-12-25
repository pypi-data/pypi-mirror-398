"""Flightline CLI - Synthetic data generation tool."""

import click

from mimic.learn import learn
from mimic.generate import generate


@click.group()
@click.version_option(version="0.1.0", prog_name="flightline")
def cli():
    """Flightline - Synthetic data generation.
    
    Learn from sample data, then generate realistic synthetic records.
    
    \b
    Quick start:
      flightline learn samples/data.json
      flightline generate -n 100
    """
    pass


# Register commands
cli.add_command(learn)
cli.add_command(generate)

# Add 'gen' as an alias for 'generate'
cli.add_command(generate, name="gen")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()









