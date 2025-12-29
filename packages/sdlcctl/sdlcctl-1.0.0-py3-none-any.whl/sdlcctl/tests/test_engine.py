"""Tests for validation engine module."""

import pytest
from pathlib import Path
import tempfile

from sdlcctl.validation.engine import (
    SDLCValidator,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from sdlcctl.validation.tier import Tier


class TestValidationSeverity:
    """Tests for ValidationSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.INFO.value == "info"


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_issue_creation(self):
        """Test ValidationIssue creation."""
        issue = ValidationIssue(
            code="SDLC-001",
            severity=ValidationSeverity.ERROR,
            message="Test error message",
            path="/test/path",
            stage_id="00",
            fix_suggestion="Fix it",
        )
        assert issue.code == "SDLC-001"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.message == "Test error message"

    def test_issue_minimal(self):
        """Test ValidationIssue with minimal fields."""
        issue = ValidationIssue(
            code="SDLC-002",
            severity=ValidationSeverity.WARNING,
            message="Warning message",
        )
        assert issue.path is None
        assert issue.stage_id is None
        assert issue.fix_suggestion is None


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create sample validation result."""
        from sdlcctl.validation.scanner import ScanResult, StageInfo
        from sdlcctl.validation.p0 import P0ValidationResult
        from sdlcctl.validation.tier import TierRequirements

        return ValidationResult(
            project_root=Path("/test"),
            docs_root=Path("/test/docs"),
            tier=Tier.PROFESSIONAL,
            tier_requirements=TierRequirements(
                tier=Tier.PROFESSIONAL,
                min_team_size=10,
                max_team_size=50,
                min_stages=10,
                required_stages=["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
                p0_required=True,
                max_depth=3,
                compliance_required=[],
            ),
            scan_result=ScanResult(
                project_root=Path("/test"),
                docs_root=Path("/test/docs"),
                stages_found={
                    "00": StageInfo(
                        stage_id="00",
                        folder_name="00-Project-Foundation",
                        path=Path("/test/docs/00-Project-Foundation"),
                        file_count=5,
                        has_readme=True,
                    )
                },
                stages_missing=["01", "02"],
                naming_violations=[],
                legacy_folders=[],
                total_files=5,
                total_folders=1,
                scan_time_ms=10.0,
            ),
            p0_result=P0ValidationResult(
                project_root=Path("/test"),
                tier=Tier.PROFESSIONAL,
                artifacts_checked=10,
                artifacts_found=5,
                artifacts_missing=5,
                coverage_percent=50.0,
                is_compliant=False,
            ),
            issues=[
                ValidationIssue(
                    code="SDLC-001",
                    severity=ValidationSeverity.ERROR,
                    message="Error 1",
                ),
                ValidationIssue(
                    code="SDLC-002",
                    severity=ValidationSeverity.ERROR,
                    message="Error 2",
                ),
                ValidationIssue(
                    code="SDLC-003",
                    severity=ValidationSeverity.WARNING,
                    message="Warning 1",
                ),
                ValidationIssue(
                    code="SDLC-010",
                    severity=ValidationSeverity.INFO,
                    message="Info 1",
                ),
            ],
            is_compliant=False,
            compliance_score=50.0,
            validation_time_ms=15.5,
        )

    def test_error_count(self, sample_result):
        """Test error_count property."""
        assert sample_result.error_count == 2

    def test_warning_count(self, sample_result):
        """Test warning_count property."""
        assert sample_result.warning_count == 1

    def test_info_count(self, sample_result):
        """Test info_count property."""
        assert sample_result.info_count == 1

    def test_to_dict(self, sample_result):
        """Test to_dict conversion."""
        result_dict = sample_result.to_dict()

        assert result_dict["project_root"] == "/test"
        assert result_dict["tier"] == "professional"
        assert result_dict["is_compliant"] is False
        assert result_dict["compliance_score"] == 50.0
        assert "summary" in result_dict
        assert "issues" in result_dict


class TestSDLCValidator:
    """Tests for SDLCValidator class."""

    @pytest.fixture
    def compliant_project(self):
        """Create a LITE-tier compliant project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"

            # Create all required stages for LITE tier
            for stage_id in ["00", "01", "02", "03"]:
                from sdlcctl.validation.tier import STAGE_NAMES
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs_root / stage_name
                stage_path.mkdir(parents=True)
                (stage_path / "README.md").write_text(
                    f"# {stage_name}\n\n"
                    f"This is the README for stage {stage_id}. "
                    f"It contains comprehensive documentation about this stage. "
                    f"This content is long enough to pass validation checks."
                )

            yield project_root

    @pytest.fixture
    def empty_project(self):
        """Create project without docs folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def partial_project(self):
        """Create project with some stages missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            docs_root = project_root / "docs"
            docs_root.mkdir()

            # Create only stage 00
            stage_00 = docs_root / "00-Project-Foundation"
            stage_00.mkdir()
            (stage_00 / "README.md").write_text(
                "# Project Foundation\n\n"
                "This is the foundation stage with proper content."
            )

            yield project_root

    def test_validator_initialization(self, compliant_project):
        """Test validator initialization."""
        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        assert validator.tier == Tier.LITE
        assert validator.project_root == compliant_project.resolve()

    def test_validator_auto_tier_detection(self, compliant_project):
        """Test validator with auto tier detection."""
        validator = SDLCValidator(compliant_project, team_size=5)
        assert validator.tier == Tier.STANDARD

    def test_validator_default_tier(self, compliant_project):
        """Test validator uses PROFESSIONAL as default."""
        validator = SDLCValidator(compliant_project)
        assert validator.tier == Tier.PROFESSIONAL

    def test_validate_compliant_project(self, compliant_project):
        """Test validation of compliant project."""
        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        result = validator.validate()

        assert result.is_compliant is True
        assert result.error_count == 0
        assert result.compliance_score >= 80.0

    def test_validate_empty_project(self, empty_project):
        """Test validation of empty project."""
        validator = SDLCValidator(empty_project, tier=Tier.LITE)
        result = validator.validate()

        assert result.is_compliant is False
        assert result.error_count > 0
        # Should have "missing docs" issue
        error_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.ERROR]
        assert "SDLC-001" in error_codes

    def test_validate_partial_project(self, partial_project):
        """Test validation of partial project."""
        validator = SDLCValidator(partial_project, tier=Tier.LITE)
        result = validator.validate()

        assert result.is_compliant is False
        # Should be missing 3 stages
        assert len(result.scan_result.stages_missing) >= 3

    def test_validate_detects_missing_stages(self, partial_project):
        """Test validator detects missing required stages."""
        validator = SDLCValidator(partial_project, tier=Tier.LITE)
        result = validator.validate()

        # Should have SDLC-002 errors for missing stages
        missing_stage_errors = [
            i for i in result.issues
            if i.code == "SDLC-002" and i.severity == ValidationSeverity.ERROR
        ]
        assert len(missing_stage_errors) >= 3

    def test_validate_p0_required_tier(self, compliant_project):
        """Test P0 validation for PROFESSIONAL tier."""
        validator = SDLCValidator(compliant_project, tier=Tier.PROFESSIONAL)
        result = validator.validate()

        # Should fail P0 validation (missing most P0 artifacts)
        assert result.p0_result.is_compliant is False

    def test_validate_p0_not_required_tier(self, compliant_project):
        """Test P0 validation for LITE tier (not required)."""
        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        result = validator.validate()

        # P0 not required for LITE
        assert result.tier_requirements.p0_required is False

    def test_validation_time(self, compliant_project):
        """Test validation completes quickly."""
        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        result = validator.validate()

        # Should complete in under 10 seconds
        assert result.validation_time_ms < 10000

    def test_compliance_score_calculation(self, compliant_project):
        """Test compliance score is calculated correctly."""
        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        result = validator.validate()

        # Score should be between 0 and 100
        assert 0 <= result.compliance_score <= 100

    def test_generate_report(self, compliant_project):
        """Test report generation."""
        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        report = validator.generate_report()

        assert "SDLC 5.0.0 Structure Validation Report" in report
        assert "Tier:" in report
        assert "Compliant:" in report

    def test_naming_violation_detection(self, compliant_project):
        """Test detection of naming violations."""
        # Create wrongly named stage
        wrong_stage = compliant_project / "docs" / "00-Wrong-Stage"
        wrong_stage.mkdir(exist_ok=True)
        (wrong_stage / "README.md").write_text("# Wrong Stage\n\nContent.")

        # Remove correctly named stage
        import shutil
        correct_stage = compliant_project / "docs" / "00-Project-Foundation"
        if correct_stage.exists():
            shutil.rmtree(correct_stage)

        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        result = validator.validate()

        # Should have naming violation warning
        naming_warnings = [
            i for i in result.issues
            if i.code == "SDLC-003"
        ]
        assert len(naming_warnings) > 0

    def test_legacy_folder_handling(self, compliant_project):
        """Test legacy folder detection and validation."""
        # Create legacy folder
        legacy = compliant_project / "docs" / "99-Legacy"
        legacy.mkdir()
        (legacy / "README.md").write_text(
            "# Legacy\n\n"
            "This is legacy content but missing AI directive."
        )

        validator = SDLCValidator(compliant_project, tier=Tier.LITE)
        result = validator.validate()

        # Should have warning about missing AI directive
        legacy_warnings = [
            i for i in result.issues
            if "SDLC-007" in i.code or "AI directive" in i.message
        ]
        assert len(legacy_warnings) > 0


class TestValidatorIntegration:
    """Integration tests for full validation workflow."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize project structure
            from sdlcctl.validation.tier import STAGE_NAMES

            docs = project_root / "docs"
            docs.mkdir()

            # Create all stages for STANDARD tier
            for stage_id in ["00", "01", "02", "03", "04", "05"]:
                stage_name = STAGE_NAMES[stage_id]
                stage_path = docs / stage_name
                stage_path.mkdir()
                (stage_path / "README.md").write_text(
                    f"# {stage_name}\n\n"
                    f"Documentation for stage {stage_id}. "
                    f"Contains detailed information about this stage."
                )
                # Create legacy folder with proper directive
                legacy = stage_path / "99-Legacy"
                legacy.mkdir()
                (legacy / "README.md").write_text(
                    "# Legacy\n\n**AI Directive**: DO NOT READ this folder.\n"
                )

            # Run validation
            validator = SDLCValidator(project_root, tier=Tier.STANDARD)
            result = validator.validate()

            # Should be compliant for STANDARD tier
            assert result.tier == Tier.STANDARD
            assert result.error_count == 0
            assert result.is_compliant is True
            assert result.compliance_score >= 80.0

            # Generate report
            report = validator.generate_report(result)
            assert "COMPLIANT" in report or "YES" in report
