"""
SDLC Structure Scanner - Configuration Management.

Handles loading and validation of .sdlc-config.json configuration files.
Supports rule customization, ignore patterns, and validator selection.

Part of Sprint 44 - SDLC Structure Scanner Engine.

Framework: SDLC 5.1.1
Epic: EP-04 - SDLC Structure Enforcement
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .violation import Severity

logger = logging.getLogger(__name__)


@dataclass
class RuleConfig:
    """
    Configuration for a single validation rule.

    Attributes:
        rule_id: Rule identifier (e.g., "STAGE-001")
        enabled: Whether this rule is enabled
        severity: Override severity level
        auto_fix: Whether auto-fix is enabled for this rule
        options: Rule-specific options
    """

    rule_id: str
    enabled: bool = True
    severity: Optional[Severity] = None
    auto_fix: Optional[bool] = None
    options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, rule_id: str, data: Dict[str, Any]) -> "RuleConfig":
        """Create RuleConfig from dictionary."""
        severity = None
        if "severity" in data:
            severity = Severity(data["severity"])

        return cls(
            rule_id=rule_id,
            enabled=data.get("enabled", True),
            severity=severity,
            auto_fix=data.get("auto_fix"),
            options=data.get("options", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {
            "enabled": self.enabled,
        }

        if self.severity is not None:
            result["severity"] = self.severity.value

        if self.auto_fix is not None:
            result["auto_fix"] = self.auto_fix

        if self.options:
            result["options"] = self.options

        return result


@dataclass
class ScannerConfig:
    """
    Configuration for SDLC Structure Scanner.

    Attributes:
        validators: List of validator IDs to enable
        rules: Rule-specific configurations
        ignore_patterns: File/folder patterns to ignore
        max_workers: Maximum parallel workers
        docs_root: Override docs root path
        fail_on_error: Whether to fail scan on ERROR violations
        fail_on_warning: Whether to fail scan on WARNING violations
        output_format: Default output format (json, text, github)
    """

    validators: List[str] = field(default_factory=list)
    rules: Dict[str, RuleConfig] = field(default_factory=dict)
    ignore_patterns: Set[str] = field(default_factory=set)
    max_workers: int = 4
    docs_root: Optional[str] = None
    fail_on_error: bool = True
    fail_on_warning: bool = False
    output_format: str = "text"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScannerConfig":
        """
        Create ScannerConfig from dictionary.

        Args:
            data: Dictionary from .sdlc-config.json

        Returns:
            ScannerConfig instance
        """
        # Parse rules
        rules = {}
        if "rules" in data:
            for rule_id, rule_data in data["rules"].items():
                rules[rule_id] = RuleConfig.from_dict(rule_id, rule_data)

        return cls(
            validators=data.get("validators", []),
            rules=rules,
            ignore_patterns=set(data.get("ignore_patterns", [])),
            max_workers=data.get("max_workers", 4),
            docs_root=data.get("docs_root"),
            fail_on_error=data.get("fail_on_error", True),
            fail_on_warning=data.get("fail_on_warning", False),
            output_format=data.get("output_format", "text"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "validators": self.validators,
            "rules": {
                rule_id: rule_config.to_dict()
                for rule_id, rule_config in self.rules.items()
            },
            "ignore_patterns": list(self.ignore_patterns),
            "max_workers": self.max_workers,
            "docs_root": self.docs_root,
            "fail_on_error": self.fail_on_error,
            "fail_on_warning": self.fail_on_warning,
            "output_format": self.output_format,
        }

    def get_rule_config(self, rule_id: str) -> Optional[RuleConfig]:
        """
        Get configuration for a specific rule.

        Args:
            rule_id: Rule identifier

        Returns:
            RuleConfig if exists, None otherwise
        """
        return self.rules.get(rule_id)

    def is_rule_enabled(self, rule_id: str) -> bool:
        """
        Check if a rule is enabled.

        Args:
            rule_id: Rule identifier

        Returns:
            True if rule is enabled (or not configured = default enabled)
        """
        rule_config = self.get_rule_config(rule_id)
        if rule_config is None:
            return True  # Default: enabled if not configured
        return rule_config.enabled

    def get_rule_severity(self, rule_id: str, default: Severity) -> Severity:
        """
        Get severity for a rule, with fallback to default.

        Args:
            rule_id: Rule identifier
            default: Default severity if not configured

        Returns:
            Configured severity or default
        """
        rule_config = self.get_rule_config(rule_id)
        if rule_config is None or rule_config.severity is None:
            return default
        return rule_config.severity

    def is_auto_fix_enabled(self, rule_id: str, default: bool = False) -> bool:
        """
        Check if auto-fix is enabled for a rule.

        Args:
            rule_id: Rule identifier
            default: Default value if not configured

        Returns:
            True if auto-fix is enabled
        """
        rule_config = self.get_rule_config(rule_id)
        if rule_config is None or rule_config.auto_fix is None:
            return default
        return rule_config.auto_fix

    def should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: Path to check

        Returns:
            True if path matches any ignore pattern
        """
        path_str = str(path)
        for pattern in self.ignore_patterns:
            # Simple glob-style matching
            if pattern in path_str or path.match(pattern):
                return True
        return False


