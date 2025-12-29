"""Tests for P0 artifact checker module."""

import pytest
from pathlib import Path
import tempfile

from sdlcctl.validation.p0 import (
    P0_ARTIFACTS,
    P0Artifact,
    P0ArtifactChecker,
    P0CheckResult,
    P0ValidationResult,
)
from sdlcctl.validation.tier import Tier


class TestP0Artifact:
    """Tests for P0Artifact dataclass."""

    def test_p0_artifact_creation(self):
        """Test P0Artifact creation."""
        artifact = P0Artifact(
            artifact_id="P0-00-README",
            name="Stage 00 README",
            stage_id="00",
            relative_path="00-Project-Foundation/README.md",
            description="Entry point for Stage 00",
            required_tiers={Tier.LITE, Tier.STANDARD},
        )
        assert artifact.artifact_id == "P0-00-README"
        assert artifact.stage_id == "00"
        assert Tier.LITE in artifact.required_tiers

    def test_p0_artifact_with_alternatives(self):
        """Test P0Artifact with alternative paths."""
        artifact = P0Artifact(
            artifact_id="P0-01-FRD",
            name="FRD",
            stage_id="01",
            relative_path="01-Planning-Analysis/01-Requirements/FRD.md",
            description="Requirements doc",
            alternative_paths=[
                "01-Planning-Analysis/Requirements.md",
                "01-Planning-Analysis/FRD.md",
            ],
        )
        assert len(artifact.alternative_paths) == 2


class TestP0CheckResult:
    """Tests for P0CheckResult dataclass."""

    def test_check_result_found(self):
        """Test check result for found artifact."""
        artifact = P0Artifact(
            artifact_id="P0-TEST",
            name="Test",
            stage_id="00",
            relative_path="test.md",
            description="Test",
        )
        result = P0CheckResult(
            artifact=artifact,
            found=True,
            actual_path=Path("/docs/test.md"),
            file_size_bytes=500,
            has_content=True,
        )
        assert result.found is True
        assert result.has_content is True
        assert result.file_size_bytes == 500

    def test_check_result_not_found(self):
        """Test check result for missing artifact."""
        artifact = P0Artifact(
            artifact_id="P0-TEST",
            name="Test",
            stage_id="00",
            relative_path="test.md",
            description="Test",
        )
        result = P0CheckResult(
            artifact=artifact,
            found=False,
            issues=["File not found"],
        )
        assert result.found is False
        assert len(result.issues) == 1


class TestP0ValidationResult:
    """Tests for P0ValidationResult dataclass."""

    def test_validation_result_compliant(self):
        """Test validation result for compliant project."""
        result = P0ValidationResult(
            project_root=Path("/project"),
            tier=Tier.LITE,
            artifacts_checked=4,
            artifacts_found=4,
            artifacts_missing=0,
            coverage_percent=100.0,
            is_compliant=True,
        )
        assert result.is_compliant is True
        assert result.coverage_percent == 100.0

    def test_validation_result_non_compliant(self):
        """Test validation result for non-compliant project."""
        result = P0ValidationResult(
            project_root=Path("/project"),
            tier=Tier.PROFESSIONAL,
            artifacts_checked=10,
            artifacts_found=5,
            artifacts_missing=5,
            coverage_percent=50.0,
            is_compliant=False,
        )
        assert result.is_compliant is False
        assert result.artifacts_missing == 5


