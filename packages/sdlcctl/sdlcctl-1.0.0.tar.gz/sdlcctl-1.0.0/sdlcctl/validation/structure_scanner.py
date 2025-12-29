"""
SDLC Structure Scanner - Main Orchestrator.

Coordinates multiple validators to scan and validate SDLC structure.
Supports parallel execution for performance.

Part of Sprint 44 - SDLC Structure Scanner Engine.

Framework: SDLC 5.1.1
Epic: EP-04 - SDLC Structure Enforcement
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Union

from .base_validator import BaseValidator, ValidationError, get_registry
from .config import ConfigLoader, ScannerConfig
from .violation import ScanResult, Severity, ViolationReport

logger = logging.getLogger(__name__)


class SDLCStructureScanner:
    """
    Main orchestrator for SDLC structure validation.

    Coordinates multiple validators to scan SDLC documentation structure.
    Supports parallel execution for performance (<30s for 1000+ files).

    Features:
    - Plugin-based validator architecture
    - Parallel execution with ThreadPoolExecutor
    - Configuration-driven rule selection
    - Multiple output formats (JSON, text, GitHub Actions)
    """

    # Default validators to run (can be overridden via config)
    DEFAULT_VALIDATORS = [
        "stage-folder",
        "sequential-numbering",
        "naming-convention",
        "header-metadata",
        "cross-reference",
    ]

    def __init__(
        self,
        docs_root: Path,
        config: Optional[Union[Dict, ScannerConfig]] = None,
        project_root: Optional[Path] = None,
    ):
        """
        Initialize SDLC structure scanner.

        Args:
            docs_root: Root directory of SDLC documentation
            config: Optional configuration (dict or ScannerConfig instance)
            project_root: Optional project root for config loading
        """
        self.docs_root = Path(docs_root).resolve()
        self.project_root = Path(project_root).resolve() if project_root else self.docs_root.parent

        if not self.docs_root.exists():
            raise ValueError(f"docs_root does not exist: {self.docs_root}")

        if not self.docs_root.is_dir():
            raise ValueError(f"docs_root is not a directory: {self.docs_root}")

        # Load or create configuration
        if isinstance(config, ScannerConfig):
            self.config = config
        elif isinstance(config, dict):
            self.config = ScannerConfig.from_dict(config)
        else:
            # Load from .sdlc-config.json or use defaults
            config_loader = ConfigLoader(self.project_root)
            self.config = config_loader.load(self.docs_root)

        # Get enabled validators from config
        enabled_validators = self.config.validators or self.DEFAULT_VALIDATORS

        # Create validator instances
        self.validators = self._create_validators(enabled_validators)

        logger.info(
            f"Initialized scanner with {len(self.validators)} validators: "
            f"{[v.VALIDATOR_ID for v in self.validators]}"
        )

    def _create_validators(self, validator_ids: List[str]) -> List[BaseValidator]:
        """
        Create validator instances from IDs.

        Args:
            validator_ids: List of validator IDs to instantiate

        Returns:
            List of validator instances

        Raises:
            ValidationError: If validator creation fails
        """
        registry = get_registry()
        validators = []

        for validator_id in validator_ids:
            try:
                instance = registry.create_instance(validator_id, self.docs_root)
                if instance:
                    validators.append(instance)
                else:
                    logger.warning(f"Validator '{validator_id}' not found in registry")
            except Exception as e:
                logger.error(f"Failed to create validator '{validator_id}': {e}")
                raise ValidationError(
                    f"Failed to create validator '{validator_id}': {e}"
                ) from e

        if not validators:
            raise ValidationError("No validators created - check configuration")

        return validators

    def scan(self, paths: Optional[List[Path]] = None) -> ScanResult:
        """
        Scan SDLC structure and validate against all enabled validators.

        Args:
            paths: Optional list of specific paths to validate.
                   If None, validates entire docs_root.

        Returns:
            ScanResult with all violations found

        Raises:
            ValidationError: If scan fails
        """
        start_time = time.time()

        logger.info(
            f"Starting scan of {self.docs_root} with {len(self.validators)} validators"
        )

        # Run validators in parallel
        all_violations = self._run_validators_parallel(paths)

        # Count files scanned (estimate based on docs_root size)
        files_scanned = self._count_files(self.docs_root)

        scan_time_ms = (time.time() - start_time) * 1000

        result = ScanResult(
            scan_path=self.docs_root,
            violations=all_violations,
            files_scanned=files_scanned,
            scan_time_ms=scan_time_ms,
        )

        logger.info(
            f"Scan complete: {len(all_violations)} violations found "
            f"({result.error_count} errors, {result.warning_count} warnings, "
            f"{result.info_count} info) in {scan_time_ms:.2f}ms"
        )

        return result

    def _run_validators_parallel(
        self, paths: Optional[List[Path]] = None
    ) -> List[ViolationReport]:
        """
        Run all validators in parallel using ThreadPoolExecutor.

        Args:
            paths: Optional list of specific paths to validate

        Returns:
            Combined list of all violations from all validators
        """
        all_violations: List[ViolationReport] = []

        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all validator tasks
            future_to_validator = {
                executor.submit(self._run_validator, validator, paths): validator
                for validator in self.validators
            }

            # Collect results as they complete
            for future in as_completed(future_to_validator):
                validator = future_to_validator[future]
                try:
                    violations = future.result()
                    all_violations.extend(violations)
                    logger.debug(
                        f"Validator '{validator.VALIDATOR_ID}' found "
                        f"{len(violations)} violations"
                    )
                except Exception as e:
                    logger.error(
                        f"Validator '{validator.VALIDATOR_ID}' failed: {e}",
                        exc_info=True,
                    )
                    # Add scanner error violation
                    all_violations.append(
                        ViolationReport(
                            rule_id="SCANNER-001",
                            severity=Severity.ERROR,
                            file_path=self.docs_root,
                            message=f"Validator '{validator.VALIDATOR_ID}' failed: {e}",
                            context={"validator_id": validator.VALIDATOR_ID},
                        )
                    )

        return all_violations

    def _run_validator(
        self, validator: BaseValidator, paths: Optional[List[Path]] = None
    ) -> List[ViolationReport]:
        """
        Run a single validator.

        Args:
            validator: Validator instance to run
            paths: Optional list of specific paths to validate

        Returns:
            List of violations found by this validator
        """
        try:
            violations = validator.validate(paths)
            return violations
        except Exception as e:
            logger.error(f"Validator '{validator.VALIDATOR_ID}' raised exception: {e}")
            raise

    def _count_files(self, root: Path) -> int:
        """
        Count files in directory tree.

        Args:
            root: Root directory to count from

        Returns:
            Number of files (excluding hidden files and ignored patterns)
        """
        count = 0
        try:
            for path in root.rglob("*"):
                if path.is_file() and not path.name.startswith("."):
                    count += 1
        except Exception as e:
            logger.warning(f"Error counting files: {e}")
            return 0

        return count

    def get_validator_info(self) -> List[Dict]:
        """
        Get information about all enabled validators.

        Returns:
            List of validator info dictionaries
        """
        return [v.get_validator_info() for v in self.validators]

    def format_json(self, result: ScanResult) -> str:
        """
        Format scan result as JSON.

        Args:
            result: ScanResult to format

        Returns:
            JSON string
        """
        return json.dumps(result.to_dict(), indent=2)

    def format_text(self, result: ScanResult, show_context: bool = False) -> str:
        """
        Format scan result as human-readable text.

        Args:
            result: ScanResult to format
            show_context: Whether to show violation context

        Returns:
            Formatted text string
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("SDLC Structure Validation Report")
        lines.append("=" * 80)
        lines.append(f"Scan path: {result.scan_path}")
        lines.append(f"Files scanned: {result.files_scanned}")
        lines.append(f"Scan time: {result.scan_time_ms:.2f}ms")
        lines.append("")

        # Summary
        lines.append("Summary:")
        lines.append(f"  Total violations: {len(result.violations)}")
        lines.append(f"  ❌ Errors: {result.error_count}")
        lines.append(f"  ⚠️  Warnings: {result.warning_count}")
        lines.append(f"  ℹ️  Info: {result.info_count}")
        lines.append(f"  🔧 Auto-fixable: {result.auto_fixable_count}")
        lines.append(f"  Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        lines.append("")

        if not result.violations:
            lines.append("✅ No violations found! Structure is compliant.")
            lines.append("=" * 80)
            return "\n".join(lines)

        # Group violations by severity
        errors = result.get_violations_by_severity(Severity.ERROR)
        warnings = result.get_violations_by_severity(Severity.WARNING)
        infos = result.get_violations_by_severity(Severity.INFO)

        # Show errors first
        if errors:
            lines.append(f"Errors ({len(errors)}):")
            lines.append("-" * 80)
            for v in errors:
                lines.append(str(v))
                if show_context and v.context:
                    lines.append(f"  Context: {v.context}")
            lines.append("")

        # Then warnings
        if warnings:
            lines.append(f"Warnings ({len(warnings)}):")
            lines.append("-" * 80)
            for v in warnings:
                lines.append(str(v))
                if show_context and v.context:
                    lines.append(f"  Context: {v.context}")
            lines.append("")

        # Finally info
        if infos:
            lines.append(f"Info ({len(infos)}):")
            lines.append("-" * 80)
            for v in infos:
                lines.append(str(v))
                if show_context and v.context:
                    lines.append(f"  Context: {v.context}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def format_github_actions(self, result: ScanResult) -> str:
        """
        Format scan result for GitHub Actions annotations.

        Args:
            result: ScanResult to format

        Returns:
            GitHub Actions annotation commands
        """
        lines = []

        for violation in result.violations:
            # GitHub Actions annotation format:
            # ::error file={name},line={line},title={title}::{message}
            severity_map = {
                Severity.ERROR: "error",
                Severity.WARNING: "warning",
                Severity.INFO: "notice",
            }

            gh_severity = severity_map.get(violation.severity, "notice")
            file_path = violation.file_path.relative_to(result.scan_path)

            annotation = (
                f"::{gh_severity} "
                f"file={file_path},"
                f"title={violation.rule_id}::"
                f"{violation.message}"
            )

            lines.append(annotation)

        return "\n".join(lines)

    def filter_violations(
        self, violations: List[ViolationReport]
    ) -> List[ViolationReport]:
        """
        Filter violations based on configuration.

        Args:
            violations: List of all violations

        Returns:
            Filtered list of violations
        """
        filtered = []

        for violation in violations:
            # Check if rule is enabled
            if not self.config.is_rule_enabled(violation.rule_id):
                logger.debug(f"Skipping disabled rule: {violation.rule_id}")
                continue

            # Check if path should be ignored
            if self.config.should_ignore(violation.file_path):
                logger.debug(f"Ignoring path: {violation.file_path}")
                continue

            # Override severity if configured
            original_severity = violation.severity
            configured_severity = self.config.get_rule_severity(
                violation.rule_id, original_severity
            )
            if configured_severity != original_severity:
                violation.severity = configured_severity
                logger.debug(
                    f"Override severity for {violation.rule_id}: "
                    f"{original_severity} → {configured_severity}"
                )

            filtered.append(violation)

        return filtered

    def get_config_summary(self) -> Dict[str, any]:
        """
        Get summary of current configuration.

        Returns:
            Dictionary with configuration summary
        """
        return {
            "validators": [v.VALIDATOR_ID for v in self.validators],
            "max_workers": self.config.max_workers,
            "ignore_patterns": list(self.config.ignore_patterns),
            "fail_on_error": self.config.fail_on_error,
            "fail_on_warning": self.config.fail_on_warning,
            "output_format": self.config.output_format,
            "rules_configured": len(self.config.rules),
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"SDLCStructureScanner(docs_root={self.docs_root}, "
            f"validators={len(self.validators)}, "
            f"max_workers={self.config.max_workers})"
        )
