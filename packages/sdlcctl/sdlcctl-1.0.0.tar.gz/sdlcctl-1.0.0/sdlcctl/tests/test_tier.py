"""Tests for tier detection module."""

import pytest

from sdlcctl.validation.tier import (
    STAGE_NAMES,
    TIER_REQUIREMENTS,
    Tier,
    TierDetector,
    TierRequirements,
)


class TestTier:
    """Tests for Tier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert Tier.LITE.value == "lite"
        assert Tier.STANDARD.value == "standard"
        assert Tier.PROFESSIONAL.value == "professional"
        assert Tier.ENTERPRISE.value == "enterprise"

    def test_tier_from_string(self):
        """Test creating tier from string."""
        assert Tier("lite") == Tier.LITE
        assert Tier("standard") == Tier.STANDARD
        assert Tier("professional") == Tier.PROFESSIONAL
        assert Tier("enterprise") == Tier.ENTERPRISE

    def test_tier_invalid_string(self):
        """Test invalid tier string raises ValueError."""
        with pytest.raises(ValueError):
            Tier("invalid")


class TestTierRequirements:
    """Tests for TierRequirements dataclass."""

    def test_tier_requirements_creation(self):
        """Test TierRequirements creation."""
        req = TierRequirements(
            tier=Tier.LITE,
            min_team_size=1,
            max_team_size=2,
            min_stages=4,
            required_stages=["00", "01", "02", "03"],
            p0_required=False,
            max_depth=1,
            compliance_required=[],
        )
        assert req.min_stages == 4
        assert len(req.required_stages) == 4
        assert req.p0_required is False
        assert req.compliance_required == []

    def test_tier_requirements_with_compliance(self):
        """Test TierRequirements with compliance requirements."""
        req = TierRequirements(
            tier=Tier.ENTERPRISE,
            min_team_size=50,
            max_team_size=None,
            min_stages=11,
            required_stages=["00", "01"],
            p0_required=True,
            max_depth=4,
            compliance_required=["iso27001", "soc2"],
        )
        assert req.compliance_required == ["iso27001", "soc2"]


class TestTierDetector:
    """Tests for TierDetector class."""

    @pytest.fixture
    def detector(self):
        """Create TierDetector instance."""
        return TierDetector()

    def test_detect_lite_tier(self, detector):
        """Test LITE tier detection for small teams."""
        assert detector.detect_from_team_size(1) == Tier.LITE
        assert detector.detect_from_team_size(2) == Tier.LITE

    def test_detect_standard_tier(self, detector):
        """Test STANDARD tier detection for medium teams."""
        assert detector.detect_from_team_size(3) == Tier.STANDARD
        assert detector.detect_from_team_size(5) == Tier.STANDARD
        assert detector.detect_from_team_size(10) == Tier.STANDARD

    def test_detect_professional_tier(self, detector):
        """Test PROFESSIONAL tier detection."""
        assert detector.detect_from_team_size(11) == Tier.PROFESSIONAL
        assert detector.detect_from_team_size(25) == Tier.PROFESSIONAL
        assert detector.detect_from_team_size(50) == Tier.PROFESSIONAL

    def test_detect_enterprise_tier(self, detector):
        """Test ENTERPRISE tier detection for large teams."""
        assert detector.detect_from_team_size(51) == Tier.ENTERPRISE
        assert detector.detect_from_team_size(100) == Tier.ENTERPRISE
        assert detector.detect_from_team_size(500) == Tier.ENTERPRISE

    def test_detect_invalid_team_size(self, detector):
        """Test invalid team size raises ValueError."""
        with pytest.raises(ValueError):
            detector.detect_from_team_size(0)
        with pytest.raises(ValueError):
            detector.detect_from_team_size(-1)

    def test_get_requirements(self, detector):
        """Test getting requirements for each tier."""
        for tier in Tier:
            req = detector.get_requirements(tier)
            assert isinstance(req, TierRequirements)
            assert req.min_stages > 0
            assert len(req.required_stages) >= req.min_stages

    def test_get_required_stages(self, detector):
        """Test getting required stages for each tier."""
        # LITE requires 4 stages
        lite_stages = detector.get_required_stages(Tier.LITE)
        assert len(lite_stages) == 4
        assert "00" in lite_stages
        assert "03" in lite_stages

        # ENTERPRISE requires all 11 stages
        enterprise_stages = detector.get_required_stages(Tier.ENTERPRISE)
        assert len(enterprise_stages) == 11
        assert "10" in enterprise_stages

    def test_p0_required(self, detector):
        """Test P0 requirement check."""
        assert detector.is_p0_required(Tier.LITE) is False
        assert detector.is_p0_required(Tier.STANDARD) is False
        assert detector.is_p0_required(Tier.PROFESSIONAL) is True
        assert detector.is_p0_required(Tier.ENTERPRISE) is True


class TestStageNames:
    """Tests for STAGE_NAMES constant."""

    def test_all_stages_defined(self):
        """Test all 11 stages are defined."""
        expected_ids = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
        assert set(STAGE_NAMES.keys()) == set(expected_ids)

    def test_stage_naming_format(self):
        """Test stage names follow format XX-Name-Name."""
        for stage_id, stage_name in STAGE_NAMES.items():
            assert stage_name.startswith(f"{stage_id}-")
            # Should be kebab-case
            assert "-" in stage_name

    def test_specific_stage_names(self):
        """Test specific stage names."""
        assert STAGE_NAMES["00"] == "00-Project-Foundation"
        assert STAGE_NAMES["01"] == "01-Planning-Analysis"
        assert STAGE_NAMES["02"] == "02-Design-Architecture"
        assert STAGE_NAMES["03"] == "03-Development-Implementation"
        assert STAGE_NAMES["10"] == "10-Archive"


class TestTierRequirementsConstants:
    """Tests for TIER_REQUIREMENTS constant."""

    def test_all_tiers_have_requirements(self):
        """Test all tiers have defined requirements."""
        for tier in Tier:
            assert tier in TIER_REQUIREMENTS

    def test_tier_progression(self):
        """Test requirements increase with tier."""
        lite_req = TIER_REQUIREMENTS[Tier.LITE]
        standard_req = TIER_REQUIREMENTS[Tier.STANDARD]
        prof_req = TIER_REQUIREMENTS[Tier.PROFESSIONAL]
        enterprise_req = TIER_REQUIREMENTS[Tier.ENTERPRISE]

        # Min stages should increase
        assert lite_req.min_stages < standard_req.min_stages
        assert standard_req.min_stages < prof_req.min_stages
        assert prof_req.min_stages <= enterprise_req.min_stages

        # P0 should be required for higher tiers
        assert lite_req.p0_required is False
        assert enterprise_req.p0_required is True


class TestTierRequirementsValidation:
    """Tests for TierRequirements validation."""

    def test_invalid_min_team_size(self):
        """Test validation of min_team_size < 1."""
        with pytest.raises(ValueError, match="min_team_size must be at least 1"):
            TierRequirements(
                tier=Tier.LITE,
                min_team_size=0,  # Invalid
                max_team_size=2,
                min_stages=4,
                required_stages=["00", "01"],
                p0_required=False,
                max_depth=1,
                compliance_required=[],
            )

    def test_invalid_max_team_size(self):
        """Test validation of max_team_size < min_team_size."""
        with pytest.raises(ValueError, match="max_team_size must be >= min_team_size"):
            TierRequirements(
                tier=Tier.LITE,
                min_team_size=5,
                max_team_size=3,  # Invalid - less than min
                min_stages=4,
                required_stages=["00", "01"],
                p0_required=False,
                max_depth=1,
                compliance_required=[],
            )


class TestTierFromString:
    """Tests for Tier.from_string class method."""

    def test_from_string_lite(self):
        """Test converting 'lite' string to Tier."""
        assert Tier.from_string("lite") == Tier.LITE
        assert Tier.from_string("LITE") == Tier.LITE
        assert Tier.from_string("  lite  ") == Tier.LITE

    def test_from_string_standard(self):
        """Test converting 'standard' string to Tier."""
        assert Tier.from_string("standard") == Tier.STANDARD
        assert Tier.from_string("STANDARD") == Tier.STANDARD

    def test_from_string_professional(self):
        """Test converting 'professional' string to Tier."""
        assert Tier.from_string("professional") == Tier.PROFESSIONAL
        assert Tier.from_string("PROFESSIONAL") == Tier.PROFESSIONAL

    def test_from_string_enterprise(self):
        """Test converting 'enterprise' string to Tier."""
        assert Tier.from_string("enterprise") == Tier.ENTERPRISE
        assert Tier.from_string("ENTERPRISE") == Tier.ENTERPRISE

    def test_from_string_invalid(self):
        """Test invalid tier string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid tier"):
            Tier.from_string("invalid")


