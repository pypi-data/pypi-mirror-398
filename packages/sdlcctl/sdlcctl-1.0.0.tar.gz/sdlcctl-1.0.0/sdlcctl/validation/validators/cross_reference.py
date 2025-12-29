"""
Cross-Reference Validator for SDLC 5.1.1 structure compliance.

Validates:
- REF-001: Broken internal links (references to non-existent files/folders)
- REF-002: Orphaned files (files not referenced by any document)
- SCANNER-001: Overall structure health metrics

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Set, Any
from collections import defaultdict

from ..base_validator import BaseValidator
from ..violation import ViolationReport, Severity


class CrossReferenceValidator(BaseValidator):
    """
    Validate cross-references and document relationships in SDLC structure.

    Checks:
    1. REF-001: Broken internal links (references to non-existent files/folders)
    2. REF-002: Orphaned files (files not referenced anywhere)
    3. SCANNER-001: Structure health metrics (completeness, consistency)

    Example violations:

    REF-001 - Broken link:
        docs/02-design/ADR-001.md references:
        - [Architecture](../03-system-architecture/architecture.md) ❌ NOT FOUND

    REF-002 - Orphaned file:
        docs/05-test/old-test-plan.md
        - Not referenced by any document ⚠️ UNUSED

    SCANNER-001 - Structure health:
        - Missing 2/5 core stages (01-planning, 04-build)
        - 15 broken links across 8 documents
        - 23 orphaned files (10% of total)
    """

    VALIDATOR_ID = "cross-reference"
    VALIDATOR_NAME = "Cross-Reference Validator"
    VALIDATOR_DESCRIPTION = "Detect broken links, orphaned files, and structure health issues"

    # Markdown link patterns
    MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    # Relative path pattern (../folder/file.md, ./file.md, folder/file.md)
    RELATIVE_LINK_PATTERN = re.compile(r'^\.{0,2}/')

    # File extensions to scan for cross-references
    SCANNABLE_EXTENSIONS = {'.md', '.txt', '.rst', '.adoc'}

    # Files to skip (binary, generated, etc.)
    SKIP_PATTERNS = {
        '.git',
        'node_modules',
        '__pycache__',
        '.venv',
        'venv',
        '.pytest_cache',
        '.mypy_cache',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.DS_Store',
    }

    def __init__(self, docs_root: Path):
        """
        Initialize cross-reference validator.

        Args:
            docs_root: Root directory of SDLC documentation structure
        """
        super().__init__(docs_root)

        # Track all files in docs_root
        self._all_files: Set[Path] = set()

        # Track references: {source_file: {target_path: line_number}}
        self._references: Dict[Path, Dict[str, int]] = defaultdict(dict)

        # Track which files are referenced: {target_path: [source_files]}
        self._referenced_by: Dict[Path, List[Path]] = defaultdict(list)

    def validate(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """
        Run cross-reference validation.

        Args:
            paths: Optional list of specific paths to validate
                   If None, validates entire docs_root

        Returns:
            List of violation reports
        """
        if not self.docs_root.exists():
            return [self._create_error_violation(
                "SCANNER-ERROR",
                self.docs_root,
                f"Documentation root does not exist: {self.docs_root}"
            )]

        violations: List[ViolationReport] = []

        # Step 1: Scan all files
        self._scan_all_files()

        # Step 2: Extract all references from markdown files
        self._extract_references()

        # Step 3: Validate references (REF-001: Broken links)
        violations.extend(self._check_broken_links())

        # Step 4: Find orphaned files (REF-002: Unreferenced files)
        violations.extend(self._check_orphaned_files())

        # Step 5: Generate structure health metrics (SCANNER-001)
        violations.extend(self._check_structure_health())

        return violations

    def _scan_all_files(self) -> None:
        """Scan docs_root and collect all file paths."""
        self._all_files.clear()

        for file_path in self.docs_root.rglob('*'):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip hidden/ignored patterns
            if self._should_skip(file_path):
                continue

            self._all_files.add(file_path)

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped during scanning."""
        # Check if any part of path matches skip patterns
        parts = path.parts
        for part in parts:
            if part.startswith('.') and part != '.':
                return True
            if part in self.SKIP_PATTERNS:
                return True

        return False

    def _extract_references(self) -> None:
        """
        Extract all markdown link references from scannable files.

        Populates self._references and self._referenced_by
        """
        self._references.clear()
        self._referenced_by.clear()

        for file_path in self._all_files:
            # Only scan text files
            if file_path.suffix not in self.SCANNABLE_EXTENSIONS:
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read
                continue

            # Find all markdown links
            for line_num, line in enumerate(content.split('\n'), start=1):
                for match in self.MARKDOWN_LINK_PATTERN.finditer(line):
                    link_text = match.group(1)
                    link_target = match.group(2)

                    # Skip external links (http://, https://, mailto:, etc.)
                    if ':' in link_target and not link_target.startswith('file://'):
                        continue

                    # Remove anchor fragments (#section)
                    if '#' in link_target:
                        link_target = link_target.split('#')[0]

                    # Skip empty links (just anchors)
                    if not link_target:
                        continue

                    # Resolve relative path
                    if self.RELATIVE_LINK_PATTERN.match(link_target):
                        target_path = (file_path.parent / link_target).resolve()
                    else:
                        # Absolute path relative to docs_root
                        target_path = (self.docs_root / link_target).resolve()

                    # Record reference
                    self._references[file_path][str(target_path)] = line_num

                    # Record reverse reference (if target exists)
                    if target_path in self._all_files:
                        self._referenced_by[target_path].append(file_path)

    def _check_broken_links(self) -> List[ViolationReport]:
        """
        REF-001: Check for broken internal links.

        Returns:
            List of violations for broken links
        """
        violations = []

        for source_file, targets in self._references.items():
            for target_str, line_num in targets.items():
                target_path = Path(target_str)

                # Check if target exists
                if not target_path.exists():
                    violations.append(ViolationReport(
                        rule_id="REF-001",
                        severity=Severity.ERROR,
                        file_path=source_file,
                        message=f"Broken link to non-existent file: {target_path.name}",
                        fix_suggestion=f"Update or remove link at line {line_num}",
                        auto_fixable=False,
                        context={
                            "source_file": str(source_file.relative_to(self.docs_root)),
                            "target_path": str(target_path),
                            "line_number": line_num,
                            "link_type": "relative" if self.RELATIVE_LINK_PATTERN.match(str(target_path)) else "absolute",
                        }
                    ))

        return violations

    def _check_orphaned_files(self) -> List[ViolationReport]:
        """
        REF-002: Check for orphaned files (not referenced by any document).

        Only reports orphaned markdown/text files that should typically be linked.
        Excludes infrastructure files (README.md, index.md, .gitignore, etc.)

        Returns:
            List of violations for orphaned files
        """
        violations = []

        # Files that are OK to be unreferenced (infrastructure, auto-generated, etc.)
        ALLOWED_UNREFERENCED = {
            'README.md',
            'readme.md',
            'INDEX.md',
            'index.md',
            '.gitignore',
            '.gitattributes',
            'CHANGELOG.md',
            'changelog.md',
            'LICENSE',
            'license.md',
        }

        # Check each scannable file
        for file_path in self._all_files:
            # Only check documentation files
            if file_path.suffix not in self.SCANNABLE_EXTENSIONS:
                continue

            # Skip allowed unreferenced files
            if file_path.name in ALLOWED_UNREFERENCED:
                continue

            # Check if file is referenced
            if file_path not in self._referenced_by or not self._referenced_by[file_path]:
                violations.append(ViolationReport(
                    rule_id="REF-002",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    message=f"Orphaned file: not referenced by any document",
                    fix_suggestion="Add references to this file from relevant documents, or consider archiving/removing if obsolete",
                    auto_fixable=False,
                    context={
                        "file_path": str(file_path.relative_to(self.docs_root)),
                        "file_size_bytes": file_path.stat().st_size,
                        "last_modified": file_path.stat().st_mtime,
                    }
                ))

        return violations

    def _check_structure_health(self) -> List[ViolationReport]:
        """
        SCANNER-001: Generate overall structure health metrics.

        Checks:
        - Broken link count and percentage
        - Orphaned file count and percentage
        - Documentation coverage
        - Cross-reference density

        Returns:
            List of informational violations with health metrics
        """
        violations = []

        # Calculate metrics
        total_files = len(self._all_files)
        total_scannable = sum(1 for f in self._all_files if f.suffix in self.SCANNABLE_EXTENSIONS)
        total_references = sum(len(targets) for targets in self._references.values())
        broken_links = sum(1 for targets in self._references.values()
                          for target in targets.keys()
                          if not Path(target).exists())
        orphaned_files = sum(1 for f in self._all_files
                            if f.suffix in self.SCANNABLE_EXTENSIONS
                            and f.name not in {'README.md', 'readme.md', 'INDEX.md', 'index.md'}
                            and (f not in self._referenced_by or not self._referenced_by[f]))

        # Calculate percentages
        broken_link_pct = (broken_links / total_references * 100) if total_references > 0 else 0
        orphaned_pct = (orphaned_files / total_scannable * 100) if total_scannable > 0 else 0

        # Determine health severity
        if broken_link_pct > 10 or orphaned_pct > 20:
            severity = Severity.WARNING
            health_status = "UNHEALTHY"
        elif broken_link_pct > 5 or orphaned_pct > 10:
            severity = Severity.INFO
            health_status = "NEEDS ATTENTION"
        else:
            severity = Severity.INFO
            health_status = "HEALTHY"

        # Generate health report
        violations.append(ViolationReport(
            rule_id="SCANNER-001",
            severity=severity,
            file_path=self.docs_root,
            message=f"Structure health: {health_status}",
            fix_suggestion=(
                f"Broken links: {broken_links} ({broken_link_pct:.1f}%), "
                f"Orphaned files: {orphaned_files} ({orphaned_pct:.1f}%)"
            ) if health_status != "HEALTHY" else "Structure is healthy",
            auto_fixable=False,
            context={
                "health_status": health_status,
                "total_files": total_files,
                "scannable_files": total_scannable,
                "total_references": total_references,
                "broken_links": broken_links,
                "broken_link_percentage": round(broken_link_pct, 2),
                "orphaned_files": orphaned_files,
                "orphaned_percentage": round(orphaned_pct, 2),
                "reference_density": round(total_references / total_scannable, 2) if total_scannable > 0 else 0,
            }
        ))

        return violations

    def _create_error_violation(
        self,
        rule_id: str,
        file_path: Path,
        message: str
    ) -> ViolationReport:
        """Helper to create error violations."""
        return ViolationReport(
            rule_id=rule_id,
            severity=Severity.ERROR,
            file_path=file_path,
            message=message,
            fix_suggestion="",
            auto_fixable=False,
            context={}
        )
