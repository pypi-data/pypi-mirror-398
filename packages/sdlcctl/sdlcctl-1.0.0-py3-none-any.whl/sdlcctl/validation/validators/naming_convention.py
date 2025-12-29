"""
Naming Convention Validator.

Validates file and folder naming conventions in SDLC documentation.

Rules:
- NAME-001: Invalid characters in names (spaces, underscores, special chars)
- NAME-002: Inconsistent casing (UPPERCASE, camelCase, PascalCase)

SDLC 5.1.1 Standard: kebab-case (lowercase with hyphens)
Example: user-guide.md, api-reference.md, sprint-plan.md

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

import re
from pathlib import Path
from typing import List, Optional

from ..base_validator import BaseValidator
from ..violation import Severity, ViolationReport


class NamingConventionValidator(BaseValidator):
    """
    Validates file and folder naming conventions.

    SDLC 5.1.1 Standard:
    - kebab-case (lowercase with hyphens)
    - No spaces, underscores, or special characters
    - Numbers allowed (e.g., sprint-44-plan.md)

    Checks:
    - Valid characters (a-z, 0-9, hyphen)
    - Lowercase only
    - No consecutive hyphens
    """

    VALIDATOR_ID = "naming-convention"
    VALIDATOR_NAME = "Naming Convention Validator"
    VALIDATOR_DESCRIPTION = "Validates kebab-case naming convention"

    # Valid name pattern: lowercase + numbers + hyphens
    # Must not start or end with hyphen, no consecutive hyphens
    VALID_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

    # Invalid characters (anything not a-z, 0-9, or hyphen)
    INVALID_CHARS_PATTERN = re.compile(r"[^a-z0-9-]")

    # Numbering prefix pattern (XX- at start)
    NUMBERING_PREFIX = re.compile(r"^(\d{2})-")

    # Legacy/archive folders to skip
    LEGACY_ARCHIVE_PATTERN = re.compile(r"^(99-[Ll]egacy|10-[Aa]rchive)$")

    # Extensions to check (focus on documentation files)
    CHECKED_EXTENSIONS = {".md", ".txt", ".json", ".yml", ".yaml"}

    def validate(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """
        Validate naming conventions.

        Args:
            paths: Optional list of specific paths to validate

        Returns:
            List of violations found
        """
        violations: List[ViolationReport] = []

        if not self.docs_root.exists():
            return violations

        # Validate folders
        violations.extend(self._validate_folders())

        # Validate files
        violations.extend(self._validate_files())

        return violations

    def _validate_folders(self) -> List[ViolationReport]:
        """
        Validate folder naming conventions.

        Returns:
            List of violations
        """
        violations = []

        for folder in self.docs_root.rglob("*"):
            if not folder.is_dir():
                continue

            # Skip hidden folders
            if folder.name.startswith("."):
                continue

            # Skip legacy/archive
            if self.LEGACY_ARCHIVE_PATTERN.match(folder.name):
                continue

            # Extract name without numbering prefix
            name = self._extract_name_without_prefix(folder.name)

            # NAME-001: Check for invalid characters
            if not self._has_valid_characters(name):
                violations.append(
                    self._create_invalid_chars_violation(folder, name)
                )

            # NAME-002: Check for proper casing
            elif not self._has_proper_casing(name):
                violations.append(self._create_casing_violation(folder, name))

        return violations

    def _validate_files(self) -> List[ViolationReport]:
        """
        Validate file naming conventions.

        Returns:
            List of violations
        """
        violations = []

        for file in self.docs_root.rglob("*"):
            if not file.is_file():
                continue

            # Skip hidden files
            if file.name.startswith("."):
                continue

            # README.md is a conventional documentation entrypoint and is
            # intentionally exempt from strict kebab-case naming.
            if file.name.lower() == "readme.md":
                continue

            # Only check specific extensions
            if file.suffix.lower() not in self.CHECKED_EXTENSIONS:
                continue

            # Extract name without extension and prefix
            name = self._extract_name_without_prefix(file.stem)

            # NAME-001: Check for invalid characters
            if not self._has_valid_characters(name):
                violations.append(self._create_invalid_chars_violation(file, name))

            # NAME-002: Check for proper casing
            elif not self._has_proper_casing(name):
                violations.append(self._create_casing_violation(file, name))

        return violations

    def _extract_name_without_prefix(self, name: str) -> str:
        """
        Extract name without numbering prefix (XX-).

        Args:
            name: Original name (e.g., "01-user-guide")

        Returns:
            Name without prefix (e.g., "user-guide")
        """
        match = self.NUMBERING_PREFIX.match(name)
        if match:
            return name[3:]  # Skip "XX-"
        return name

    def _has_valid_characters(self, name: str) -> bool:
        """
        Check if name contains only valid characters.

        Valid: a-z, 0-9, hyphen
        Invalid: spaces, underscores, special chars, uppercase

        Args:
            name: Name to check

        Returns:
            True if valid characters only
        """
        return bool(self.VALID_NAME_PATTERN.match(name))

    def _has_proper_casing(self, name: str) -> bool:
        """
        Check if name uses proper lowercase casing.

        Args:
            name: Name to check

        Returns:
            True if lowercase only
        """
        return name == name.lower()

    def _create_invalid_chars_violation(
        self, path: Path, name: str
    ) -> ViolationReport:
        """
        Create NAME-001 violation for invalid characters.

        Args:
            path: File or folder path
            name: Name being checked

        Returns:
            ViolationReport
        """
        # Suggest kebab-case version
        suggested = self._to_kebab_case(name)

        # Reconstruct full name with prefix/extension
        if path.is_file():
            prefix = (
                path.stem[: len(path.stem) - len(name)]
                if len(path.stem) > len(name)
                else ""
            )
            suggested_full = f"{prefix}{suggested}{path.suffix}"
        else:
            prefix = (
                path.name[: len(path.name) - len(name)]
                if len(path.name) > len(name)
                else ""
            )
            suggested_full = f"{prefix}{suggested}"

        return ViolationReport(
            rule_id="NAME-001",
            severity=Severity.WARNING,
            file_path=path,
            message=f"Invalid characters in name: '{path.name}'",
            fix_suggestion=f"Rename to '{suggested_full}' (use kebab-case)",
            auto_fixable=True,
            context={
                "current_name": path.name,
                "invalid_part": name,
                "suggested_name": suggested_full,
                "invalid_chars": self._find_invalid_chars(name),
            },
        )

    def _create_casing_violation(self, path: Path, name: str) -> ViolationReport:
        """
        Create NAME-002 violation for improper casing.

        Args:
            path: File or folder path
            name: Name being checked

        Returns:
            ViolationReport
        """
        # Suggest lowercase version
        suggested = name.lower()

        # Reconstruct full name
        if path.is_file():
            prefix = (
                path.stem[: len(path.stem) - len(name)]
                if len(path.stem) > len(name)
                else ""
            )
            suggested_full = f"{prefix}{suggested}{path.suffix}"
        else:
            prefix = (
                path.name[: len(path.name) - len(name)]
                if len(path.name) > len(name)
                else ""
            )
            suggested_full = f"{prefix}{suggested}"

        return ViolationReport(
            rule_id="NAME-002",
            severity=Severity.INFO,
            file_path=path,
            message=f"Inconsistent casing: '{path.name}'",
            fix_suggestion=f"Rename to '{suggested_full}' (use lowercase)",
            auto_fixable=True,
            context={
                "current_name": path.name,
                "casing_issue": "UPPERCASE or camelCase detected",
                "suggested_name": suggested_full,
            },
        )

    def _to_kebab_case(self, name: str) -> str:
        """
        Convert name to kebab-case.

        Handles:
        - Spaces → hyphens
        - Underscores → hyphens
        - camelCase → kebab-case
        - PascalCase → kebab-case
        - Special chars → removed
        - Multiple hyphens → single hyphen

        Args:
            name: Original name

        Returns:
            kebab-case version
        """
        # Convert camelCase/PascalCase to hyphenated
        # Insert hyphen before uppercase letters
        name = re.sub(r"([a-z])([A-Z])", r"\1-\2", name)

        # Convert to lowercase
        name = name.lower()

        # Replace spaces and underscores with hyphens
        name = re.sub(r"[_\s]+", "-", name)

        # Remove invalid characters
        name = re.sub(r"[^a-z0-9-]", "", name)

        # Remove consecutive hyphens
        name = re.sub(r"-+", "-", name)

        # Remove leading/trailing hyphens
        name = name.strip("-")

        return name

    def _find_invalid_chars(self, name: str) -> List[str]:
        """
        Find all invalid characters in name.

        Args:
            name: Name to check

        Returns:
            List of invalid characters found
        """
        invalid = set()
        for char in name:
            if not char.isalnum() and char != "-":
                invalid.add(char)
        return sorted(invalid)
