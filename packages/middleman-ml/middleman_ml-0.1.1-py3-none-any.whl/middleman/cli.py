"""Middleman CLI."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .client import MiddlemanClient, MiddlemanError, AuthenticationError, ApiError
from .models import JobStatus, GpuType, Framework

app = typer.Typer(
    name="middleman",
    help="Middleman ML Training Platform CLI",
    add_completion=False,
)

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".middleman"
CONFIG_FILE = CONFIG_DIR / "config"


def get_api_key() -> str:
    """Get API key from environment or config file."""
    # First check environment variable
    api_key = os.environ.get("MIDDLEMAN_API_KEY")
    if api_key:
        return api_key

    # Then check config file
    if CONFIG_FILE.exists():
        return CONFIG_FILE.read_text().strip()

    console.print("[red]Error:[/red] No API key configured.")
    console.print("Run [cyan]middleman auth[/cyan] to configure your API key.")
    console.print("Or set the [cyan]MIDDLEMAN_API_KEY[/cyan] environment variable.")
    raise typer.Exit(1)


def get_client() -> MiddlemanClient:
    """Get an authenticated client."""
    try:
        return MiddlemanClient(api_key=get_api_key())
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}")
        raise typer.Exit(1)


def handle_error(e: Exception):
    """Handle and display errors."""
    if isinstance(e, AuthenticationError):
        console.print(f"[red]Authentication Error:[/red] {e}")
    elif isinstance(e, ApiError):
        console.print(f"[red]API Error ({e.status_code}):[/red] {e.detail or str(e)}")
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)


# === Auth Commands ===

@app.command()
def auth(
    api_key: Optional[str] = typer.Argument(None, help="Your Middleman API key"),
):
    """Configure your Middleman API key."""
    if not api_key:
        api_key = typer.prompt("Enter your API key", hide_input=True)

    # Validate the key
    try:
        client = MiddlemanClient(api_key=api_key)
        balance = client.get_balance()
        client.close()
    except Exception as e:
        console.print(f"[red]Invalid API key:[/red] {e}")
        raise typer.Exit(1)

    # Save to config file
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(api_key)
    CONFIG_FILE.chmod(0o600)  # Secure permissions

    console.print("[green]✓[/green] API key configured successfully!")
    console.print(f"  Balance: [cyan]{balance.available:,}[/cyan] credits available")


@app.command()
def whoami():
    """Show current authentication status."""
    try:
        client = get_client()
        balance = client.get_balance()
        client.close()

        console.print(Panel.fit(
            f"[green]Authenticated[/green]\n"
            f"Balance: [cyan]{balance.balance:,}[/cyan] credits\n"
            f"Reserved: [yellow]{balance.reserved:,}[/yellow] credits\n"
            f"Available: [green]{balance.available:,}[/green] credits",
            title="Middleman Account"
        ))
    except Exception as e:
        handle_error(e)


# === Jobs Commands ===

jobs_app = typer.Typer(help="Manage training jobs")
app.add_typer(jobs_app, name="jobs")


@jobs_app.command("list")
def list_jobs(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum jobs to show"),
):
    """List your training jobs."""
    try:
        client = get_client()
        status_filter = JobStatus(status) if status else None
        jobs, total = client.list_jobs(status=status_filter, limit=limit)
        client.close()

        if not jobs:
            console.print("[dim]No jobs found.[/dim]")
            return

        table = Table(title=f"Training Jobs ({len(jobs)} of {total})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Status", style="bold")
        table.add_column("GPU", style="magenta")
        table.add_column("Progress", style="green")
        table.add_column("Cost", style="yellow")

        status_colors = {
            "queued": "dim",
            "provisioning": "cyan",
            "running": "green",
            "paused": "yellow",
            "checkpointing": "blue",
            "completed": "green bold",
            "cancelled": "dim",
            "failed": "red",
        }

        for job in jobs:
            status_style = status_colors.get(job.status.value, "white")
            progress = f"{job.current_epoch}/{job.total_epochs or '?'}" if job.current_epoch else "-"

            table.add_row(
                job.id[:8],
                job.name or "-",
                f"[{status_style}]{job.status.value}[/{status_style}]",
                f"{job.gpu_type.value}×{job.gpu_count}",
                progress,
                f"{job.actual_cost:,}",
            )

        console.print(table)

    except Exception as e:
        handle_error(e)


@jobs_app.command("create")
def create_job(
    script: str = typer.Argument(..., help="Path to training script"),
    data: str = typer.Argument(..., help="Path to input data"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Job name"),
    gpu: str = typer.Option("t4", "--gpu", "-g", help="GPU type (t4, v100, a100)"),
    gpu_count: int = typer.Option(1, "--gpu-count", "-c", help="Number of GPUs (1-8)"),
    framework: str = typer.Option("pytorch", "--framework", "-f", help="ML framework"),
    max_hours: int = typer.Option(4, "--max-hours", "-h", help="Maximum runtime hours"),
    requirements: Optional[str] = typer.Option(None, "--requirements", "-r", help="Requirements file"),
):
    """Create a new training job."""
    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Creating job...", total=None)

            response = client.create_job(
                script_path=script,
                input_data_path=data,
                name=name,
                gpu_type=GpuType(gpu),
                gpu_count=gpu_count,
                framework=Framework(framework),
                max_runtime_hours=max_hours,
                requirements_file=requirements,
            )

        client.close()

        console.print(Panel.fit(
            f"[green]Job created successfully![/green]\n\n"
            f"ID: [cyan]{response.id}[/cyan]\n"
            f"Status: [yellow]{response.status.value}[/yellow]\n"
            f"Queue Position: [magenta]{response.queue_position}[/magenta]\n"
            f"Estimated Cost: [yellow]{response.estimated_cost:,}[/yellow] credits\n"
            f"Reserved: [dim]{response.reserved_credits:,}[/dim] credits",
            title="New Training Job"
        ))

        console.print(f"\nRun [cyan]middleman jobs status {response.id[:8]}[/cyan] to check progress.")

    except Exception as e:
        handle_error(e)


@jobs_app.command("status")
def job_status(
    job_id: str = typer.Argument(..., help="Job ID (full or prefix)"),
):
    """Get detailed job status."""
    try:
        client = get_client()
        job = client.get_job(job_id)
        client.close()

        status_emoji = {
            "queued": "⏳",
            "provisioning": "🔧",
            "running": "🏃",
            "paused": "⏸️",
            "checkpointing": "💾",
            "completed": "✅",
            "cancelled": "🚫",
            "failed": "❌",
        }.get(job.status.value, "❓")

        info = f"""
{status_emoji} Status: [bold]{job.status.value}[/bold]
Name: {job.name or '-'}
GPU: [magenta]{job.gpu_type.value}[/magenta] × {job.gpu_count}
Framework: {job.framework.value}

