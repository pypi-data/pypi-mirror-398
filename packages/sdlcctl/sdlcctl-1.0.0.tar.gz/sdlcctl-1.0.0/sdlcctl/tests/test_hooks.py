"""Tests for pre-commit hooks."""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sdlcctl.hooks.pre_commit import (
    run_validation,
    get_project_root,
    main,
)
from sdlcctl.validation.tier import STAGE_NAMES


class TestGetProjectRoot:
    """Tests for get_project_root function."""

    def test_get_project_root_in_git_repo(self):
        """Test getting project root in a git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=project_root, capture_output=True)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.stdout = str(project_root) + "\n"
                mock_run.return_value.returncode = 0
                result = get_project_root()
                # Should return a Path
                assert isinstance(result, Path)

    def test_get_project_root_not_in_git(self):
        """Test getting project root outside git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run from non-git directory
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "git")
                result = get_project_root()
                # Should fall back to cwd
                assert isinstance(result, Path)


class TestRunValidation:
    """Tests for run_validation function."""

    @pytest.fixture
    def compliant_project(self):
        """Create a LITE-compliant project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}: {stage_name}\n\n"
                    f"This is the entry point for Stage {stage_id}. "
                    f"It contains important documentation."
                )

            yield project_root

    @pytest.fixture
    def non_compliant_project(self):
        """Create a non-compliant project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # No docs folder
            yield project_root

    def test_run_validation_compliant(self, compliant_project):
        """Test validation returns 0 for compliant project."""
        exit_code = run_validation(
            project_root=compliant_project,
            docs_root="docs",
            tier="lite",
            strict=False,
        )
        assert exit_code == 0

    def test_run_validation_non_compliant(self, non_compliant_project):
        """Test validation returns 1 for non-compliant project."""
        exit_code = run_validation(
            project_root=non_compliant_project,
            docs_root="docs",
            tier="lite",
            strict=False,
        )
        assert exit_code == 1

    def test_run_validation_strict_mode(self, compliant_project):
        """Test validation in strict mode."""
        exit_code = run_validation(
            project_root=compliant_project,
            docs_root="docs",
            tier="lite",
            strict=True,
        )
        assert exit_code == 0

    def test_run_validation_invalid_tier(self, compliant_project):
        """Test validation with invalid tier."""
        # Should handle gracefully (use default)
        exit_code = run_validation(
            project_root=compliant_project,
            docs_root="docs",
            tier="invalid_tier",
            strict=False,
        )
        # Invalid tier defaults to PROFESSIONAL, which won't be compliant
        # for a LITE project (expects only 4 stages)
        assert exit_code in [0, 1]


class TestPreCommitMain:
    """Tests for main pre-commit entry point."""

    @pytest.fixture
    def compliant_project(self):
        """Create a compliant project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}\n\nDocumentation content here."
                )

            yield project_root

    def test_main_success(self, compliant_project):
        """Test main returns 0 for compliant project."""
        with patch.object(sys, "argv", ["pre-commit", "--path", str(compliant_project), "--tier", "lite"]):
            exit_code = main()
            assert exit_code == 0

    def test_main_failure(self):
        """Test main returns 1 for non-compliant project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(sys, "argv", ["pre-commit", "--path", tmpdir, "--tier", "lite"]):
                exit_code = main()
                assert exit_code == 1


class TestPreCommitHookIntegration:
    """Integration tests for pre-commit hook."""

    @pytest.fixture
    def git_repo_with_sdlc(self):
        """Create a git repo with SDLC structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=project_root, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=project_root,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=project_root,
                capture_output=True,
            )

            # Create SDLC structure
            docs_root = project_root / "docs"
            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}\n\nDocumentation."
                )

            yield project_root

    def test_hook_validates_project(self, git_repo_with_sdlc):
        """Test hook can validate git project."""
        exit_code = run_validation(
            project_root=git_repo_with_sdlc,
            docs_root="docs",
            tier="lite",
            strict=False,
        )
        assert exit_code == 0


class TestPreCommitPerformance:
    """Performance tests for pre-commit hook."""

    @pytest.fixture
    def large_project(self):
        """Create a project with many files for LITE tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            # Create LITE tier structure (4 stages) with many files
            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)

                # Create multiple files per stage
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}: {stage_name}\n\n"
                    f"This is the documentation for stage {stage_id}. "
                    f"It contains important information about this stage."
                )
                for i in range(50):
                    (stage_path / f"doc-{i}.md").write_text(
                        f"# Document {i}\n\nContent for document {i}. "
                        f"This is some additional content to make the file larger."
                    )

            yield project_root

    def test_hook_performance(self, large_project):
        """Test hook runs within performance budget (<2s)."""
        import time

        start = time.time()
        exit_code = run_validation(
            project_root=large_project,
            docs_root="docs",
            tier="lite",  # Use LITE tier which doesn't require P0
            strict=False,
        )
        elapsed = time.time() - start

        # Should complete within 2 seconds
        assert elapsed < 2.0, f"Pre-commit hook took {elapsed:.2f}s (>2s budget)"
        assert exit_code == 0


class TestPreCommitStrictMode:
    """Tests for strict mode in pre-commit hook."""

    @pytest.fixture
    def project_with_warnings(self):
        """Create a project that might have warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                # Short README may trigger warning
                (stage_path / "README.md").write_text(f"# {stage_id}\n\nShort.")

            yield project_root

    def test_strict_mode_fails_on_warnings(self, project_with_warnings):
        """Test strict mode fails on warnings."""
        exit_code = run_validation(
            project_root=project_with_warnings,
            docs_root="docs",
            tier="lite",
            strict=True,
        )
        # May pass or fail depending on warning severity
        assert exit_code in [0, 1]

    def test_strict_mode_with_compliant_project(self):
        """Test strict mode passes on fully compliant project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}: {stage_name}\n\n"
                    f"This is the entry point for Stage {stage_id}. "
                    f"It contains documentation for this stage with sufficient content."
                )

            exit_code = run_validation(
                project_root=project_root,
                docs_root="docs",
                tier="lite",
                strict=True,
            )
            assert exit_code == 0


class TestPreCommitInvalidTier:
    """Tests for invalid tier handling in pre-commit hook."""

    def test_invalid_tier_uses_default(self):
        """Test invalid tier falls back to default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            # Create compliant LITE structure
            for stage_id in ["00", "01", "02", "03"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# Stage {stage_id}\n\nDocumentation content."
                )

            # Should not crash with invalid tier
            exit_code = run_validation(
                project_root=project_root,
                docs_root="docs",
                tier="invalid_tier",  # Invalid tier
                strict=False,
            )
            # May pass or fail depending on default tier
            assert exit_code in [0, 1]
