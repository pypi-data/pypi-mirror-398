"""
=========================================================================
Generate Command - Generate backend scaffold from AppBlueprint.
SDLC Orchestrator - Sprint 46 + Sprint 52 Enhancement

Version: 2.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 CLI Streaming
Authority: Backend Team + CTO Approved

Purpose:
- Generate FastAPI backend scaffold from AppBlueprint (Sprint 46)
- Stream generation progress via SSE (Sprint 52)
- Resume interrupted generation sessions (Sprint 52)

Usage:
    sdlcctl generate blueprint.json --output ./my-app
    sdlcctl generate blueprint.yaml -o ./my-app --preview
    sdlcctl generate blueprint.json -o ./my-app --force
    sdlcctl generate blueprint.json -o ./my-app --stream  # Sprint 52
    sdlcctl generate --resume SESSION_ID -o ./my-app      # Sprint 52

References:
- docs/02-design/14-Technical-Specs/IR-Processor-Specification.md
- docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
=========================================================================
"""

import asyncio
import json
import io
import os
import sys
import contextvars
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree


_ECHO_STREAM: contextvars.ContextVar[Optional[io.TextIOBase]] = contextvars.ContextVar(
    "SDLCCTL_ECHO_STREAM", default=None
)


def _get_echo_stream() -> io.TextIOBase:
    stream = _ECHO_STREAM.get()
    return stream if stream is not None else sys.stdout


def _is_click_captured_stream(stream: io.TextIOBase) -> bool:
    stdout_buffer = getattr(stream, "buffer", None)
    return isinstance(stdout_buffer, io.BytesIO)


def _is_click_captured_stdout() -> bool:
    """Return True when Click/Typer CliRunner has replaced sys.stdout.

    Click's CliRunner isolation uses an in-memory BytesIO as the underlying
    buffer. Relying on pytest env vars is not safe because CliRunner can run
    with a sanitized environment.
    """

    return _is_click_captured_stream(sys.stdout)


def _get_console() -> Console:
    # Bind to the current sys.stdout (important for Click isolation).
    return Console(file=_get_echo_stream())


def _use_rich_output() -> bool:
    # Rich live rendering and some Rich components can interact poorly with
    # Click/Typer's captured stdout in tests and other non-TTY contexts.
    # Keep Rich UX for real terminal usage only.
    if _is_click_captured_stream(_get_echo_stream()):
        return False
    stream = _get_echo_stream()
    return hasattr(stream, "isatty") and bool(stream.isatty())


def _echo(message: str = "") -> None:
    """Print message in a capture-safe way."""
    stream = _get_echo_stream()
    if _use_rich_output():
        _get_console().print(message)
    else:
        # Write directly to the current stdout stream.
        # This avoids Click/Typer echo helpers that can interact poorly with
        # CliRunner's in-memory capture streams in combined test runs.
        if message.endswith("\n"):
            stream.write(message)
        else:
            stream.write(message + "\n")


