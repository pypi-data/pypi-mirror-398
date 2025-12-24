"""Minimal entry point for the ``rai-dev`` CLI."""

from __future__ import annotations

import click

VERSION = "1.0.0a1"


@click.command()
@click.version_option(version=VERSION, prog_name="rai-dev")
def cli() -> None:
    """Display the CLI version."""
    click.echo(f"rai-dev version {VERSION}")


if __name__ == "__main__":
    cli()

