#!/usr/bin/env python3
"""
SDLC 5.0.0 Pre-commit Hook.

Validates SDLC structure before commits.
Performance target: <2s execution time.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get project root from git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return Path.cwd()


def run_validation(
    project_root: Path,
    docs_root: str = "docs",
    tier: Optional[str] = None,
    strict: bool = False,
) -> int:
    """
    Run SDLC validation.

    Returns:
        Exit code (0 = pass, 1 = fail)
    """
    start_time = time.time()

    # Import here to avoid slow startup
    from ..validation.engine import SDLCValidator, ValidationSeverity
    from ..validation.tier import Tier

    # Parse tier if provided
    project_tier: Optional[Tier] = None
    if tier:
        try:
            project_tier = Tier(tier.lower())
        except ValueError:
            print(f"Warning: Invalid tier '{tier}', using default")

    # Initialize validator
    validator = SDLCValidator(
        project_root=project_root,
        docs_root=docs_root,
        tier=project_tier,
    )

    # Run validation
    result = validator.validate()
    elapsed = time.time() - start_time

    # Performance check
    if elapsed > 2.0:
        print(f"Warning: Validation took {elapsed:.1f}s (target: <2s)")

    # Output results
    if result.is_compliant:
        print(f"✓ SDLC 5.0.0 compliant ({result.compliance_score}/100) [{elapsed:.1f}s]")
        return 0
    else:
        print(f"✗ SDLC 5.0.0 validation failed ({result.compliance_score}/100)")
        print(f"  Errors: {result.error_count}, Warnings: {result.warning_count}")

        # Show errors
        for issue in result.issues:
            if issue.severity == ValidationSeverity.ERROR:
                print(f"  - [{issue.code}] {issue.message}")

        if strict:
            # Fail on any warning in strict mode
            for issue in result.issues:
                if issue.severity == ValidationSeverity.WARNING:
                    print(f"  - [{issue.code}] (warning) {issue.message}")

        print("\nRun 'sdlcctl fix' to automatically fix issues")

        if result.error_count > 0:
            return 1
        elif strict and result.warning_count > 0:
            return 1
        return 0


def main() -> int:
    """Pre-commit hook entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="SDLC 5.0.0 pre-commit hook")
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=None,
        help="Project root path",
    )
    parser.add_argument(
        "--docs",
        "-d",
        type=str,
        default="docs",
        help="Documentation folder name",
    )
    parser.add_argument(
        "--tier",
        "-t",
        type=str,
        default=None,
        help="Project tier",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Fail on warnings",
    )

    args = parser.parse_args()

    project_root = args.path or get_project_root()

    return run_validation(
        project_root=project_root,
        docs_root=args.docs,
        tier=args.tier,
        strict=args.strict,
    )


if __name__ == "__main__":
    sys.exit(main())
