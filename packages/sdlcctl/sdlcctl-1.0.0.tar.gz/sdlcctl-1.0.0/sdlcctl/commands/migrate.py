"""
SDLC 5.0.0 Migration Command.

Migrate projects from SDLC 4.9.x to SDLC 5.0.0 Contract-First structure.

Key Changes in 5.0.0:
- Stage Restructuring: INTEGRATE moved from Stage 07 → Stage 03
- Simplified Naming: Lowercase, hyphenated stage names
- Contract-First: API Design (OpenAPI specs) BEFORE coding
- ISO/IEC 12207:2017 Alignment

Stage Mapping (4.9.x → 5.0.0):
  03-Development-Implementation   → 04-build
  04-Testing-Quality              → 05-test
  05-Deployment-Release           → 06-deploy
  06-Operations-Maintenance       → 07-operate
  07-Integration-APIs             → 03-integration (MOVED)
  08-Team-Management              → 08-collaborate
  09-Executive-Reports            → 09-govern
"""

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..validation.tier import STAGE_NAMES, STAGE_NAMES_4_9

console = Console()


@dataclass
class MigrationChange:
    """Represents a single migration change."""

    change_type: str  # rename, move, update
    source: str
    target: str
    description: str
    applied: bool = False
    error: Optional[str] = None


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    version_from: str
    version_to: str
    changes: List[MigrationChange] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# Stage migration mapping (4.9.x folder name → 5.0.0 folder name)
STAGE_MIGRATION_MAP = {
    "00-Project-Foundation": "00-foundation",
    "01-Planning-Analysis": "01-planning",
    "02-Design-Architecture": "02-design",
    "03-Development-Implementation": "04-build",  # Shifted +1
    "04-Testing-Quality": "05-test",  # Shifted +1
    "05-Deployment-Release": "06-deploy",  # Shifted +1
    "06-Operations-Maintenance": "07-operate",  # Shifted +1
    "07-Integration-APIs": "03-integration",  # MOVED from 07 → 03
    "08-Team-Management": "08-collaborate",
    "09-Executive-Reports": "09-govern",
    "10-Archive": "10-archive",
}

# Reverse mapping for validation
STAGE_MIGRATION_MAP_REVERSE = {v: k for k, v in STAGE_MIGRATION_MAP.items()}


