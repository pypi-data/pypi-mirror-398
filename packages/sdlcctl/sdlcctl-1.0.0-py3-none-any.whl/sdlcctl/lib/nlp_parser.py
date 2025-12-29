"""
=========================================================================
Natural Language Parser - Convert Description to AppBlueprint
SDLC Orchestrator - Sprint 52

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 Implementation
Authority: Backend Team + CTO Approved

Purpose:
- Parse natural language description into AppBlueprint structure
- Use domain templates to generate modules and entities
- Extract app name from description
- Support Vietnamese and English input

References:
- docs/02-design/14-Technical-Specs/Vietnamese-Domain-Templates.md
- backend/app/schemas/onboarding.py (AppBlueprint schema)
=========================================================================
"""

import re
import unicodedata
from datetime import datetime
from typing import Any, Optional


# ============================================================================
# Domain Templates
# ============================================================================

# Templates for each business domain
DOMAIN_TEMPLATES: dict[str, dict[str, Any]] = {
    "restaurant": {
        "modules": [
            {
                "name": "menu",
                "description": "Menu management with dishes and categories",
                "entities": [
                    {
                        "name": "MenuItem",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "description", "type": "text", "required": False},
                            {"name": "price", "type": "decimal", "required": True},
                            {"name": "category_id", "type": "uuid", "required": True},
                            {"name": "image_url", "type": "string", "required": False},
                            {"name": "is_available", "type": "boolean", "default": True},
                        ],
                    },
                    {
                        "name": "Category",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "description", "type": "text", "required": False},
                            {"name": "display_order", "type": "integer", "default": 0},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "delete", "list"],
            },
            {
                "name": "reservations",
                "description": "Table reservation system",
                "entities": [
                    {
                        "name": "Reservation",
                        "fields": [
                            {"name": "customer_name", "type": "string", "required": True},
                            {"name": "customer_phone", "type": "string", "required": True},
                            {"name": "table_id", "type": "uuid", "required": True},
                            {"name": "reservation_time", "type": "datetime", "required": True},
                            {"name": "party_size", "type": "integer", "required": True},
                            {"name": "status", "type": "enum", "values": ["pending", "confirmed", "cancelled", "completed"]},
                            {"name": "notes", "type": "text", "required": False},
                        ],
                    },
                    {
                        "name": "Table",
                        "fields": [
                            {"name": "number", "type": "integer", "required": True},
                            {"name": "capacity", "type": "integer", "required": True},
                            {"name": "location", "type": "string", "required": False},
                            {"name": "is_available", "type": "boolean", "default": True},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "cancel", "list"],
            },
            {
                "name": "orders",
                "description": "Order management",
                "entities": [
                    {
                        "name": "Order",
                        "fields": [
                            {"name": "table_id", "type": "uuid", "required": True},
                            {"name": "status", "type": "enum", "values": ["pending", "preparing", "ready", "served", "paid"]},
                            {"name": "total_amount", "type": "decimal", "required": True},
                            {"name": "notes", "type": "text", "required": False},
                        ],
                    },
                    {
                        "name": "OrderItem",
                        "fields": [
                            {"name": "order_id", "type": "uuid", "required": True},
                            {"name": "menu_item_id", "type": "uuid", "required": True},
                            {"name": "quantity", "type": "integer", "required": True},
                            {"name": "unit_price", "type": "decimal", "required": True},
                            {"name": "notes", "type": "text", "required": False},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "list"],
            },
        ],
        "keywords": ["menu", "order", "table", "reservation", "dish", "food", "restaurant"],
    },
    "ecommerce": {
        "modules": [
            {
                "name": "products",
                "description": "Product catalog management",
                "entities": [
                    {
                        "name": "Product",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "description", "type": "text", "required": False},
                            {"name": "price", "type": "decimal", "required": True},
                            {"name": "sku", "type": "string", "required": True},
                            {"name": "category_id", "type": "uuid", "required": True},
                            {"name": "stock_quantity", "type": "integer", "default": 0},
                            {"name": "is_active", "type": "boolean", "default": True},
                        ],
                    },
                    {
                        "name": "Category",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "parent_id", "type": "uuid", "required": False},
                            {"name": "description", "type": "text", "required": False},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "delete", "list", "search"],
            },
            {
                "name": "cart",
                "description": "Shopping cart management",
                "entities": [
                    {
                        "name": "Cart",
                        "fields": [
                            {"name": "user_id", "type": "uuid", "required": True},
                            {"name": "session_id", "type": "string", "required": False},
                        ],
                    },
                    {
                        "name": "CartItem",
                        "fields": [
                            {"name": "cart_id", "type": "uuid", "required": True},
                            {"name": "product_id", "type": "uuid", "required": True},
                            {"name": "quantity", "type": "integer", "required": True},
                        ],
                    },
                ],
                "operations": ["add", "remove", "update", "clear", "get"],
            },
            {
                "name": "orders",
                "description": "Order processing",
                "entities": [
                    {
                        "name": "Order",
                        "fields": [
                            {"name": "user_id", "type": "uuid", "required": True},
                            {"name": "status", "type": "enum", "values": ["pending", "paid", "shipped", "delivered", "cancelled"]},
                            {"name": "total_amount", "type": "decimal", "required": True},
                            {"name": "shipping_address", "type": "text", "required": True},
                            {"name": "payment_method", "type": "string", "required": True},
                        ],
                    },
                    {
                        "name": "OrderItem",
                        "fields": [
                            {"name": "order_id", "type": "uuid", "required": True},
                            {"name": "product_id", "type": "uuid", "required": True},
                            {"name": "quantity", "type": "integer", "required": True},
                            {"name": "unit_price", "type": "decimal", "required": True},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "list", "cancel"],
            },
        ],
        "keywords": ["product", "cart", "checkout", "payment", "shipping", "store", "shop"],
    },
    "hrm": {
        "modules": [
            {
                "name": "employees",
                "description": "Employee management",
                "entities": [
                    {
                        "name": "Employee",
                        "fields": [
                            {"name": "employee_code", "type": "string", "required": True},
                            {"name": "full_name", "type": "string", "required": True},
                            {"name": "email", "type": "email", "required": True},
                            {"name": "phone", "type": "string", "required": False},
                            {"name": "department_id", "type": "uuid", "required": True},
                            {"name": "position_id", "type": "uuid", "required": True},
                            {"name": "hire_date", "type": "date", "required": True},
                            {"name": "status", "type": "enum", "values": ["active", "on_leave", "terminated"]},
                        ],
                    },
                    {
                        "name": "Department",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "code", "type": "string", "required": True},
                            {"name": "manager_id", "type": "uuid", "required": False},
                        ],
                    },
                    {
                        "name": "Position",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "level", "type": "integer", "required": True},
                            {"name": "base_salary", "type": "decimal", "required": False},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "list", "search"],
            },
            {
                "name": "attendance",
                "description": "Attendance tracking",
                "entities": [
                    {
                        "name": "Attendance",
                        "fields": [
                            {"name": "employee_id", "type": "uuid", "required": True},
                            {"name": "check_in", "type": "datetime", "required": True},
                            {"name": "check_out", "type": "datetime", "required": False},
                            {"name": "work_hours", "type": "decimal", "required": False},
                            {"name": "status", "type": "enum", "values": ["present", "late", "absent", "leave"]},
                        ],
                    },
                    {
                        "name": "Leave",
                        "fields": [
                            {"name": "employee_id", "type": "uuid", "required": True},
                            {"name": "leave_type", "type": "enum", "values": ["annual", "sick", "unpaid", "maternity"]},
                            {"name": "start_date", "type": "date", "required": True},
                            {"name": "end_date", "type": "date", "required": True},
                            {"name": "status", "type": "enum", "values": ["pending", "approved", "rejected"]},
                            {"name": "reason", "type": "text", "required": False},
                        ],
                    },
                ],
                "operations": ["check_in", "check_out", "request_leave", "approve", "list"],
            },
            {
                "name": "payroll",
                "description": "Payroll management",
                "entities": [
                    {
                        "name": "Salary",
                        "fields": [
                            {"name": "employee_id", "type": "uuid", "required": True},
                            {"name": "month", "type": "integer", "required": True},
                            {"name": "year", "type": "integer", "required": True},
                            {"name": "base_salary", "type": "decimal", "required": True},
                            {"name": "bonus", "type": "decimal", "default": 0},
                            {"name": "deductions", "type": "decimal", "default": 0},
                            {"name": "net_salary", "type": "decimal", "required": True},
                            {"name": "status", "type": "enum", "values": ["draft", "approved", "paid"]},
                        ],
                    },
                ],
                "operations": ["calculate", "approve", "pay", "list"],
            },
        ],
        "keywords": ["employee", "staff", "attendance", "salary", "leave", "hr", "payroll"],
    },
    "crm": {
        "modules": [
            {
                "name": "customers",
                "description": "Customer management",
                "entities": [
                    {
                        "name": "Customer",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "email", "type": "email", "required": True},
                            {"name": "phone", "type": "string", "required": False},
                            {"name": "company", "type": "string", "required": False},
                            {"name": "source", "type": "enum", "values": ["website", "referral", "social", "cold_call", "event"]},
                            {"name": "status", "type": "enum", "values": ["lead", "prospect", "customer", "churned"]},
                        ],
                    },
                    {
                        "name": "Contact",
                        "fields": [
                            {"name": "customer_id", "type": "uuid", "required": True},
                            {"name": "name", "type": "string", "required": True},
                            {"name": "title", "type": "string", "required": False},
                            {"name": "email", "type": "email", "required": False},
                            {"name": "phone", "type": "string", "required": False},
                            {"name": "is_primary", "type": "boolean", "default": False},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "list", "search"],
            },
            {
                "name": "deals",
                "description": "Sales pipeline management",
                "entities": [
                    {
                        "name": "Deal",
                        "fields": [
                            {"name": "customer_id", "type": "uuid", "required": True},
                            {"name": "title", "type": "string", "required": True},
                            {"name": "value", "type": "decimal", "required": True},
                            {"name": "stage", "type": "enum", "values": ["qualification", "proposal", "negotiation", "closed_won", "closed_lost"]},
                            {"name": "probability", "type": "integer", "default": 0},
                            {"name": "expected_close_date", "type": "date", "required": False},
                            {"name": "owner_id", "type": "uuid", "required": True},
                        ],
                    },
                    {
                        "name": "Pipeline",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "stages", "type": "json", "required": True},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "move_stage", "list"],
            },
            {
                "name": "activities",
                "description": "Activity tracking",
                "entities": [
                    {
                        "name": "Activity",
                        "fields": [
                            {"name": "customer_id", "type": "uuid", "required": True},
                            {"name": "deal_id", "type": "uuid", "required": False},
                            {"name": "type", "type": "enum", "values": ["call", "email", "meeting", "task", "note"]},
                            {"name": "subject", "type": "string", "required": True},
                            {"name": "description", "type": "text", "required": False},
                            {"name": "due_date", "type": "datetime", "required": False},
                            {"name": "status", "type": "enum", "values": ["pending", "completed", "cancelled"]},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "complete", "list"],
            },
        ],
        "keywords": ["customer", "lead", "deal", "pipeline", "sales", "crm", "contact"],
    },
    "inventory": {
        "modules": [
            {
                "name": "products",
                "description": "Product/goods management",
                "entities": [
                    {
                        "name": "Product",
                        "fields": [
                            {"name": "code", "type": "string", "required": True},
                            {"name": "name", "type": "string", "required": True},
                            {"name": "unit", "type": "string", "required": True},
                            {"name": "category_id", "type": "uuid", "required": True},
                            {"name": "min_stock", "type": "integer", "default": 0},
                            {"name": "current_stock", "type": "integer", "default": 0},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "list", "search"],
            },
            {
                "name": "stock",
                "description": "Stock movement tracking",
                "entities": [
                    {
                        "name": "StockIn",
                        "fields": [
                            {"name": "product_id", "type": "uuid", "required": True},
                            {"name": "quantity", "type": "integer", "required": True},
                            {"name": "supplier_id", "type": "uuid", "required": False},
                            {"name": "unit_cost", "type": "decimal", "required": True},
                            {"name": "batch_number", "type": "string", "required": False},
                            {"name": "received_date", "type": "date", "required": True},
                        ],
                    },
                    {
                        "name": "StockOut",
                        "fields": [
                            {"name": "product_id", "type": "uuid", "required": True},
                            {"name": "quantity", "type": "integer", "required": True},
                            {"name": "reason", "type": "enum", "values": ["sale", "transfer", "damage", "expired"]},
                            {"name": "reference", "type": "string", "required": False},
                            {"name": "issued_date", "type": "date", "required": True},
                        ],
                    },
                ],
                "operations": ["receive", "issue", "transfer", "list"],
            },
            {
                "name": "inventory",
                "description": "Inventory counting",
                "entities": [
                    {
                        "name": "InventoryCount",
                        "fields": [
                            {"name": "count_date", "type": "date", "required": True},
                            {"name": "status", "type": "enum", "values": ["draft", "in_progress", "completed"]},
                            {"name": "notes", "type": "text", "required": False},
                        ],
                    },
                    {
                        "name": "CountItem",
                        "fields": [
                            {"name": "count_id", "type": "uuid", "required": True},
                            {"name": "product_id", "type": "uuid", "required": True},
                            {"name": "system_qty", "type": "integer", "required": True},
                            {"name": "actual_qty", "type": "integer", "required": True},
                            {"name": "variance", "type": "integer", "required": True},
                        ],
                    },
                ],
                "operations": ["start", "count", "complete", "adjust"],
            },
        ],
        "keywords": ["inventory", "stock", "warehouse", "goods", "material", "storage"],
    },
    "general": {
        "modules": [
            {
                "name": "core",
                "description": "Core application module",
                "entities": [
                    {
                        "name": "Item",
                        "fields": [
                            {"name": "name", "type": "string", "required": True},
                            {"name": "description", "type": "text", "required": False},
                            {"name": "status", "type": "enum", "values": ["active", "inactive"]},
                        ],
                    },
                ],
                "operations": ["create", "read", "update", "delete", "list"],
            },
        ],
        "keywords": [],
    },
}


# ============================================================================
# NLP Parser
# ============================================================================


class NLPParser:
    """
    Parse natural language description into AppBlueprint structure.

    Uses domain templates to generate appropriate modules and entities.
    """

    def __init__(self, lang: str = "en"):
        """
        Initialize NLP parser.

        Args:
            lang: Language for output ("vi" or "en")
        """
        self.lang = lang
        self.domain_templates = DOMAIN_TEMPLATES

    def parse(
        self,
        description: str,
        domain: str,
        app_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Parse description into AppBlueprint structure.

        Args:
            description: Natural language app description
            domain: Business domain (from DomainDetector)
            app_name: Optional custom app name

        Returns:
            AppBlueprint dictionary
        """
        # Get template for domain
        template = self.domain_templates.get(domain, self.domain_templates["general"])

        # Extract or generate app name
        if not app_name:
            app_name = self._extract_app_name(description)

        # Build modules based on template and description
        modules = self._build_modules(template, description)

        # Generate blueprint
        blueprint: dict[str, Any] = {
            "name": app_name,
            "version": "1.0.0",
            "business_domain": domain,
            "description": description,
            "modules": modules,
            "metadata": {
                "generated_by": "magic_mode",
                "generated_at": datetime.utcnow().isoformat(),
                "language": self.lang,
                "source_description": description,
            },
        }

        return blueprint

    def _extract_app_name(self, description: str) -> str:
        """
        Extract app name from description.

        Uses first 2-3 meaningful words, converts to snake_case.

        Args:
            description: App description

        Returns:
            App name in snake_case
        """
        # Remove Vietnamese diacritics for ASCII-safe name
        normalized = self._remove_diacritics(description.lower())

        # Extract words (alphanumeric only)
        words = re.findall(r"[a-z0-9]+", normalized)

        # Filter out common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "for",
            "with",
            "and",
            "or",
            "to",
            "of",
            "in",
            "on",
            "at",
            "voi",
            "va",
            "cho",
            "cua",
            "trong",
            "tren",
            "de",
            "ung",
            "dung",
            "quan",
            "ly",
            "he",
            "thong",
        }

        filtered = [w for w in words if w not in stop_words and len(w) > 1]

        # Take first 3 words
        name_parts = filtered[:3]

        if not name_parts:
            return "my_app"

        return "_".join(name_parts)

    def _remove_diacritics(self, text: str) -> str:
        """
        Remove Vietnamese diacritics from text.

        Args:
            text: Input text with diacritics

        Returns:
            Text with diacritics removed
        """
        # Vietnamese character mappings
        replacements = {
            "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
            "ă": "a", "ằ": "a", "ắ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
            "â": "a", "ầ": "a", "ấ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
            "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
            "ê": "e", "ề": "e", "ế": "e", "ể": "e", "ễ": "e", "ệ": "e",
            "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
            "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
            "ô": "o", "ồ": "o", "ố": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
            "ơ": "o", "ờ": "o", "ớ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
            "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
            "ư": "u", "ừ": "u", "ứ": "u", "ử": "u", "ữ": "u", "ự": "u",
            "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
            "đ": "d",
        }

        result = text
        for viet, ascii_char in replacements.items():
            result = result.replace(viet, ascii_char)

        # Also use unicodedata for any remaining diacritics
        result = unicodedata.normalize("NFD", result)
        result = "".join(c for c in result if unicodedata.category(c) != "Mn")

        return result

    def _build_modules(
        self,
        template: dict[str, Any],
        description: str,
    ) -> list[dict[str, Any]]:
        """
        Build modules based on template and description.

        Filters modules based on keywords mentioned in description.

        Args:
            template: Domain template
            description: App description

        Returns:
            List of module dictionaries
        """
        desc_lower = description.lower()
        keywords = template.get("keywords", [])

        # If description mentions specific features, filter modules
        if keywords:
            relevant_modules = []

            for module in template["modules"]:
                module_name = module["name"]
                module_keywords = [
                    kw for kw in keywords if module_name in kw or kw in module_name
                ]

                # Check if any related keyword is in description
                if any(kw in desc_lower for kw in module_keywords):
                    relevant_modules.append(module)

            # If we found relevant modules, use them; otherwise use all
            if relevant_modules:
                return relevant_modules

        # Return all modules from template
        return template["modules"]

    def get_supported_domains(self) -> list[str]:
        """
        Get list of supported domains.

        Returns:
            List of domain names
        """
        return list(self.domain_templates.keys())
