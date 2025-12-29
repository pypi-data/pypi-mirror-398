"""
Sequential Numbering Validator.

Validates sequential numbering of subfolders and files within SDLC stages.

Rules:
- NUM-001: Duplicate numbering (e.g., two "01-" folders)
- NUM-002: Non-sequential numbering (e.g., 01, 03 but no 02)
- NUM-003: Invalid number format (e.g., "1-" instead of "01-")

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..base_validator import BaseValidator
from ..violation import Severity, ViolationReport


class SequentialNumberingValidator(BaseValidator):
    """
    Validates sequential numbering within SDLC stage folders.

    Checks:
    - No duplicate numbers in same folder
    - Sequential ordering (01, 02, 03...)
    - Proper 2-digit format (01 not 1)
    """

    VALIDATOR_ID = "sequential-numbering"
    VALIDATOR_NAME = "Sequential Numbering Validator"
    VALIDATOR_DESCRIPTION = "Validates sequential numbering of subfolders"

    # Numbering pattern: 2 digits + hyphen
    NUMBERING_PATTERN = re.compile(r"^(\d{2})-(.+)$")

    # Legacy/archive folders to skip
    LEGACY_ARCHIVE_PATTERN = re.compile(r"^(99-[Ll]egacy|10-[Aa]rchive)$")

    def validate(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """
        Validate sequential numbering within stage folders.

        Args:
            paths: Optional list of specific paths to validate

        Returns:
            List of violations found
        """
        violations: List[ViolationReport] = []

        if not self.docs_root.exists():
            return violations

        # Get all stage folders
        stage_folders = self._get_stage_folders()

        for stage_folder in stage_folders:
            # Get numbered subfolders/files
            numbered_items = self._get_numbered_items(stage_folder)

            if not numbered_items:
                continue  # No numbered items to validate

            # NUM-001: Check for duplicates
            violations.extend(self._check_duplicates(stage_folder, numbered_items))

            # NUM-002: Check for gaps in sequence
            violations.extend(
                self._check_sequence_gaps(stage_folder, numbered_items)
            )

            # NUM-003: Check number format
            violations.extend(self._check_number_format(stage_folder))

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

            # Check if it looks like a stage folder (XX-name)
            if re.match(r"^\d{2}-", item.name):
                stage_folders.append(item)

        return stage_folders

    def _get_numbered_items(self, folder: Path) -> List[tuple[str, Path]]:
        """
        Get all numbered items (folders/files) in a folder.

        Args:
            folder: Folder to scan

        Returns:
            List of (number, path) tuples
        """
        numbered_items = []

        if not folder.exists():
            return numbered_items

        for item in folder.iterdir():
            # Skip hidden items
            if item.name.startswith("."):
                continue

            # Skip legacy/archive
            if self.LEGACY_ARCHIVE_PATTERN.match(item.name):
                continue

            # Check for number prefix
            match = self.NUMBERING_PATTERN.match(item.name)
            if match:
                number = match.group(1)
                numbered_items.append((number, item))

        return numbered_items

    def _check_duplicates(
        self, stage_folder: Path, numbered_items: List[tuple[str, Path]]
    ) -> List[ViolationReport]:
        """
        Check for NUM-001: Duplicate numbering.

        Example: Both "01-doc1" and "01-doc2" in same folder

        Args:
            stage_folder: Stage folder being checked
            numbered_items: List of (number, path) tuples

        Returns:
            List of violations
        """
        violations = []

        # Count occurrences of each number
        number_counts = Counter(number for number, _ in numbered_items)

        # Find duplicates
        duplicates = {num for num, count in number_counts.items() if count > 1}

        if duplicates:
            for dup_number in sorted(duplicates):
                dup_items = [path for num, path in numbered_items if num == dup_number]

                # Report violation for first occurrence
                violations.append(
                    ViolationReport(
                        rule_id="NUM-001",
                        severity=Severity.ERROR,
                        file_path=stage_folder,
                        message=f"Duplicate numbering '{dup_number}' found: {len(dup_items)} items",
                        fix_suggestion=f"Renumber duplicates starting from next available number",
                        auto_fixable=False,
                        context={
                            "duplicate_number": dup_number,
                            "duplicate_count": len(dup_items),
                            "duplicate_items": [item.name for item in dup_items],
                            "stage_folder": stage_folder.name,
                        },
                    )
                )

        return violations

    def _check_sequence_gaps(
        self, stage_folder: Path, numbered_items: List[tuple[str, Path]]
    ) -> List[ViolationReport]:
        """
        Check for NUM-002: Non-sequential numbering (gaps).

        Example: 01, 03, 04 (missing 02)

        Args:
            stage_folder: Stage folder being checked
            numbered_items: List of (number, path) tuples

        Returns:
            List of violations
        """
        violations = []

        if len(numbered_items) < 2:
            return violations  # Need at least 2 items to check sequence

        # Get unique numbers and convert to int
        numbers = sorted(set(int(num) for num, _ in numbered_items))

        # Check for gaps
        gaps = []
        for i in range(len(numbers) - 1):
            current = numbers[i]
            next_num = numbers[i + 1]

            # If difference > 1, there's a gap
            if next_num - current > 1:
                missing_numbers = list(range(current + 1, next_num))
                gaps.extend(missing_numbers)

        if gaps:
            violations.append(
                ViolationReport(
                    rule_id="NUM-002",
                    severity=Severity.INFO,
                    file_path=stage_folder,
                    message=f"Non-sequential numbering: gaps found at {', '.join(f'{n:02d}' for n in gaps)}",
                    fix_suggestion="Consider renumbering to fill gaps for consistency",
                    auto_fixable=True,
                    context={
                        "existing_numbers": [f"{n:02d}" for n in numbers],
                        "missing_numbers": [f"{n:02d}" for n in gaps],
                        "stage_folder": stage_folder.name,
                    },
                )
            )

        return violations

    def _check_number_format(self, stage_folder: Path) -> List[ViolationReport]:
        """
        Check for NUM-003: Invalid number format.

        Valid: 01-, 02-, etc. (2 digits)
        Invalid: 1-, 001-, etc.

        Args:
            stage_folder: Stage folder being checked

        Returns:
            List of violations
        """
        violations = []

        if not stage_folder.exists():
            return violations

        for item in stage_folder.iterdir():
            # Skip hidden items
            if item.name.startswith("."):
                continue

            # Skip legacy/archive
            if self.LEGACY_ARCHIVE_PATTERN.match(item.name):
                continue

            # Check for invalid number formats
            # Pattern: starts with digit(s) and hyphen, but not exactly 2 digits
            if "-" in item.name:
                prefix = item.name.split("-")[0]

                # Check if prefix is all digits but not exactly 2 digits
                if prefix.isdigit() and len(prefix) != 2:
                    # Suggest proper format
                    if len(prefix) == 1:
                        suggested = f"0{prefix}"
                    elif len(prefix) > 2:
                        suggested = prefix[-2:]  # Take last 2 digits
                    else:
                        suggested = prefix

                    suggested_name = item.name.replace(
                        f"{prefix}-", f"{suggested}-", 1
                    )

                    violations.append(
                        ViolationReport(
                            rule_id="NUM-003",
                            severity=Severity.WARNING,
                            file_path=item,
                            message=f"Invalid number format: '{prefix}' should be 2 digits",
                            fix_suggestion=f"Rename to '{suggested_name}'",
                            auto_fixable=True,
                            context={
                                "current_name": item.name,
                                "invalid_prefix": prefix,
                                "suggested_prefix": suggested,
                                "suggested_name": suggested_name,
                            },
                        )
                    )

        return violations
