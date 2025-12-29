"""Tests for folder scanner module."""

import pytest
from pathlib import Path
import tempfile
import os

from sdlcctl.validation.scanner import FolderScanner, ScanResult, StageInfo


class TestStageInfo:
    """Tests for StageInfo dataclass."""

    def test_stage_info_creation(self):
        """Test StageInfo creation with required fields."""
        info = StageInfo(
            stage_id="00",
            folder_name="00-Project-Foundation",
            path=Path("/docs/00-Project-Foundation"),
            file_count=10,
            has_readme=True,
        )
        assert info.stage_id == "00"
        assert info.folder_name == "00-Project-Foundation"
        assert info.file_count == 10
        assert info.has_readme is True
        assert info.subfolders == []
        assert info.depth == 1

    def test_stage_info_with_subfolders(self):
        """Test StageInfo with subfolders."""
        info = StageInfo(
            stage_id="01",
            folder_name="01-Planning-Analysis",
            path=Path("/docs/01-Planning-Analysis"),
            file_count=5,
            has_readme=False,
            subfolders=["01-Requirements", "02-User-Stories"],
            depth=2,
        )
        assert len(info.subfolders) == 2
        assert info.depth == 2


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_scan_result_creation(self):
        """Test ScanResult creation."""
        result = ScanResult(
            project_root=Path("/project"),
            docs_root=Path("/project/docs"),
            stages_found={},
            stages_missing=["00", "01"],
            naming_violations=[],
            legacy_folders=[],
            total_files=0,
            total_folders=0,
            scan_time_ms=10.5,
        )
        assert result.project_root == Path("/project")
        assert len(result.stages_missing) == 2
        assert result.scan_time_ms == 10.5


class TestFolderScanner:
    """Tests for FolderScanner class."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"
            docs_root.mkdir()

            # Create some stages
            stage_00 = docs_root / "00-Project-Foundation"
            stage_00.mkdir()
            (stage_00 / "README.md").write_text("# Stage 00\n\nContent here.")

            stage_01 = docs_root / "01-Planning-Analysis"
            stage_01.mkdir()
            (stage_01 / "README.md").write_text("# Stage 01")
            (stage_01 / "requirements.md").write_text("Requirements doc")

            yield project_root

    @pytest.fixture
    def empty_project(self):
        """Create project without docs folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_scanner_initialization(self, temp_project):
        """Test scanner initialization."""
        scanner = FolderScanner(temp_project, "docs")
        assert scanner.project_root == temp_project.resolve()
        assert scanner.docs_root == temp_project.resolve() / "docs"

    def test_scanner_with_custom_docs_root(self, temp_project):
        """Test scanner with custom docs folder name."""
        # Create custom docs folder
        custom_docs = temp_project / "documentation"
        custom_docs.mkdir()

        scanner = FolderScanner(temp_project, "documentation")
        assert scanner.docs_root == temp_project.resolve() / "documentation"

    def test_scan_finds_stages(self, temp_project):
        """Test scan finds existing stages."""
        scanner = FolderScanner(temp_project)
        result = scanner.scan()

        assert "00" in result.stages_found
        assert "01" in result.stages_found
        assert result.stages_found["00"].has_readme is True
        assert result.stages_found["01"].file_count >= 2

    def test_scan_identifies_missing_stages(self, temp_project):
        """Test scan identifies missing stages."""
        scanner = FolderScanner(temp_project)
        result = scanner.scan()

        # Should be missing most stages
        assert "02" in result.stages_missing
        assert "03" in result.stages_missing

    def test_scan_empty_project(self, empty_project):
        """Test scan handles missing docs folder."""
        scanner = FolderScanner(empty_project)
        result = scanner.scan()

        assert len(result.stages_found) == 0
        assert len(result.stages_missing) == 11  # All stages missing
        assert len(result.naming_violations) == 1
        assert result.naming_violations[0]["type"] == "missing_docs"

    def test_scan_detects_naming_violations(self, temp_project):
        """Test scan detects naming violations."""
        # Create wrongly named stage
        wrong_name = temp_project / "docs" / "00-Wrong-Name"
        wrong_name.mkdir()
        (wrong_name / "README.md").write_text("# Wrong")

        # Remove correct one first
        import shutil
        shutil.rmtree(temp_project / "docs" / "00-Project-Foundation")

        scanner = FolderScanner(temp_project)
        result = scanner.scan()

        violations = [v for v in result.naming_violations if v.get("type") == "stage_naming"]
        assert len(violations) >= 1
        assert violations[0]["found"] == "00-Wrong-Name"
        assert violations[0]["expected"] == "00-Project-Foundation"

    def test_scan_detects_legacy_folders(self, temp_project):
        """Test scan detects legacy folders."""
        legacy = temp_project / "docs" / "99-Legacy"
        legacy.mkdir()
        (legacy / "old-doc.md").write_text("Old content")

        scanner = FolderScanner(temp_project)
        result = scanner.scan()

        assert len(result.legacy_folders) == 1
        assert result.legacy_folders[0].name == "99-Legacy"

    def test_scan_ignores_patterns(self, temp_project):
        """Test scan ignores specified patterns."""
        # Create folders that should be ignored
        (temp_project / "docs" / "node_modules").mkdir()
        (temp_project / "docs" / ".git").mkdir()

        scanner = FolderScanner(temp_project)
        result = scanner.scan()

        # Should not count ignored folders as stages
        assert "node_modules" not in result.stages_found
        assert ".git" not in result.stages_found

    def test_scan_performance(self, temp_project):
        """Test scan completes within reasonable time."""
        scanner = FolderScanner(temp_project)
        result = scanner.scan()

        # Should complete in under 1 second for small project
        assert result.scan_time_ms < 1000

    def test_find_file(self, temp_project):
        """Test find_file method."""
        scanner = FolderScanner(temp_project)

        # Should find README.md
        found = scanner.find_file("README.md")
        assert found is not None
        assert found.name == "README.md"

        # Should not find non-existent file
        not_found = scanner.find_file("nonexistent.md")
        assert not_found is None

    def test_file_exists(self, temp_project):
        """Test file_exists method."""
        scanner = FolderScanner(temp_project)

        assert scanner.file_exists("docs/00-Project-Foundation/README.md") is True
        assert scanner.file_exists("docs/nonexistent.md") is False

    def test_get_stage_path(self, temp_project):
        """Test get_stage_path method."""
        scanner = FolderScanner(temp_project)

        # Should find existing stage
        path = scanner.get_stage_path("00")
        assert path is not None
        assert path.name == "00-Project-Foundation"

        # Should return None for non-existent stage
        path = scanner.get_stage_path("99")
        assert path is None

    def test_custom_ignore_patterns(self, temp_project):
        """Test scanner with custom ignore patterns."""
        # Create custom folder that should be ignored
        (temp_project / "docs" / "custom_ignore").mkdir()

        scanner = FolderScanner(
            temp_project,
            ignore_patterns={"custom_ignore"},
        )

        # Access internal patterns to verify
        assert "custom_ignore" in scanner.ignore_patterns
        assert "node_modules" in scanner.ignore_patterns  # Default still present

    def test_scan_counts_files(self, temp_project):
        """Test scan correctly counts files."""
        # Add more files to stage
        stage = temp_project / "docs" / "00-Project-Foundation"
        (stage / "doc1.md").write_text("Doc 1")
        (stage / "doc2.md").write_text("Doc 2")
        (stage / "doc3.md").write_text("Doc 3")

        scanner = FolderScanner(temp_project)
        result = scanner.scan()

        # Should count README + 3 new docs = 4 files
        assert result.stages_found["00"].file_count == 4