[bold]Progress[/bold]
Epoch: {job.current_epoch}/{job.total_epochs or '?'}
Loss: {job.current_loss or '-'}

[bold]Paths[/bold]
Script: {job.script_path}
Data: {job.input_data_path}

[bold]Cost[/bold]
Reserved: {job.reserved_credits:,} credits
Actual: {job.actual_cost:,} credits

[bold]Timing[/bold]
Created: {job.created_at}
Started: {job.started_at or '-'}
Completed: {job.completed_at or '-'}
"""

        console.print(Panel(info.strip(), title=f"Job {job.id[:8]}"))

    except Exception as e:
        handle_error(e)


@jobs_app.command("cancel")
def cancel_job(
    job_id: str = typer.Argument(..., help="Job ID to cancel"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Cancel a running or queued job."""
    if not yes:
        confirm = typer.confirm(f"Cancel job {job_id[:8]}?")
        if not confirm:
            raise typer.Abort()

    try:
        client = get_client()
        result = client.cancel_job(job_id)
        client.close()

        console.print(f"[green]✓[/green] Job [cyan]{job_id[:8]}[/cyan] cancelled.")
        if "refunded_credits" in result:
            console.print(f"  Refunded: [yellow]{result['refunded_credits']:,}[/yellow] credits")

    except Exception as e:
        handle_error(e)


@jobs_app.command("pause")
def pause_job(
    job_id: str = typer.Argument(..., help="Job ID to pause"),
):
    """Pause a running job."""
    try:
        client = get_client()
        job = client.pause_job(job_id)
        client.close()

        console.print(f"[green]✓[/green] Job [cyan]{job_id[:8]}[/cyan] paused.")
        console.print(f"  Status: [yellow]{job.status.value}[/yellow]")

    except Exception as e:
        handle_error(e)


