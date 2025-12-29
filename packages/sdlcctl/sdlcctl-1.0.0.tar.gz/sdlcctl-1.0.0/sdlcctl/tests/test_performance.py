"""
Performance benchmarks for sdlcctl.

Target: <10s validation for 1000+ files.
"""

import shutil
import tempfile
import time
from pathlib import Path

import pytest


class TestPerformanceBenchmarks:
    """Performance benchmarks for sdlcctl validation."""

    @pytest.fixture
    def large_project(self, tmp_path: Path) -> Path:
        """Create a large project structure with 1000+ files."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        # Create main README
        (docs_path / "README.md").write_text(
            "# Test Project\n\n**Framework**: SDLC 5.0.0\n**Tier**: PROFESSIONAL\n"
        )

        # Create 11 stages
        stages = [
            "00-Project-Foundation",
            "01-Planning-Analysis",
            "02-Design-Architecture",
            "03-Development-Implementation",
            "04-Testing-QA",
            "05-Deployment-Release",
            "06-Operations-Monitoring",
            "07-Integration-External",
            "08-Collaboration-Team",
            "09-Executive-Reports",
            "10-Archive-Lessons",
        ]

        file_count = 0
        for stage in stages:
            stage_path = docs_path / stage
            stage_path.mkdir()

            # Create README
            (stage_path / "README.md").write_text(
                f"# {stage}\n\n**Status**: ACTIVE\n"
            )
            file_count += 1

            # Create subfolders with many files
            for i in range(1, 10):
                subfolder = stage_path / f"{i:02d}-Subfolder-{i}"
                subfolder.mkdir()

                # Create 10 files per subfolder (90 files per stage)
                for j in range(1, 11):
                    file_path = subfolder / f"document-{j:03d}.md"
                    file_path.write_text(
                        f"# Document {j}\n\nContent for document {j} in {stage}.\n"
                        * 10  # Make each file substantial
                    )
                    file_count += 1

            # Create 99-Legacy folder
            legacy_path = stage_path / "99-Legacy"
            legacy_path.mkdir()
            (legacy_path / "README.md").write_text(
                "# Legacy\n\n**AI Directive**: DO NOT READ\n"
            )
            file_count += 1

        return tmp_path

    def test_validation_performance_1000_files(self, large_project: Path) -> None:
        """Test that validation completes in <10s for 1000+ files."""
        from sdlcctl.validation.engine import SDLCValidator
        from sdlcctl.validation.tier import Tier

        # Count files to verify we have 1000+
        docs_path = large_project / "docs"
        file_count = sum(1 for _ in docs_path.rglob("*") if _.is_file())
        assert file_count >= 1000, f"Expected 1000+ files, got {file_count}"

        # Run validation and measure time
        validator = SDLCValidator(
            project_root=large_project,
            docs_root="docs",
            tier=Tier.PROFESSIONAL,
        )

        start_time = time.time()
        result = validator.validate()
        elapsed = time.time() - start_time

        # Assert performance target
        assert elapsed < 10.0, f"Validation took {elapsed:.2f}s (target: <10s)"

        # Log performance metrics
        print(f"\n{'='*60}")
        print(f"PERFORMANCE BENCHMARK RESULTS")
        print(f"{'='*60}")
        print(f"Files scanned: {file_count}")
        print(f"Validation time: {elapsed:.2f}s")
        print(f"Files per second: {file_count/elapsed:.0f}")
        print(f"Compliance score: {result.compliance_score}/100")
        print(f"Target: <10s for 1000+ files")
        print(f"Status: {'PASS' if elapsed < 10.0 else 'FAIL'}")
        print(f"{'='*60}\n")

    def test_scanner_performance(self, large_project: Path) -> None:
        """Test folder scanner performance."""
        from sdlcctl.validation.scanner import FolderScanner

        docs_path = large_project / "docs"

        # Run scanner and measure time
        scanner = FolderScanner(docs_path)

        start_time = time.time()
        result = scanner.scan()
        elapsed = time.time() - start_time

        # Scanner should be fast (<2s)
        assert elapsed < 2.0, f"Scanner took {elapsed:.2f}s (target: <2s)"

        print(f"\nScanner performance: {elapsed:.2f}s")
        print(f"Stages found: {len(result.stages_found)}")
        print(f"Total files: {result.total_files}")

    def test_p0_checker_performance(self, large_project: Path) -> None:
        """Test P0 artifact checker performance."""
        from sdlcctl.validation.p0 import P0ArtifactChecker
        from sdlcctl.validation.tier import Tier

        # Run P0 checker and measure time
        checker = P0ArtifactChecker(
            large_project, "docs", tier=Tier.PROFESSIONAL
        )

        start_time = time.time()
        result = checker.check_all()
        elapsed = time.time() - start_time

        # P0 checker should be fast (<1s)
        assert elapsed < 1.0, f"P0 checker took {elapsed:.2f}s (target: <1s)"

        print(f"\nP0 checker performance: {elapsed:.2f}s")
        print(f"Artifacts checked: {result.artifacts_checked}")

    def test_precommit_hook_performance(self, large_project: Path) -> None:
        """Test pre-commit hook meets <2s target."""
        from sdlcctl.hooks.pre_commit import run_validation
        from sdlcctl.validation.tier import Tier

        # Run pre-commit validation and measure time
        start_time = time.time()
        exit_code = run_validation(
            project_root=large_project,
            docs_root="docs",
            tier=Tier.PROFESSIONAL.value,
            strict=False,
        )
        elapsed = time.time() - start_time

        # Pre-commit hook target: <2s
        assert elapsed < 2.0, f"Pre-commit took {elapsed:.2f}s (target: <2s)"

        print(f"\nPre-commit hook performance: {elapsed:.2f}s")
        print(f"Exit code: {exit_code}")
        print(f"Target: <2s")
        print(f"Status: {'PASS' if elapsed < 2.0 else 'FAIL'}")


class TestMemoryUsage:
    """Memory usage tests."""

    def test_memory_efficient_scanning(self, tmp_path: Path) -> None:
        """Test that scanning is memory efficient."""
        import sys

        from sdlcctl.validation.scanner import FolderScanner

        # Create docs structure
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        (docs_path / "README.md").write_text("# Test\n")
        for i in range(11):
            stage = docs_path / f"{i:02d}-Stage-{i}"
            stage.mkdir()
            (stage / "README.md").write_text(f"# Stage {i}\n")

        scanner = FolderScanner(docs_path)

        # Get memory before
        initial_size = sys.getsizeof(scanner)

        result = scanner.scan()

        # Result should be reasonably sized
        result_size = sys.getsizeof(result)
        assert result_size < 100000, f"Result too large: {result_size} bytes"

        print(f"\nMemory usage:")
        print(f"Scanner object: {initial_size} bytes")
        print(f"Scan result: {result_size} bytes")


class TestScalability:
    """Scalability tests for different project sizes."""

    @pytest.mark.parametrize(
        "num_files,max_time",
        [
            (100, 1.0),
            (500, 3.0),
            (1000, 10.0),
        ],
    )
    def test_validation_scales_linearly(
        self, tmp_path: Path, num_files: int, max_time: float
    ) -> None:
        """Test that validation time scales roughly linearly with file count."""
        from sdlcctl.validation.engine import SDLCValidator
        from sdlcctl.validation.tier import Tier

        # Create project with specified number of files
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        (docs_path / "README.md").write_text("# Test\n")

        # Calculate files per stage
        files_per_stage = max(num_files // 10, 10)

        for i in range(10):
            stage = docs_path / f"{i:02d}-Stage-{i}"
            stage.mkdir()
            (stage / "README.md").write_text(f"# Stage {i}\n")

            for j in range(files_per_stage):
                (stage / f"file-{j:04d}.md").write_text(f"# File {j}\n")

        # Run validation
        validator = SDLCValidator(
            project_root=tmp_path,
            docs_root="docs",
            tier=Tier.LITE,
        )

        start_time = time.time()
        validator.validate()
        elapsed = time.time() - start_time

        assert elapsed < max_time, (
            f"Validation of {num_files} files took {elapsed:.2f}s "
            f"(target: <{max_time}s)"
        )

        print(f"\n{num_files} files: {elapsed:.2f}s (target: <{max_time}s)")
