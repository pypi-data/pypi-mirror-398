"""
Stage Folder Validator.

Validates SDLC 5.1.1 stage folder structure and naming.

Rules:
- STAGE-001: Invalid stage folder naming (e.g., "1-planning" → "01-planning")
- STAGE-002: Unknown stage number (not in 00-10)
- STAGE-003: Stage name mismatch (e.g., "01-design" should be "01-planning")
- STAGE-004: Duplicate stage number
- STAGE-005: Missing required stages

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

import re
from collections import Counter
from pathlib import Path
from typing import List, Optional

from ..base_validator import BaseValidator
from ..tier import STAGE_NAMES
from ..violation import Severity, ViolationReport


class StageFolderValidator(BaseValidator):
    """
    Validates SDLC stage folder structure.

    Checks:
    - Stage folder naming (2-digit prefix)
    - Valid stage numbers (00-10)
    - Correct stage names
    - No duplicate stage numbers
    - Required stages present
    """

    VALIDATOR_ID = "stage-folder"
    VALIDATOR_NAME = "Stage Folder Validator"
    VALIDATOR_DESCRIPTION = "Validates SDLC 5.1.1 stage folder structure"

    # Stage pattern: 2 digits + hyphen + name
    STAGE_PATTERN = re.compile(r"^(\d{2})-(.+)$")

    # Valid stage IDs (00-10 in SDLC 5.1.1)
    VALID_STAGE_IDS = set(STAGE_NAMES.keys())

    # Legacy/archive folders to skip
    LEGACY_ARCHIVE_PATTERN = re.compile(r"^(99-[Ll]egacy|10-[Aa]rchive)$")

    def validate(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """
        Validate stage folder structure.

        Args:
            paths: Optional list of specific paths to validate

        Returns:
            List of violations found
        """
        violations: List[ViolationReport] = []

        if not self.docs_root.exists():
            violations.append(
                ViolationReport(
                    rule_id="STAGE-ERROR",
                    severity=Severity.ERROR,
                    file_path=self.docs_root,
                    message="docs_root does not exist",
                )
            )
            return violations

        # Get all stage folders
        stage_folders = self._get_stage_folders()

        # STAGE-001: Invalid naming (missing 2-digit prefix)
        violations.extend(self._check_invalid_naming(stage_folders))

        # STAGE-002: Unknown stage number
        violations.extend(self._check_unknown_stages(stage_folders))

        # STAGE-003: Stage name mismatch
        violations.extend(self._check_name_mismatch(stage_folders))

        # STAGE-004: Duplicate stage numbers
        violations.extend(self._check_duplicates(stage_folders))

        # STAGE-005: Missing required stages (optional - can be customized)
        # Only warn for core stages (00, 01, 02, 04 are most critical)
        # violations.extend(self._check_missing_stages(stage_folders))

        return violations

    def _get_stage_folders(self) -> List[Path]:
        """
        Get all stage folders in docs_root.

        Returns:
            List of stage folder paths
        """
        stage_folders = []

        if not self.docs_root.exists():
            return stage_folders

        for item in self.docs_root.iterdir():
            if not item.is_dir():
                continue

            # Skip hidden folders
            if item.name.startswith("."):
                continue

            # Skip legacy/archive folders
            if self.LEGACY_ARCHIVE_PATTERN.match(item.name):
                continue

            stage_folders.append(item)

        return stage_folders

    def _check_invalid_naming(self, stage_folders: List[Path]) -> List[ViolationReport]:
        """
        Check for STAGE-001: Invalid stage folder naming.

        Valid format: XX-name (2 digits, hyphen, name)
        Invalid: X-name, name-only, XX_name, etc.

        Args:
            stage_folders: List of stage folder paths

        Returns:
            List of violations
        """
        violations = []

        for folder in stage_folders:
            match = self.STAGE_PATTERN.match(folder.name)

            if not match:
                # Check if it looks like a stage folder (has number prefix)
                if any(char.isdigit() for char in folder.name[:3]):
                    # Try to extract stage number
                    digits = "".join(c for c in folder.name if c.isdigit())[:2]
                    if digits and len(digits) == 1:
                        digits = f"0{digits}"

                    expected_name = STAGE_NAMES.get(digits, f"{digits}-<name>")

                    violations.append(
                        ViolationReport(
                            rule_id="STAGE-001",
                            severity=Severity.ERROR,
                            file_path=folder,
                            message=f"Invalid stage folder naming: '{folder.name}'",
                            fix_suggestion=f"Rename to '{expected_name}'",
                            auto_fixable=True,
                            context={
                                "current_name": folder.name,
                                "expected_format": "XX-name (2 digits + hyphen + name)",
                                "suggested_name": expected_name,
                            },
                        )
                    )

        return violations

    def _check_unknown_stages(self, stage_folders: List[Path]) -> List[ViolationReport]:
        """
        Check for STAGE-002: Unknown stage number.

        Valid stage IDs: 00-10 (SDLC 5.1.1)
        Invalid: 11+, negative numbers, etc.

        Args:
            stage_folders: List of stage folder paths

        Returns:
            List of violations
        """
        violations = []

        for folder in stage_folders:
            match = self.STAGE_PATTERN.match(folder.name)

            if match:
                stage_id = match.group(1)

                if stage_id not in self.VALID_STAGE_IDS:
                    violations.append(
                        ViolationReport(
                            rule_id="STAGE-002",
                            severity=Severity.ERROR,
                            file_path=folder,
                            message=f"Unknown stage number: '{stage_id}' in '{folder.name}'",
                            fix_suggestion=f"Valid stage IDs are: {', '.join(sorted(self.VALID_STAGE_IDS))}",
                            auto_fixable=False,
                            context={
                                "stage_id": stage_id,
                                "valid_ids": sorted(self.VALID_STAGE_IDS),
                            },
                        )
                    )

        return violations

    def _check_name_mismatch(self, stage_folders: List[Path]) -> List[ViolationReport]:
        """
        Check for STAGE-003: Stage name mismatch.

        Example: "01-design" should be "01-planning"

        Args:
            stage_folders: List of stage folder paths

        Returns:
            List of violations
        """
        violations = []

        for folder in stage_folders:
            match = self.STAGE_PATTERN.match(folder.name)

            if match:
                stage_id = match.group(1)
                actual_name = match.group(2)
                expected_full_name = STAGE_NAMES.get(stage_id)

                if expected_full_name:
                    expected_suffix = expected_full_name.split("-", 1)[1]

                    if actual_name != expected_suffix:
                        violations.append(
                            ViolationReport(
                                rule_id="STAGE-003",
                                severity=Severity.WARNING,
                                file_path=folder,
                                message=f"Stage name mismatch: '{folder.name}' should be '{expected_full_name}'",
                                fix_suggestion=f"Rename to '{expected_full_name}'",
                                auto_fixable=True,
                                context={
                                    "current_name": folder.name,
                                    "expected_name": expected_full_name,
                                    "stage_id": stage_id,
                                },
                            )
                        )

        return violations

    def _check_duplicates(self, stage_folders: List[Path]) -> List[ViolationReport]:
        """
        Check for STAGE-004: Duplicate stage numbers.

        Example: Both "01-planning" and "01-analysis" exist

        Args:
            stage_folders: List of stage folder paths

        Returns:
            List of violations
        """
        violations = []

        # Count stage IDs
        stage_ids = []
        for folder in stage_folders:
            match = self.STAGE_PATTERN.match(folder.name)
            if match:
                stage_ids.append((match.group(1), folder))

        # Find duplicates
        id_counts = Counter(stage_id for stage_id, _ in stage_ids)
        duplicates = {stage_id for stage_id, count in id_counts.items() if count > 1}

        if duplicates:
            for stage_id in duplicates:
                duplicate_folders = [
                    folder for sid, folder in stage_ids if sid == stage_id
                ]

                for folder in duplicate_folders:
                    violations.append(
                        ViolationReport(
                            rule_id="STAGE-004",
                            severity=Severity.ERROR,
                            file_path=folder,
                            message=f"Duplicate stage number '{stage_id}': {len(duplicate_folders)} folders found",
                            fix_suggestion="Remove or renumber duplicate stage folders",
                            auto_fixable=False,
                            context={
                                "stage_id": stage_id,
                                "duplicate_count": len(duplicate_folders),
                                "duplicate_folders": [str(f) for f in duplicate_folders],
                            },
                        )
                    )

        return violations

    def _check_missing_stages(self, stage_folders: List[Path]) -> List[ViolationReport]:
        """
        Check for STAGE-005: Missing required stages.

        Core stages: 00 (WHY), 01 (WHAT), 02 (HOW), 04 (BUILD)
        Recommended: All stages 00-09

        Args:
            stage_folders: List of stage folder paths

        Returns:
            List of violations
        """
        violations = []

        # Extract existing stage IDs
        existing_ids = set()
        for folder in stage_folders:
            match = self.STAGE_PATTERN.match(folder.name)
            if match:
                existing_ids.add(match.group(1))

        # Core stages (minimum for any project)
        core_stages = {"00", "01", "02", "04"}
        missing_core = core_stages - existing_ids

        if missing_core:
            for stage_id in sorted(missing_core):
                expected_name = STAGE_NAMES.get(stage_id, f"{stage_id}-<unknown>")

                violations.append(
                    ViolationReport(
                        rule_id="STAGE-005",
                        severity=Severity.WARNING,
                        file_path=self.docs_root,
                        message=f"Missing core stage: {expected_name}",
                        fix_suggestion=f"Create folder '{expected_name}' in docs root",
                        auto_fixable=True,
                        context={
                            "stage_id": stage_id,
                            "expected_name": expected_name,
                            "missing_core_stages": sorted(missing_core),
                        },
                    )
                )

        return violations