class SDLCMigrator:
    """Migrates SDLC 4.9.x projects to 5.0.0 Contract-First structure."""

    def __init__(
        self,
        project_path: Path,
        dry_run: bool = False,
        backup: bool = True,
    ):
        self.project_path = project_path
        self.dry_run = dry_run
        self.backup = backup
        self.docs_path = project_path / "docs"
        self.backup_path: Optional[Path] = None
        self.changes: List[MigrationChange] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def detect_version(self) -> Tuple[str, bool]:
        """
        Detect current SDLC version from project structure.

        Returns:
            Tuple of (version_string, is_migrated)
        """
        if not self.docs_path.exists():
            return ("unknown", False)

        # Check for 5.0.0 stage names (Contract-First)
        has_5_0_stages = any(
            (self.docs_path / stage_name).exists()
            for stage_name in STAGE_NAMES.values()
        )

        # Check for 4.9.x stage names
        has_4_9_stages = any(
            (self.docs_path / stage_name).exists()
            for stage_name in STAGE_NAMES_4_9.values()
        )

        # Check for .sdlc-config.json
        config_path = self.project_path / ".sdlc-config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    framework_version = config.get("sdlc", {}).get(
                        "frameworkVersion", "unknown"
                    )
                    return (framework_version, framework_version.startswith("5."))
            except (json.JSONDecodeError, KeyError):
                pass

        if has_5_0_stages and not has_4_9_stages:
            return ("5.0.0", True)
        elif has_4_9_stages and not has_5_0_stages:
            return ("4.9.x", False)
        elif has_5_0_stages and has_4_9_stages:
            return ("mixed", False)
        else:
            return ("unknown", False)

    def create_backup(self) -> Optional[Path]:
        """Create backup of docs folder before migration."""
        if not self.backup or self.dry_run:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"docs_backup_4.9_{timestamp}"
        backup_path = self.project_path / backup_name

        if self.docs_path.exists():
            shutil.copytree(self.docs_path, backup_path)
            self.backup_path = backup_path
            return backup_path
        return None

    def plan_migration(self) -> List[MigrationChange]:
        """Plan migration changes without applying them."""
        changes = []

        if not self.docs_path.exists():
            self.warnings.append(f"docs folder not found at {self.docs_path}")
            return changes

        # Plan folder renames
        for old_name, new_name in STAGE_MIGRATION_MAP.items():
            old_path = self.docs_path / old_name
            new_path = self.docs_path / new_name

            if old_path.exists():
                if new_path.exists():
                    self.warnings.append(
                        f"Both {old_name} and {new_name} exist. Skipping rename."
                    )
                else:
                    changes.append(
                        MigrationChange(
                            change_type="rename",
                            source=str(old_path.relative_to(self.project_path)),
                            target=str(new_path.relative_to(self.project_path)),
                            description=f"Rename stage folder: {old_name} → {new_name}",
                        )
                    )

        # Plan .sdlc-config.json update
        config_path = self.project_path / ".sdlc-config.json"
        if config_path.exists():
            changes.append(
                MigrationChange(
                    change_type="update",
                    source=".sdlc-config.json",
                    target=".sdlc-config.json",
                    description="Update frameworkVersion to 5.0.0 and stage mappings",
                )
            )

        self.changes = changes
        return changes

    def apply_migration(self) -> MigrationResult:
        """Apply planned migration changes."""
        if not self.changes:
            self.plan_migration()

        if self.dry_run:
            return MigrationResult(
                success=True,
                version_from="4.9.x",
                version_to="5.0.0",
                changes=self.changes,
                warnings=self.warnings,
                errors=self.errors,
            )

        # Create backup first
        if self.backup:
            self.create_backup()

        # Apply folder renames
        for change in self.changes:
            if change.change_type == "rename":
                try:
                    source_path = self.project_path / change.source
                    target_path = self.project_path / change.target

                    if source_path.exists() and not target_path.exists():
                        source_path.rename(target_path)
                        change.applied = True
                    else:
                        change.error = "Source not found or target already exists"
                except OSError as e:
                    change.error = str(e)
                    self.errors.append(f"Failed to rename {change.source}: {e}")

            elif change.change_type == "update":
                try:
                    self._update_sdlc_config()
                    change.applied = True
                except Exception as e:
                    change.error = str(e)
                    self.errors.append(f"Failed to update config: {e}")

        # Update internal document references
        self._update_document_references()

        success = len(self.errors) == 0
        return MigrationResult(
            success=success,
            version_from="4.9.x",
            version_to="5.0.0",
            changes=self.changes,
            warnings=self.warnings,
            errors=self.errors,
        )

    def _update_sdlc_config(self) -> None:
        """Update .sdlc-config.json with new stage mappings."""
        config_path = self.project_path / ".sdlc-config.json"

        if not config_path.exists():
            # Create new config
            config = {
                "$schema": "https://sdlc-orchestrator.io/schemas/config-v1.json",
                "version": "1.0.0",
                "sdlc": {
                    "frameworkVersion": "5.0.0",
                    "tier": "STANDARD",
                    "stages": {
                        stage_id: f"docs/{stage_name}"
                        for stage_id, stage_name in STAGE_NAMES.items()
                    },
                },
            }
        else:
            with open(config_path) as f:
                config = json.load(f)

            # Update framework version
            if "sdlc" not in config:
                config["sdlc"] = {}
            config["sdlc"]["frameworkVersion"] = "5.0.0"

            # Update stage mappings
            config["sdlc"]["stages"] = {
                stage_id: f"docs/{stage_name}"
                for stage_id, stage_name in STAGE_NAMES.items()
            }

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _update_document_references(self) -> None:
        """Update internal document references to new stage paths."""
        if not self.docs_path.exists():
            return

        # Find all markdown files
        md_files = list(self.docs_path.rglob("*.md"))

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8")
                original_content = content

                # Replace old stage names with new ones
                for old_name, new_name in STAGE_MIGRATION_MAP.items():
                    content = content.replace(old_name, new_name)

                # Update version references
                content = re.sub(r"SDLC 4\.9\.\d+", "SDLC 5.0.0", content)
                content = re.sub(r"SDLC 4\.9\.x", "SDLC 5.0.0", content)

                if content != original_content:
                    md_file.write_text(content, encoding="utf-8")

            except (OSError, UnicodeDecodeError) as e:
                self.warnings.append(f"Could not update {md_file}: {e}")