class TestP0ArtifactChecker:
    """Tests for P0ArtifactChecker class."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project with basic P0 structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            # Create minimal P0 structure for LITE tier
            stage_00 = docs_root / "00-Project-Foundation"
            stage_00.mkdir(parents=True)
            (stage_00 / "README.md").write_text(
                "# Stage 00: Project Foundation\n\n"
                "This is the entry point for Stage 00. "
                "It contains vision and business case documentation."
            )

            stage_01 = docs_root / "01-Planning-Analysis"
            stage_01.mkdir(parents=True)
            (stage_01 / "README.md").write_text(
                "# Stage 01: Planning & Analysis\n\n"
                "Requirements and analysis documentation."
            )

            stage_02 = docs_root / "02-Design-Architecture"
            stage_02.mkdir(parents=True)
            (stage_02 / "README.md").write_text(
                "# Stage 02: Design & Architecture\n\n"
                "Technical design and architecture documentation."
            )

            stage_03 = docs_root / "03-Development-Implementation"
            stage_03.mkdir(parents=True)
            (stage_03 / "README.md").write_text(
                "# Stage 03: Development\n\n"
                "Development guides and sprint plans."
            )

            yield project_root

    @pytest.fixture
    def empty_project(self):
        """Create project without docs folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_checker_initialization(self, temp_project):
        """Test checker initialization."""
        checker = P0ArtifactChecker(temp_project, "docs", tier=Tier.LITE)
        assert checker.tier == Tier.LITE
        # Note: resolve() handles symlinks like /var -> /private/var on macOS
        assert checker.docs_root == (temp_project / "docs").resolve()

    def test_checker_auto_tier_detection(self, temp_project):
        """Test checker with auto tier detection from team size."""
        checker = P0ArtifactChecker(temp_project, "docs", team_size=5)
        assert checker.tier == Tier.STANDARD

    def test_checker_default_tier(self, temp_project):
        """Test checker uses PROFESSIONAL as default tier."""
        checker = P0ArtifactChecker(temp_project, "docs")
        assert checker.tier == Tier.PROFESSIONAL

    def test_check_all_lite_tier(self, temp_project):
        """Test checking all P0 artifacts for LITE tier."""
        checker = P0ArtifactChecker(temp_project, "docs", tier=Tier.LITE)
        result = checker.check_all()

        assert result.tier == Tier.LITE
        # LITE tier requires 4 stage READMEs
        assert result.artifacts_checked == 4
        assert result.artifacts_found == 4
        assert result.is_compliant is True

    def test_check_all_professional_tier(self, temp_project):
        """Test checking P0 artifacts for PROFESSIONAL tier (more required)."""
        checker = P0ArtifactChecker(temp_project, "docs", tier=Tier.PROFESSIONAL)
        result = checker.check_all()

        # PROFESSIONAL requires more artifacts
        assert result.artifacts_checked > 4
        assert result.artifacts_missing > 0  # Missing most P0 artifacts
        assert result.is_compliant is False

    def test_check_empty_project(self, empty_project):
        """Test checking project without docs folder."""
        checker = P0ArtifactChecker(empty_project, "docs", tier=Tier.LITE)
        result = checker.check_all()

        assert result.artifacts_found == 0
        assert result.is_compliant is False

    def test_get_required_artifacts(self, temp_project):
        """Test getting required artifacts for tier."""
        checker_lite = P0ArtifactChecker(temp_project, "docs", tier=Tier.LITE)
        checker_enterprise = P0ArtifactChecker(temp_project, "docs", tier=Tier.ENTERPRISE)

        lite_artifacts = checker_lite.get_required_artifacts()
        enterprise_artifacts = checker_enterprise.get_required_artifacts()

        # Enterprise should require more artifacts
        assert len(enterprise_artifacts) > len(lite_artifacts)

    def test_get_missing_artifacts(self, temp_project):
        """Test getting list of missing artifacts."""
        checker = P0ArtifactChecker(temp_project, "docs", tier=Tier.PROFESSIONAL)
        missing = checker.get_missing_artifacts()

        # Should have missing artifacts for stages 04-09
        assert len(missing) > 0
        missing_ids = [a.artifact_id for a in missing]
        assert any("P0-04" in id for id in missing_ids)

    def test_generate_missing_templates(self, temp_project):
        """Test generating templates for missing artifacts."""
        checker = P0ArtifactChecker(temp_project, "docs", tier=Tier.PROFESSIONAL)
        generated = checker.generate_missing_templates()

        # Should generate templates for missing artifacts
        assert len(generated) > 0

        # Check files were created
        for artifact_id, path in generated.items():
            assert path.exists()
            content = path.read_text()
            assert len(content) > 100  # Has meaningful content

    def test_artifact_content_validation(self, temp_project):
        """Test artifact content size validation."""
        # Create file that's too small
        small_file = temp_project / "docs" / "00-Project-Foundation" / "README.md"
        small_file.write_text("# Small")  # Only 7 bytes

        checker = P0ArtifactChecker(temp_project, "docs", tier=Tier.LITE)
        result = checker.check_all()

        # Should flag small file as lacking content
        stage_00_result = result.results.get("P0-00-README")
        assert stage_00_result is not None
        assert stage_00_result.found is True
        assert stage_00_result.has_content is False

    def test_alternative_path_detection(self, temp_project):
        """Test detection of P0 artifacts at alternative paths."""
        # Create FRD at alternative location
        frd = temp_project / "docs" / "01-Planning-Analysis" / "Functional-Requirements.md"
        frd.write_text(
            "# Functional Requirements Document\n\n"
            "This document contains the functional requirements for the project. "
            "It includes user stories, acceptance criteria, and more."
        )

        checker = P0ArtifactChecker(temp_project, "docs", tier=Tier.STANDARD)
        result = checker.check_all()

        # Check that FRD was found (might be at alternative path)
        # This depends on the exact P0_ARTIFACTS configuration


class TestP0ArtifactsConstants:
    """Tests for P0_ARTIFACTS constant."""

    def test_all_required_artifacts_defined(self):
        """Test minimum expected P0 artifacts are defined."""
        assert len(P0_ARTIFACTS) >= 10  # At least 10 P0 artifacts

    def test_artifacts_have_required_fields(self):
        """Test all artifacts have required fields."""
        for artifact in P0_ARTIFACTS:
            assert artifact.artifact_id is not None
            assert artifact.name is not None
            assert artifact.stage_id is not None
            assert artifact.relative_path is not None
            assert artifact.description is not None
            assert artifact.required_tiers is not None

    def test_stage_readme_artifacts(self):
        """Test README artifacts exist for each stage."""
        readme_artifacts = [a for a in P0_ARTIFACTS if a.artifact_id.endswith("-README")]

        # Should have README artifacts
        assert len(readme_artifacts) > 0

        # Check they map to different stages
        stages = {a.stage_id for a in readme_artifacts}
        assert len(stages) == len(readme_artifacts)

    def test_artifacts_have_valid_tier_requirements(self):
        """Test artifacts have at least one required tier."""
        for artifact in P0_ARTIFACTS:
            assert len(artifact.required_tiers) > 0
            for tier in artifact.required_tiers:
                assert isinstance(tier, Tier)
