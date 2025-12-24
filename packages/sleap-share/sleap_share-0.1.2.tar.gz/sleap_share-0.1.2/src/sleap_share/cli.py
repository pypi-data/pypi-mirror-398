"""Command-line interface for sleap-share."""

import json
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from . import __version__
from .auth import clear_token, load_token, run_device_auth_flow
from .client import SleapShareClient
from .config import get_config
from .exceptions import AuthenticationError, NotFoundError, SleapShareError

# Typer app
app = typer.Typer(
    name="sleap-share",
    help="Upload and share SLEAP datasets with slp.sh",
    add_completion=False,
    no_args_is_help=True,
)

# Rich console
console = Console()
err_console = Console(stderr=True)


def _get_env_option() -> Any:
    """Get the --env option for environment targeting."""
    return typer.Option(
        None,
        "--env",
        "-e",
        help="Target environment (production or staging)",
    )


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _format_date(dt: datetime | None) -> str:
    """Format datetime for display."""
    if dt is None:
        return "Never"
    return dt.strftime("%Y-%m-%d %H:%M")


@app.command()
def login(
    env: str | None = _get_env_option(),
) -> None:
    """Authenticate with SLEAP Share via browser."""
    config = get_config(env=env)

    with httpx.Client() as http_client:
        try:
            run_device_auth_flow(http_client, config, console)
        except AuthenticationError as e:
            err_console.print(f"[red]Error:[/red] {e.message}")
            raise typer.Exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Login cancelled.[/yellow]")
            raise typer.Exit(1)


@app.command()
def logout(
    env: str | None = _get_env_option(),
) -> None:
    """Clear stored authentication credentials."""
    config = get_config(env=env)

    if clear_token(config):
        console.print("[green]Logged out successfully.[/green]")
    else:
        console.print("[yellow]No credentials found.[/yellow]")


@app.command()
def whoami(
    env: str | None = _get_env_option(),
) -> None:
    """Show the current authenticated user."""
    config = get_config(env=env)
    token = load_token(config)

    if not token:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("Run [bold]sleap-share login[/bold] to authenticate.")
        raise typer.Exit(1)

    try:
        client = SleapShareClient(token=token, env=env)
        user = client.whoami()

        console.print()
        console.print(f"[bold]Username:[/bold] {user.username}")
        console.print(f"[bold]Email:[/bold] {user.email}")
        console.print(f"[bold]Files:[/bold] {user.total_files}")
        console.print(f"[bold]Storage:[/bold] {_format_size(user.total_storage)}")
        console.print()

    except SleapShareError as e:
        err_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command()
def upload(
    file: Path = typer.Argument(..., help="Path to .slp file to upload"),
    permanent: bool = typer.Option(
        False, "--permanent", "-p", help="Request permanent storage (superusers only)"
    ),
    open_browser: bool = typer.Option(
        False, "--open", "-o", help="Open share URL in browser after upload"
    ),
    env: str | None = _get_env_option(),
) -> None:
    """Upload a .slp file to SLEAP Share."""
    if not file.exists():
        err_console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    if file.suffix.lower() != ".slp":
        err_console.print("[red]Error:[/red] Only .slp files are supported.")
        raise typer.Exit(1)

    try:
        client = SleapShareClient(env=env)
        file_size = file.stat().st_size

        # Track current status for display updates
        current_status = {"value": "uploading"}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Uploading...", total=file_size)

            def update_progress(sent: int, total: int) -> None:
                progress.update(task, completed=sent)

            def update_status(status: str) -> None:
                current_status["value"] = status
                if status == "validating":
                    # Switch to indeterminate spinner for validation
                    progress.update(
                        task,
                        description="[cyan]Validating...[/cyan]",
                        total=None,  # Indeterminate
                    )

            result = client.upload(
                file,
                permanent=permanent,
                progress_callback=update_progress,
                status_callback=update_status,
            )

        # Display result
        console.print()
        console.print("[bold green]Upload complete![/bold green]")
        console.print()
        console.print(
            f"[bold]Share URL:[/bold] [link={result.share_url}]{result.share_url}[/link]"
        )

        if result.expires_at:
            console.print(f"[bold]Expires:[/bold] {_format_date(result.expires_at)}")
        else:
            console.print("[bold]Expires:[/bold] [green]Never (permanent)[/green]")

        # Show metadata if available
        if result.metadata:
            m = result.metadata
            stats = []
            if m.labeled_frames_count is not None:
                stats.append(f"{m.labeled_frames_count} labeled frames")
            if m.user_instances_count is not None:
                stats.append(f"{m.user_instances_count} user instances")
            if m.predicted_instances_count is not None:
                stats.append(f"{m.predicted_instances_count} predictions")
            if m.videos_count is not None:
                stats.append(f"{m.videos_count} videos")

            if stats:
                console.print(f"[bold]Dataset:[/bold] {', '.join(stats)}")

        console.print()

        if open_browser:
            webbrowser.open(result.share_url)

    except SleapShareError as e:
        err_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command()
