"""
SDLC 5.0.0 P0 Artifact Checker.

Validates presence of 15 P0 (Priority 0) artifacts for AI discoverability.
These are the minimum required documents for AI assistants to understand a project.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from .tier import Tier, TierDetector


@dataclass
class P0Artifact:
    """Definition of a P0 artifact."""

    artifact_id: str
    name: str
    stage_id: str
    relative_path: str  # Relative to docs folder
    description: str
    required_tiers: Set[Tier] = field(default_factory=set)
    alternative_paths: List[str] = field(default_factory=list)


@dataclass
class P0CheckResult:
    """Result of checking a single P0 artifact."""

    artifact: P0Artifact
    found: bool
    actual_path: Optional[Path] = None
    file_size_bytes: int = 0
    has_content: bool = False
    issues: List[str] = field(default_factory=list)


@dataclass
class P0ValidationResult:
    """Result of validating all P0 artifacts."""

    project_root: Path
    tier: Tier
    artifacts_checked: int
    artifacts_found: int
    artifacts_missing: int
    results: Dict[str, P0CheckResult] = field(default_factory=dict)
    coverage_percent: float = 0.0
    is_compliant: bool = False


# 15 P0 Artifacts defined by SDLC 5.0.0
P0_ARTIFACTS: List[P0Artifact] = [
    # Stage 00: Project Foundation
    P0Artifact(
        artifact_id="P0-00-README",
        name="Stage 00 README",
        stage_id="00",
        relative_path="00-Project-Foundation/README.md",
        description="Entry point for Project Foundation stage",
        required_tiers={Tier.LITE, Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
    ),
    P0Artifact(
        artifact_id="P0-00-VISION",
        name="Product Vision",
        stage_id="00",
        relative_path="00-Project-Foundation/01-Vision/Product-Vision.md",
        description="Product vision and value proposition",
        required_tiers={Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
        alternative_paths=["00-Project-Foundation/Product-Vision.md"],
    ),
    # Stage 01: Planning & Analysis
    P0Artifact(
        artifact_id="P0-01-README",
        name="Stage 01 README",
        stage_id="01",
        relative_path="01-Planning-Analysis/README.md",
        description="Entry point for Planning & Analysis stage",
        required_tiers={Tier.LITE, Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
    ),
    P0Artifact(
        artifact_id="P0-01-FRD",
        name="Functional Requirements Document",
        stage_id="01",
        relative_path="01-Planning-Analysis/01-Requirements/Functional-Requirements-Document.md",
        description="Functional requirements specification",
        required_tiers={Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
        alternative_paths=[
            "01-Planning-Analysis/Functional-Requirements.md",
            "01-Planning-Analysis/Requirements.md",
        ],
    ),
    # Stage 02: Design & Architecture
    P0Artifact(
        artifact_id="P0-02-README",
        name="Stage 02 README",
        stage_id="02",
        relative_path="02-Design-Architecture/README.md",
        description="Entry point for Design & Architecture stage",
        required_tiers={Tier.LITE, Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
    ),
    P0Artifact(
        artifact_id="P0-02-SAD",
        name="System Architecture Document",
        stage_id="02",
        relative_path="02-Design-Architecture/01-System-Architecture/System-Architecture-Document.md",
        description="System architecture overview",
        required_tiers={Tier.PROFESSIONAL, Tier.ENTERPRISE},
        alternative_paths=[
            "02-Design-Architecture/System-Architecture.md",
            "02-Design-Architecture/Architecture.md",
        ],
    ),
    P0Artifact(
        artifact_id="P0-02-OPENAPI",
        name="OpenAPI Specification",
        stage_id="02",
        relative_path="02-Design-Architecture/03-API-Design/openapi.yml",
        description="API contract definition",
        required_tiers={Tier.PROFESSIONAL, Tier.ENTERPRISE},
        alternative_paths=[
            "02-Design-Architecture/openapi.yaml",
            "02-Design-Architecture/openapi.json",
            "02-Design-Architecture/03-API-Design/openapi.yaml",
        ],
    ),
    # Stage 03: Development & Implementation
    P0Artifact(
        artifact_id="P0-03-README",
        name="Stage 03 README",
        stage_id="03",
        relative_path="03-Development-Implementation/README.md",
        description="Entry point for Development stage",
        required_tiers={Tier.LITE, Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
    ),
    # Stage 04: Testing & QA
    P0Artifact(
        artifact_id="P0-04-README",
        name="Stage 04 README",
        stage_id="04",
        relative_path="04-Testing-QA/README.md",
        description="Entry point for Testing & QA stage",
        required_tiers={Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
        alternative_paths=[
            "04-Testing-Quality/README.md",
            "04-Testing/README.md",
        ],
    ),
    # Stage 05: Deployment & Release
    P0Artifact(
        artifact_id="P0-05-README",
        name="Stage 05 README",
        stage_id="05",
        relative_path="05-Deployment-Release/README.md",
        description="Entry point for Deployment stage",
        required_tiers={Tier.STANDARD, Tier.PROFESSIONAL, Tier.ENTERPRISE},
    ),
    # Stage 06: Operations & Monitoring
    P0Artifact(
        artifact_id="P0-06-README",
        name="Stage 06 README",
        stage_id="06",
        relative_path="06-Operations-Monitoring/README.md",
        description="Entry point for Operations stage",
        required_tiers={Tier.PROFESSIONAL, Tier.ENTERPRISE},
        alternative_paths=[
            "06-Operations-Maintenance/README.md",
            "06-Operations/README.md",
        ],
    ),
    # Stage 07: Integration Hub
    P0Artifact(
        artifact_id="P0-07-README",
        name="Stage 07 README",
        stage_id="07",
        relative_path="07-Integration-Hub/README.md",
        description="Entry point for Integration Hub stage",
        required_tiers={Tier.PROFESSIONAL, Tier.ENTERPRISE},
        alternative_paths=[
            "07-Integration-APIs/README.md",
            "07-Integration/README.md",
        ],
    ),
    # Stage 08: Team Management
    P0Artifact(
        artifact_id="P0-08-README",
        name="Stage 08 README",
        stage_id="08",
        relative_path="08-Team-Management/README.md",
        description="Entry point for Team Management stage",
        required_tiers={Tier.PROFESSIONAL, Tier.ENTERPRISE},
    ),
    # Stage 09: Executive Reports
    P0Artifact(
        artifact_id="P0-09-README",
        name="Stage 09 README",
        stage_id="09",
        relative_path="09-Executive-Reports/README.md",
        description="Entry point for Executive Reports stage",
        required_tiers={Tier.PROFESSIONAL, Tier.ENTERPRISE},
    ),
    # Stage 10: Archive
    P0Artifact(
        artifact_id="P0-10-README",
        name="Stage 10 README",
        stage_id="10",
        relative_path="10-Archive/README.md",
        description="Entry point for Archive stage",
        required_tiers={Tier.ENTERPRISE},
    ),
]


class P0ArtifactChecker:
    """
    Checker for SDLC 5.0.0 P0 (Priority 0) artifacts.

    P0 artifacts are the minimum required documents for AI assistants
    to understand and navigate a project effectively.
    """

    # Minimum content size to be considered valid (bytes)
    MIN_CONTENT_SIZE = 100

    def __init__(
        self,
        project_root: Path,
        docs_root: str = "docs",
        tier: Optional[Tier] = None,
        team_size: Optional[int] = None,
    ):
        """
        Initialize P0 artifact checker.

        Args:
            project_root: Root directory of the project
            docs_root: Relative path to docs folder (default: "docs")
            tier: Project tier (if known)
            team_size: Team size for tier detection (if tier not specified)
        """
        self.project_root = Path(project_root).resolve()
        self.docs_root = self.project_root / docs_root

        # Determine tier
        if tier:
            self.tier = tier
        elif team_size:
            detector = TierDetector()
            self.tier = detector.detect_from_team_size(team_size)
        else:
            # Default to PROFESSIONAL tier
            self.tier = Tier.PROFESSIONAL

    def check_all(self) -> P0ValidationResult:
        """
        Check all P0 artifacts for the project tier.

        Returns:
            P0ValidationResult with check results for all artifacts
        """
        results: Dict[str, P0CheckResult] = {}
        artifacts_found = 0

        # Filter artifacts by tier
        required_artifacts = [
            a for a in P0_ARTIFACTS if self.tier in a.required_tiers
        ]

        for artifact in required_artifacts:
            result = self._check_artifact(artifact)
            results[artifact.artifact_id] = result
            if result.found:
                artifacts_found += 1

        artifacts_checked = len(required_artifacts)
        artifacts_missing = artifacts_checked - artifacts_found

        coverage = (artifacts_found / artifacts_checked * 100) if artifacts_checked > 0 else 0.0

        # Compliance requires 100% of required artifacts
        is_compliant = artifacts_missing == 0

        return P0ValidationResult(
            project_root=self.project_root,
            tier=self.tier,
            artifacts_checked=artifacts_checked,
            artifacts_found=artifacts_found,
            artifacts_missing=artifacts_missing,
            results=results,
            coverage_percent=round(coverage, 1),
            is_compliant=is_compliant,
        )

    def _check_artifact(self, artifact: P0Artifact) -> P0CheckResult:
        """
        Check a single P0 artifact.

        Args:
            artifact: Artifact definition to check

        Returns:
            P0CheckResult with check details
        """
        issues: List[str] = []

        # Try primary path first
        primary_path = self.docs_root / artifact.relative_path
        if primary_path.exists() and primary_path.is_file():
            return self._create_result(artifact, primary_path, issues)

        # Try alternative paths
        for alt_path in artifact.alternative_paths:
            full_path = self.docs_root / alt_path
            if full_path.exists() and full_path.is_file():
                issues.append(
                    f"Found at alternative path: {alt_path} (expected: {artifact.relative_path})"
                )
                return self._create_result(artifact, full_path, issues)

        # Not found
        issues.append(f"File not found: {artifact.relative_path}")
        return P0CheckResult(
            artifact=artifact,
            found=False,
            actual_path=None,
            file_size_bytes=0,
            has_content=False,
            issues=issues,
        )

    def _create_result(
        self, artifact: P0Artifact, path: Path, issues: List[str]
    ) -> P0CheckResult:
        """
        Create a P0CheckResult for a found file.

        Args:
            artifact: Artifact definition
            path: Path where file was found
            issues: List of issues found

        Returns:
            P0CheckResult with file details
        """
        try:
            file_size = path.stat().st_size
            has_content = file_size >= self.MIN_CONTENT_SIZE

            if not has_content:
                issues.append(
                    f"File too small ({file_size} bytes). "
                    f"Minimum: {self.MIN_CONTENT_SIZE} bytes"
                )

            return P0CheckResult(
                artifact=artifact,
                found=True,
                actual_path=path,
                file_size_bytes=file_size,
                has_content=has_content,
                issues=issues,
            )
        except OSError as e:
            issues.append(f"Error reading file: {str(e)}")
            return P0CheckResult(
                artifact=artifact,
                found=False,
                actual_path=path,
                file_size_bytes=0,
                has_content=False,
                issues=issues,
            )

    def get_required_artifacts(self) -> List[P0Artifact]:
        """
        Get list of required P0 artifacts for current tier.

        Returns:
            List of P0Artifact definitions required for tier
        """
        return [a for a in P0_ARTIFACTS if self.tier in a.required_tiers]

    def get_missing_artifacts(self) -> List[P0Artifact]:
        """
        Get list of missing P0 artifacts.

        Returns:
            List of P0Artifact definitions that are missing
        """
        result = self.check_all()
        return [
            r.artifact
            for r in result.results.values()
            if not r.found
        ]

    def generate_missing_templates(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        Generate template files for missing P0 artifacts.

        Args:
            output_dir: Directory to write templates (default: docs_root)

        Returns:
            Dict mapping artifact_id to generated file path
        """
        output = output_dir or self.docs_root
        missing = self.get_missing_artifacts()
        generated: Dict[str, Path] = {}

        for artifact in missing:
            template = self._generate_template(artifact)
            file_path = output / artifact.relative_path

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write template
            file_path.write_text(template, encoding="utf-8")
            generated[artifact.artifact_id] = file_path

        return generated

    def _generate_template(self, artifact: P0Artifact) -> str:
        """
        Generate a template for a P0 artifact.

        Args:
            artifact: Artifact definition

        Returns:
            Template content as string
        """
        stage_id = artifact.stage_id
        stage_name = self._get_stage_name(stage_id)

        if artifact.artifact_id.endswith("-README"):
            return self._generate_readme_template(stage_id, stage_name)
        elif artifact.artifact_id.endswith("-VISION"):
            return self._generate_vision_template()
        elif artifact.artifact_id.endswith("-FRD"):
            return self._generate_frd_template()
        elif artifact.artifact_id.endswith("-SAD"):
            return self._generate_sad_template()
        elif artifact.artifact_id.endswith("-OPENAPI"):
            return self._generate_openapi_template()
        else:
            return self._generate_generic_template(artifact)

    def _get_stage_name(self, stage_id: str) -> str:
        """Get stage name from ID."""
        from .tier import STAGE_NAMES
        full_name = STAGE_NAMES.get(stage_id, f"{stage_id}-Unknown")
        # Extract just the name part (e.g., "Project Foundation" from "00-Project-Foundation")
        return full_name.split("-", 1)[1].replace("-", " ") if "-" in full_name else full_name

    def _generate_readme_template(self, stage_id: str, stage_name: str) -> str:
        """Generate README template for a stage."""
        return f"""# Stage {stage_id}: {stage_name}

**Version**: 5.0.0
**Stage**: {stage_id} - {stage_name}
**Status**: DRAFT
**Framework**: SDLC 5.0.0 Complete Lifecycle

---

## Purpose

[Describe the purpose of this stage in 2-3 sentences]

---

## Folder Structure

```
{stage_id}-{stage_name.replace(' ', '-')}/
├── README.md                         # This file (P0 entry point)
├── 01-[Subfolder]/                   # [Description]
├── 02-[Subfolder]/                   # [Description]
└── 99-Legacy/                        # Archived content (AI: DO NOT READ)
```

---

## Key Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [Document-Name.md](./Document-Name.md) | [Purpose] | Draft |

---

## AI Assistant Guidance

**DO Read**:
- This README for context
- Key documents listed above

**DO NOT Read**:
- `99-Legacy/` folder - Contains archived, outdated content

---

**Document Status**: P0 Entry Point
**Compliance**: SDLC 5.0.0 Stage {stage_id}
**Last Updated**: [Date]
**Owner**: [Role]

"""

    def _generate_vision_template(self) -> str:
        """Generate Product Vision template."""
        return """# Product Vision

**Version**: 1.0.0
**Status**: DRAFT
**Owner**: Product Owner
**Last Updated**: [Date]

---

## Vision Statement

[One-sentence vision statement that captures the product's ultimate purpose]

---

## Problem Statement

### Current State
[Describe the current pain points and challenges]

### Desired State
[Describe what success looks like]

### Gap
[What prevents users from achieving the desired state today?]

---

## Value Proposition

**For** [target customer]
**Who** [statement of need or opportunity]
**The** [product name]
**Is a** [product category]
**That** [key benefit, compelling reason to buy]
**Unlike** [primary competitive alternative]
**Our product** [primary differentiation]

---

## Success Metrics

| Metric | Current | Target | Timeframe |
|--------|---------|--------|-----------|
| [Metric 1] | [Value] | [Value] | [Date] |
| [Metric 2] | [Value] | [Value] | [Date] |

---

**Document Status**: P0 Artifact
**Compliance**: SDLC 5.0.0 Stage 00
**Last Updated**: [Date]

"""

    def _generate_frd_template(self) -> str:
        """Generate Functional Requirements Document template."""
        return """# Functional Requirements Document

**Version**: 1.0.0
**Status**: DRAFT
**Owner**: Product Manager
**Last Updated**: [Date]

---

## Overview

[Brief description of what this document covers]

---

## Functional Requirements

### FR-001: [Feature Name]

**Priority**: P0 | P1 | P2
**Status**: Draft | Approved | Implemented

**Description**: [Clear description of the requirement]

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Dependencies**: [List any dependencies]

---

### FR-002: [Feature Name]

**Priority**: P0 | P1 | P2
**Status**: Draft | Approved | Implemented

**Description**: [Clear description of the requirement]

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

---

## Non-Functional Requirements

### NFR-001: Performance

[Performance requirements]

### NFR-002: Security

[Security requirements]

---

**Document Status**: P0 Artifact
**Compliance**: SDLC 5.0.0 Stage 01
**Last Updated**: [Date]

"""

    def _generate_sad_template(self) -> str:
        """Generate System Architecture Document template."""
        return """# System Architecture Document

**Version**: 1.0.0
**Status**: DRAFT
**Owner**: Technical Architect
**Last Updated**: [Date]

---

## Overview

[Brief description of the system architecture]

---

## Architecture Principles

1. [Principle 1]
2. [Principle 2]
3. [Principle 3]

---

## High-Level Architecture

```
[ASCII diagram or description of high-level architecture]
```

---

## Components

### Component 1: [Name]

**Purpose**: [Description]
**Technology**: [Tech stack]
**Dependencies**: [List dependencies]

### Component 2: [Name]

**Purpose**: [Description]
**Technology**: [Tech stack]
**Dependencies**: [List dependencies]

---

## Data Architecture

[Description of data flow and storage]

---

## Security Architecture

[Security considerations and controls]

---

## Deployment Architecture

[Deployment topology and infrastructure]

---

**Document Status**: P0 Artifact
**Compliance**: SDLC 5.0.0 Stage 02
**Last Updated**: [Date]

"""

    def _generate_openapi_template(self) -> str:
        """Generate OpenAPI specification template."""
        return """openapi: 3.0.3
info:
  title: API Specification
  description: |
    API specification for the project.

    ## Overview
    [Brief description of the API]

  version: 1.0.0
  contact:
    name: API Support
    email: api@example.com

servers:
  - url: http://localhost:8000/api/v1
    description: Development server
  - url: https://api.example.com/v1
    description: Production server

tags:
  - name: health
    description: Health check endpoints

paths:
  /health:
    get:
      tags:
        - health
      summary: Health check
      description: Check if the API is running
      operationId: healthCheck
      responses:
        '200':
          description: API is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: healthy
                  timestamp:
                    type: string
                    format: date-time

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []

"""

    def _generate_generic_template(self, artifact: P0Artifact) -> str:
        """Generate a generic template."""
        return f"""# {artifact.name}

**Version**: 1.0.0
**Status**: DRAFT
**Owner**: [Role]
**Last Updated**: [Date]

---

## Purpose

{artifact.description}

---

## Content

[Add content here]

---

**Document Status**: P0 Artifact
**Compliance**: SDLC 5.0.0 Stage {artifact.stage_id}
**Last Updated**: [Date]

"""
