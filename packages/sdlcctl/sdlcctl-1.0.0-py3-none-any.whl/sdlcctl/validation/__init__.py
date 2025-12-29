"""SDLC 5.0.0 Validation Engine Components."""

from .engine import SDLCValidator, ValidationResult
from .tier import Tier, TierDetector
from .scanner import FolderScanner
from .p0 import P0ArtifactChecker

# Sprint 44: SDLC Structure Scanner Engine
from .violation import ViolationReport, Severity, ScanResult
from .base_validator import (
    BaseValidator,
    ValidationError,
    ValidatorRegistry,
    get_registry,
    register_validator,
    get_validator,
)
from .config import (
    RuleConfig,
    ScannerConfig,
    ConfigLoader,
    load_config,
)
from .structure_scanner import SDLCStructureScanner

# Import validators to trigger auto-registration
from . import validators  # noqa: F401

__all__ = [
    # Legacy components
    "SDLCValidator",
    "ValidationResult",
    "Tier",
    "TierDetector",
    "FolderScanner",
    "P0ArtifactChecker",
    # Sprint 44: Structure Scanner
    "ViolationReport",
    "Severity",
    "ScanResult",
    "BaseValidator",
    "ValidationError",
    "ValidatorRegistry",
    "get_registry",
    "register_validator",
    "get_validator",
    "RuleConfig",
    "ScannerConfig",
    "ConfigLoader",
    "load_config",
    "SDLCStructureScanner",
]
