"""Run command for submitting training jobs."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils.api import APIError, ConfigError, MiddlemanClient

console = Console()

GPU_TYPES = ["t4", "v100", "a100", "a100-80gb", "h100"]
FRAMEWORKS = ["pytorch", "tensorflow", "jax", "custom"]


def run(
    script: str = typer.Argument(..., help="Training script to run (e.g., train.py)"),
    gpu: str = typer.Option("t4", "--gpu", "-g", help="GPU type (t4, v100, a100, h100)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Job name"),
    framework: str = typer.Option("pytorch", "--framework", "-f", help="ML framework"),
    gpu_count: int = typer.Option(1, "--gpu-count", help="Number of GPUs"),
    max_runtime: int = typer.Option(4, "--max-runtime", "-t", help="Max runtime in hours"),
    env: Optional[list[str]] = typer.Option(None, "--env", "-e", help="Environment variables (KEY=VALUE)"),
    requirements: Optional[str] = typer.Option(None, "--requirements", "-r", help="Requirements file"),
    wait: bool = typer.Option(False, "--wait", "-w", help="Wait for job to complete"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be submitted without actually submitting"),
):
    """Submit a training job.

    Examples:
        middleman run train.py --gpu a100
        middleman run train.py --gpu v100 --name "my-experiment"
        middleman run train.py --framework tensorflow --max-runtime 8
        middleman run train.py --gpu t4 --dry-run
    """
    # Validate GPU type
    gpu = gpu.lower()
    if gpu not in GPU_TYPES:
        console.print(f"[red]Invalid GPU type.[/red] Choose from: {', '.join(GPU_TYPES)}")
        raise typer.Exit(1)

    # Validate framework
    framework = framework.lower()
    if framework not in FRAMEWORKS:
        console.print(f"[red]Invalid framework.[/red] Choose from: {', '.join(FRAMEWORKS)}")
        raise typer.Exit(1)

    # Check script exists
    script_path = Path(script)
    if not script_path.exists():
        console.print(f"[red]Script not found:[/red] {script}")
        raise typer.Exit(1)

    # Parse environment variables
    env_vars = {}
    if env:
        for e in env:
            if "=" not in e:
                console.print(f"[red]Invalid env format:[/red] {e} (use KEY=VALUE)")
                raise typer.Exit(1)
            key, value = e.split("=", 1)
            env_vars[key] = value

    # Build job config
    job_config = {
        "name": name or script_path.stem,
        "gpu_type": gpu,
        "gpu_count": gpu_count,
        "framework": framework,
        "max_runtime_hours": max_runtime,
        "script": script_path.name,
        "environment": env_vars,
    }

    # Read requirements if specified
    if requirements:
        req_path = Path(requirements)
        if req_path.exists():
            job_config["requirements"] = req_path.read_text()

    # Dry run - show what would be submitted
    if dry_run:
        console.print(Panel(
            f"[yellow]DRY RUN - No job will be submitted[/yellow]\n\n"
            f"[bold]Job Configuration:[/bold]\n"
            f"  Name: {job_config['name']}\n"
            f"  Script: {job_config['script']}\n"
            f"  GPU: {gpu.upper()} x {gpu_count}\n"
            f"  Framework: {framework}\n"
            f"  Max Runtime: {max_runtime} hours\n"
            f"  Environment: {env_vars if env_vars else 'None'}\n"
            f"  Requirements: {'Yes' if 'requirements' in job_config else 'No'}\n\n"
            f"[dim]Remove --dry-run to submit this job[/dim]",
            title="Dry Run",
        ))
        return

    # Submit job
    try:
        with MiddlemanClient() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Submitting job...", total=None)
                result = client.create_job(job_config)

            job_id = result.get("id", "")
            console.print(Panel(
                f"[green]Job submitted successfully![/green]\n\n"
                f"Job ID: {job_id[:8]}\n"
                f"Name: {job_config['name']}\n"
                f"GPU: {gpu.upper()}\n"
                f"Framework: {framework}\n\n"
                f"[dim]View status: middleman jobs status {job_id[:8]}[/dim]\n"
                f"[dim]View logs: middleman jobs logs {job_id[:8]}[/dim]",
                title="Job Submitted",
            ))

            if wait:
                console.print("\n[dim]Waiting for job to complete...[/dim]\n")
                _wait_for_job(client, job_id)

    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


def _wait_for_job(client: MiddlemanClient, job_id: str):
    """Wait for job to complete."""
    import time

    STATUS_COLORS = {
        "queued": "yellow",
        "provisioning": "yellow",
        "running": "green",
        "completed": "blue",
        "failed": "red",
        "cancelled": "dim",
    }

    try:
        while True:
            job = client.get_job(job_id)
            status = job.get("status", "unknown")
            color = STATUS_COLORS.get(status, "white")

            console.print(f"\r[{color}]Status: {status}[/{color}]", end="")

            if status in ("completed", "failed", "cancelled"):
                console.print()
                if status == "completed":
                    console.print("\n[green]Job completed successfully![/green]")
                elif status == "failed":
                    error = job.get("error_message", "Unknown error")
                    console.print(f"\n[red]Job failed:[/red] {error}")
                break

            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped waiting. Job is still running.[/dim]")


def credits():
    """Show your credit balance."""
    try:
        with MiddlemanClient() as client:
            balance = client.get_balance()
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)

    available = balance.get("available", 0)
    reserved = balance.get("reserved", 0)
    total = balance.get("balance", 0)

    # Convert to dollars (100 credits = $1)
    available_usd = available / 100
    reserved_usd = reserved / 100
    total_usd = total / 100

    console.print(Panel(
        f"Available: [green]{available:,}[/green] credits (${available_usd:.2f})\n"
        f"Reserved: [yellow]{reserved:,}[/yellow] credits (${reserved_usd:.2f})\n"
        f"Total: [blue]{total:,}[/blue] credits (${total_usd:.2f})\n\n"
        f"[dim]Add credits at https://app.middleman.run/dashboard/billing[/dim]",
        title="Credit Balance",
    ))
