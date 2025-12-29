"""
SDLC 5.1.1 Tier Detection and Classification.

4-Tier Classification:
- LITE: 1-2 people, 4 required stages (00, 01, 02, 04)
- STANDARD: 3-10 people, 6 required stages (00-02, 04-06)
- PROFESSIONAL: 10-50 people, 10 required stages (00-09)
- ENTERPRISE: 50+ people, 10 required stages + compliance (00-09)

Reference: SDLC-Enterprise-Framework/README.md (v5.1.1)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Tier(Enum):
    """SDLC 5.0.0 Project Tier Classification."""

    LITE = "lite"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

    @classmethod
    def from_string(cls, value: str) -> "Tier":
        """Convert string to Tier enum."""
        value_lower = value.lower().strip()
        for tier in cls:
            if tier.value == value_lower:
                return tier
        raise ValueError(f"Invalid tier: {value}. Must be one of: {[t.value for t in cls]}")


@dataclass
class TierRequirements:
    """Requirements for each project tier."""

    tier: Tier
    min_team_size: int
    max_team_size: Optional[int]
    min_stages: int
    required_stages: List[str]
    p0_required: bool
    max_depth: int
    compliance_required: List[str]

    def __post_init__(self):
        """Validate requirements."""
        if self.min_team_size < 1:
            raise ValueError("min_team_size must be at least 1")
        if self.max_team_size is not None and self.max_team_size < self.min_team_size:
            raise ValueError("max_team_size must be >= min_team_size")


# SDLC 5.1.1 Stage definitions (10 Stages: 00-09 + Archive folder)
# Reference: SDLC-Enterprise-Framework/README.md
# Note: 10-archive is a project-level archive folder, not a formal stage
STAGE_NAMES = {
    "00": "00-foundation",    # FOUNDATION - Strategic Discovery & Validation
    "01": "01-planning",      # PLANNING - Requirements & User Stories
    "02": "02-design",        # DESIGN - Architecture & Technical Design
    "03": "03-integrate",     # INTEGRATE - API Contracts & Third-party Setup
    "04": "04-build",         # BUILD - Development & Implementation
    "05": "05-test",          # TEST - Quality Assurance & Validation
    "06": "06-deploy",        # DEPLOY - Release & Deployment
    "07": "07-operate",       # OPERATE - Production Operations & Monitoring
    "08": "08-collaborate",   # COLLABORATE - Team Coordination & Knowledge
    "09": "09-govern",        # GOVERN - Compliance & Strategic Oversight
    "10": "10-archive",       # ARCHIVE - Project-level archive (optional, for legacy docs)
}

# Stage display names and questions (SDLC 5.1.1)
STAGE_QUESTIONS = {
    "00": "FOUNDATION",   # WHY? - Strategic Discovery & Validation
    "01": "PLANNING",     # WHAT? - Requirements & User Stories
    "02": "DESIGN",       # HOW? - Architecture & Technical Design
    "03": "INTEGRATE",    # How connect? - API Contracts & Third-party Setup
    "04": "BUILD",        # Building right? - Development & Implementation
    "05": "TEST",         # Works correctly? - Quality Assurance & Validation
    "06": "DEPLOY",       # Ship safely? - Release & Deployment
    "07": "OPERATE",      # Running reliably? - Production Operations & Monitoring
    "08": "COLLABORATE",  # Team effective? - Team Coordination & Knowledge
    "09": "GOVERN",       # Compliant? - Compliance & Strategic Oversight
    "10": "ARCHIVE",      # Archive - Project-level archive (optional)
}

# Old stage names for migration support (SDLC 4.9.x)
STAGE_NAMES_4_9 = {
    "00": "00-Project-Foundation",
    "01": "01-Planning-Analysis",
    "02": "02-Design-Architecture",
    "03": "03-Development-Implementation",  # Was BUILD
    "04": "04-Testing-Quality",             # Was TEST
    "05": "05-Deployment-Release",          # Was DEPLOY
    "06": "06-Operations-Maintenance",      # Was OPERATE
    "07": "07-Integration-APIs",            # Was INTEGRATE
    "08": "08-Team-Management",             # Was COLLABORATE
    "09": "09-Executive-Reports",           # Was GOVERN
    "10": "10-Archive",                     # Was ARCHIVE
}

# Tier-specific requirements
TIER_REQUIREMENTS = {
    Tier.LITE: TierRequirements(
        tier=Tier.LITE,
        min_team_size=1,
        max_team_size=2,
        min_stages=4,
        required_stages=["00", "01", "02", "03"],
        p0_required=False,
        max_depth=1,
        compliance_required=[],
    ),
    Tier.STANDARD: TierRequirements(
        tier=Tier.STANDARD,
        min_team_size=3,
        max_team_size=10,
        min_stages=6,
        required_stages=["00", "01", "02", "03", "04", "05"],
        p0_required=False,
        max_depth=2,
        compliance_required=[],
    ),
    Tier.PROFESSIONAL: TierRequirements(
        tier=Tier.PROFESSIONAL,
        min_team_size=10,
        max_team_size=50,
        min_stages=10,
        required_stages=["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
        p0_required=True,
        max_depth=3,
        compliance_required=[],
    ),
    Tier.ENTERPRISE: TierRequirements(
        tier=Tier.ENTERPRISE,
        min_team_size=50,
        max_team_size=None,
        min_stages=11,
        required_stages=["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
        p0_required=True,
        max_depth=4,
        compliance_required=["iso27001", "soc2"],
    ),
}


class TierDetector:
    """Detect project tier based on team size or configuration."""

    @staticmethod
    def detect_from_team_size(team_size: int) -> Tier:
        """
        Detect tier based on team size.

        Args:
            team_size: Number of people on the team

        Returns:
            Tier enum value

        Raises:
            ValueError: If team_size is invalid
        """
        if team_size < 1:
            raise ValueError("Team size must be at least 1")

        if team_size <= 2:
            return Tier.LITE
        elif team_size <= 10:
            return Tier.STANDARD
        elif team_size <= 50:
            return Tier.PROFESSIONAL
        else:
            return Tier.ENTERPRISE

    @staticmethod
    def get_requirements(tier: Tier) -> TierRequirements:
        """
        Get requirements for a specific tier.

        Args:
            tier: Tier enum value

        Returns:
            TierRequirements for the tier
        """
        return TIER_REQUIREMENTS[tier]

    @staticmethod
    def get_required_stages(tier: Tier) -> List[str]:
        """
        Get list of required stage IDs for a tier.

        Args:
            tier: Tier enum value

        Returns:
            List of stage IDs (e.g., ["00", "01", "02", "03"])
        """
        return TIER_REQUIREMENTS[tier].required_stages

    @staticmethod
    def get_stage_name(stage_id: str) -> Optional[str]:
        """
        Get full stage name from stage ID.

        Args:
            stage_id: Stage ID (e.g., "00", "01")

        Returns:
            Full stage name or None if invalid
        """
        return STAGE_NAMES.get(stage_id)

    @staticmethod
    def get_stage_question(stage_id: str) -> Optional[str]:
        """
        Get the question answered by a stage.

        Args:
            stage_id: Stage ID (e.g., "00", "01")

        Returns:
            Question (e.g., "WHY", "WHAT") or None if invalid
        """
        return STAGE_QUESTIONS.get(stage_id)

    @staticmethod
    def is_p0_required(tier: Tier) -> bool:
        """Check if P0 artifacts are required for a tier."""
        return TIER_REQUIREMENTS[tier].p0_required

    @staticmethod
    def validate_tier_for_team_size(tier: Tier, team_size: int) -> bool:
        """
        Check if a tier is valid for a given team size.

        Args:
            tier: Tier to validate
            team_size: Team size to check against

        Returns:
            True if tier is valid for team size
        """
        req = TIER_REQUIREMENTS[tier]
        if team_size < req.min_team_size:
            return False
        if req.max_team_size is not None and team_size > req.max_team_size:
            return False
        return True