def generate_command(
    blueprint_path: Optional[Path] = typer.Argument(
        None,
        help="Path to AppBlueprint file (JSON or YAML)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path = typer.Option(
        Path("./generated"),
        "--output",
        "-o",
        help="Output directory for generated files",
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Preview files without writing to disk",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files without confirmation",
    ),
    validate_only: bool = typer.Option(
        False,
        "--validate",
        "-v",
        help="Only validate the blueprint without generating",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed output",
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        "-s",
        help="Stream generation progress via SSE (Sprint 52)",
    ),
    resume: Optional[str] = typer.Option(
        None,
        "--resume",
        "-r",
        help="Resume from a previous session ID (Sprint 52)",
    ),
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        envvar="SDLC_API_URL",
        help="API URL for streaming (default: http://localhost:8320/api/v1)",
    ),
) -> None:
    """
    Generate backend scaffold from AppBlueprint.

    Takes an AppBlueprint specification file (JSON/YAML) and generates
    a complete FastAPI backend scaffold with:

    - SQLAlchemy models
    - Pydantic schemas
    - CRUD API endpoints
    - Service layer
    - Docker configuration
    - Project structure

    Examples:

        # Generate from JSON blueprint (local mode)
        sdlcctl generate my-app.json -o ./output

        # Preview without writing files
        sdlcctl generate my-app.yaml --preview

        # Validate blueprint only
        sdlcctl generate my-app.json --validate

        # Force overwrite existing files
        sdlcctl generate my-app.json -o ./output --force

        # Stream generation via SSE (Sprint 52)
        sdlcctl generate my-app.json -o ./output --stream

        # Resume interrupted session (Sprint 52)
        sdlcctl generate --resume SESSION_ID -o ./output
    """
    captured_stdout = sys.stdout
    captured_stderr = sys.stderr
    captured_is_click = _is_click_captured_stream(captured_stdout)
    token = _ECHO_STREAM.set(captured_stdout)
    use_rich = _use_rich_output()

    try:
        # Handle streaming mode (Sprint 52)
        if stream or resume:
            _run_streaming_generation(
                blueprint_path=blueprint_path,
                output=output,
                force=force,
                resume_session=resume,
                api_url=api_url or "http://localhost:8320/api/v1",
                verbose=verbose,
            )
            return

        # Validate arguments for local mode
        if blueprint_path is None:
            _echo("❌ Blueprint path is required for local generation")
            _echo("Use --stream flag or provide a blueprint file")
            raise typer.Exit(code=1)

        # Load blueprint
        blueprint = _load_blueprint(blueprint_path)

        # Import IR processors (delayed import for faster CLI startup)
        from app.services.codegen.ir import BundleBuilder, IRValidator

        # Get template directory
        template_dir = _get_template_dir()

        # Validate blueprint
        _echo()
        _echo("🔍 Validating blueprint...")

        validator = IRValidator()
        validation_result = validator.validate_app_blueprint(blueprint)

        if not validation_result.valid:
            _show_validation_errors(validation_result)
            raise typer.Exit(code=1)

        _echo("✅ Blueprint is valid")

        if validate_only:
            _show_validation_summary(validation_result)
            raise typer.Exit(code=0)

        # Get normalized blueprint
        normalized = validation_result.normalized_ir

        # Build bundle
        _echo()
        _echo("🔨 Generating backend scaffold...")

        builder = BundleBuilder(template_dir=template_dir)

        # Rich live rendering (Progress/Live) can interact poorly with Click's
        # captured stdout in tests and other non-TTY contexts.
        if use_rich:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=_get_console(),
            ) as progress:
                task = progress.add_task("Processing...", total=None)
                bundle = builder.build(normalized)
                progress.update(task, completed=True)
        else:
            bundle = builder.build(normalized)

        if not bundle.success:
            _echo("❌ Generation failed:")
            for error in bundle.errors:
                _echo(f"  • {error}")
            raise typer.Exit(code=1)

        # Show results
        _echo(f"✅ Generated {bundle.file_count} files ({bundle.total_lines} lines)")

        if preview:
            _show_preview(bundle, verbose)
            raise typer.Exit(code=0)

        # Write files
        _write_files(bundle, output, force, verbose)

        # Show success message
        _echo()
        if use_rich:
            _get_console().print(
                Panel(
                    f"[bold green]✅ Backend scaffold generated successfully![/bold green]\n\n"
                    f"[dim]Output directory:[/dim] {output.absolute()}\n"
                    f"[dim]Files generated:[/dim] {bundle.file_count}\n"
                    f"[dim]Total lines:[/dim] {bundle.total_lines}\n\n"
                    f"[yellow]Next steps:[/yellow]\n"
                    f"  1. cd {output}\n"
                    f"  2. pip install -r requirements.txt\n"
                    f"  3. docker-compose up -d db\n"
                    f"  4. alembic upgrade head\n"
                    f"  5. uvicorn app.main:app --reload",
                    title="Generation Complete",
                    border_style="green",
                )
            )
        else:
            _echo("✅ Backend scaffold generated successfully!")
            _echo(f"Output directory: {output.absolute()}")
            _echo(f"Files generated: {bundle.file_count}")
            _echo(f"Total lines: {bundle.total_lines}")

    except (typer.Exit, typer.Abort):
        raise
    except FileNotFoundError as e:
        _echo(f"❌ File not found: {e}")
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        _echo(f"❌ Invalid JSON: {e}")
        raise typer.Exit(code=1)
    except ImportError as e:
        _echo(f"❌ Import error: {e}")
        _echo("Make sure you're running from the backend directory")
        raise typer.Exit(code=1)
    except Exception as e:
        _echo(f"❌ Error: {e}")
        if verbose:
            if _use_rich_output():
                _get_console().print_exception()
        raise typer.Exit(code=1)
    finally:
        # Ensure Click's captured streams remain intact.
        # Some libraries/tools may temporarily replace sys.stdout/sys.stderr;
        # if that happens under CliRunner isolation, the original wrapper can
        # be garbage-collected which closes the underlying BytesIO and causes
        # Click to crash when reading captured output.
        if captured_is_click:
            if sys.stdout is not captured_stdout:
                sys.stdout = captured_stdout
            if sys.stderr is not captured_stderr:
                sys.stderr = captured_stderr
        _ECHO_STREAM.reset(token)


