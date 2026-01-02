"""Authentication commands."""

import typer
from rich.console import Console
from rich.panel import Panel

from ..utils.api import (
    APIError,
    ConfigError,
    MiddlemanClient,
    get_config,
    save_config,
    CONFIG_FILE,
)

console = Console()


def login(
    api_key: str = typer.Option(
        None,
        "--api-key", "-k",
        help="API key (or enter interactively)",
        prompt="API Key",
        hide_input=True,
    ),
):
    """Authenticate with your Middleman API key.

    Get your API key from https://app.middleman.run/dashboard/api-keys
    """
    # Validate the API key by making a request
    try:
        with MiddlemanClient(api_key=api_key) as client:
            user = client.get_user()
    except APIError as e:
        console.print(f"[red]Authentication failed:[/red] {e.message}")
        raise typer.Exit(1)

    # Save to config
    config = get_config()
    config["api_key"] = api_key
    save_config(config)

    console.print(Panel(
        f"[green]Successfully authenticated![/green]\n\n"
        f"Email: {user.get('email', 'N/A')}\n"
        f"Tier: {user.get('tier', 'free')}",
        title="Welcome to Middleman",
    ))


def logout():
    """Remove stored credentials."""
    config = get_config()

    if "api_key" not in config:
        console.print("[yellow]Not currently logged in.[/yellow]")
        return

    del config["api_key"]
    save_config(config)
    console.print("[green]Successfully logged out.[/green]")


def whoami():
    """Show current authenticated user."""
    try:
        with MiddlemanClient() as client:
            user = client.get_user()
            balance = client.get_balance()
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)

    console.print(Panel(
        f"Email: {user.get('email', 'N/A')}\n"
        f"Name: {user.get('name', 'N/A')}\n"
        f"Tier: {user.get('tier', 'free')}\n"
        f"Credits: {balance.get('available', 0):,}",
        title="Current User",
    ))
