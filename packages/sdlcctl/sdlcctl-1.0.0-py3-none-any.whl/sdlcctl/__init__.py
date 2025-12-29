"""
SDLC 5.0.0 Structure Validator CLI (sdlcctl)

A CLI tool for validating SDLC 5.0.0 folder structure compliance.
Supports 4-Tier Classification: LITE, STANDARD, PROFESSIONAL, ENTERPRISE.

Usage:
    sdlcctl validate [--path PATH] [--tier TIER] [--format FORMAT]
    sdlcctl fix [--dry-run] [--interactive]
    sdlcctl init [--tier TIER] [--scaffold]
    sdlcctl report [--format FORMAT] [--output PATH]

Version: 1.0.0
Framework: SDLC 5.0.0
"""

__version__ = "1.0.0"
__author__ = "SDLC Orchestrator Team"
__framework__ = "SDLC 5.0.0"

from .validation.engine import SDLCValidator, ValidationResult
from .validation.tier import Tier, TierDetector
from .validation.scanner import FolderScanner
from .validation.p0 import P0ArtifactChecker

__all__ = [
    "SDLCValidator",
    "ValidationResult",
    "Tier",
    "TierDetector",
    "FolderScanner",
    "P0ArtifactChecker",
]
