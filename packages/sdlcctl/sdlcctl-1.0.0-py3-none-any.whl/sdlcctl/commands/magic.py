"""
=========================================================================
Magic Mode Command - Natural Language to Code Generation
SDLC Orchestrator - Sprint 52

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 Implementation
Authority: Backend Team + CTO Approved

Purpose:
- Convert natural language description to AppBlueprint
- Auto-detect business domain (restaurant, ecommerce, hrm, etc.)
- Support Vietnamese and English input
- Generate production-ready code with streaming

Usage:
    sdlcctl magic "Nhà hàng Phở 24 với menu và đặt bàn"
    sdlcctl magic "E-commerce store for phones" --domain ecommerce
    sdlcctl magic "HR management system" -y -o ./hr-app

References:
- docs/02-design/14-Technical-Specs/Vietnamese-Domain-Templates.md
=========================================================================
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.tree import Tree


# ============================================================================
# Console Utilities (shared with generate.py)
# ============================================================================


def _get_console() -> Console:
    """Get Rich console for output."""
    return Console()


def _echo(message: str = "") -> None:
    """Print message to console."""
    console = _get_console()
    console.print(message)


# ============================================================================
# Magic Mode Command
# ============================================================================


def magic_command(
    description: str = typer.Argument(
        ...,
        help="Natural language description of your app (Vietnamese or English)",
    ),
    lang: str = typer.Option(
        "auto",
        "--lang",
        "-l",
        help="Language: vi (Vietnamese), en (English), auto (detect)",
    ),
    domain: Optional[str] = typer.Option(
        None,
        "--domain",
        "-d",
        help="Business domain: restaurant, ecommerce, hrm, crm, inventory, education, healthcare",
    ),
    output: Path = typer.Option(
        Path("./generated"),
        "--output",
        "-o",
        help="Output directory for generated files",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help="Stream generation progress (default: true)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Preview blueprint without generating code",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files without confirmation",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed output",
    ),
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        envvar="SDLC_API_URL",
        help="API URL for streaming (default: http://localhost:8320/api/v1)",
    ),
) -> None:
    """
    Generate app from natural language description.

    Magic Mode converts your description into a complete app blueprint
    and generates production-ready code. Supports Vietnamese and English.

    Supported Domains:
        - restaurant: Nhà hàng, quán ăn, cafe
        - ecommerce: Cửa hàng online, bán hàng
        - hrm: Quản lý nhân sự, chấm công, lương
        - crm: Quản lý khách hàng, sales
        - inventory: Quản lý kho, tồn kho
        - education: Trường học, khóa học
        - healthcare: Bệnh viện, phòng khám

    Examples:

        # Vietnamese input (auto-detected)
        sdlcctl magic "Nhà hàng Phở 24 với menu và đặt bàn"

        # English input with explicit domain
        sdlcctl magic "E-commerce store for phones" --domain ecommerce

        # Skip confirmation
        sdlcctl magic "HR management system" -y -o ./hr-app

        # Preview blueprint only (no code generation)
        sdlcctl magic "Quán cà phê với đặt bàn online" --preview

        # Specify output directory
        sdlcctl magic "Hệ thống quản lý kho" -o ./warehouse-app
    """
    console = _get_console()

    # Delayed imports for faster CLI startup
    from ..lib.domain_detector import DomainDetector
    from ..lib.nlp_parser import NLPParser

    # Show banner
    console.print()
    console.print(
        Panel(
            "[bold magenta]🪄 Magic Mode[/bold magenta]\n"
            "[dim]Natural Language → Production Code[/dim]",
            border_style="magenta",
        )
    )
    console.print()

    # Step 1: Detect language
    detector = DomainDetector()
    detected_lang = lang if lang != "auto" else detector._detect_language(description.lower())
    console.print(f"🌐 Language: [cyan]{_lang_display(detected_lang)}[/cyan]")

    # Step 2: Detect domain
    if domain is None:
        domain_result = detector.detect(description, lang=detected_lang)
        domain = domain_result.domain
        confidence = domain_result.confidence
        matched = domain_result.matched_keywords

        console.print(
            f"🔍 Detected Domain: [cyan]{domain}[/cyan] "
            f"(confidence: {confidence:.0%})"
        )
        if verbose and matched:
            console.print(f"   Matched keywords: {', '.join(matched[:5])}")
    else:
        console.print(f"🏷️  Domain: [cyan]{domain}[/cyan] (specified)")

    # Step 3: Parse to blueprint
    parser = NLPParser(lang=detected_lang)
    blueprint = parser.parse(description, domain=domain)

    # Step 4: Show blueprint preview
    console.print()
    _show_blueprint_preview(console, blueprint, verbose)

    # Handle preview-only mode
    if preview:
        console.print()
        console.print("[dim]Preview mode: No code generated[/dim]")

        # Save blueprint to file
        blueprint_file = output.parent / f"{blueprint['name']}_blueprint.json"
        blueprint_file.parent.mkdir(parents=True, exist_ok=True)
        blueprint_file.write_text(
            json.dumps(blueprint, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        console.print(f"💾 Blueprint saved to: {blueprint_file}")
        raise typer.Exit(code=0)

    # Step 5: Confirm generation
    if not yes:
        console.print()
        if not Confirm.ask("❓ Proceed with generation?", default=True):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(code=0)

    # Step 6: Generate code
    console.print()

    # Save blueprint to temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as f:
        json.dump(blueprint, f, ensure_ascii=False, indent=2)
        blueprint_path = Path(f.name)

    try:
        if stream:
            # Use streaming generation
            _run_streaming_magic(
                blueprint=blueprint,
                output=output,
                force=force,
                api_url=api_url or "http://localhost:8320/api/v1",
                verbose=verbose,
                console=console,
            )
        else:
            # Use local generation (fallback)
            from .generate import generate_command

            generate_command(
                blueprint_path=blueprint_path,
                output=output,
                preview=False,
                force=force,
                validate_only=False,
                verbose=verbose,
                stream=False,
                resume=None,
                api_url=None,
            )
    finally:
        # Cleanup temp file
        blueprint_path.unlink(missing_ok=True)


# ============================================================================
# Helper Functions
# ============================================================================


def _lang_display(lang: str) -> str:
    """Get display name for language code."""
    return {
        "vi": "Vietnamese (Tiếng Việt)",
        "en": "English",
    }.get(lang, lang)


def _show_blueprint_preview(
    console: Console,
    blueprint: dict,
    verbose: bool,
) -> None:
    """Show blueprint preview in a formatted way."""
    # Blueprint summary table
    table = Table(
        title="📋 Generated Blueprint",
        show_header=True,
        border_style="blue",
    )
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value")

    table.add_row("Name", blueprint.get("name", "N/A"))
    table.add_row("Version", blueprint.get("version", "N/A"))
    table.add_row("Domain", blueprint.get("business_domain", "general"))

    modules = blueprint.get("modules", [])
    table.add_row("Modules", str(len(modules)))

    total_entities = sum(len(m.get("entities", [])) for m in modules)
    table.add_row("Total Entities", str(total_entities))

    console.print(table)

    # Module tree
    if modules:
        console.print()
        tree = Tree("[bold]📦 Modules[/bold]")

        for module in modules:
            module_branch = tree.add(
                f"[blue]{module['name']}[/blue] "
                f"[dim]({len(module.get('entities', []))} entities)[/dim]"
            )

            # Show entities
            for entity in module.get("entities", []):
                entity_name = entity.get("name", "Unknown")
                field_count = len(entity.get("fields", []))
                entity_branch = module_branch.add(
                    f"[cyan]{entity_name}[/cyan] "
                    f"[dim]({field_count} fields)[/dim]"
                )

                # Show fields if verbose
                if verbose:
                    for field in entity.get("fields", []):
                        field_name = field.get("name", "unknown")
                        field_type = field.get("type", "string")
                        required = "required" if field.get("required") else "optional"
                        entity_branch.add(
                            f"[dim]{field_name}: {field_type} ({required})[/dim]"
                        )

            # Show operations
            operations = module.get("operations", [])
            if operations and verbose:
                for op in operations:
                    module_branch.add(
                        f"[yellow]⚡ {op.get('name', 'unknown')}[/yellow] "
                        f"[dim]({op.get('type', 'unknown')})[/dim]"
                    )

        console.print(tree)


def _run_streaming_magic(
    blueprint: dict,
    output: Path,
    force: bool,
    api_url: str,
    verbose: bool,
    console: Console,
) -> None:
    """
    Run streaming generation for magic mode.

    Args:
        blueprint: Generated AppBlueprint dictionary
        output: Output directory
        force: Force overwrite
        api_url: Backend API URL
        verbose: Show detailed output
        console: Rich console for output
    """
    from ..lib.sse_client import SSEStreamClient
    from ..lib.progress import StreamingProgress

    # Check output directory
    if output.exists() and not force:
        existing_files = list(output.rglob("*"))
        if existing_files:
            console.print()
            console.print(f"⚠️  Output directory '{output}' already contains files.")
            if not Confirm.ask("Overwrite existing files?", default=False):
                console.print("[yellow]Aborted.[/yellow]")
                raise typer.Exit(code=0)

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Initialize SSE client and progress display
    client = SSEStreamClient(api_url=api_url)
    progress = StreamingProgress(console)

    console.print()
    console.print("🚀 [bold]Starting code generation...[/bold]")
    console.print()

    async def stream_and_write():
        """Async function to stream and write files."""
        files_written = 0
        session_id: Optional[str] = None

        try:
            async for event in client.stream_generate(blueprint=blueprint):
                # Handle event with progress display
                progress.handle_event(event)

                # Track session ID
                if hasattr(event, "session_id"):
                    session_id = event.session_id

                # Write file to disk when generated
                if event.type == "file_generated":
                    file_path = output / event.path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(event.content, encoding="utf-8")
                    files_written += 1

                # Handle completion
                if event.type == "completed":
                    progress.show_file_tree()
                    console.print()
                    console.print(
                        Panel(
                            f"[bold green]✅ Magic complete![/bold green]\n\n"
                            f"[dim]Output directory:[/dim] {output.absolute()}\n"
                            f"[dim]Files generated:[/dim] {event.total_files}\n"
                            f"[dim]Total lines:[/dim] {event.total_lines}\n"
                            f"[dim]Duration:[/dim] {event.duration_ms / 1000:.1f}s\n\n"
                            f"[yellow]Next steps:[/yellow]\n"
                            f"  1. cd {output}\n"
                            f"  2. pip install -r requirements.txt\n"
                            f"  3. docker-compose up -d db\n"
                            f"  4. alembic upgrade head\n"
                            f"  5. uvicorn app.main:app --reload",
                            title="🪄 Magic Complete",
                            border_style="green",
                        )
                    )
                    return

                # Handle error
                if event.type == "error":
                    console.print()
                    console.print(f"[red]❌ Generation failed: {event.message}[/red]")
                    if event.recovery_id:
                        console.print(
                            f"[yellow]💡 Resume with: "
                            f"sdlcctl generate --resume {event.recovery_id}[/yellow]"
                        )
                    raise typer.Exit(code=1)

        except Exception as e:
            console.print()
            console.print(f"[red]❌ Streaming error: {e}[/red]")
            if session_id:
                console.print(
                    f"[yellow]💡 Resume with: "
                    f"sdlcctl generate --resume {session_id}[/yellow]"
                )
            raise typer.Exit(code=1)

    # Run async event loop
    try:
        asyncio.run(stream_and_write())
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]⚠️  Generation interrupted by user[/yellow]")
        console.print("[dim]💡 Files written so far are saved in the output directory[/dim]")
        raise typer.Exit(code=130)
