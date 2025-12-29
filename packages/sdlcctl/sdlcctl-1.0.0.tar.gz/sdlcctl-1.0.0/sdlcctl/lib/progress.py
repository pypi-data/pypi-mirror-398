"""
=========================================================================
Rich Progress Display for CLI Streaming
SDLC Orchestrator - Sprint 52

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 Implementation
Authority: Backend Team + CTO Approved

Purpose:
- Display real-time streaming progress with Rich console
- Handle various SSE event types with appropriate UI
- Show file tree, progress bar, and summary panels
- Support session resume display

References:
- docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
- backend/sdlcctl/lib/sse_client.py
=========================================================================
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.tree import Tree

from .sse_client import (
    CheckpointEvent,
    CompletedEvent,
    ErrorEvent,
    FileGeneratedEvent,
    FileGeneratingEvent,
    SessionResumedEvent,
    StartedEvent,
    StreamEvent,
)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class FileInfo:
    """Information about a generated file."""

    path: str
    lines: int
    language: str
    valid: bool


@dataclass
class GenerationStats:
    """Statistics for generation session."""

    total_files: int = 0
    completed_files: int = 0
    total_lines: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    files: list[FileInfo] = field(default_factory=list)
    current_file: Optional[str] = None
    session_id: Optional[str] = None
    provider: str = ""
    model: str = ""
    checkpoints: int = 0
    resumed_from: Optional[int] = None

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def files_per_second(self) -> float:
        """Get files generated per second."""
        duration = self.duration_seconds
        if duration > 0:
            return self.completed_files / duration
        return 0.0


# ============================================================================
# Progress Display
# ============================================================================


class StreamingProgress:
    """
    Display streaming generation progress using Rich.

    Provides real-time feedback on code generation with:
    - Spinner for in-progress files
    - Checkmark for completed files
    - Progress bar for overall completion
    - Summary panel on completion
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize progress display.

        Args:
            console: Rich console instance (created if not provided)
        """
        self.console = console or Console()
        self.stats = GenerationStats()
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None

    def handle_event(self, event: StreamEvent) -> None:
        """
        Handle incoming SSE event and update display.

        Args:
            event: SSE event from backend
        """
        if isinstance(event, StartedEvent):
            self._on_started(event)
        elif isinstance(event, FileGeneratingEvent):
            self._on_file_generating(event)
        elif isinstance(event, FileGeneratedEvent):
            self._on_file_generated(event)
        elif isinstance(event, CheckpointEvent):
            self._on_checkpoint(event)
        elif isinstance(event, CompletedEvent):
            self._on_completed(event)
        elif isinstance(event, ErrorEvent):
            self._on_error(event)
        elif isinstance(event, SessionResumedEvent):
            self._on_session_resumed(event)

    def _on_started(self, event: StartedEvent) -> None:
        """Handle generation started event."""
        self.stats.start_time = time.time()
        self.stats.session_id = event.session_id
        self.stats.provider = event.provider
        self.stats.model = event.model

        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]🚀 Starting Code Generation[/bold cyan]\n\n"
                f"[dim]Session:[/dim] {event.session_id[:8]}...\n"
                f"[dim]Provider:[/dim] {event.provider}\n"
                f"[dim]Model:[/dim] {event.model}",
                title="Generation Started",
                border_style="cyan",
            )
        )
        self.console.print()

    def _on_session_resumed(self, event: SessionResumedEvent) -> None:
        """Handle session resumed event."""
        self.stats.session_id = event.session_id
        self.stats.resumed_from = event.resumed_from_checkpoint
        self.stats.completed_files = event.files_already_completed
        self.stats.total_files = event.files_already_completed + event.files_remaining

        self.console.print()
        self.console.print(
            Panel(
                f"[bold yellow]🔄 Resuming Generation[/bold yellow]\n\n"
                f"[dim]Session:[/dim] {event.session_id[:8]}...\n"
                f"[dim]Checkpoint:[/dim] #{event.resumed_from_checkpoint}\n"
                f"[dim]Files recovered:[/dim] {event.files_already_completed}\n"
                f"[dim]Files remaining:[/dim] {event.files_remaining}",
                title="Session Resumed",
                border_style="yellow",
            )
        )
        self.console.print()

    def _on_file_generating(self, event: FileGeneratingEvent) -> None:
        """Handle file generating event."""
        self.stats.current_file = event.path
        self.console.print(f"  [dim]⏳[/dim] {event.path} [dim](generating...)[/dim]")

    def _on_file_generated(self, event: FileGeneratedEvent) -> None:
        """Handle file generated event."""
        self.stats.completed_files += 1
        self.stats.total_lines += event.lines

        file_info = FileInfo(
            path=event.path,
            lines=event.lines,
            language=event.language,
            valid=event.syntax_valid,
        )
        self.stats.files.append(file_info)

        # Display status
        if event.syntax_valid:
            status = "[green]✅[/green]"
        else:
            status = "[yellow]⚠️[/yellow]"

        self.console.print(
            f"  {status} {event.path} "
            f"[dim]({event.lines} lines, {event.language})[/dim]"
        )

    def _on_checkpoint(self, event: CheckpointEvent) -> None:
        """Handle checkpoint event."""
        self.stats.checkpoints += 1
        self.stats.total_files = event.total_files

        self.console.print(
            f"\n  [cyan]💾 Checkpoint #{event.checkpoint_number}[/cyan] "
            f"[dim]({event.files_completed}/{event.total_files} files)[/dim]\n"
        )

    def _on_completed(self, event: CompletedEvent) -> None:
        """Handle generation completed event."""
        self.stats.end_time = time.time()
        self.stats.total_files = event.total_files
        self.stats.total_lines = event.total_lines

        duration = self.stats.duration_seconds

        # Build summary panel
        if event.success:
            status_text = "[bold green]✅ Generation Complete![/bold green]"
            border_style = "green"
        else:
            status_text = "[bold yellow]⚠️ Generation Finished with Issues[/bold yellow]"
            border_style = "yellow"

        # Calculate stats
        files_per_sec = self.stats.files_per_second
        lines_per_sec = self.stats.total_lines / duration if duration > 0 else 0

        summary = (
            f"{status_text}\n\n"
            f"[dim]Files:[/dim] {event.total_files}\n"
            f"[dim]Lines:[/dim] {event.total_lines:,}\n"
            f"[dim]Duration:[/dim] {duration:.1f}s\n"
            f"[dim]Speed:[/dim] {files_per_sec:.1f} files/s, {lines_per_sec:.0f} lines/s"
        )

        if self.stats.checkpoints > 0:
            summary += f"\n[dim]Checkpoints:[/dim] {self.stats.checkpoints}"

        if self.stats.resumed_from is not None:
            summary += f"\n[dim]Resumed from:[/dim] Checkpoint #{self.stats.resumed_from}"

        self.console.print()
        self.console.print(
            Panel(
                summary,
                title="Summary",
                border_style=border_style,
            )
        )

    def _on_error(self, event: ErrorEvent) -> None:
        """Handle error event."""
        self.console.print()

        error_text = f"[bold red]❌ Error[/bold red]\n\n{event.message}"

        if event.recovery_id:
            error_text += (
                f"\n\n[dim]Recovery available! Run:[/dim]\n"
                f"  sdlcctl generate --resume {event.recovery_id}"
            )

        self.console.print(
            Panel(
                error_text,
                title="Generation Failed",
                border_style="red",
            )
        )

    def show_file_tree(self) -> None:
        """Display generated files as a tree structure."""
        if not self.stats.files:
            return

        tree = Tree("[bold]Generated Files[/bold]")

        # Group files by directory
        dirs: dict[str, list[FileInfo]] = {}
        for f in self.stats.files:
            parts = f.path.split("/")
            dir_path = "/".join(parts[:-1]) if len(parts) > 1 else "."
            if dir_path not in dirs:
                dirs[dir_path] = []
            dirs[dir_path].append(f)

        # Build tree
        for dir_path in sorted(dirs.keys()):
            if dir_path == ".":
                branch = tree
            else:
                branch = tree.add(f"[blue]{dir_path}/[/blue]")

            for f in sorted(dirs[dir_path], key=lambda x: x.path):
                filename = f.path.split("/")[-1]
                status = "[green]✓[/green]" if f.valid else "[yellow]![/yellow]"
                branch.add(f"{status} {filename} [dim]({f.lines} lines)[/dim]")

        self.console.print()
        self.console.print(tree)

    def show_summary_table(self) -> None:
        """Display summary as a table."""
        if not self.stats.files:
            return

        table = Table(title="Generated Files", show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Lines", justify="right")
        table.add_column("Language")
        table.add_column("Status", justify="center")

        for f in sorted(self.stats.files, key=lambda x: x.path):
            status = "✅" if f.valid else "⚠️"
            table.add_row(f.path, str(f.lines), f.language, status)

        self.console.print()
        self.console.print(table)


# ============================================================================
# Utility Functions
# ============================================================================


def create_progress_bar(console: Console) -> Progress:
    """
    Create a Rich progress bar for file generation.

    Args:
        console: Rich console instance

    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )
