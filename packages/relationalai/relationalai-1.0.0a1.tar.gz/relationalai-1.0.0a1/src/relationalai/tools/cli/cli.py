"""
RelationalAI CLI - Tools for working with semantic models.
For more documentation on these commands, visit: https://docs.relationalai.com
"""

from __future__ import annotations

from pathlib import Path

import click

from rich.console import Console

from .config_template import CONFIG_TEMPLATE

console = Console()


@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def cli(ctx: click.Context):
    """RelationalAI CLI - Tools for working with semantic models. For more documentation on these commands, visit: https://docs.relationalai.com"""
    if ctx.invoked_subcommand is None:
        # Show help if no command provided
        click.echo(ctx.get_help())


@cli.command()
def analyze():
    """Check for errors, warnings, and performance issues in the models."""
    console.print("analyze")


@cli.command()
def build():
    """Create artifacts, show compilation errors, and produce SQL for the models."""
    console.print("build")


@cli.command()
def connect():
    """Validate config and database connection."""
    console.print("connect")


@cli.command()
def deploy():
    """Deploy models/views to the database and produce SQL for execution."""
    console.print("deploy")


@cli.command()
def explore():
    """Model explorer for visualization of data."""
    console.print("explore")


@cli.command()
def init():
    """Create a template for the YAML config file."""
    config_file = Path("raiconfig.yml")

    if config_file.exists():
        console.print(f"[yellow]Config file '{config_file}' already exists. Skipping creation.[/yellow]")
        return

    try:
        config_file.write_text(CONFIG_TEMPLATE, encoding="utf-8")
        console.print(f"[green]✓ Created config file '{config_file}'[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to create config file: {e}[/red]")
        raise click.ClickException(f"Failed to create config file: {e}")


@cli.command()
@click.option("--uninstall", is_flag=True, help="Nukes the database")
def clean(uninstall: bool):
    """Clean up build folder and remove artifacts."""
    console.print("clean")


@cli.command()
def test():
    """Run constraints and tests."""
    console.print("test")


if __name__ == "__main__":
    cli()
