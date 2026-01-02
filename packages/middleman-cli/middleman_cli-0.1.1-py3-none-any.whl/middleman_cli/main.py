"""Main CLI entry point."""

import typer
from rich.console import Console

from . import __version__
from .commands import auth, config, jobs, run

app = typer.Typer(
    name="middleman",
    help="Middleman CLI - Affordable GPU compute for ML training",
    no_args_is_help=True,
)
console = Console()

# Register command groups
app.add_typer(jobs.app, name="jobs", help="Manage training jobs")
app.command()(auth.login)
app.command()(auth.logout)
app.command()(auth.whoami)
app.command()(run.run)
app.command(name="credits")(run.credits)
app.command()(config.configure)


@app.command()
def version():
    """Show CLI version."""
    console.print(f"middleman-cli v{__version__}")


@app.callback()
def callback():
    """
    Middleman CLI - Train ML models on affordable GPUs.

    Get started:
      middleman login
      middleman run train.py --gpu a100
      middleman jobs list
    """
    pass


if __name__ == "__main__":
    app()
