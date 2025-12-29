"""
Header Metadata Validator.

Validates document header metadata (YAML frontmatter or markdown headers).

Rules:
- HDR-001: Missing required header fields (Framework, Sprint, Epic)
- HDR-002: Invalid header format or values

SDLC 5.1.1 Standard:
- YAML frontmatter preferred (---)
- Required: Framework, Sprint, Epic
- Format: "Framework: SDLC X.Y.Z", "Sprint: N", "Epic: EP-N"

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..base_validator import BaseValidator
from ..violation import Severity, ViolationReport


class HeaderMetadataValidator(BaseValidator):
    """
    Validates document header metadata.

    Checks:
    - Required fields present (Framework, Sprint, Epic)
    - Valid field formats
    - YAML frontmatter or markdown header format
    """

    VALIDATOR_ID = "header-metadata"
    VALIDATOR_NAME = "Header Metadata Validator"
    VALIDATOR_DESCRIPTION = "Validates document header metadata"

    # Required header fields
    REQUIRED_FIELDS = {"Framework", "Sprint", "Epic"}

    # Field validation patterns
    FIELD_PATTERNS = {
        "Framework": re.compile(r"^SDLC\s+\d+\.\d+\.\d+$"),
        "Sprint": re.compile(r"^\d+$"),
        "Epic": re.compile(r"^EP-\d+"),
    }

    # YAML frontmatter pattern
    YAML_FRONTMATTER = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n", re.MULTILINE | re.DOTALL
    )

    # Markdown header pattern (## Field: Value)
    MD_HEADER = re.compile(r"^##?\s+(\w+):\s+(.+)$", re.MULTILINE)

    # Files to check (only markdown documentation)
    CHECKED_EXTENSIONS = {".md"}

    # Folders to skip
    SKIP_FOLDERS = {"node_modules", ".git", "__pycache__", "99-legacy", "10-archive"}

    def validate(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """
        Validate document headers.

        Args:
            paths: Optional list of specific paths to validate

        Returns:
            List of violations found
        """
        violations: List[ViolationReport] = []

        if not self.docs_root.exists():
            return violations

        # Find all markdown files
        for file in self.docs_root.rglob("*.md"):
            # Skip files in ignored folders
            if self._should_skip_file(file):
                continue

            # Stage/section READMEs are conventional and may not include
            # the full metadata header.
            if file.name.lower() == "readme.md":
                continue

            # Extract headers
            headers = self._extract_headers(file)

            # HDR-001: Check for missing required fields
            missing = self._check_missing_fields(headers)
            if missing:
                violations.append(
                    self._create_missing_fields_violation(file, missing, headers)
                )

            # HDR-002: Check field formats
            format_violations = self._check_field_formats(file, headers)
            violations.extend(format_violations)

        return violations

    def _should_skip_file(self, file: Path) -> bool:
        """
        Check if file should be skipped.

        Args:
            file: File path to check

        Returns:
            True if file should be skipped
        """
        # Skip files in ignored folders
        for part in file.parts:
            if part in self.SKIP_FOLDERS:
                return True

        # Skip hidden files
        if file.name.startswith("."):
            return True

        return False

    def _extract_headers(self, file: Path) -> Dict[str, str]:
        """
        Extract header fields from document.

        Tries:
        1. YAML frontmatter (---)
        2. Markdown headers (## Field: Value)

        Args:
            file: File to extract headers from

        Returns:
            Dictionary of field -> value
        """
        try:
            content = file.read_text(encoding="utf-8")
        except Exception:
            return {}

        # Try YAML frontmatter first
        yaml_headers = self._parse_yaml_frontmatter(content)
        if yaml_headers:
            return yaml_headers

        # Fall back to markdown headers
        return self._parse_markdown_headers(content)

    def _parse_yaml_frontmatter(self, content: str) -> Dict[str, str]:
        """
        Parse YAML frontmatter from content.

        Format:
        ---
        Framework: SDLC 5.1.1
        Sprint: 44
        Epic: EP-04
        ---

        Args:
            content: File content

        Returns:
            Dictionary of headers
        """
        match = self.YAML_FRONTMATTER.match(content)
        if not match:
            return {}

        frontmatter = match.group(1)
        headers = {}

        # Parse simple key: value pairs
        for line in frontmatter.split("\n"):
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

        return headers

    def _parse_markdown_headers(self, content: str) -> Dict[str, str]:
        """
        Parse markdown headers from content.

        Format:
        ## Framework: SDLC 5.1.1
        ## Sprint: 44
        ## Epic: EP-04

        Args:
            content: File content

        Returns:
            Dictionary of headers
        """
        headers = {}

        for match in self.MD_HEADER.finditer(content):
            key = match.group(1)
            value = match.group(2)
            headers[key] = value

        return headers

    def _check_missing_fields(self, headers: Dict[str, str]) -> Set[str]:
        """
        Check for missing required fields.

        Args:
            headers: Extracted headers

        Returns:
            Set of missing field names
        """
        return self.REQUIRED_FIELDS - set(headers.keys())

    def _check_field_formats(
        self, file: Path, headers: Dict[str, str]
    ) -> List[ViolationReport]:
        """
        Check field format validity.

        Args:
            file: File being checked
            headers: Extracted headers

        Returns:
            List of format violations
        """
        violations = []

        for field, value in headers.items():
            if field not in self.FIELD_PATTERNS:
                continue

            pattern = self.FIELD_PATTERNS[field]
            if not pattern.match(value):
                violations.append(
                    self._create_format_violation(file, field, value, pattern)
                )

        return violations

    def _create_missing_fields_violation(
        self, file: Path, missing: Set[str], current_headers: Dict[str, str]
    ) -> ViolationReport:
        """
        Create HDR-001 violation for missing fields.

        Args:
            file: File with missing headers
            missing: Set of missing field names
            current_headers: Current headers present

        Returns:
            ViolationReport
        """
        # Generate header template
        template = self._generate_header_template(current_headers, missing)

        return ViolationReport(
            rule_id="HDR-001",
            severity=Severity.WARNING,
            file_path=file,
            message=f"Missing required header fields: {', '.join(sorted(missing))}",
            fix_suggestion=f"Add missing fields to document header:\n{template}",
            auto_fixable=True,
            context={
                "missing_fields": sorted(missing),
                "current_headers": current_headers,
                "suggested_template": template,
            },
        )

    def _create_format_violation(
        self, file: Path, field: str, value: str, pattern: re.Pattern
    ) -> ViolationReport:
        """
        Create HDR-002 violation for invalid format.

        Args:
            file: File with format issue
            field: Field name
            value: Current value
            pattern: Expected pattern

        Returns:
            ViolationReport
        """
        # Suggest correct format based on field
        suggestions = {
            "Framework": "SDLC 5.1.1",
            "Sprint": "44",
            "Epic": "EP-04",
        }

        suggested = suggestions.get(field, "<correct-format>")

        return ViolationReport(
            rule_id="HDR-002",
            severity=Severity.WARNING,
            file_path=file,
            message=f"Invalid format for '{field}': '{value}'",
            fix_suggestion=f"Use format: '{field}: {suggested}'",
            auto_fixable=True,
            context={
                "field": field,
                "current_value": value,
                "expected_pattern": pattern.pattern,
                "suggested_value": suggested,
            },
        )

    def _generate_header_template(
        self, current_headers: Dict[str, str], missing: Set[str]
    ) -> str:
        """
        Generate header template with missing fields.

        Args:
            current_headers: Current headers
            missing: Missing field names

        Returns:
            Header template string
        """
        # Merge current + missing with defaults
        all_headers = current_headers.copy()

        for field in missing:
            if field == "Framework":
                all_headers[field] = "SDLC 5.1.1"
            elif field == "Sprint":
                all_headers[field] = "<sprint-number>"
            elif field == "Epic":
                all_headers[field] = "EP-<epic-number>"

        # Generate YAML frontmatter
        lines = ["---"]
        for field in ["Framework", "Sprint", "Epic"]:
            if field in all_headers:
                lines.append(f"{field}: {all_headers[field]}")
        lines.append("---")

        return "\n".join(lines)