@jobs_app.command("resume")
def resume_job(
    job_id: str = typer.Argument(..., help="Job ID to resume"),
):
    """Resume a paused job."""
    try:
        client = get_client()
        job = client.resume_job(job_id)
        client.close()

        console.print(f"[green]✓[/green] Job [cyan]{job_id[:8]}[/cyan] resuming.")
        console.print(f"  Status: [cyan]{job.status.value}[/cyan]")

    except Exception as e:
        handle_error(e)


@jobs_app.command("logs")
def job_logs(
    job_id: str = typer.Argument(..., help="Job ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
):
    """View job logs."""
    try:
        client = get_client()
        logs = client.get_job_logs(job_id)
        client.close()

        if not logs:
            console.print("[dim]No logs available yet.[/dim]")
            return

        for entry in logs:
            timestamp = entry.get("timestamp", "")[:19]
            level = entry.get("level", "INFO")
            message = entry.get("message", "")

            level_style = {
                "ERROR": "red",
                "WARNING": "yellow",
                "INFO": "white",
                "DEBUG": "dim",
            }.get(level, "white")

            console.print(f"[dim]{timestamp}[/dim] [{level_style}]{level}[/{level_style}] {message}")

    except Exception as e:
        handle_error(e)


@jobs_app.command("watch")
def watch_job(
    job_id: str = typer.Argument(..., help="Job ID to watch"),
    interval: int = typer.Option(5, "--interval", "-i", help="Poll interval in seconds"),
):
    """Watch a job until completion."""
    try:
        client = get_client()

        console.print(f"Watching job [cyan]{job_id[:8]}[/cyan]... (Ctrl+C to stop)\n")

        for job in client.stream_job_status(job_id, poll_interval=interval):
            progress = f"{job.current_epoch}/{job.total_epochs}" if job.total_epochs else f"{job.current_epoch}"
            loss = f"loss={job.current_loss:.4f}" if job.current_loss else ""

            console.print(
                f"[dim]{job.status.value:15}[/dim] "
                f"epoch {progress:10} "
                f"{loss}"
            )

            if job.is_terminal:
                break

        client.close()

        emoji = "✅" if job.status == JobStatus.COMPLETED else "❌"
        console.print(f"\n{emoji} Job finished with status: [bold]{job.status.value}[/bold]")

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")
    except Exception as e:
        handle_error(e)


# === Billing Commands ===

billing_app = typer.Typer(help="Manage billing and credits")
app.add_typer(billing_app, name="billing")


@billing_app.command("balance")
def show_balance():
    """Show your credit balance."""
    try:
        client = get_client()
        balance = client.get_balance()
        client.close()

        table = Table(title="Credit Balance")
        table.add_column("Type", style="white")
        table.add_column("Credits", style="cyan", justify="right")

        table.add_row("Total", f"{balance.balance:,}")
        table.add_row("Reserved", f"[yellow]{balance.reserved:,}[/yellow]")
        table.add_row("Available", f"[green]{balance.available:,}[/green]")

        if balance.expires_at:
            table.add_row("Expires", str(balance.expires_at)[:10])

        console.print(table)

    except Exception as e:
        handle_error(e)


@billing_app.command("packages")
def show_packages():
    """Show available credit packages."""
    try:
        client = get_client()
        packages = client.get_packages()
        client.close()

        table = Table(title="Credit Packages")
        table.add_column("Package", style="white")
        table.add_column("Credits", style="cyan", justify="right")
        table.add_column("Price", style="green", justify="right")
        table.add_column("$/Credit", style="dim", justify="right")

        for pkg in packages:
            price_per = pkg.price_cents / pkg.credits / 100
            table.add_row(
                pkg.name,
                f"{pkg.credits:,}",
                f"${pkg.price_dollars:.2f}",
                f"${price_per:.4f}",
            )

        console.print(table)
        console.print("\n[dim]Purchase credits at https://middleman.cloud/dashboard/billing[/dim]")

    except Exception as e:
        handle_error(e)


@billing_app.command("history")
def transaction_history(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of transactions"),
):
    """Show transaction history."""
    try:
        client = get_client()
        transactions, total = client.get_transactions(limit=limit)
        client.close()

        if not transactions:
            console.print("[dim]No transactions found.[/dim]")
            return

        table = Table(title=f"Transaction History ({len(transactions)} of {total})")
        table.add_column("Date", style="dim")
        table.add_column("Type", style="white")
        table.add_column("Credits", justify="right")
        table.add_column("Description", style="dim")

        for tx in transactions:
            amount = tx.get("amount", 0)
            amount_str = f"[green]+{amount:,}[/green]" if amount > 0 else f"[red]{amount:,}[/red]"

            table.add_row(
                tx.get("created_at", "")[:10],
                tx.get("type", "-"),
                amount_str,
                tx.get("description", "-")[:40],
            )

        console.print(table)

    except Exception as e:
        handle_error(e)


# === Data Commands ===

data_app = typer.Typer(help="Upload and download data")
app.add_typer(data_app, name="data")


@data_app.command("upload")
def upload_file(
    file: Path = typer.Argument(..., help="File to upload", exists=True),
    job_id: Optional[str] = typer.Option(None, "--job", "-j", help="Associate with job"),
):
    """Upload a file to Middleman storage."""
    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(f"Uploading {file.name}...", total=None)
            blob_path = client.upload_file(file, job_id=job_id)

        client.close()

        console.print(f"[green]✓[/green] Uploaded successfully!")
        console.print(f"  Path: [cyan]{blob_path}[/cyan]")

    except Exception as e:
        handle_error(e)


@data_app.command("download-url")
def get_download(
    job_id: str = typer.Argument(..., help="Job ID"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Specific file path"),
):
    """Get a download URL for job outputs."""
    try:
        client = get_client()
        download = client.get_download_url(job_id, path=path)
        client.close()

        console.print(f"[green]Download URL[/green] (expires {download.expires_at}):\n")
        console.print(download.download_url)

        if download.size_bytes:
            size_mb = download.size_bytes / 1024 / 1024
            console.print(f"\n[dim]Size: {size_mb:.2f} MB[/dim]")

    except Exception as e:
        handle_error(e)


# === API Keys Commands ===

keys_app = typer.Typer(help="Manage API keys")
app.add_typer(keys_app, name="keys")


@keys_app.command("list")
def list_keys():
    """List your API keys."""
    try:
        client = get_client()
        keys = client.list_api_keys()
        client.close()

        if not keys:
            console.print("[dim]No API keys found.[/dim]")
            return

        table = Table(title="API Keys")
        table.add_column("Name", style="white")
        table.add_column("Prefix", style="cyan")
        table.add_column("Scopes", style="magenta")
        table.add_column("Created", style="dim")
        table.add_column("Last Used", style="dim")

        for key in keys:
            table.add_row(
                key.name,
                key.key_prefix + "...",
                ", ".join(key.scopes),
                str(key.created_at)[:10],
                str(key.last_used_at)[:10] if key.last_used_at else "-",
            )

        console.print(table)

    except Exception as e:
        handle_error(e)


@keys_app.command("create")
def create_key(
    name: str = typer.Argument(..., help="Name for the API key"),
    expires: Optional[int] = typer.Option(None, "--expires", "-e", help="Days until expiration"),
):
    """Create a new API key."""
    try:
        client = get_client()
        key_info, full_key = client.create_api_key(name=name, expires_in_days=expires)
        client.close()

        console.print(Panel.fit(
            f"[green]API key created![/green]\n\n"
            f"Name: {key_info.name}\n"
            f"Key: [cyan]{full_key}[/cyan]\n\n"
            f"[yellow]Save this key now - it won't be shown again![/yellow]",
            title="New API Key"
        ))

    except Exception as e:
        handle_error(e)


@keys_app.command("revoke")
def revoke_key(
    key_id: str = typer.Argument(..., help="API key ID to revoke"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Revoke an API key."""
    if not yes:
        confirm = typer.confirm(f"Revoke API key {key_id[:8]}?")
        if not confirm:
            raise typer.Abort()

    try:
        client = get_client()
        client.revoke_api_key(key_id)
        client.close()

        console.print(f"[green]✓[/green] API key revoked.")

    except Exception as e:
        handle_error(e)


# === Version ===

@app.command()
def version():
    """Show CLI version."""
    from . import __version__
    console.print(f"Middleman CLI v{__version__}")


if __name__ == "__main__":
    app()
