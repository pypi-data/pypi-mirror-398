"""
=========================================================================
SDLC 5.0.0 Structure Validator CLI.
SDLC Orchestrator - Sprint 52

Version: 2.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 Magic Mode
Authority: Backend Team + CTO Approved

Purpose:
- Main entry point for the sdlcctl command-line tool
- Structure validation, fixing, and initialization
- Code generation from AppBlueprint (Sprint 46)
- Magic Mode - Natural language to code (Sprint 52)

Usage:
    sdlcctl validate ./my-project
    sdlcctl generate blueprint.json -o ./output
    sdlcctl magic "Nhà hàng Phở 24" -o ./pho24
=========================================================================
"""

import typer
from rich.console import Console

from . import __version__, __framework__
from .commands.validate import validate_command
from .commands.fix import fix_command
from .commands.init import init_command
from .commands.report import report_command
from .commands.migrate import migrate_command
from .commands.generate import generate_command
from .commands.magic import magic_command

console = Console()

# Create main Typer app
app = typer.Typer(
    name="sdlcctl",
    help="SDLC 5.0.0 Structure Validator CLI",
    add_completion=True,
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version information."""
    if value:
        console.print(f"[bold blue]sdlcctl[/bold blue] v{__version__}")
        console.print(f"[dim]Framework: {__framework__}[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    SDLC 5.0.0 Structure Validator CLI.

    Validate, fix, and initialize SDLC 5.0.0 compliant project structures.

    Supports 4-Tier Classification:
    - LITE: 1-2 people, 4 stages
    - STANDARD: 3-10 people, 6 stages
    - PROFESSIONAL: 10-50 people, 10 stages (P0 required)
    - ENTERPRISE: 50+ people, 11 stages (full compliance)
    """
    pass


# Register commands
app.command(name="validate", help="Validate SDLC 5.0.0 folder structure")(
    validate_command
)
app.command(name="fix", help="Automatically fix SDLC structure issues")(
    fix_command
)
app.command(name="init", help="Initialize SDLC 5.0.0 project structure")(
    init_command
)
app.command(name="report", help="Generate SDLC compliance report")(
    report_command
)
app.command(name="migrate", help="Migrate from SDLC 4.9.x to 5.0.0")(
    migrate_command
)
app.command(name="generate", help="Generate backend scaffold from AppBlueprint")(
    generate_command
)
app.command(name="magic", help="Generate app from natural language (Vietnamese/English)")(
    magic_command
)


@app.command(name="tiers")
def show_tiers() -> None:
    """Show tier classification details."""
    from rich.table import Table

    from .validation.tier import TIER_REQUIREMENTS, Tier

    table = Table(title="SDLC 5.0.0 Tier Classification", show_header=True)
    table.add_column("Tier", style="cyan", width=15)
    table.add_column("Team Size", justify="right", width=12)
    table.add_column("Stages", justify="right", width=10)
    table.add_column("P0 Required", justify="center", width=12)
    table.add_column("Compliance", width=20)

    tier_sizes = {
        Tier.LITE: "1-2",
        Tier.STANDARD: "3-10",
        Tier.PROFESSIONAL: "10-50",
        Tier.ENTERPRISE: "50+",
    }

    for tier, req in TIER_REQUIREMENTS.items():
        compliance = ", ".join(req.compliance_required) if req.compliance_required else "-"
        table.add_row(
            tier.value.upper(),
            tier_sizes[tier],
            str(req.min_stages),
            "✅" if req.p0_required else "❌",
            compliance,
        )

    console.print()
    console.print(table)
    console.print()


@app.command(name="stages")
def show_stages() -> None:
    """Show SDLC 5.0.0 stage definitions (Contract-First Order)."""
    from rich.table import Table

    from .validation.tier import STAGE_NAMES

    table = Table(title="SDLC 5.0.0 Stages (Contract-First Order)", show_header=True)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Stage Name", width=20)
    table.add_column("Purpose", width=50)
    table.add_column("Type", width=12)

    # SDLC 5.1.1 Stage Definitions (10 Stages: 00-09 + Archive folder)
    # Reference: SDLC-Enterprise-Framework/README.md (v5.1.1)
    questions = {
        "00": ("FOUNDATION - Strategic Discovery & Validation (WHY?)", "LINEAR"),
        "01": ("PLANNING - Requirements & User Stories (WHAT?)", "LINEAR"),
        "02": ("DESIGN - Architecture & Technical Design (HOW?)", "LINEAR"),
        "03": ("INTEGRATE - API Contracts & Third-party Setup", "LINEAR"),
        "04": ("BUILD - Development & Implementation", "LINEAR"),
        "05": ("TEST - Quality Assurance & Validation", "LINEAR"),
        "06": ("DEPLOY - Release & Deployment", "LINEAR"),
        "07": ("OPERATE - Production Operations & Monitoring", "LINEAR"),
        "08": ("COLLABORATE - Team Coordination & Knowledge", "CONTINUOUS"),
        "09": ("GOVERN - Compliance & Strategic Oversight", "CONTINUOUS"),
        "10": ("ARCHIVE - Project Archive (Legacy Docs)", "OPTIONAL"),
    }

    for stage_id, stage_name in sorted(STAGE_NAMES.items()):
        purpose, stage_type = questions.get(stage_id, ("", ""))
        table.add_row(stage_id, stage_name, purpose, stage_type)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Contract-First: API Design (Stage 03) must happen BEFORE coding (Stage 04)[/dim]")
    console.print()


@app.command(name="p0")
def show_p0() -> None:
    """Show P0 artifact requirements."""
    from rich.table import Table

    from .validation.p0 import P0_ARTIFACTS
    from .validation.tier import Tier

    table = Table(title="SDLC 5.0.0 P0 Artifacts", show_header=True)
    table.add_column("Artifact", style="cyan", width=25)
    table.add_column("Stage", width=8)
    table.add_column("Path", width=45)
    table.add_column("LITE", justify="center", width=6)
    table.add_column("STD", justify="center", width=6)
    table.add_column("PRO", justify="center", width=6)
    table.add_column("ENT", justify="center", width=6)

    for artifact in P0_ARTIFACTS:
        table.add_row(
            artifact.name,
            artifact.stage_id,
            artifact.relative_path[:42] + "..." if len(artifact.relative_path) > 45 else artifact.relative_path,
            "✅" if Tier.LITE in artifact.required_tiers else "❌",
            "✅" if Tier.STANDARD in artifact.required_tiers else "❌",
            "✅" if Tier.PROFESSIONAL in artifact.required_tiers else "❌",
            "✅" if Tier.ENTERPRISE in artifact.required_tiers else "❌",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Total P0 Artifacts: {len(P0_ARTIFACTS)}[/dim]")
    console.print()


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()
