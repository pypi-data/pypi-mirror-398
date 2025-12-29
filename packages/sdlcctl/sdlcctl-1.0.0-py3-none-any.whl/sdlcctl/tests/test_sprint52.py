"""
=========================================================================
Test Suite for Sprint 52 Features
SDLC Orchestrator - Sprint 52

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 Implementation
Authority: Backend Team + CTO Approved

Test Coverage:
- Domain Detector (Vietnamese/English keyword detection)
- NLP Parser (Natural language to AppBlueprint)
- SSE Client (Event parsing)
- Progress Display (Event handling)
- Magic Mode Command (CLI integration)

References:
- docs/02-design/14-Technical-Specs/Vietnamese-Domain-Templates.md
=========================================================================
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner


# ============================================================================
# Domain Detector Tests
# ============================================================================


class TestDomainDetector:
    """Tests for DomainDetector class."""

    @pytest.fixture
    def detector(self):
        """Create DomainDetector instance."""
        from sdlcctl.lib.domain_detector import DomainDetector
        return DomainDetector()

    def test_detect_restaurant_vietnamese(self, detector):
        """Test detection of restaurant domain from Vietnamese text."""
        result = detector.detect("Nhà hàng Phở 24 với thực đơn và đặt bàn")
        assert result.domain == "restaurant"
        assert result.confidence > 0.5
        assert result.detected_language == "vi"
        assert len(result.matched_keywords) > 0

    def test_detect_restaurant_english(self, detector):
        """Test detection of restaurant domain from English text."""
        result = detector.detect("Restaurant menu and table reservation system")
        assert result.domain == "restaurant"
        assert result.confidence > 0.5
        assert result.detected_language == "en"

    def test_detect_ecommerce_vietnamese(self, detector):
        """Test detection of e-commerce domain from Vietnamese text."""
        result = detector.detect("Cửa hàng bán điện thoại online với giỏ hàng")
        assert result.domain == "ecommerce"
        assert result.confidence > 0.5
        assert result.detected_language == "vi"

    def test_detect_ecommerce_english(self, detector):
        """Test detection of e-commerce domain from English text."""
        result = detector.detect("Online store with shopping cart and checkout")
        assert result.domain == "ecommerce"
        assert result.confidence > 0.5

    def test_detect_hrm_vietnamese(self, detector):
        """Test detection of HRM domain from Vietnamese text."""
        result = detector.detect("Quản lý nhân sự, chấm công và tính lương nhân viên")
        assert result.domain == "hrm"
        assert result.confidence > 0.5
        assert result.detected_language == "vi"

    def test_detect_hrm_english(self, detector):
        """Test detection of HRM domain from English text."""
        result = detector.detect("HR management system for employee attendance and payroll")
        assert result.domain == "hrm"
        assert result.confidence > 0.5

    def test_detect_crm_vietnamese(self, detector):
        """Test detection of CRM domain from Vietnamese text."""
        result = detector.detect("Quản lý khách hàng và pipeline sales")
        assert result.domain == "crm"
        assert result.confidence > 0.5

    def test_detect_crm_english(self, detector):
        """Test detection of CRM domain from English text."""
        result = detector.detect("Customer relationship management with sales pipeline")
        assert result.domain == "crm"
        assert result.confidence > 0.5

    def test_detect_inventory_vietnamese(self, detector):
        """Test detection of inventory domain from Vietnamese text."""
        result = detector.detect("Quản lý kho và tồn kho hàng hóa")
        assert result.domain == "inventory"
        assert result.confidence > 0.5

    def test_detect_inventory_english(self, detector):
        """Test detection of inventory domain from English text."""
        result = detector.detect("Warehouse inventory and stock management")
        assert result.domain == "inventory"
        assert result.confidence > 0.5

    def test_detect_education_vietnamese(self, detector):
        """Test detection of education domain from Vietnamese text."""
        result = detector.detect("Trường học quản lý sinh viên và khóa học")
        assert result.domain == "education"
        assert result.confidence > 0.5

    def test_detect_healthcare_vietnamese(self, detector):
        """Test detection of healthcare domain from Vietnamese text."""
        result = detector.detect("Bệnh viện quản lý bệnh nhân và đặt lịch khám")
        assert result.domain == "healthcare"
        assert result.confidence > 0.5

    def test_detect_general_unknown_text(self, detector):
        """Test detection returns general for unknown text."""
        result = detector.detect("Random text without any domain keywords xyz123")
        assert result.domain == "general"
        assert result.confidence == 0.0

    def test_language_detection_vietnamese_diacritics(self, detector):
        """Test language detection with Vietnamese diacritics."""
        lang = detector._detect_language("quản lý nhà hàng và đặt bàn")
        assert lang == "vi"

    def test_language_detection_vietnamese_no_diacritics(self, detector):
        """Test language detection with Vietnamese words without diacritics."""
        lang = detector._detect_language("nha hang quan an")
        assert lang == "vi"

    def test_language_detection_english(self, detector):
        """Test language detection for English text."""
        lang = detector._detect_language("restaurant management system")
        assert lang == "en"

    def test_get_domain_description_vietnamese(self, detector):
        """Test getting domain description in Vietnamese."""
        desc = detector.get_domain_description("restaurant", "vi")
        assert "nhà hàng" in desc.lower()

    def test_get_domain_description_english(self, detector):
        """Test getting domain description in English."""
        desc = detector.get_domain_description("restaurant", "en")
        assert "restaurant" in desc.lower()

    def test_list_supported_domains(self, detector):
        """Test listing supported domains."""
        domains = detector.list_supported_domains()
        assert "restaurant" in domains
        assert "ecommerce" in domains
        assert "hrm" in domains
        assert "crm" in domains
        assert "inventory" in domains
        assert "education" in domains
        assert "healthcare" in domains


# ============================================================================
# NLP Parser Tests
# ============================================================================


class TestNLPParser:
    """Tests for NLPParser class."""

    @pytest.fixture
    def parser_vi(self):
        """Create NLPParser instance for Vietnamese."""
        from sdlcctl.lib.nlp_parser import NLPParser
        return NLPParser(lang="vi")

    @pytest.fixture
    def parser_en(self):
        """Create NLPParser instance for English."""
        from sdlcctl.lib.nlp_parser import NLPParser
        return NLPParser(lang="en")

    def test_parse_restaurant_vietnamese(self, parser_vi):
        """Test parsing Vietnamese restaurant description."""
        blueprint = parser_vi.parse(
            "Nhà hàng Phở 24 với menu và đặt bàn",
            domain="restaurant"
        )
        assert blueprint["name"] == "pho_24"
        assert blueprint["business_domain"] == "restaurant"
        assert len(blueprint["modules"]) > 0
        assert blueprint["metadata"]["language"] == "vi"

    def test_parse_ecommerce_english(self, parser_en):
        """Test parsing English e-commerce description."""
        blueprint = parser_en.parse(
            "Online phone store with cart and checkout",
            domain="ecommerce"
        )
        assert blueprint["name"] == "online_phone_store"
        assert blueprint["business_domain"] == "ecommerce"
        assert len(blueprint["modules"]) > 0

    def test_parse_custom_app_name(self, parser_vi):
        """Test parsing with custom app name."""
        blueprint = parser_vi.parse(
            "Quán cà phê",
            domain="restaurant",
            app_name="my_cafe_app"
        )
        assert blueprint["name"] == "my_cafe_app"

    def test_parse_includes_modules(self, parser_vi):
        """Test that parsed blueprint includes modules."""
        blueprint = parser_vi.parse(
            "Quản lý nhân sự với chấm công",
            domain="hrm"
        )
        modules = blueprint["modules"]
        assert len(modules) > 0
        # HRM should have employees module
        module_names = [m["name"] for m in modules]
        assert "employees" in module_names

    def test_parse_includes_entities(self, parser_vi):
        """Test that parsed blueprint includes entities."""
        blueprint = parser_vi.parse(
            "Cửa hàng bán điện thoại",
            domain="ecommerce"
        )
        modules = blueprint["modules"]
        # Products module should have entities
        products_module = next((m for m in modules if m["name"] == "products"), None)
        assert products_module is not None
        assert len(products_module["entities"]) > 0

    def test_parse_includes_operations(self, parser_vi):
        """Test that parsed blueprint includes operations."""
        blueprint = parser_vi.parse(
            "Nhà hàng với đặt bàn",
            domain="restaurant"
        )
        modules = blueprint["modules"]
        # Check if any module has operations
        has_operations = any(len(m.get("operations", [])) > 0 for m in modules)
        assert has_operations

    def test_extract_vietnamese_app_name(self, parser_vi):
        """Test extracting app name from Vietnamese text."""
        name = parser_vi._extract_app_name("Nhà hàng Phở Bò Kho 24h")
        assert name == "pho_bo_kho"
        # Should be ASCII-safe
        assert name.isascii()

    def test_remove_vietnamese_diacritics(self, parser_vi):
        """Test removing Vietnamese diacritics."""
        result = parser_vi._remove_vietnamese_diacritics("Phở Bò Kho")
        assert result == "Pho Bo Kho"
        assert result.isascii()


# ============================================================================
# SSE Event Types Tests
# ============================================================================


class TestSSEEventTypes:
    """Tests for SSE event type models."""

    def test_started_event(self):
        """Test StartedEvent model."""
        from sdlcctl.lib.sse_client import StartedEvent
        event = StartedEvent(
            type="started",
            timestamp="2025-12-26T10:00:00Z",
            session_id="session-123",
            model="qwen2.5-coder:32b",
            provider="ollama"
        )
        assert event.type == "started"
        assert event.model == "qwen2.5-coder:32b"
        assert event.provider == "ollama"

    def test_file_generated_event(self):
        """Test FileGeneratedEvent model."""
        from sdlcctl.lib.sse_client import FileGeneratedEvent
        event = FileGeneratedEvent(
            type="file_generated",
            timestamp="2025-12-26T10:00:00Z",
            session_id="session-123",
            path="app/main.py",
            content="# Main app",
            lines=10,
            language="python",
            syntax_valid=True
        )
        assert event.type == "file_generated"
        assert event.path == "app/main.py"
        assert event.lines == 10
        assert event.syntax_valid is True

    def test_completed_event(self):
        """Test CompletedEvent model."""
        from sdlcctl.lib.sse_client import CompletedEvent
        event = CompletedEvent(
            type="completed",
            timestamp="2025-12-26T10:00:00Z",
            session_id="session-123",
            total_files=10,
            total_lines=500,
            duration_ms=5000,
            success=True
        )
        assert event.type == "completed"
        assert event.total_files == 10
        assert event.total_lines == 500
        assert event.success is True

    def test_error_event(self):
        """Test ErrorEvent model."""
        from sdlcctl.lib.sse_client import ErrorEvent
        event = ErrorEvent(
            type="error",
            timestamp="2025-12-26T10:00:00Z",
            session_id="session-123",
            message="Generation failed",
            recovery_id="recovery-456"
        )
        assert event.type == "error"
        assert event.message == "Generation failed"
        assert event.recovery_id == "recovery-456"


# ============================================================================
# Progress Display Tests
# ============================================================================


class TestStreamingProgress:
    """Tests for StreamingProgress class."""

    @pytest.fixture
    def progress(self):
        """Create StreamingProgress instance with mock console."""
        from sdlcctl.lib.progress import StreamingProgress
        mock_console = MagicMock()
        return StreamingProgress(mock_console)

    def test_handle_started_event(self, progress):
        """Test handling started event."""
        from sdlcctl.lib.sse_client import StartedEvent
        event = StartedEvent(
            type="started",
            timestamp="2025-12-26T10:00:00Z",
            session_id="session-123",
            model="qwen2.5-coder:32b",
            provider="ollama"
        )
        progress.handle_event(event)
        assert progress.stats.provider == "ollama"
        assert progress.stats.model == "qwen2.5-coder:32b"

    def test_handle_file_generated_event(self, progress):
        """Test handling file_generated event."""
        from sdlcctl.lib.sse_client import FileGeneratedEvent
        event = FileGeneratedEvent(
            type="file_generated",
            timestamp="2025-12-26T10:00:00Z",
            session_id="session-123",
            path="app/main.py",
            content="# Main app",
            lines=10,
            language="python",
            syntax_valid=True
        )
        progress.handle_event(event)
        assert len(progress.files) == 1
        assert progress.files[0].path == "app/main.py"
        assert progress.files[0].lines == 10
        assert progress.files[0].valid is True

    def test_handle_completed_event(self, progress):
        """Test handling completed event."""
        from sdlcctl.lib.sse_client import CompletedEvent
        event = CompletedEvent(
            type="completed",
            timestamp="2025-12-26T10:00:00Z",
            session_id="session-123",
            total_files=10,
            total_lines=500,
            duration_ms=5000,
            success=True
        )
        progress.handle_event(event)
        assert progress.stats.total_files == 10
        assert progress.stats.total_lines == 500


# ============================================================================
# Vietnamese Prompts Tests
# ============================================================================


class TestVietnamesePrompts:
    """Tests for Vietnamese domain prompts."""

    def test_domain_prompts_available(self):
        """Test that all domain prompts are available."""
        from sdlcctl.prompts.vietnamese import DOMAIN_PROMPTS
        expected_domains = ["restaurant", "ecommerce", "hrm", "crm", "inventory", "education", "healthcare"]
        for domain in expected_domains:
            assert domain in DOMAIN_PROMPTS
            assert len(DOMAIN_PROMPTS[domain]) > 100  # Has substantial content

    def test_get_domain_prompt(self):
        """Test getting domain prompt."""
        from sdlcctl.prompts.vietnamese import get_domain_prompt
        prompt = get_domain_prompt("restaurant", "vi")
        assert "thực đơn" in prompt.lower()
        assert "đặt bàn" in prompt.lower()

    def test_entity_templates_available(self):
        """Test that entity templates are available."""
        from sdlcctl.prompts.vietnamese import ENTITY_TEMPLATES
        assert "menu_item" in ENTITY_TEMPLATES
        assert "reservation" in ENTITY_TEMPLATES
        assert "product" in ENTITY_TEMPLATES
        assert "order" in ENTITY_TEMPLATES
        assert "employee" in ENTITY_TEMPLATES
        assert "attendance" in ENTITY_TEMPLATES

    def test_get_entity_template(self):
        """Test getting entity template."""
        from sdlcctl.prompts.vietnamese import get_entity_template
        template = get_entity_template("menu_item")
        assert template is not None
        assert template["name"] == "MenuItem"
        assert len(template["fields"]) > 0

    def test_system_prompt_vi(self):
        """Test Vietnamese system prompt."""
        from sdlcctl.prompts.vietnamese import SYSTEM_PROMPT_VI
        assert "SDLC Orchestrator" in SYSTEM_PROMPT_VI
        assert "AppBlueprint" in SYSTEM_PROMPT_VI


# ============================================================================
# CLI Integration Tests
# ============================================================================


class TestMagicCommandCLI:
    """Tests for magic command CLI integration."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def cli_app(self):
        """Get CLI app."""
        from sdlcctl.cli import app
        return app

    def test_magic_command_help(self, runner, cli_app):
        """Test magic command help."""
        result = runner.invoke(cli_app, ["magic", "--help"])
        assert result.exit_code == 0
        assert "natural language" in result.output.lower()

    def test_magic_command_preview_mode(self, runner, cli_app, tmp_path):
        """Test magic command in preview mode (no code generation)."""
        result = runner.invoke(
            cli_app,
            [
                "magic",
                "Nhà hàng Phở 24",
                "--preview",
                "-o", str(tmp_path / "output"),
            ]
        )
        assert result.exit_code == 0
        assert "Blueprint" in result.output or "Preview" in result.output

    def test_generate_command_stream_flag_help(self, runner, cli_app):
        """Test generate command shows --stream flag."""
        result = runner.invoke(cli_app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--stream" in result.output

    def test_generate_command_resume_flag_help(self, runner, cli_app):
        """Test generate command shows --resume flag."""
        result = runner.invoke(cli_app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--resume" in result.output


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
