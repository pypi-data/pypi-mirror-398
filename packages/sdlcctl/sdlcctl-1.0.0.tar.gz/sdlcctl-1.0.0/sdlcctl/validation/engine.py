"""
SDLC 5.0.0 Validation Engine.

Main orchestrator for SDLC structure validation.
Combines folder scanning, tier detection, and P0 artifact checking.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .p0 import P0ArtifactChecker, P0ValidationResult
from .scanner import FolderScanner, ScanResult
from .tier import Tier, TierDetector, TierRequirements


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Blocks compliance
    WARNING = "warning"  # Should fix but not blocking
    INFO = "info"  # Informational only


@dataclass
class ValidationIssue:
    """A single validation issue."""

    code: str
    severity: ValidationSeverity
    message: str
    path: Optional[str] = None
    stage_id: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result for a project."""

    project_root: Path
    docs_root: Path
    tier: Tier
    tier_requirements: TierRequirements
    scan_result: ScanResult
    p0_result: P0ValidationResult
    issues: List[ValidationIssue] = field(default_factory=list)
    is_compliant: bool = False
    compliance_score: float = 0.0
    validation_time_ms: float = 0.0

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of info-level issues."""
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.INFO)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "project_root": str(self.project_root),
            "docs_root": str(self.docs_root),
            "tier": self.tier.value,
            "is_compliant": self.is_compliant,
            "compliance_score": self.compliance_score,
            "validation_time_ms": self.validation_time_ms,
            "summary": {
                "stages_found": len(self.scan_result.stages_found),
                "stages_missing": len(self.scan_result.stages_missing),
                "p0_artifacts_found": self.p0_result.artifacts_found,
                "p0_artifacts_missing": self.p0_result.artifacts_missing,
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
            },
            "issues": [
                {
                    "code": i.code,
                    "severity": i.severity.value,
                    "message": i.message,
                    "path": i.path,
                    "stage_id": i.stage_id,
                    "fix_suggestion": i.fix_suggestion,
                }
                for i in self.issues
            ],
        }


class SDLCValidator:
    """
    Main SDLC 5.0.0 Structure Validator.

    Orchestrates validation of:
    - Folder structure (10 stages)
    - Stage naming conventions
    - P0 artifact presence
    - Tier-specific requirements
    - Legacy folder handling
    """

    def __init__(
        self,
        project_root: Path,
        docs_root: str = "docs",
        tier: Optional[Tier] = None,
        team_size: Optional[int] = None,
    ):
        """
        Initialize SDLC validator.

        Args:
            project_root: Root directory of the project
            docs_root: Relative path to docs folder (default: "docs")
            tier: Project tier (if known)
            team_size: Team size for tier detection (if tier not specified)
        """
        self.project_root = Path(project_root).resolve()
        self.docs_folder = docs_root

        # Determine tier
        self.tier_detector = TierDetector()
        if tier:
            self.tier = tier
        elif team_size:
            self.tier = self.tier_detector.detect_from_team_size(team_size)
        else:
            # Default to PROFESSIONAL tier
            self.tier = Tier.PROFESSIONAL

        self.tier_requirements = self.tier_detector.get_requirements(self.tier)

    def validate(self) -> ValidationResult:
        """
        Perform complete SDLC structure validation.

        Returns:
            ValidationResult with all findings
        """
        import time

        start_time = time.time()
        issues: List[ValidationIssue] = []

        # Step 1: Scan folder structure
        scanner = FolderScanner(self.project_root, self.docs_folder)
        scan_result = scanner.scan()

        # Step 2: Check P0 artifacts
        p0_checker = P0ArtifactChecker(
            self.project_root, self.docs_folder, tier=self.tier
        )
        p0_result = p0_checker.check_all()

        # Step 3: Validate against tier requirements
        issues.extend(self._validate_docs_folder(scan_result))
        issues.extend(self._validate_stages(scan_result))
        issues.extend(self._validate_naming(scan_result))
        issues.extend(self._validate_p0_artifacts(p0_result))
        issues.extend(self._validate_legacy_folders(scan_result))

        # Calculate compliance
        is_compliant = not any(
            i.severity == ValidationSeverity.ERROR for i in issues
        )
        compliance_score = self._calculate_compliance_score(
            scan_result, p0_result, issues
        )

        validation_time = (time.time() - start_time) * 1000

        return ValidationResult(
            project_root=self.project_root,
            docs_root=scanner.docs_root,
            tier=self.tier,
            tier_requirements=self.tier_requirements,
            scan_result=scan_result,
            p0_result=p0_result,
            issues=issues,
            is_compliant=is_compliant,
            compliance_score=compliance_score,
            validation_time_ms=validation_time,
        )

    def _validate_docs_folder(self, scan_result: ScanResult) -> List[ValidationIssue]:
        """Validate docs folder exists."""
        issues: List[ValidationIssue] = []

        if not scan_result.docs_root.exists():
            issues.append(
                ValidationIssue(
                    code="SDLC-001",
                    severity=ValidationSeverity.ERROR,
                    message=f"Documentation folder not found: {self.docs_folder}/",
                    path=str(self.project_root / self.docs_folder),
                    fix_suggestion=f"Create docs folder: mkdir -p {self.docs_folder}",
                )
            )

        return issues

    def _validate_stages(self, scan_result: ScanResult) -> List[ValidationIssue]:
        """Validate required stages are present."""
        issues: List[ValidationIssue] = []

        required_stages = self.tier_requirements.required_stages

        for stage_id in required_stages:
            if stage_id in scan_result.stages_missing:
                from .tier import STAGE_NAMES

                expected_name = STAGE_NAMES.get(stage_id, f"{stage_id}-Unknown")
                issues.append(
                    ValidationIssue(
                        code="SDLC-002",
                        severity=ValidationSeverity.ERROR,
                        message=f"Required stage missing: {expected_name}",
                        stage_id=stage_id,
                        fix_suggestion=f"Create stage folder: mkdir -p {self.docs_folder}/{expected_name}",
                    )
                )

        # Check for stages beyond tier requirement (informational)
        for stage_id in scan_result.stages_found:
            if stage_id not in required_stages:
                stage_info = scan_result.stages_found[stage_id]
                issues.append(
                    ValidationIssue(
                        code="SDLC-010",
                        severity=ValidationSeverity.INFO,
                        message=f"Optional stage present: {stage_info.folder_name}",
                        stage_id=stage_id,
                        path=str(stage_info.path),
                    )
                )

        return issues

    def _validate_naming(self, scan_result: ScanResult) -> List[ValidationIssue]:
        """Validate stage naming conventions."""
        issues: List[ValidationIssue] = []

        for violation in scan_result.naming_violations:
            if violation.get("type") == "stage_naming":
                issues.append(
                    ValidationIssue(
                        code="SDLC-003",
                        severity=ValidationSeverity.WARNING,
                        message=(
                            f"Stage naming mismatch: found '{violation['found']}', "
                            f"expected '{violation['expected']}'"
                        ),
                        stage_id=violation.get("stage_id"),
                        path=violation.get("path"),
                        fix_suggestion=(
                            f"Rename folder: mv '{violation['found']}' '{violation['expected']}'"
                        ),
                    )
                )
            elif violation.get("type") == "missing_docs":
                # Already handled in _validate_docs_folder
                pass

        return issues

    def _validate_p0_artifacts(
        self, p0_result: P0ValidationResult
    ) -> List[ValidationIssue]:
        """Validate P0 artifacts."""
        issues: List[ValidationIssue] = []

        if not self.tier_requirements.p0_required:
            # P0 not required for this tier
            if p0_result.artifacts_missing > 0:
                issues.append(
                    ValidationIssue(
                        code="SDLC-011",
                        severity=ValidationSeverity.INFO,
                        message=(
                            f"P0 artifacts recommended but not required for {self.tier.value} tier. "
                            f"Missing: {p0_result.artifacts_missing}"
                        ),
                    )
                )
            return issues

        # P0 is required for this tier
        for artifact_id, result in p0_result.results.items():
            if not result.found:
                issues.append(
                    ValidationIssue(
                        code="SDLC-004",
                        severity=ValidationSeverity.ERROR,
                        message=f"Required P0 artifact missing: {result.artifact.name}",
                        stage_id=result.artifact.stage_id,
                        path=str(
                            self.project_root
                            / self.docs_folder
                            / result.artifact.relative_path
                        ),
                        fix_suggestion=(
                            f"Create file: {result.artifact.relative_path} "
                            f"(use 'sdlcctl fix' to generate template)"
                        ),
                    )
                )
            elif not result.has_content:
                issues.append(
                    ValidationIssue(
                        code="SDLC-005",
                        severity=ValidationSeverity.WARNING,
                        message=(
                            f"P0 artifact has insufficient content: {result.artifact.name} "
                            f"({result.file_size_bytes} bytes)"
                        ),
                        stage_id=result.artifact.stage_id,
                        path=str(result.actual_path) if result.actual_path else None,
                        fix_suggestion="Add meaningful content to the document",
                    )
                )

            # Report issues found during check
            for issue_msg in result.issues:
                if "alternative path" in issue_msg.lower():
                    issues.append(
                        ValidationIssue(
                            code="SDLC-006",
                            severity=ValidationSeverity.WARNING,
                            message=f"P0 artifact at non-standard path: {issue_msg}",
                            stage_id=result.artifact.stage_id,
                            path=str(result.actual_path) if result.actual_path else None,
                            fix_suggestion=(
                                f"Move to standard path: {result.artifact.relative_path}"
                            ),
                        )
                    )

        return issues

    def _validate_legacy_folders(
        self, scan_result: ScanResult
    ) -> List[ValidationIssue]:
        """Validate 99-Legacy folder handling."""
        issues: List[ValidationIssue] = []

        for legacy_path in scan_result.legacy_folders:
            # Check if legacy folder has AI directive
            readme_path = legacy_path / "README.md"
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding="utf-8")
                    if "AI: DO NOT READ" not in content and "AI-NEVER-READ" not in content:
                        issues.append(
                            ValidationIssue(
                                code="SDLC-007",
                                severity=ValidationSeverity.WARNING,
                                message=(
                                    "Legacy folder README missing AI directive. "
                                    "Add 'AI: DO NOT READ' or 'AI-NEVER-READ'"
                                ),
                                path=str(readme_path),
                                fix_suggestion=(
                                    "Add to README: '**AI Directive**: DO NOT READ this folder'"
                                ),
                            )
                        )
                except OSError:
                    pass
            else:
                issues.append(
                    ValidationIssue(
                        code="SDLC-008",
                        severity=ValidationSeverity.INFO,
                        message="Legacy folder found without README",
                        path=str(legacy_path),
                        fix_suggestion="Add README.md with AI directive to prevent confusion",
                    )
                )

        # Check for legacy folders inside stages
        for stage_id, stage_info in scan_result.stages_found.items():
            stage_legacy = stage_info.path / "99-Legacy"
            if stage_legacy.exists() and stage_legacy not in scan_result.legacy_folders:
                issues.append(
                    ValidationIssue(
                        code="SDLC-009",
                        severity=ValidationSeverity.INFO,
                        message=f"Stage {stage_id} has local legacy folder",
                        stage_id=stage_id,
                        path=str(stage_legacy),
                    )
                )

        return issues

    def _calculate_compliance_score(
        self,
        scan_result: ScanResult,
        p0_result: P0ValidationResult,
        issues: List[ValidationIssue],
    ) -> float:
        """
        Calculate compliance score (0-100).

        Scoring:
        - Stage presence: 40% weight
        - P0 artifacts: 40% weight
        - No errors: 20% weight
        """
        # Stage score (40%)
        required_count = len(self.tier_requirements.required_stages)
        found_required = sum(
            1
            for s in self.tier_requirements.required_stages
            if s in scan_result.stages_found
        )
        stage_score = (found_required / required_count * 40) if required_count > 0 else 40

        # P0 score (40%)
        if self.tier_requirements.p0_required:
            p0_score = p0_result.coverage_percent * 0.4
        else:
            # Full P0 score if not required
            p0_score = 40.0

        # Error penalty (20%)
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        error_score = max(0, 20 - error_count * 5)  # -5 per error

        total = stage_score + p0_score + error_score
        return round(min(100, total), 1)

    def generate_report(self, result: Optional[ValidationResult] = None) -> str:
        """
        Generate human-readable validation report.

        Args:
            result: Validation result (runs validation if not provided)

        Returns:
            Formatted report string
        """
        if result is None:
            result = self.validate()

        lines = [
            "=" * 60,
            "SDLC 5.0.0 Structure Validation Report",
            "=" * 60,
            "",
            f"Project: {result.project_root}",
            f"Docs Root: {result.docs_root}",
            f"Tier: {result.tier.value.upper()}",
            f"Compliant: {'YES' if result.is_compliant else 'NO'}",
            f"Score: {result.compliance_score}/100",
            f"Validation Time: {result.validation_time_ms:.1f}ms",
            "",
            "-" * 60,
            "SUMMARY",
            "-" * 60,
            f"Stages Found: {len(result.scan_result.stages_found)}/{len(self.tier_requirements.required_stages)} required",
            f"Stages Missing: {len(result.scan_result.stages_missing)}",
            f"P0 Artifacts: {result.p0_result.artifacts_found}/{result.p0_result.artifacts_checked}",
            f"Total Files Scanned: {result.scan_result.total_files}",
            f"Legacy Folders: {len(result.scan_result.legacy_folders)}",
            "",
            f"Errors: {result.error_count}",
            f"Warnings: {result.warning_count}",
            f"Info: {result.info_count}",
            "",
        ]

        if result.issues:
            lines.extend(["-" * 60, "ISSUES", "-" * 60, ""])

            # Group by severity
            for severity in [
                ValidationSeverity.ERROR,
                ValidationSeverity.WARNING,
                ValidationSeverity.INFO,
            ]:
                severity_issues = [
                    i for i in result.issues if i.severity == severity
                ]
                if severity_issues:
                    lines.append(f"[{severity.value.upper()}]")
                    for issue in severity_issues:
                        lines.append(f"  [{issue.code}] {issue.message}")
                        if issue.path:
                            lines.append(f"           Path: {issue.path}")
                        if issue.fix_suggestion:
                            lines.append(f"           Fix: {issue.fix_suggestion}")
                    lines.append("")

        lines.extend(["=" * 60, "End of Report", "=" * 60])

        return "\n".join(lines)
