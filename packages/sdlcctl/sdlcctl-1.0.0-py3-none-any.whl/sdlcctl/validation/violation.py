"""
SDLC Structure Validation - Violation Report.

Core data structures for reporting SDLC structure violations.
Part of Sprint 44 - SDLC Structure Scanner Engine.

Framework: SDLC 5.1.1
Epic: EP-04 - SDLC Structure Enforcement
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class Severity(str, Enum):
    """Violation severity levels."""

    ERROR = "ERROR"  # Blocking issues that must be fixed
    WARNING = "WARNING"  # Important issues that should be fixed
    INFO = "INFO"  # Suggestions for improvement


@dataclass
class ViolationReport:
    """
    Report of a single SDLC structure violation.

    Attributes:
        rule_id: Unique rule identifier (e.g., STAGE-001, NUM-001)
        severity: Violation severity level
        file_path: Path to the file/folder with violation
        message: Human-readable violation message
        fix_suggestion: Optional suggestion for fixing the violation
        auto_fixable: Whether the violation can be auto-fixed
        context: Additional context about the violation
    """

    rule_id: str
    severity: Severity
    file_path: Path
    message: str
    fix_suggestion: Optional[str] = None
    auto_fixable: bool = False
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation for display."""
        severity_emoji = {
            Severity.ERROR: "❌",
            Severity.WARNING: "⚠️",
            Severity.INFO: "ℹ️",
        }
        emoji = severity_emoji.get(self.severity, "•")

        parts = [
            f"{emoji} {self.severity.value}",
            f"[{self.rule_id}]",
            f"{self.file_path}:",
            self.message,
        ]

        if self.fix_suggestion:
            parts.append(f"\n  💡 Suggestion: {self.fix_suggestion}")

        if self.auto_fixable:
            parts.append("\n  🔧 Auto-fixable with --fix")

        return " ".join(parts[:4]) + "".join(parts[4:])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "file_path": str(self.file_path),
            "message": self.message,
            "fix_suggestion": self.fix_suggestion,
            "auto_fixable": self.auto_fixable,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ViolationReport":
        """Create from dictionary."""
        return cls(
            rule_id=data["rule_id"],
            severity=Severity(data["severity"]),
            file_path=Path(data["file_path"]),
            message=data["message"],
            fix_suggestion=data.get("fix_suggestion"),
            auto_fixable=data.get("auto_fixable", False),
            context=data.get("context", {}),
        )


@dataclass
class ScanResult:
    """
    Result of SDLC structure scan.

    Attributes:
        scan_path: Root path that was scanned
        violations: List of violations found
        files_scanned: Number of files scanned
        scan_time_ms: Time taken to scan in milliseconds
        scanner_version: Version of the scanner
    """

    scan_path: Path
    violations: list[ViolationReport] = field(default_factory=list)
    files_scanned: int = 0
    scan_time_ms: float = 0.0
    scanner_version: str = "1.0.0"

    @property
    def error_count(self) -> int:
        """Count of ERROR severity violations."""
        return sum(1 for v in self.violations if v.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of WARNING severity violations."""
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of INFO severity violations."""
        return sum(1 for v in self.violations if v.severity == Severity.INFO)

    @property
    def auto_fixable_count(self) -> int:
        """Count of auto-fixable violations."""
        return sum(1 for v in self.violations if v.auto_fixable)

    @property
    def passed(self) -> bool:
        """Whether the scan passed (no ERRORs)."""
        return self.error_count == 0

    def get_violations_by_severity(self, severity: Severity) -> list[ViolationReport]:
        """Get all violations of a specific severity."""
        return [v for v in self.violations if v.severity == severity]

    def get_violations_by_rule(self, rule_id: str) -> list[ViolationReport]:
        """Get all violations for a specific rule."""
        return [v for v in self.violations if v.rule_id == rule_id]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scan_path": str(self.scan_path),
            "violations": [v.to_dict() for v in self.violations],
            "files_scanned": self.files_scanned,
            "scan_time_ms": self.scan_time_ms,
            "scanner_version": self.scanner_version,
            "summary": {
                "total_violations": len(self.violations),
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "auto_fixable": self.auto_fixable_count,
                "passed": self.passed,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanResult":
        """Create from dictionary."""
        return cls(
            scan_path=Path(data["scan_path"]),
            violations=[ViolationReport.from_dict(v) for v in data["violations"]],
            files_scanned=data["files_scanned"],
            scan_time_ms=data["scan_time_ms"],
            scanner_version=data.get("scanner_version", "1.0.0"),
        )

    def __str__(self) -> str:
        """String representation for display."""
        lines = [
            f"Scan Results for {self.scan_path}",
            f"Files scanned: {self.files_scanned}",
            f"Scan time: {self.scan_time_ms:.2f}ms",
            "",
            f"Summary:",
            f"  ❌ Errors: {self.error_count}",
            f"  ⚠️  Warnings: {self.warning_count}",
            f"  ℹ️  Info: {self.info_count}",
            f"  🔧 Auto-fixable: {self.auto_fixable_count}",
            "",
        ]

        if self.violations:
            lines.append("Violations:")
            for v in self.violations:
                lines.append(f"  {v}")
        else:
            lines.append("✅ No violations found!")

        return "\n".join(lines)