class ConfigLoader:
    """
    Loader for .sdlc-config.json configuration files.

    Searches for config files in project hierarchy and merges them.
    """

    CONFIG_FILENAME = ".sdlc-config.json"

    def __init__(self, project_root: Path):
        """
        Initialize config loader.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()

    def load(self, search_path: Optional[Path] = None) -> ScannerConfig:
        """
        Load configuration from .sdlc-config.json.

        Searches for config file starting from search_path up to project_root.
        Returns default config if no file found.

        Args:
            search_path: Path to start searching from (default: project_root)

        Returns:
            ScannerConfig instance
        """
        search_start = search_path or self.project_root

        # Find config file
        config_path = self._find_config_file(search_start)

        if config_path is None:
            logger.debug("No config file found, using defaults")
            return self._get_default_config()

        # Load config file
        try:
            return self._load_config_file(config_path)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            logger.info("Using default configuration")
            return self._get_default_config()

    def _find_config_file(self, start_path: Path) -> Optional[Path]:
        """
        Search for config file in directory hierarchy.

        Args:
            start_path: Path to start searching from

        Returns:
            Path to config file if found, None otherwise
        """
        current = start_path.resolve()

        # Search up to project root
        while current >= self.project_root:
            config_path = current / self.CONFIG_FILENAME
            if config_path.exists():
                logger.info(f"Found config file: {config_path}")
                return config_path

            # Move up one directory
            parent = current.parent
            if parent == current:
                break  # Reached filesystem root
            current = parent

        return None

    def _load_config_file(self, config_path: Path) -> ScannerConfig:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to .sdlc-config.json

        Returns:
            ScannerConfig instance

        Raises:
            ValueError: If config file is invalid
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate schema
            self._validate_config_schema(data)

            return ScannerConfig.from_dict(data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}") from e

    def _validate_config_schema(self, data: Dict[str, Any]) -> None:
        """
        Validate configuration schema.

        Args:
            data: Configuration dictionary

        Raises:
            ValueError: If schema is invalid
        """
        # Check top-level keys
        valid_keys = {
            "validators",
            "rules",
            "ignore_patterns",
            "max_workers",
            "docs_root",
            "fail_on_error",
            "fail_on_warning",
            "output_format",
        }

        invalid_keys = set(data.keys()) - valid_keys
        if invalid_keys:
            logger.warning(f"Unknown config keys (ignored): {invalid_keys}")

        # Validate validators
        if "validators" in data:
            if not isinstance(data["validators"], list):
                raise ValueError("'validators' must be a list")

        # Validate max_workers
        if "max_workers" in data:
            if not isinstance(data["max_workers"], int) or data["max_workers"] < 1:
                raise ValueError("'max_workers' must be a positive integer")

        # Validate output_format
        if "output_format" in data:
            valid_formats = {"json", "text", "github"}
            if data["output_format"] not in valid_formats:
                raise ValueError(
                    f"'output_format' must be one of {valid_formats}, "
                    f"got '{data['output_format']}'"
                )

    def _get_default_config(self) -> ScannerConfig:
        """
        Get default configuration.

        Returns:
            ScannerConfig with default values
        """
        return ScannerConfig(
            validators=[
                "stage-folder",
                "sequential-numbering",
                "naming-convention",
                "header-metadata",
                "cross-reference",
            ],
            max_workers=4,
            fail_on_error=True,
            fail_on_warning=False,
            output_format="text",
        )

    def save(self, config: ScannerConfig, output_path: Optional[Path] = None) -> Path:
        """
        Save configuration to .sdlc-config.json.

        Args:
            config: ScannerConfig to save
            output_path: Optional output path (default: project_root/.sdlc-config.json)

        Returns:
            Path to saved config file
        """
        if output_path is None:
            output_path = self.project_root / self.CONFIG_FILENAME

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)

        logger.info(f"Saved config to {output_path}")
        return output_path


def load_config(
    project_root: Path, search_path: Optional[Path] = None
) -> ScannerConfig:
    """
    Convenience function to load configuration.

    Args:
        project_root: Root directory of the project
        search_path: Optional path to start searching from

    Returns:
        ScannerConfig instance
    """
    loader = ConfigLoader(project_root)
    return loader.load(search_path)
