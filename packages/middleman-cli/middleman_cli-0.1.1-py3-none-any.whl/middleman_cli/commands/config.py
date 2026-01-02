"""Configuration commands."""

import typer
from rich.console import Console
from rich.table import Table

from ..utils.api import (
    get_config,
    save_config,
    CONFIG_FILE,
    DEFAULT_API_URL,
)

console = Console()


def configure(
    api_url: str = typer.Option(
        None,
        "--api-url",
        help="Custom API URL",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current configuration",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Reset configuration to defaults",
    ),
):
    """View or modify CLI configuration.

    Examples:
        middleman configure --show
        middleman configure --api-url https://custom.api.url
        middleman configure --reset
    """
    if reset:
        save_config({})
        console.print("[green]Configuration reset to defaults.[/green]")
        return

    config = get_config()

    if show:
        _show_config(config)
        return

    if api_url:
        config["api_url"] = api_url
        save_config(config)
        console.print(f"[green]API URL set to:[/green] {api_url}")
        return

    # Interactive configuration
    _show_config(config)


def _show_config(config: dict):
    """Display current configuration."""
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row(
        "Config file",
        str(CONFIG_FILE),
    )
    table.add_row(
        "API URL",
        config.get("api_url", DEFAULT_API_URL),
    )
    table.add_row(
        "API Key",
        _mask_key(config.get("api_key", "")),
    )

    console.print(table)


def _mask_key(key: str) -> str:
    """Mask API key for display."""
    if not key:
        return "[dim]Not set[/dim]"
    if len(key) < 12:
        return "***"
    return f"{key[:8]}...{key[-4:]}"
