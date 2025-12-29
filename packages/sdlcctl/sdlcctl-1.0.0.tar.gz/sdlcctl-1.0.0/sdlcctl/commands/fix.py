"""
SDLC 5.0.0 Fix Command.

Automatically fixes SDLC structure issues.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from ..validation.engine import SDLCValidator, ValidationSeverity
from ..validation.structure_scanner import SDLCStructureScanner
from ..validation.violation import Severity as ScannerSeverity
from ..validation.p0 import P0ArtifactChecker
from ..validation.scanner import FolderScanner
from ..validation.tier import STAGE_NAMES, Tier, TierDetector

console = Console()


def fix_command(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path to fix",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    docs_root: str = typer.Option(
        "docs",
        "--docs",
        "-d",
        help="Documentation folder name",
    ),
    tier: Optional[str] = typer.Option(
        None,
        "--tier",
        "-t",
        help="Project tier: lite, standard, professional, enterprise",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be fixed without making changes",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive",
        "-i",
        help="Prompt before each fix",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Do not prompt before each fix",
    ),
    fix_stages: bool = typer.Option(
        True,
        "--stages",
        help="Fix missing stage folders",
    ),
    no_stages: bool = typer.Option(
        False,
        "--no-stages",
        help="Do not fix missing stage folders",
    ),
    fix_p0: bool = typer.Option(
        True,
        "--p0",
        help="Generate missing P0 artifacts",
    ),
    no_p0: bool = typer.Option(
        False,
        "--no-p0",
        help="Do not generate missing P0 artifacts",
    ),
    fix_naming: bool = typer.Option(
        False,
        "--naming",
        help="Fix stage naming violations (requires confirmation)",
    ),
    no_naming: bool = typer.Option(
        False,
        "--no-naming",
        help="Do not fix stage naming violations",
    ),
) -> None:
    """
    Automatically fix SDLC structure issues.

    Creates missing stage folders and generates P0 artifact templates.
    Use --dry-run to preview changes without applying them.

    Examples:

        sdlcctl fix --dry-run

        sdlcctl fix --no-interactive

        sdlcctl fix --p0 --no-stages
    """
    # Parse tier
    project_tier: Optional[Tier] = None
    if tier:
        try:
            project_tier = Tier(tier.lower())
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid tier '{tier}'")
            raise typer.Exit(code=1)

    # Resolve boolean flag precedence (Click 8.3.x is incompatible with
    # Typer's '--foo/--no-foo' style declarations).
    if no_interactive:
        interactive = False
    if no_stages:
        fix_stages = False
    if no_p0:
        fix_p0 = False
    if no_naming:
        fix_naming = False

    # Conservative auto-fix using Sprint 44 structure scanner:
    # - Create missing required stages for the selected tier (if provided)
    # - Rename stage folders for STAGE-001 / STAGE-003
    # - Fix invalid numbering prefixes for NUM-003
    # This runs before the legacy fix flow so we can normalize structure.
    docs_path = path / docs_root
    if docs_path.exists():
        _apply_scanner_autofix(
            project_root=path,
            docs_path=docs_path,
            tier=project_tier,
            dry_run=dry_run,
            interactive=interactive,
        )

    # Run validation first
    validator = SDLCValidator(
        project_root=path,
        docs_root=docs_root,
        tier=project_tier,
    )

    with console.status("[bold blue]Analyzing SDLC structure...[/bold blue]"):
        result = validator.validate()

    if result.is_compliant:
        console.print("[bold green]✓ Project is already SDLC 5.0.0 compliant![/bold green]")
        return

    # Show current status
    console.print()
    console.print(
        Panel(
            f"[bold]SDLC 5.0.0 Fix Tool[/bold]\n\n"
            f"Project: {path}\n"
            f"Tier: {result.tier.value.upper()}\n"
            f"Mode: {'DRY RUN' if dry_run else 'APPLY CHANGES'}",
            title="[bold blue]sdlcctl fix[/bold blue]",
            border_style="blue",
        )
    )

    fixes_applied = 0
    fixes_skipped = 0

    # Fix 1: Create docs folder if missing
    if not docs_path.exists():
        if _should_apply("Create docs folder", docs_path, dry_run, interactive):
            if not dry_run:
                docs_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✓ Created:[/green] {docs_path}")
            else:
                console.print(f"[yellow]Would create:[/yellow] {docs_path}")
            fixes_applied += 1
        else:
            fixes_skipped += 1

    # Fix 2: Create missing stage folders
    if fix_stages:
        fixes_applied, fixes_skipped = _fix_missing_stages(
            result, docs_path, dry_run, interactive, fixes_applied, fixes_skipped
        )

    # Fix 3: Generate missing P0 artifacts
    if fix_p0 and result.tier_requirements.p0_required:
        fixes_applied, fixes_skipped = _fix_missing_p0(
            result, path, docs_root, dry_run, interactive, fixes_applied, fixes_skipped
        )

    # Fix 4: Fix naming violations
    if fix_naming and result.scan_result.naming_violations:
        fixes_applied, fixes_skipped = _fix_naming_violations(
            result, docs_path, dry_run, interactive, fixes_applied, fixes_skipped
        )

    # Summary
    console.print()
    if dry_run:
        console.print(
            f"[yellow]DRY RUN:[/yellow] Would apply {fixes_applied} fix(es), "
            f"skip {fixes_skipped}"
        )
        console.print(
            "[dim]Run without --dry-run to apply changes[/dim]"
        )
    else:
        console.print(
            f"[green]Applied {fixes_applied} fix(es)[/green], "
            f"skipped {fixes_skipped}"
        )

        if fixes_applied > 0:
            console.print()
            console.print("[dim]Run 'sdlcctl validate' to verify compliance[/dim]")


def _apply_scanner_autofix(
    project_root: Path,
    docs_path: Path,
    tier: Optional[Tier],
    dry_run: bool,
    interactive: bool,
) -> None:
    """Apply conservative auto-fixes based on Sprint 44 scanner violations."""
    try:
        scanner = SDLCStructureScanner(docs_root=docs_path, project_root=project_root)
        scan_result = scanner.scan()
        scan_result.violations = scanner.filter_violations(scan_result.violations)
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Structure scanner autofix skipped: {e}")
        return

    fixes_applied = 0
    fixes_skipped = 0

    # 1) If tier is provided, create missing required stage folders.
    if tier is not None:
        requirements = TierDetector.get_requirements(tier)
        for stage_id in requirements.required_stages:
            stage_name = STAGE_NAMES.get(stage_id)
            if not stage_name:
                continue
            stage_path = docs_path / stage_name
            if stage_path.exists():
                continue

            if _should_apply("Create required stage folder", stage_path, dry_run, interactive):
                if not dry_run:
                    stage_path.mkdir(parents=True, exist_ok=True)
                    readme_path = stage_path / "README.md"
                    if not readme_path.exists():
                        readme_path.write_text(
                            f"# Stage {stage_id}: {stage_name}\n\n",
                            encoding="utf-8",
                        )
                    console.print(f"[green]✓ Created:[/green] {stage_path}")
                else:
                    console.print(f"[yellow]Would create:[/yellow] {stage_path}")
                fixes_applied += 1
            else:
                fixes_skipped += 1

    # 2) Apply rename-based fixes from violations.
    for v in scan_result.violations:
        if not v.auto_fixable:
            continue
        if v.rule_id not in {"STAGE-001", "STAGE-003", "NUM-003"}:
            continue

        suggested_name = v.context.get("suggested_name") or v.context.get("expected_name")
        if not suggested_name:
            continue

        src = Path(v.file_path)
        if not src.exists():
            continue

        dest = src.with_name(str(suggested_name))
        if dest.exists():
            continue

        if _should_apply(f"Rename ({v.rule_id})", src, dry_run, interactive):
            if not dry_run:
                src.rename(dest)
                console.print(f"[green]✓ Renamed:[/green] {src.name} → {dest.name}")
            else:
                console.print(f"[yellow]Would rename:[/yellow] {src.name} → {dest.name}")
            fixes_applied += 1
        else:
            fixes_skipped += 1

    if fixes_applied or fixes_skipped:
        console.print(
            f"[dim]Scanner auto-fix:[/dim] applied {fixes_applied}, skipped {fixes_skipped}"
        )


def _should_apply(
    action: str,
    target: Path,
    dry_run: bool,
    interactive: bool,
) -> bool:
    """Determine if an action should be applied."""
    if dry_run:
        return True

    if not interactive:
        return True

    return Confirm.ask(f"[cyan]{action}[/cyan]: {target}?")


def _fix_missing_stages(
    result,
    docs_path: Path,
    dry_run: bool,
    interactive: bool,
    fixes_applied: int,
    fixes_skipped: int,
) -> tuple:
    """Fix missing stage folders."""
    for stage_id in result.scan_result.stages_missing:
        if stage_id not in result.tier_requirements.required_stages:
            continue  # Skip optional stages

        stage_name = STAGE_NAMES.get(stage_id, f"{stage_id}-Unknown")
        stage_path = docs_path / stage_name

        if _should_apply(f"Create stage folder", stage_path, dry_run, interactive):
            if not dry_run:
                stage_path.mkdir(parents=True, exist_ok=True)

                # Create README.md
                readme_path = stage_path / "README.md"
                readme_content = _generate_stage_readme(stage_id, stage_name)
                readme_path.write_text(readme_content, encoding="utf-8")

                # Create 99-Legacy folder
                legacy_path = stage_path / "99-Legacy"
                legacy_path.mkdir(exist_ok=True)
                legacy_readme = legacy_path / "README.md"
                legacy_readme.write_text(
                    "# Legacy Content\n\n"
                    "**AI Directive**: DO NOT READ this folder.\n\n"
                    "This folder contains archived, outdated content.\n",
                    encoding="utf-8",
                )

                console.print(f"[green]✓ Created:[/green] {stage_path}")
            else:
                console.print(f"[yellow]Would create:[/yellow] {stage_path}")
            fixes_applied += 1
        else:
            fixes_skipped += 1

    return fixes_applied, fixes_skipped


def _fix_missing_p0(
    result,
    project_root: Path,
    docs_root: str,
    dry_run: bool,
    interactive: bool,
    fixes_applied: int,
    fixes_skipped: int,
) -> tuple:
    """Fix missing P0 artifacts."""
    p0_checker = P0ArtifactChecker(
        project_root, docs_root, tier=result.tier
    )
    missing = p0_checker.get_missing_artifacts()

    for artifact in missing:
        artifact_path = project_root / docs_root / artifact.relative_path

        if _should_apply(
            f"Generate P0 artifact ({artifact.name})",
            artifact_path,
            dry_run,
            interactive,
        ):
            if not dry_run:
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                template = p0_checker._generate_template(artifact)
                artifact_path.write_text(template, encoding="utf-8")
                console.print(f"[green]✓ Generated:[/green] {artifact_path}")
            else:
                console.print(f"[yellow]Would generate:[/yellow] {artifact_path}")
            fixes_applied += 1
        else:
            fixes_skipped += 1

    return fixes_applied, fixes_skipped


def _fix_naming_violations(
    result,
    docs_path: Path,
    dry_run: bool,
    interactive: bool,
    fixes_applied: int,
    fixes_skipped: int,
) -> tuple:
    """Fix stage naming violations."""
    for violation in result.scan_result.naming_violations:
        if violation.get("type") != "stage_naming":
            continue

        found_name = violation["found"]
        expected_name = violation["expected"]
        found_path = docs_path / found_name
        expected_path = docs_path / expected_name

        if not found_path.exists():
            continue

        if _should_apply(
            f"Rename '{found_name}' to '{expected_name}'",
            found_path,
            dry_run,
            interactive,
        ):
            if not dry_run:
                found_path.rename(expected_path)
                console.print(
                    f"[green]✓ Renamed:[/green] {found_name} → {expected_name}"
                )
            else:
                console.print(
                    f"[yellow]Would rename:[/yellow] {found_name} → {expected_name}"
                )
            fixes_applied += 1
        else:
            fixes_skipped += 1

    return fixes_applied, fixes_skipped


def _generate_stage_readme(stage_id: str, stage_name: str) -> str:
    """Generate README content for a stage folder."""
    # Extract stage name without prefix
    display_name = stage_name.split("-", 1)[1].replace("-", " ") if "-" in stage_name else stage_name

    # Stage descriptions
    descriptions = {
        "00": "Define **WHY** this project exists. Vision, problem statement, and business case.",
        "01": "Define **WHAT** needs to be built. Requirements, user stories, and acceptance criteria.",
        "02": "Define **HOW** it will be built. Architecture, design, and technical specifications.",
        "03": "**BUILD** the solution. Sprint plans, coding standards, and implementation guides.",
        "04": "**TEST** the implementation. Test plans, test cases, and quality assurance.",
        "05": "**DEPLOY** to production. Release plans, deployment guides, and rollback procedures.",
        "06": "**OPERATE** the system. Monitoring, alerting, and incident response.",
        "07": "**INTEGRATE** with other systems. API documentation, integration guides.",
        "08": "**COLLABORATE** effectively. Team structure, RACI, communication protocols.",
        "09": "**GOVERN** the project. Executive reports, metrics, and compliance.",
        "10": "**ARCHIVE** completed work. Historical records and lessons learned.",
    }

    description = descriptions.get(stage_id, "[Describe the purpose of this stage]")

    return f"""# Stage {stage_id}: {display_name}

**Version**: 5.0.0
**Stage**: {stage_id} - {display_name}
**Status**: ACTIVE
**Framework**: SDLC 5.0.0 Complete Lifecycle

---

## Purpose

{description}

---

## Folder Structure

```
{stage_name}/
├── README.md                         # This file (P0 entry point)
├── 01-[Subfolder]/                   # [Description]
├── 02-[Subfolder]/                   # [Description]
└── 99-Legacy/                        # Archived content (AI: DO NOT READ)
```

---

## Key Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [Document-Name.md](./Document-Name.md) | [Purpose] | Draft |

---

## AI Assistant Guidance

**DO Read**:
- This README for context
- Key documents listed above

**DO NOT Read**:
- `99-Legacy/` folder - Contains archived, outdated content

---

**Document Status**: P0 Entry Point
**Compliance**: SDLC 5.0.0 Stage {stage_id}
**Last Updated**: [Date]
**Owner**: [Role]

"""
