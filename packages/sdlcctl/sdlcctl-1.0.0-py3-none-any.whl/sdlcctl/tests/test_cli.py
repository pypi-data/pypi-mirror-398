"""Tests for CLI commands."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from sdlcctl.cli import app
from sdlcctl.validation.tier import STAGE_NAMES, Tier


runner = CliRunner()


class TestValidateCommand:
    """Tests for the validate command."""

    @pytest.fixture
    def compliant_project(self):
        """Create a LITE-compliant project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            # Create minimal LITE structure
            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}: {stage_name}\n\n"
                    f"This is the entry point for Stage {stage_id}. "
                    f"It contains important documentation for this stage."
                )

            yield project_root

    @pytest.fixture
    def empty_project(self):
        """Create an empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_validate_compliant_project(self, compliant_project):
        """Test validate command on compliant project."""
        result = runner.invoke(
            app, ["validate", "--path", str(compliant_project), "--tier", "lite"]
        )
        assert result.exit_code == 0
        assert "compliant" in result.stdout.lower() or "passed" in result.stdout.lower()

    def test_validate_empty_project(self, empty_project):
        """Test validate command on empty project."""
        result = runner.invoke(
            app, ["validate", "--path", str(empty_project), "--tier", "lite"]
        )
        assert result.exit_code == 1  # Non-compliant

    def test_validate_json_format(self, compliant_project):
        """Test validate command with JSON output."""
        result = runner.invoke(
            app,
            [
                "validate",
                "--path", str(compliant_project),
                "--tier", "lite",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0

        output = json.loads(result.stdout)
        assert "violations" in output
        assert "summary" in output
        assert "errors" in output["summary"]

    def test_validate_summary_format(self, compliant_project):
        """Test validate command with summary output."""
        result = runner.invoke(
            app,
            [
                "validate",
                "--path", str(compliant_project),
                "--tier", "lite",
                "--format", "summary",
            ],
        )
        assert result.exit_code == 0
        assert "PASS" in result.stdout or "FAIL" in result.stdout

    def test_validate_strict_mode(self, compliant_project):
        """Test validate command in strict mode."""
        result = runner.invoke(
            app,
            [
                "validate",
                "--path", str(compliant_project),
                "--tier", "lite",
                "--strict",
            ],
        )
        # Strict mode should still pass for compliant project
        assert result.exit_code == 0

    def test_validate_with_team_size(self, compliant_project):
        """Test validate command with team size auto-detection."""
        result = runner.invoke(
            app,
            [
                "validate",
                "--path", str(compliant_project),
                "--team-size", "2",  # Should auto-detect LITE tier
            ],
        )
        assert result.exit_code == 0

    def test_validate_invalid_tier(self, compliant_project):
        """Test validate command with invalid tier."""
        result = runner.invoke(
            app,
            [
                "validate",
                "--path", str(compliant_project),
                "--tier", "invalid",
            ],
        )
        assert result.exit_code != 0

    def test_validate_nonexistent_path(self):
        """Test validate command with non-existent path."""
        result = runner.invoke(
            app,
            [
                "validate",
                "--path", "/nonexistent/path/that/does/not/exist",
                "--tier", "lite",
            ],
        )
        assert result.exit_code != 0


class TestFixCommand:
    """Tests for the fix command."""

    @pytest.fixture
    def empty_project(self):
        """Create an empty project for fixing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def partial_project(self):
        """Create a partial project missing some stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"
            docs_root.mkdir()

            # Create only first 2 stages
            for stage_id in ["00", "01"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir()
                (stage_path / "README.md").write_text(f"# Stage {stage_id}\n\nContent here.")

            yield project_root

    def test_fix_dry_run(self, empty_project):
        """Test fix command in dry-run mode."""
        result = runner.invoke(
            app,
            [
                "fix",
                "--path", str(empty_project),
                "--tier", "lite",
                "--dry-run",
                "--no-interactive",
            ],
        )
        # Should show what would be fixed without making changes
        assert "would" in result.stdout.lower() or "dry" in result.stdout.lower() or result.exit_code == 0

    def test_fix_stages_only(self, partial_project):
        """Test fix command creating only stages."""
        result = runner.invoke(
            app,
            [
                "fix",
                "--path", str(partial_project),
                "--tier", "lite",
                "--stages",
                "--no-p0",
                "--no-interactive",
            ],
        )
        # Should create missing stages
        assert result.exit_code == 0

        # Verify stages were created
        docs_root = partial_project / "docs"
        for stage_id in ["00", "01", "02", "03"]:
            stage_name = STAGE_NAMES[stage_id]
            assert (docs_root / stage_name).exists()

    def test_fix_p0_only(self, partial_project):
        """Test fix command creating only P0 artifacts."""
        result = runner.invoke(
            app,
            [
                "fix",
                "--path", str(partial_project),
                "--tier", "lite",
                "--p0",
                "--no-stages",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0

    def test_fix_all(self, empty_project):
        """Test fix command creating everything."""
        result = runner.invoke(
            app,
            [
                "fix",
                "--path", str(empty_project),
                "--tier", "lite",
                "--no-interactive",
            ],
        )
        # Should create docs folder and stages
        assert result.exit_code == 0

    def test_fix_naming(self, partial_project):
        """Test fix command with naming corrections."""
        # Create a stage with wrong naming
        wrong_name = partial_project / "docs" / "02-Design"
        wrong_name.mkdir()
        (wrong_name / "README.md").write_text("# Design\n\nContent.")

        result = runner.invoke(
            app,
            [
                "fix",
                "--path", str(partial_project),
                "--tier", "lite",
                "--naming",
                "--no-interactive",
            ],
        )
        # Fix should handle naming issues
        assert result.exit_code == 0


class TestInitCommand:
    """Tests for the init command."""

    @pytest.fixture
    def empty_dir(self):
        """Create an empty directory for initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_init_lite_tier(self, empty_dir):
        """Test init command for LITE tier."""
        result = runner.invoke(
            app,
            [
                "init",
                "--path", str(empty_dir),
                "--tier", "lite",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0

        # Verify LITE structure created
        docs_root = empty_dir / "docs"
        assert docs_root.exists()
        for stage_id in ["00", "01", "02", "03"]:
            stage_name = STAGE_NAMES[stage_id]
            assert (docs_root / stage_name).exists()

    def test_init_standard_tier(self, empty_dir):
        """Test init command for STANDARD tier."""
        result = runner.invoke(
            app,
            [
                "init",
                "--path", str(empty_dir),
                "--tier", "standard",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0

        # Verify STANDARD structure created (6 stages)
        docs_root = empty_dir / "docs"
        for stage_id in ["00", "01", "02", "03", "04", "05"]:
            stage_name = STAGE_NAMES[stage_id]
            assert (docs_root / stage_name).exists()

    def test_init_professional_tier(self, empty_dir):
        """Test init command for PROFESSIONAL tier."""
        result = runner.invoke(
            app,
            [
                "init",
                "--path", str(empty_dir),
                "--tier", "professional",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0

        # Verify PROFESSIONAL structure (10 stages)
        docs_root = empty_dir / "docs"
        for stage_id in ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]:
            stage_name = STAGE_NAMES[stage_id]
            assert (docs_root / stage_name).exists()

    def test_init_with_team_size(self, empty_dir):
        """Test init command with team size auto-detection."""
        result = runner.invoke(
            app,
            [
                "init",
                "--path", str(empty_dir),
                "--team-size", "5",  # Should auto-select STANDARD
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0

    def test_init_existing_docs(self, empty_dir):
        """Test init command when docs folder already exists."""
        # Create existing docs
        docs_root = empty_dir / "docs"
        docs_root.mkdir()
        (docs_root / "existing.md").write_text("# Existing\n\nExisting content.")

        result = runner.invoke(
            app,
            [
                "init",
                "--path", str(empty_dir),
                "--tier", "lite",
                "--no-interactive",
            ],
        )
        # Should handle gracefully - may warn but should still work
        # Existing files should be preserved
        assert (docs_root / "existing.md").exists()

    def test_init_creates_readme_files(self, empty_dir):
        """Test init command creates README files in stages."""
        result = runner.invoke(
            app,
            [
                "init",
                "--path", str(empty_dir),
                "--tier", "lite",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0

        # Check README files are created
        docs_root = empty_dir / "docs"
        for stage_id in ["00", "01", "02", "03"]:
            stage_name = STAGE_NAMES[stage_id]
            readme = docs_root / stage_name / "README.md"
            assert readme.exists(), f"README.md should exist in {stage_name}"


class TestReportCommand:
    """Tests for the report command."""

    @pytest.fixture
    def compliant_project(self):
        """Create a compliant project for reporting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}: {stage_name}\n\n"
                    f"This is the documentation for stage {stage_id}."
                )

            yield project_root

    def test_report_markdown_format(self, compliant_project):
        """Test report command with Markdown output."""
        result = runner.invoke(
            app,
            [
                "report",
                "--path", str(compliant_project),
                "--tier", "lite",
                "--format", "markdown",
            ],
        )
        assert result.exit_code == 0
        assert "#" in result.stdout  # Markdown headers

    def test_report_json_format(self, compliant_project):
        """Test report command with JSON output."""
        result = runner.invoke(
            app,
            [
                "report",
                "--path", str(compliant_project),
                "--tier", "lite",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        # Should be valid JSON
        try:
            output = json.loads(result.stdout)
            assert "is_compliant" in output or "compliance" in str(output).lower()
        except json.JSONDecodeError:
            pass  # May have additional output

    def test_report_html_format(self, compliant_project):
        """Test report command with HTML output."""
        result = runner.invoke(
            app,
            [
                "report",
                "--path", str(compliant_project),
                "--tier", "lite",
                "--format", "html",
            ],
        )
        assert result.exit_code == 0
        assert "<html" in result.stdout.lower() or "html" in result.stdout.lower()

    def test_report_to_file(self, compliant_project):
        """Test report command writing to file."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            output_path = f.name

        result = runner.invoke(
            app,
            [
                "report",
                "--path", str(compliant_project),
                "--tier", "lite",
                "--format", "markdown",
                "--output", output_path,
            ],
        )
        assert result.exit_code == 0
        assert Path(output_path).exists()
        content = Path(output_path).read_text()
        assert len(content) > 0


class TestInfoCommands:
    """Tests for info commands (tiers, stages, p0)."""

    def test_tiers_command(self):
        """Test tiers info command."""
        result = runner.invoke(app, ["tiers"])
        assert result.exit_code == 0
        assert "lite" in result.stdout.lower()
        assert "standard" in result.stdout.lower()
        assert "professional" in result.stdout.lower()
        assert "enterprise" in result.stdout.lower()

    def test_stages_command(self):
        """Test stages info command."""
        result = runner.invoke(app, ["stages"])
        assert result.exit_code == 0
        assert "00" in result.stdout
        assert "foundation" in result.stdout.lower()

    def test_p0_command(self):
        """Test p0 info command."""
        result = runner.invoke(app, ["p0"])
        assert result.exit_code == 0
        assert "artifact" in result.stdout.lower() or "p0" in result.stdout.lower()

    def test_p0_command_shows_all_artifacts(self):
        """Test p0 info command shows all artifacts."""
        result = runner.invoke(app, ["p0"])
        assert result.exit_code == 0
        # Should list artifacts with count
        assert "Total P0 Artifacts: 15" in result.stdout


class TestCLIHelp:
    """Tests for CLI help functionality."""

    def test_main_help(self):
        """Test main CLI help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "validate" in result.stdout
        assert "fix" in result.stdout
        assert "init" in result.stdout
        assert "report" in result.stdout

    def test_validate_help(self):
        """Test validate command help."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout
        assert "--tier" in result.stdout

    def test_fix_help(self):
        """Test fix command help."""
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout

    def test_init_help(self):
        """Test init command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--tier" in result.stdout

    def test_report_help(self):
        """Test report command help."""
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.stdout