def download(
    shortcode: str = typer.Argument(..., help="Shortcode or URL of file to download"),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output path (file or directory)"
    ),
    overwrite: bool | None = typer.Option(
        None,
        "--overwrite/--no-overwrite",
        "-f",
        help="Overwrite existing files. Default: overwrite if -o is a file, otherwise append (1), (2), etc.",
    ),
    env: str | None = _get_env_option(),
) -> None:
    """Download a file from SLEAP Share."""
    try:
        client = SleapShareClient(env=env)

        # Get file info first for size
        info = client.get_info(shortcode)

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading...", total=info.file_size)

            def update_progress(received: int, total: int) -> None:
                progress.update(task, completed=received)

            output_path = client.download(
                shortcode,
                output=output,
                progress_callback=update_progress,
                overwrite=overwrite,
            )

        console.print()
        console.print(f"[bold green]Downloaded:[/bold green] {output_path}")
        console.print()

    except NotFoundError:
        err_console.print("[red]Error:[/red] File not found or expired.")
        raise typer.Exit(1)
    except SleapShareError as e:
        err_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("list")
def list_files(
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum files to show"),
    env: str | None = _get_env_option(),
) -> None:
    """List your uploaded files."""
    config = get_config(env=env)
    token = load_token(config)

    if not token:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("Run [bold]sleap-share login[/bold] to authenticate.")
        raise typer.Exit(1)

    try:
        client = SleapShareClient(token=token, env=env)
        files = client.list_files(limit=limit)

        if not files:
            console.print("[yellow]No files found.[/yellow]")
            return

        table = Table(title="Your Files")
        table.add_column("Shortcode", style="cyan")
        table.add_column("Filename")
        table.add_column("Size", justify="right")
        table.add_column("Created")
        table.add_column("Expires")

        for f in files:
            table.add_row(
                f.shortcode,
                f.filename,
                _format_size(f.file_size),
                _format_date(f.created_at),
                _format_date(f.expires_at),
            )

        console.print()
        console.print(table)
        console.print()

    except SleapShareError as e:
        err_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command()
def info(
    shortcode: str = typer.Argument(..., help="Shortcode or URL of file"),
    as_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    env: str | None = _get_env_option(),
) -> None:
    """Show information about a file."""
    try:
        client = SleapShareClient(env=env)
        metadata = client.get_metadata(shortcode)
        urls = client.get_urls(shortcode)

        if as_json:
            console.print(json.dumps(metadata.to_dict(), indent=2))
            return

        console.print()
        console.print(Panel(f"[bold]{metadata.original_filename}[/bold]", expand=False))
        console.print()

        console.print(f"[bold]Shortcode:[/bold] {metadata.shortcode}")
        console.print(f"[bold]Size:[/bold] {_format_size(metadata.file_size)}")
        console.print(
            f"[bold]Uploaded:[/bold] {_format_date(metadata.upload_timestamp)}"
        )
        console.print(f"[bold]Expires:[/bold] {_format_date(metadata.expires_at)}")
        console.print(f"[bold]Status:[/bold] {metadata.validation_status}")
        console.print()

        console.print(
            f"[bold]Share URL:[/bold] [link={urls.share_url}]{urls.share_url}[/link]"
        )
        console.print(
            f"[bold]Download:[/bold] [link={urls.download_url}]{urls.download_url}[/link]"
        )
        console.print()

        # Show SLP stats if available
        if metadata.labeled_frames_count is not None:
            console.print("[bold]Dataset Statistics:[/bold]")
            if metadata.labeled_frames_count is not None:
                console.print(f"  Labeled frames: {metadata.labeled_frames_count}")
            if metadata.user_instances_count is not None:
                console.print(f"  User instances: {metadata.user_instances_count}")
            if metadata.predicted_instances_count is not None:
                console.print(f"  Predictions: {metadata.predicted_instances_count}")
            if metadata.tracks_count is not None:
                console.print(f"  Tracks: {metadata.tracks_count}")
            if metadata.videos_count is not None:
                console.print(f"  Videos: {metadata.videos_count}")
            console.print()

    except NotFoundError:
        err_console.print("[red]Error:[/red] File not found or expired.")
        raise typer.Exit(1)
    except SleapShareError as e:
        err_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command()
def preview(
    shortcode: str = typer.Argument(..., help="Shortcode or URL of file"),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output path for preview image"
    ),
    env: str | None = _get_env_option(),
) -> None:
    """Download the preview image for a file."""
    try:
        client = SleapShareClient(env=env)

        # Default output name
        if output is None:
            sc = shortcode.split("/")[-1]  # Extract shortcode from URL
            output = Path(f"{sc}_preview.png")

        output_path = client.get_preview(shortcode, output=output)

        console.print(f"[bold green]Preview saved:[/bold green] {output_path!s}")

    except NotFoundError:
        err_console.print("[red]Error:[/red] Preview not available for this file.")
        raise typer.Exit(1)
    except SleapShareError as e:
        err_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command()
def delete(
    shortcode: str = typer.Argument(..., help="Shortcode or URL of file to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    env: str | None = _get_env_option(),
) -> None:
    """Delete a file you own."""
    config = get_config(env=env)
    token = load_token(config)

    if not token:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("Run [bold]sleap-share login[/bold] to authenticate.")
        raise typer.Exit(1)

    if not yes:
        confirm = typer.confirm(f"Delete file {shortcode}?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    try:
        client = SleapShareClient(token=token, env=env)
        client.delete(shortcode)
        console.print(f"[bold green]Deleted:[/bold green] {shortcode}")

    except NotFoundError:
        err_console.print("[red]Error:[/red] File not found.")
        raise typer.Exit(1)
    except SleapShareError as e:
        err_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"sleap-share {__version__}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
