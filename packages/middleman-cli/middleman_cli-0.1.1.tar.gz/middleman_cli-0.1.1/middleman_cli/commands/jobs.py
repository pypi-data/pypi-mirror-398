"""Job management commands."""

import time
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel

from ..utils.api import APIError, ConfigError, MiddlemanClient

app = typer.Typer(help="Manage training jobs")
console = Console()

STATUS_COLORS = {
    "queued": "yellow",
    "provisioning": "yellow",
    "running": "green",
    "completed": "blue",
    "failed": "red",
    "cancelled": "dim",
    "evicted": "magenta",
}


def format_duration(seconds: Optional[float]) -> str:
    """Format duration in human-readable format."""
    if not seconds:
        return "-"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


@app.command(name="list")
def list_jobs(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of jobs to show"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    all_jobs: bool = typer.Option(False, "--all", "-a", help="Show all jobs"),
):
    """List your training jobs."""
    try:
        with MiddlemanClient() as client:
            result = client.list_jobs(limit=100 if all_jobs else limit, status=status)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)

    jobs = result.get("data", [])

    if not jobs:
        console.print("[dim]No jobs found.[/dim]")
        return

    table = Table(title="Training Jobs")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Status")
    table.add_column("GPU", style="magenta")
    table.add_column("Duration")
    table.add_column("Credits")

    for job in jobs:
        job_id = job.get("id", "")[:8]
        name = job.get("name", "Unnamed")[:30]
        status = job.get("status", "unknown")
        color = STATUS_COLORS.get(status, "white")
        gpu = job.get("gpu_type", "-")
        duration = format_duration(job.get("duration_seconds"))
        credits = job.get("credits_used", 0)

        table.add_row(
            job_id,
            name,
            f"[{color}]{status}[/{color}]",
            gpu.upper() if gpu else "-",
            duration,
            f"{credits:,}" if credits else "-",
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(jobs)} of {result.get('total', len(jobs))} jobs[/dim]")


@app.command()
def status(
    job_id: str = typer.Argument(..., help="Job ID"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch status updates"),
):
    """Get job status and details."""
    try:
        with MiddlemanClient() as client:
            if watch:
                _watch_job(client, job_id)
            else:
                job = client.get_job(job_id)
                _print_job_details(job)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


def _print_job_details(job: dict):
    """Print job details."""
    status = job.get("status", "unknown")
    color = STATUS_COLORS.get(status, "white")

    details = [
        f"Name: {job.get('name', 'Unnamed')}",
        f"Status: [{color}]{status}[/{color}]",
        f"GPU: {job.get('gpu_type', '-').upper()}",
        f"Framework: {job.get('framework', '-')}",
        f"Duration: {format_duration(job.get('duration_seconds'))}",
        f"Credits Used: {job.get('credits_used', 0):,}",
    ]

    if job.get("started_at"):
        details.append(f"Started: {job['started_at']}")

    if job.get("completed_at"):
        details.append(f"Completed: {job['completed_at']}")

    if job.get("error_message"):
        details.append(f"\n[red]Error: {job['error_message']}[/red]")

    console.print(Panel(
        "\n".join(details),
        title=f"Job {job.get('id', '')[:8]}",
    ))


def _watch_job(client: MiddlemanClient, job_id: str):
    """Watch job status updates."""
    console.print(f"[dim]Watching job {job_id[:8]}... (Ctrl+C to stop)[/dim]\n")

    try:
        while True:
            job = client.get_job(job_id)
            status = job.get("status", "unknown")
            color = STATUS_COLORS.get(status, "white")

            console.clear()
            _print_job_details(job)

            # Stop watching if job is done
            if status in ("completed", "failed", "cancelled"):
                break

            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")


@app.command()
def logs(
    job_id: str = typer.Argument(..., help="Job ID"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
):
    """View job logs."""
    try:
        with MiddlemanClient() as client:
            if follow:
                _follow_logs(client, job_id)
            else:
                result = client.get_job_logs(job_id, tail=tail)
                logs = result.get("logs", [])

                if not logs:
                    console.print("[dim]No logs available.[/dim]")
                    return

                for log in logs:
                    timestamp = log.get("timestamp", "")[:19]
                    message = log.get("message", "")
                    level = log.get("level", "info").lower()

                    if level == "error":
                        console.print(f"[dim]{timestamp}[/dim] [red]{message}[/red]")
                    elif level == "warning":
                        console.print(f"[dim]{timestamp}[/dim] [yellow]{message}[/yellow]")
                    else:
                        console.print(f"[dim]{timestamp}[/dim] {message}")

    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


def _follow_logs(client: MiddlemanClient, job_id: str):
    """Follow job logs in real-time."""
    console.print(f"[dim]Following logs for {job_id[:8]}... (Ctrl+C to stop)[/dim]\n")

    seen_ids = set()
    try:
        while True:
            result = client.get_job_logs(job_id, tail=50)
            logs = result.get("logs", [])

            for log in logs:
                log_id = log.get("id") or log.get("timestamp")
                if log_id not in seen_ids:
                    seen_ids.add(log_id)
                    timestamp = log.get("timestamp", "")[:19]
                    message = log.get("message", "")
                    console.print(f"[dim]{timestamp}[/dim] {message}")

            # Check if job is done
            job = client.get_job(job_id)
            if job.get("status") in ("completed", "failed", "cancelled"):
                console.print(f"\n[dim]Job {job.get('status')}.[/dim]")
                break

            time.sleep(2)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped following logs.[/dim]")


@app.command()
def cancel(
    job_id: str = typer.Argument(..., help="Job ID to cancel"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Cancel a running job."""
    if not force:
        confirm = typer.confirm(f"Cancel job {job_id[:8]}?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            return

    try:
        with MiddlemanClient() as client:
            client.cancel_job(job_id)
            console.print(f"[green]Job {job_id[:8]} cancelled.[/green]")
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