def migrate_command(
    path: Path = typer.Argument(
        ...,
        help="Path to SDLC project to migrate",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    from_version: str = typer.Option(
        "4.9.1",
        "--from",
        "-f",
        help="Source SDLC version (default: 4.9.1)",
    ),
    to_version: str = typer.Option(
        "5.0.0",
        "--to",
        "-t",
        help="Target SDLC version (default: 5.0.0)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview changes without applying them",
    ),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        help="Skip creating backup of docs folder",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-F",
        help="Force migration even if already migrated",
    ),
) -> None:
    """
    Migrate SDLC project from 4.9.x to 5.0.0 Contract-First structure.

    Key Changes in 5.0.0:
    - Stage Restructuring: INTEGRATE moved from Stage 07 → Stage 03
    - Simplified Naming: Lowercase, hyphenated stage names
    - Contract-First: API Design (OpenAPI specs) BEFORE coding
    - ISO/IEC 12207:2017 Alignment

    Example:
        sdlcctl migrate /path/to/project --from 4.9.1 --to 5.0.0
        sdlcctl migrate /path/to/project --dry-run
    """
    console.print()
    console.print(
        Panel(
            "[bold blue]SDLC 5.0.0 Migration Tool[/bold blue]\n"
            "[dim]Contract-First Stage Restructuring[/dim]",
            expand=False,
        )
    )
    console.print()

    # Validate version parameters
    if not from_version.startswith("4.9"):
        console.print(
            f"[red]Error:[/red] Source version must be 4.9.x, got: {from_version}"
        )
        raise typer.Exit(1)

    if to_version != "5.0.0":
        console.print(f"[red]Error:[/red] Target version must be 5.0.0, got: {to_version}")
        raise typer.Exit(1)

    # Create migrator
    migrator = SDLCMigrator(
        project_path=path,
        dry_run=dry_run,
        backup=not no_backup,
    )

    # Detect current version
    current_version, is_migrated = migrator.detect_version()
    console.print(f"[bold]Project:[/bold] {path}")
    console.print(f"[bold]Detected Version:[/bold] {current_version}")
    console.print()

    if is_migrated and not force:
        console.print(
            "[yellow]Project appears to already be migrated to SDLC 5.0.0[/yellow]"
        )
        console.print("[dim]Use --force to migrate anyway[/dim]")
        raise typer.Exit(0)

    # Plan migration
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Planning migration...", total=None)
        changes = migrator.plan_migration()
        progress.update(task, completed=True)

    if not changes:
        console.print("[yellow]No changes needed.[/yellow]")
        if migrator.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in migrator.warnings:
                console.print(f"  ⚠️  {warning}")
        raise typer.Exit(0)

    # Show planned changes
    console.print(f"[bold]Planned Changes ({len(changes)}):[/bold]")
    console.print()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Type", width=8)
    table.add_column("Source", width=35)
    table.add_column("Target", width=35)

    for change in changes:
        table.add_row(change.change_type.upper(), change.source, change.target)

    console.print(table)
    console.print()

    # Show stage mapping explanation
    console.print("[bold]Stage Mapping (Contract-First):[/bold]")
    console.print("  [dim]03-Development-Implementation → 04-build (shifted +1)[/dim]")
    console.print("  [dim]04-Testing-Quality → 05-test (shifted +1)[/dim]")
    console.print("  [dim]05-Deployment-Release → 06-deploy (shifted +1)[/dim]")
    console.print("  [dim]06-Operations-Maintenance → 07-operate (shifted +1)[/dim]")
    console.print(
        "  [bold cyan]07-Integration-APIs → 03-integration (MOVED to Stage 03)[/bold cyan]"
    )
    console.print()

    if dry_run:
        console.print("[bold yellow]DRY RUN[/bold yellow] - No changes applied")
        raise typer.Exit(0)

    # Confirm migration
    if not force:
        confirm = typer.confirm("Apply these changes?")
        if not confirm:
            console.print("[yellow]Migration cancelled.[/yellow]")
            raise typer.Exit(0)

    # Apply migration
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Applying migration...", total=None)
        result = migrator.apply_migration()
        progress.update(task, completed=True)

    console.print()

    # Show results
    if result.success:
        console.print("[bold green]✅ Migration completed successfully![/bold green]")

        if migrator.backup_path:
            console.print(f"\n[dim]Backup created at: {migrator.backup_path}[/dim]")

        applied_count = sum(1 for c in result.changes if c.applied)
        console.print(f"\n[bold]Applied Changes:[/bold] {applied_count}/{len(result.changes)}")

    else:
        console.print("[bold red]❌ Migration completed with errors[/bold red]")

    # Show warnings
    if result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  ⚠️  {warning}")

    # Show errors
    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  ❌ {error}")

    console.print()
    console.print("[bold]Next Steps:[/bold]")
    console.print("  1. Review migrated folder structure")
    console.print("  2. Run [bold]sdlcctl validate[/bold] to check compliance")
    console.print("  3. Update any custom stage references in your code")
    console.print()

    if not result.success:
        raise typer.Exit(1)