def _run_streaming_generation(
    blueprint_path: Optional[Path],
    output: Path,
    force: bool,
    resume_session: Optional[str],
    api_url: str,
    verbose: bool,
) -> None:
    """
    Run streaming code generation via SSE.

    Sprint 52: CLI Streaming + Session Resume

    Args:
        blueprint_path: Path to blueprint file (optional if resuming)
        output: Output directory for generated files
        force: Overwrite existing files without confirmation
        resume_session: Session ID to resume from
        api_url: Backend API URL
        verbose: Show detailed output
    """
    # Delayed import for faster CLI startup
    from ..lib.sse_client import SSEStreamClient
    from ..lib.progress import StreamingProgress

    console = _get_console()

    # Validate arguments
    if resume_session is None and blueprint_path is None:
        _echo("❌ Either blueprint path or --resume session ID is required")
        raise typer.Exit(code=1)

    # Load blueprint if provided
    blueprint: dict = {}
    if blueprint_path is not None:
        blueprint = _load_blueprint(blueprint_path)
        _echo(f"📋 Loaded blueprint: {blueprint.get('name', 'unknown')}")

    # Check output directory
    if output.exists() and not force:
        existing_files = list(output.rglob("*"))
        if existing_files:
            _echo()
            _echo(f"⚠️  Output directory '{output}' already contains files.")
            confirm = typer.confirm("Overwrite existing files?", default=False)
            if not confirm:
                _echo("Aborted.")
                raise typer.Exit(code=0)

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Initialize SSE client and progress display
    client = SSEStreamClient(api_url=api_url)
    progress = StreamingProgress(console)

    # Run streaming generation
    _echo()
    if resume_session:
        _echo(f"🔄 Resuming session: {resume_session}")
    else:
        _echo("🚀 Starting streaming generation...")

    async def stream_and_write():
        """Async function to stream and write files."""
        files_written = 0
        session_id: Optional[str] = None

        try:
            async for event in client.stream_generate(
                blueprint=blueprint,
                session_id=resume_session,
            ):
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
                    _echo()
                    if _use_rich_output():
                        console.print(
                            Panel(
                                f"[bold green]✅ Generation complete![/bold green]\n\n"
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
                                title="Generation Complete",
                                border_style="green",
                            )
                        )
                    else:
                        _echo("✅ Generation complete!")
                        _echo(f"Output directory: {output.absolute()}")
                        _echo(f"Files generated: {event.total_files}")
                        _echo(f"Total lines: {event.total_lines}")
                        _echo(f"Duration: {event.duration_ms / 1000:.1f}s")
                    return

                # Handle error
                if event.type == "error":
                    _echo()
                    _echo(f"❌ Generation failed: {event.message}")
                    if event.recovery_id:
                        _echo(f"💡 Resume with: sdlcctl generate --resume {event.recovery_id}")
                    raise typer.Exit(code=1)

        except Exception as e:
            _echo()
            _echo(f"❌ Streaming error: {e}")
            if session_id:
                _echo(f"💡 Resume with: sdlcctl generate --resume {session_id}")
            raise typer.Exit(code=1)

    # Run async event loop
    try:
        asyncio.run(stream_and_write())
    except KeyboardInterrupt:
        _echo()
        _echo("⚠️  Generation interrupted by user")
        _echo("💡 Files written so far are saved in the output directory")
        raise typer.Exit(code=130)


def _load_blueprint(path: Path) -> dict:
    """Load blueprint from JSON or YAML file."""
    content = path.read_text(encoding="utf-8")

    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml

            return yaml.safe_load(content)
        except ImportError:
            _echo("❌ PyYAML not installed. Install with: pip install pyyaml")
            raise typer.Exit(code=1)
    else:
        return json.loads(content)


def _get_template_dir() -> Path:
    """Get the template directory path."""
    # Try relative to this file first
    base = Path(__file__).parent.parent.parent
    template_dir = base / "app" / "services" / "codegen" / "templates"

    if template_dir.exists():
        return template_dir

    # Try from current working directory
    cwd_template = Path.cwd() / "app" / "services" / "codegen" / "templates"
    if cwd_template.exists():
        return cwd_template

    # Fallback to package path
    try:
        import app.services.codegen.templates

        return Path(app.services.codegen.templates.__file__).parent
    except ImportError:
        pass

    _echo("❌ Template directory not found")
    raise typer.Exit(code=1)


def _show_validation_errors(result) -> None:
    """Show validation errors in a formatted way."""
    _echo()
    _echo("❌ Blueprint validation failed:")

    errors = [i for i in result.issues if i.severity == "error"]
    warnings = [i for i in result.issues if i.severity == "warning"]

    if errors:
        _echo()
        _echo("Errors:")
        for issue in errors:
            _echo(f"  ✗ {issue.message}")
            if issue.path:
                _echo(f"    Path: {issue.path}")

    if warnings:
        _echo()
        _echo("Warnings:")
        for issue in warnings:
            _echo(f"  ! {issue.message}")


