"""Pytest configuration and shared fixtures for sdlcctl tests."""

import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def project_structure():
    """Create a complete project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create project files
        (project_root / "README.md").write_text("# Test Project\n")
        (project_root / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # Create docs folder
        docs_root = project_root / "docs"
        docs_root.mkdir()

        yield {
            "root": project_root,
            "docs": docs_root,
        }


@pytest.fixture
def lite_tier_project(project_structure):
    """Create a LITE tier compliant project structure."""
    from sdlcctl.validation.tier import STAGE_NAMES

    docs_root = project_structure["docs"]

    # Create required stages for LITE tier (00, 01, 02, 03)
    for stage_id in ["00", "01", "02", "03"]:
        stage_name = STAGE_NAMES[stage_id]
        stage_path = docs_root / stage_name
        stage_path.mkdir()
        (stage_path / "README.md").write_text(
            f"# {stage_name}\n\n"
            f"Documentation for stage {stage_id}. "
            f"This stage covers important aspects of the project lifecycle. "
            f"Please refer to the documents in this folder for more details."
        )
        # Create 99-Legacy with AI directive
        legacy = stage_path / "99-Legacy"
        legacy.mkdir()
        (legacy / "README.md").write_text(
            "# Legacy Content\n\n**AI Directive**: DO NOT READ this folder.\n"
        )

    return project_structure


@pytest.fixture
def standard_tier_project(project_structure):
    """Create a STANDARD tier compliant project structure."""
    from sdlcctl.validation.tier import STAGE_NAMES

    docs_root = project_structure["docs"]

    # Create required stages for STANDARD tier
    for stage_id in ["00", "01", "02", "03", "04", "05"]:
        stage_name = STAGE_NAMES[stage_id]
        stage_path = docs_root / stage_name
        stage_path.mkdir()
        (stage_path / "README.md").write_text(
            f"# {stage_name}\n\n"
            f"Documentation for stage {stage_id}. "
            f"This stage covers important aspects of the project lifecycle."
        )
        legacy = stage_path / "99-Legacy"
        legacy.mkdir()
        (legacy / "README.md").write_text(
            "# Legacy Content\n\n**AI Directive**: DO NOT READ this folder.\n"
        )

    return project_structure


@pytest.fixture
def professional_tier_project(project_structure):
    """Create a PROFESSIONAL tier compliant project structure with P0 artifacts."""
    from sdlcctl.validation.tier import STAGE_NAMES

    docs_root = project_structure["docs"]

    # Create all 10 required stages for PROFESSIONAL tier
    for stage_id in ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]:
        stage_name = STAGE_NAMES[stage_id]
        stage_path = docs_root / stage_name
        stage_path.mkdir()
        (stage_path / "README.md").write_text(
            f"# {stage_name}\n\n"
            f"Documentation for stage {stage_id}. "
            f"This stage covers important aspects of the project lifecycle. "
            f"Please refer to the documents in this folder for more details."
        )
        legacy = stage_path / "99-Legacy"
        legacy.mkdir()
        (legacy / "README.md").write_text(
            "# Legacy Content\n\n**AI Directive**: DO NOT READ this folder.\n"
        )

    # Create additional P0 artifacts for PROFESSIONAL tier
    # Vision document
    vision_path = docs_root / "00-Project-Foundation" / "01-Vision"
    vision_path.mkdir(exist_ok=True)
    (vision_path / "Product-Vision.md").write_text(
        "# Product Vision\n\n"
        "Our vision is to create a world-class platform. "
        "This document outlines the strategic direction and goals."
    )

    # FRD
    req_path = docs_root / "01-Planning-Analysis" / "01-Requirements"
    req_path.mkdir(exist_ok=True)
    (req_path / "Functional-Requirements-Document.md").write_text(
        "# Functional Requirements Document\n\n"
        "This document specifies the functional requirements. "
        "It includes user stories and acceptance criteria."
    )

    # Architecture
    arch_path = docs_root / "02-Design-Architecture" / "01-System-Architecture"
    arch_path.mkdir(exist_ok=True)
    (arch_path / "System-Architecture-Document.md").write_text(
        "# System Architecture Document\n\n"
        "This document describes the system architecture. "
        "It includes component diagrams and integration points."
    )

    # OpenAPI
    api_path = docs_root / "02-Design-Architecture" / "03-API-Design"
    api_path.mkdir(exist_ok=True)
    (api_path / "openapi.yml").write_text(
        "openapi: 3.0.3\n"
        "info:\n"
        "  title: Test API\n"
        "  version: 1.0.0\n"
        "paths: {}\n"
    )

    return project_structure
