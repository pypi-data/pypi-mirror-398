"""Terminal UI components for vmux.

Clean, minimal output inspired by uv/bun/cargo.
Uses Rich for progress bars, spinners, and styled output.
"""

import os
import sys
from contextlib import contextmanager
from typing import Iterator

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    DownloadColumn,
)
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Check if we should suppress progress (for CI/pipes)
NO_PROGRESS = os.environ.get("TUP_NO_PROGRESS", "").lower() in ("1", "true", "yes")
NO_COLOR = os.environ.get("NO_COLOR", "") != "" or os.environ.get("TUP_NO_COLOR", "").lower() in ("1", "true", "yes")

console = Console(
    force_terminal=None if not NO_COLOR else False,
    no_color=NO_COLOR,
)


def success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}", style="red")


def warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]![/yellow] {message}", style="yellow")


def info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim]→[/dim] {message}")


def dim(message: str) -> None:
    """Print dimmed/secondary text."""
    console.print(message, style="dim")


@contextmanager
def spinner(message: str) -> Iterator[None]:
    """Show a spinner for indeterminate operations.

    Usage:
        with spinner("Connecting..."):
            do_something()
    """
    if NO_PROGRESS:
        console.print(f"[dim]→[/dim] {message}")
        yield
        return

    with console.status(f"[dim]{message}[/dim]", spinner="dots"):
        yield


@contextmanager
def progress_bar(description: str, total: int | float) -> Iterator[Progress]:
    """Show a progress bar for determinate operations.

    Usage:
        with progress_bar("Uploading", total=100) as progress:
            task = progress.add_task("files", total=100)
            for i in range(100):
                progress.update(task, advance=1)
    """
    if NO_PROGRESS:
        console.print(f"[dim]→[/dim] {description}")
        # Return a dummy progress that does nothing
        yield _DummyProgress()
        return

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[dim]{task.description}[/dim]"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )
    with progress:
        yield progress


@contextmanager
def upload_progress() -> Iterator[Progress]:
    """Show upload progress with bytes."""
    if NO_PROGRESS:
        yield _DummyProgress()
        return

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[dim]{task.description}[/dim]"),
        BarColumn(bar_width=20),
        DownloadColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )
    with progress:
        yield progress


class _DummyProgress:
    """Dummy progress that does nothing (for NO_PROGRESS mode)."""

    def add_task(self, *args, **kwargs):
        return 0

    def update(self, *args, **kwargs):
        pass

    def advance(self, *args, **kwargs):
        pass


def job_status_table(jobs: list[dict]) -> None:
    """Print a table of job statuses."""
    if not jobs:
        dim("No jobs found.")
        return

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Created", style="dim")

    for job in jobs:
        job_id = job.get("job_id", "???")[:8]
        status = job.get("status", "unknown")

        # Color-code status
        if status == "running":
            status_str = "[yellow]● running[/yellow]"
        elif status == "completed":
            status_str = "[green]✓ completed[/green]"
        elif status == "failed":
            status_str = "[red]✗ failed[/red]"
        else:
            status_str = f"[dim]{status}[/dim]"

        created = job.get("created_at", "")[:16].replace("T", " ")

        table.add_row(job_id, status_str, created)

    console.print(table)


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def bundling_summary(file_count: int, total_size: int, excluded_count: int = 0) -> None:
    """Print a summary of what was bundled."""
    size_str = format_size(total_size)
    msg = f"Bundled {file_count} files ({size_str})"
    if excluded_count > 0:
        msg += f" [dim]({excluded_count} excluded)[/dim]"
    success(msg)
