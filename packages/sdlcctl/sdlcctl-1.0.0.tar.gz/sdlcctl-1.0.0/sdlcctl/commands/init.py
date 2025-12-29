"""
SDLC 5.0.0 Init Command.

Initialize a new SDLC 5.0.0 project structure.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from ..validation.tier import STAGE_NAMES, Tier, TierDetector

console = Console()


def init_command(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path to initialize",
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
    team_size: Optional[int] = typer.Option(
        None,
        "--team-size",
        help="Team size (used to auto-detect tier)",
    ),
    scaffold: bool = typer.Option(
        True,
        "--scaffold",
        help="Create full folder structure with READMEs",
    ),
    no_scaffold: bool = typer.Option(
        False,
        "--no-scaffold",
        help="Do not create READMEs and templates",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing docs folder",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive",
        "-i",
        help="Interactive mode with prompts",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Do not prompt; use defaults where needed",
    ),
) -> None:
    """
    Initialize SDLC 5.0.0 project structure.

    Creates the complete documentation folder structure with stage folders,
    README templates, and P0 artifacts based on the selected tier.

    Examples:

        sdlcctl init --tier professional

        sdlcctl init --team-size 25

        sdlcctl init --no-interactive --tier standard
    """
    console.print()
    console.print(
        Panel(
            "[bold]SDLC 5.0.0 Project Initialization[/bold]\n\n"
            "This wizard will set up your documentation structure\n"
            "following SDLC 5.0.0 best practices.",
            title="[bold blue]sdlcctl init[/bold blue]",
            border_style="blue",
        )
    )

    # Resolve boolean flag precedence (Click 8.3.x is incompatible with
    # Typer's '--foo/--no-foo' style declarations).
    if no_interactive:
        interactive = False
    if no_scaffold:
        scaffold = False

    # Check if docs folder already exists
    docs_path = path / docs_root
    if docs_path.exists() and not force:
        if interactive:
            if not Confirm.ask(
                f"[yellow]Warning:[/yellow] {docs_path} already exists. Overwrite?"
            ):
                console.print("[dim]Initialization cancelled.[/dim]")
                raise typer.Exit(code=0)
        else:
            console.print(
                f"[red]Error:[/red] {docs_path} already exists. "
                f"Use --force to overwrite."
            )
            raise typer.Exit(code=1)

    # Determine tier
    project_tier: Tier
    if tier:
        try:
            project_tier = Tier(tier.lower())
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid tier '{tier}'")
            raise typer.Exit(code=1)
    elif team_size:
        detector = TierDetector()
        project_tier = detector.detect_from_team_size(team_size)
        console.print(
            f"[cyan]Auto-detected tier:[/cyan] {project_tier.value.upper()} "
            f"(team size: {team_size})"
        )
    elif interactive:
        project_tier = _prompt_for_tier()
    else:
        project_tier = Tier.PROFESSIONAL
        console.print(
            f"[cyan]Using default tier:[/cyan] {project_tier.value.upper()}"
        )

    # Get tier requirements
    detector = TierDetector()
    requirements = detector.get_requirements(project_tier)

    # Show what will be created
    console.print()
    console.print(f"[bold]Tier:[/bold] {project_tier.value.upper()}")
    console.print(f"[bold]Required Stages:[/bold] {len(requirements.required_stages)}")
    console.print(f"[bold]P0 Artifacts Required:[/bold] {'Yes' if requirements.p0_required else 'No'}")

    if interactive:
        console.print()
        if not Confirm.ask("Proceed with initialization?"):
            console.print("[dim]Initialization cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Create structure
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating SDLC structure...", total=None)

        # Create docs folder
        docs_path.mkdir(parents=True, exist_ok=True)

        # Create main README
        main_readme = docs_path / "README.md"
        main_readme.write_text(
            _generate_main_readme(path.name, project_tier, requirements),
            encoding="utf-8",
        )
        progress.update(task, description="Created main README")

        # Create stage folders
        for stage_id in requirements.required_stages:
            stage_name = STAGE_NAMES.get(stage_id, f"{stage_id}-Unknown")
            stage_path = docs_path / stage_name

            if scaffold:
                _create_stage_folder(stage_path, stage_id, stage_name)
            else:
                stage_path.mkdir(parents=True, exist_ok=True)

            progress.update(task, description=f"Created {stage_name}")

        # Create optional stages (as placeholders)
        if scaffold:
            optional_stages = [
                s for s in STAGE_NAMES.keys()
                if s not in requirements.required_stages
            ]
            for stage_id in optional_stages:
                stage_name = STAGE_NAMES.get(stage_id)
                if stage_name:
                    stage_path = docs_path / stage_name
                    if not stage_path.exists():
                        stage_path.mkdir(parents=True, exist_ok=True)
                        readme = stage_path / "README.md"
                        readme.write_text(
                            f"# {stage_name}\n\n"
                            f"**Status**: OPTIONAL for {project_tier.value.upper()} tier\n\n"
                            f"This stage is not required for your current tier.\n",
                            encoding="utf-8",
                        )
                    progress.update(task, description=f"Created {stage_name} (optional)")

    # Success message
    console.print()
    console.print("[bold green]✓ SDLC 5.0.0 structure initialized successfully![/bold green]")
    console.print()
    console.print(f"[dim]Project root:[/dim] {path}")
    console.print(f"[dim]Docs folder:[/dim] {docs_path}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Review and customize the generated READMEs")
    console.print("  2. Fill in P0 artifacts for your tier")
    console.print("  3. Run 'sdlcctl validate' to check compliance")
    console.print()


def _prompt_for_tier() -> Tier:
    """Interactive prompt for tier selection."""
    console.print()
    console.print("[bold]Select your project tier:[/bold]")
    console.print()
    console.print("  [cyan]1)[/cyan] LITE        - 1-2 people, 4 stages")
    console.print("  [cyan]2)[/cyan] STANDARD    - 3-10 people, 6 stages")
    console.print("  [cyan]3)[/cyan] PROFESSIONAL- 10-50 people, 10 stages, P0 required")
    console.print("  [cyan]4)[/cyan] ENTERPRISE  - 50+ people, 11 stages, full compliance")
    console.print()

    choice = Prompt.ask(
        "Enter choice",
        choices=["1", "2", "3", "4"],
        default="3",
    )

    tier_map = {
        "1": Tier.LITE,
        "2": Tier.STANDARD,
        "3": Tier.PROFESSIONAL,
        "4": Tier.ENTERPRISE,
    }

    return tier_map[choice]


def _create_stage_folder(stage_path: Path, stage_id: str, stage_name: str) -> None:
    """Create a stage folder with full scaffolding."""
    stage_path.mkdir(parents=True, exist_ok=True)

    # Create README
    readme_path = stage_path / "README.md"
    readme_path.write_text(
        _generate_stage_readme(stage_id, stage_name),
        encoding="utf-8",
    )

    # Create standard subfolders based on stage
    subfolders = _get_stage_subfolders(stage_id)
    for subfolder in subfolders:
        subfolder_path = stage_path / subfolder
        subfolder_path.mkdir(exist_ok=True)
        # Create placeholder README
        subfolder_readme = subfolder_path / "README.md"
        if not subfolder_readme.exists():
            subfolder_readme.write_text(
                f"# {subfolder}\n\n[Add content here]\n",
                encoding="utf-8",
            )

    # Create 99-Legacy folder
    legacy_path = stage_path / "99-Legacy"
    legacy_path.mkdir(exist_ok=True)
    legacy_readme = legacy_path / "README.md"
    legacy_readme.write_text(
        "# Legacy Content\n\n"
        "**AI Directive**: DO NOT READ this folder.\n\n"
        "This folder contains archived, outdated content.\n"
        "Move deprecated documents here instead of deleting them.\n",
        encoding="utf-8",
    )


def _get_stage_subfolders(stage_id: str) -> list:
    """Get recommended subfolders for a stage."""
    subfolders = {
        "00": ["01-Vision", "02-Business-Case", "03-Design-Thinking", "04-Roadmap"],
        "01": ["01-Requirements", "02-User-Stories", "03-Analysis"],
        "02": ["01-System-Architecture", "02-Data-Model", "03-API-Design", "04-ADRs"],
        "03": ["01-Coding-Standards", "02-Sprint-Plans", "03-Setup-Guides", "04-Phase-Plans"],
        "04": ["01-Test-Plans", "02-Test-Cases", "03-Test-Reports"],
        "05": ["01-Release-Plans", "02-Deployment-Guides", "03-Runbooks"],
        "06": ["01-Monitoring", "02-Alerting", "03-Incident-Response"],
        "07": ["01-API-Documentation", "02-Integration-Guides", "03-External-Systems"],
        "08": ["01-Team-Structure", "02-RACI", "03-Communication"],
        "09": ["01-Executive-Reports", "02-Metrics", "03-Compliance"],
        "10": ["01-Archive", "02-Lessons-Learned", "03-Historical"],
    }
    return subfolders.get(stage_id, [])


def _generate_main_readme(project_name: str, tier: Tier, requirements) -> str:
    """Generate main docs README."""
    stage_list = "\n".join(
        f"- [{STAGE_NAMES[s]}](./{STAGE_NAMES[s]}/)"
        for s in requirements.required_stages
    )

    return f"""# {project_name} Documentation

**Framework**: SDLC 5.0.0
**Tier**: {tier.value.upper()}
**Status**: ACTIVE

---

## Overview

This documentation follows the SDLC 5.0.0 Complete Lifecycle methodology
with {len(requirements.required_stages)} stages.

---

## Documentation Structure

### Required Stages

{stage_list}

---

## Quick Navigation

| Stage | Purpose | Status |
|-------|---------|--------|
| 00 - Project Foundation | WHY - Vision & Business Case | Active |
| 01 - Planning & Analysis | WHAT - Requirements | Active |
| 02 - Design & Architecture | HOW - Technical Design | Active |
| 03 - Development | BUILD - Implementation | Active |

---

## AI Assistant Guidance

AI assistants should:
1. Start with this README for navigation
2. Read stage README.md files for context
3. **NEVER** read `99-Legacy/` folders

---

**Generated by**: sdlcctl init
**Framework**: SDLC 5.0.0
**Tier**: {tier.value.upper()}

"""


def _generate_stage_readme(stage_id: str, stage_name: str) -> str:
    """Generate README content for a stage folder."""
    display_name = stage_name.split("-", 1)[1].replace("-", " ") if "-" in stage_name else stage_name

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