def _show_validation_summary(result) -> None:
    """Show validation summary."""
    blueprint = result.normalized_ir

    _echo()
    if _use_rich_output():
        table = Table(title="Blueprint Summary", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Name", blueprint.get("name", "N/A"))
        table.add_row("Version", blueprint.get("version", "N/A"))
        table.add_row("Business Domain", blueprint.get("business_domain", "general"))

        modules = blueprint.get("modules", [])
        table.add_row("Modules", str(len(modules)))

        total_entities = sum(len(m.get("entities", [])) for m in modules)
        table.add_row("Total Entities", str(total_entities))

        _get_console().print(table)
    else:
        modules = blueprint.get("modules", [])
        total_entities = sum(len(m.get("entities", [])) for m in modules)
        _echo(f"Name: {blueprint.get('name', 'N/A')}")
        _echo(f"Version: {blueprint.get('version', 'N/A')}")
        _echo(f"Business Domain: {blueprint.get('business_domain', 'general')}")
        _echo(f"Modules: {len(modules)}")
        _echo(f"Total Entities: {total_entities}")

    # Show modules
    if modules:
        _echo()
        _echo("Modules:")
        for module in modules:
            entities = module.get("entities", [])
            operations = module.get("operations", [])
            _echo(
                f"  • {module['name']}: {len(entities)} entities, {len(operations)} operations"
            )


def _show_preview(bundle, verbose: bool) -> None:
    """Show preview of generated files."""
    _echo()
    _echo("📋 Preview of generated files:")
    _echo()

    if _use_rich_output():
        # Build file tree
        tree = Tree(f"[bold]{bundle.app_name}[/bold]")
        paths_by_dir: dict[str, list] = {}

        for file in bundle.files:
            parts = Path(file.path).parts
            dir_path = "/".join(parts[:-1]) if len(parts) > 1 else ""
            if dir_path not in paths_by_dir:
                paths_by_dir[dir_path] = []
            paths_by_dir[dir_path].append(file)

        # Sort directories
        for dir_path in sorted(paths_by_dir.keys()):
            if dir_path:
                branch = tree.add(f"[blue]{dir_path}/[/blue]")
            else:
                branch = tree

            for file in sorted(paths_by_dir[dir_path], key=lambda f: f.path):
                filename = Path(file.path).name
                lines = len(file.content.split("\n"))
                lang = file.language or "text"
                branch.add(f"{filename} [dim]({lines} lines, {lang})[/dim]")

        _get_console().print(tree)
        _echo()
        _echo(f"Total: {bundle.file_count} files, {bundle.total_lines} lines")
    else:
        _echo(bundle.app_name)
        for file in sorted(bundle.files, key=lambda f: f.path):
            lines = len(file.content.split("\n"))
            lang = file.language or "text"
            _echo(f"- {file.path} ({lines} lines, {lang})")
        _echo()
        _echo(f"Total: {bundle.file_count} files, {bundle.total_lines} lines")

    if verbose:
        _echo()
        if _use_rich_output():
            _get_console().print("[bold]File details:[/bold]")
            table = Table(show_header=True)
            table.add_column("Path", style="cyan")
            table.add_column("Lines", justify="right")
            table.add_column("Language")

            for file in sorted(bundle.files, key=lambda f: f.path):
                lines = len(file.content.split("\n"))
                table.add_row(file.path, str(lines), file.language or "text")

            _get_console().print(table)
        else:
            _echo("File details:")
            for file in sorted(bundle.files, key=lambda f: f.path):
                lines = len(file.content.split("\n"))
                _echo(f"- {file.path}: {lines} lines ({file.language or 'text'})")


def _write_files(bundle, output: Path, force: bool, verbose: bool) -> None:
    """Write generated files to disk."""
    # Check if output exists
    if output.exists() and not force:
        existing_files = list(output.rglob("*"))
        if existing_files:
            _echo()
            _echo(f"⚠️  Output directory '{output}' already contains files.")
            confirm = typer.confirm("Overwrite existing files?", default=False)
            if not confirm:
                _echo("Aborted.")
                raise typer.Exit(code=0)

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Write files
    _echo()
    _echo(f"📝 Writing files to {output}...")

    written = 0
    for file in bundle.files:
        file_path = output / file.path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file.content, encoding="utf-8")
        written += 1

        if verbose:
            _echo(f"  ✓ {file.path}")

    _echo(f"✅ Written {written} files")