class TestTierDetectorStageHelpers:
    """Tests for TierDetector stage helper methods."""

    def test_get_stage_name_valid(self):
        """Test getting stage name for valid stage IDs."""
        assert TierDetector.get_stage_name("00") == "00-Project-Foundation"
        assert TierDetector.get_stage_name("01") == "01-Planning-Analysis"
        assert TierDetector.get_stage_name("10") == "10-Archive"

    def test_get_stage_name_invalid(self):
        """Test getting stage name for invalid stage ID."""
        assert TierDetector.get_stage_name("99") is None
        assert TierDetector.get_stage_name("invalid") is None

    def test_get_stage_question_valid(self):
        """Test getting stage question for valid stage IDs."""
        assert TierDetector.get_stage_question("00") == "WHY"
        assert TierDetector.get_stage_question("01") == "WHAT"
        assert TierDetector.get_stage_question("02") == "HOW"

    def test_get_stage_question_invalid(self):
        """Test getting stage question for invalid stage ID."""
        assert TierDetector.get_stage_question("99") is None


class TestTierValidationForTeamSize:
    """Tests for tier validation against team size."""

    def test_validate_lite_tier(self):
        """Test LITE tier validation."""
        assert TierDetector.validate_tier_for_team_size(Tier.LITE, 1) is True
        assert TierDetector.validate_tier_for_team_size(Tier.LITE, 2) is True
        assert TierDetector.validate_tier_for_team_size(Tier.LITE, 3) is False  # Too large

    def test_validate_standard_tier(self):
        """Test STANDARD tier validation."""
        assert TierDetector.validate_tier_for_team_size(Tier.STANDARD, 2) is False  # Too small
        assert TierDetector.validate_tier_for_team_size(Tier.STANDARD, 5) is True
        assert TierDetector.validate_tier_for_team_size(Tier.STANDARD, 10) is True
        assert TierDetector.validate_tier_for_team_size(Tier.STANDARD, 11) is False  # Too large

    def test_validate_professional_tier(self):
        """Test PROFESSIONAL tier validation."""
        assert TierDetector.validate_tier_for_team_size(Tier.PROFESSIONAL, 9) is False
        assert TierDetector.validate_tier_for_team_size(Tier.PROFESSIONAL, 25) is True
        assert TierDetector.validate_tier_for_team_size(Tier.PROFESSIONAL, 50) is True
        assert TierDetector.validate_tier_for_team_size(Tier.PROFESSIONAL, 51) is False

    def test_validate_enterprise_tier(self):
        """Test ENTERPRISE tier validation (no upper limit)."""
        assert TierDetector.validate_tier_for_team_size(Tier.ENTERPRISE, 49) is False
        assert TierDetector.validate_tier_for_team_size(Tier.ENTERPRISE, 50) is True
        assert TierDetector.validate_tier_for_team_size(Tier.ENTERPRISE, 1000) is True
