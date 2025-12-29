"""
=========================================================================
Domain Detector - Auto-detect Business Domain
SDLC Orchestrator - Sprint 52.1

Version: 1.1.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52.1 English Keyword Enhancement
Authority: Backend Team + CTO Approved

Purpose:
- Auto-detect business domain from natural language description
- Support Vietnamese and English keywords
- Calculate confidence score for domain detection
- Provide matched keywords for transparency

References:
- docs/02-design/14-Technical-Specs/Vietnamese-Domain-Templates.md
=========================================================================
"""

import re
from dataclasses import dataclass


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class DomainResult:
    """Result of domain detection."""

    domain: str
    confidence: float
    matched_keywords: list[str]
    detected_language: str


# ============================================================================
# Domain Keywords
# ============================================================================

# Vietnamese and English keywords for each domain
DOMAIN_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "restaurant": {
        "vi": [
            "nhà hàng",
            "quán ăn",
            "thực đơn",
            "menu",
            "món ăn",
            "đặt bàn",
            "phở",
            "bún",
            "cơm",
            "đồ uống",
            "thức ăn",
            "bếp",
            "phục vụ",
            "order",
            "gọi món",
            "thanh toán",
            "hóa đơn",
            "ẩm thực",
            "quán cà phê",
            "cafe",
            "coffee",
            "trà sữa",
            "bánh mì",
            "lẩu",
            "nướng",
        ],
        "en": [
            "restaurant",
            "menu",
            "food",
            "dish",
            "table",
            "reservation",
            "order",
            "kitchen",
            "dining",
            "cafe",
            "coffee",
            "cook",
            "chef",
            "meal",
            "recipe",
            "waiter",
            "bill",
            "tip",
        ],
    },
    "ecommerce": {
        "vi": [
            "cửa hàng",
            "bán hàng",
            "sản phẩm",
            "giỏ hàng",
            "thanh toán",
            "đơn hàng",
            "ship",
            "giao hàng",
            "online",
            "điện thoại",
            "thương mại",
            "mua bán",
            "khuyến mãi",
            "giảm giá",
            "voucher",
            "mã giảm giá",
            "vnpay",
            "momo",
            "cod",
            "shopee",
            "lazada",
        ],
        "en": [
            "store",
            "shop",
            "product",
            "cart",
            "checkout",
            "payment",
            "shipping",
            "ecommerce",
            "e-commerce",
            "online",
            "order",
            "catalog",
            "inventory",
            "price",
            "discount",
            "coupon",
            "sale",
            "buy",
            "sell",
            "selling",
            "marketplace",
            "webshop",
            "retail",
            "wholesale",
            "merchant",
            "customer",
            "purchase",
            "transaction",
            "electronics",
            "phones",
            "gadgets",
        ],
    },
    "hrm": {
        "vi": [
            "nhân sự",
            "nhân viên",
            "lương",
            "chấm công",
            "nghỉ phép",
            "tuyển dụng",
            "phòng ban",
            "công ty",
            "hợp đồng",
            "bảo hiểm",
            "thưởng",
            "kpi",
            "đánh giá",
            "đào tạo",
            "ứng viên",
            "phỏng vấn",
            "onboarding",
            "hr",
        ],
        "en": [
            "hr",
            "human resource",
            "human resources",
            "employee",
            "employees",
            "staff",
            "salary",
            "salaries",
            "attendance",
            "leave",
            "payroll",
            "department",
            "company",
            "contract",
            "insurance",
            "bonus",
            "performance",
            "training",
            "recruitment",
            "interview",
            "onboarding",
            "workforce",
            "personnel",
            "hiring",
            "timesheet",
            "overtime",
            "benefits",
            "compensation",
            "management",
        ],
    },
    "crm": {
        "vi": [
            "khách hàng",
            "sales",
            "bán hàng",
            "lead",
            "pipeline",
            "giao dịch",
            "liên hệ",
            "chăm sóc",
            "tư vấn",
            "báo giá",
            "hợp đồng",
            "doanh số",
            "kpi",
            "telesales",
            "marketing",
        ],
        "en": [
            "customer",
            "customers",
            "crm",
            "sales",
            "lead",
            "leads",
            "deal",
            "deals",
            "pipeline",
            "contact",
            "contacts",
            "client",
            "clients",
            "opportunity",
            "prospect",
            "account",
            "accounts",
            "revenue",
            "quote",
            "proposal",
            "marketing",
            "relationship",
            "engagement",
            "conversion",
            "funnel",
            "campaign",
            "retention",
        ],
    },
    "inventory": {
        "vi": [
            "kho",
            "tồn kho",
            "nhập kho",
            "xuất kho",
            "hàng hóa",
            "kiểm kê",
            "quản lý kho",
            "vật tư",
            "nguyên liệu",
            "đóng gói",
            "barcode",
            "mã vạch",
            "lô hàng",
            "nhà cung cấp",
        ],
        "en": [
            "inventory",
            "stock",
            "warehouse",
            "supply",
            "storage",
            "goods",
            "material",
            "barcode",
            "batch",
            "supplier",
            "procurement",
            "logistics",
        ],
    },
    "education": {
        "vi": [
            "trường học",
            "sinh viên",
            "học sinh",
            "giáo viên",
            "lớp học",
            "khóa học",
            "điểm số",
            "bài giảng",
            "thi cử",
            "học phí",
            "đào tạo",
            "giáo dục",
        ],
        "en": [
            "school",
            "student",
            "teacher",
            "course",
            "class",
            "grade",
            "exam",
            "lesson",
            "education",
            "training",
            "tuition",
            "curriculum",
        ],
    },
    "healthcare": {
        "vi": [
            "bệnh viện",
            "bác sĩ",
            "bệnh nhân",
            "khám bệnh",
            "đặt lịch",
            "thuốc",
            "y tế",
            "phòng khám",
            "điều trị",
            "hồ sơ bệnh án",
        ],
        "en": [
            "hospital",
            "doctor",
            "patient",
            "appointment",
            "medicine",
            "healthcare",
            "clinic",
            "treatment",
            "medical",
            "prescription",
        ],
    },
}


# ============================================================================
# Domain Detector
# ============================================================================


class DomainDetector:
    """
    Detect business domain from natural language description.

    Supports both Vietnamese and English input with confidence scoring.
    """

    def __init__(self):
        """Initialize domain detector with keyword dictionaries."""
        self.domain_keywords = DOMAIN_KEYWORDS

    def detect(
        self,
        description: str,
        lang: str = "auto",
    ) -> DomainResult:
        """
        Detect domain from description.

        Args:
            description: Natural language description of the app
            lang: Language hint ("vi", "en", or "auto" for auto-detect)

        Returns:
            DomainResult with domain, confidence, and matched keywords
        """
        desc_lower = description.lower()

        # Detect language if auto
        detected_lang = lang if lang != "auto" else self._detect_language(desc_lower)

        # Score each domain
        scores: dict[str, tuple[int, list[str]]] = {}

        for domain, keywords in self.domain_keywords.items():
            matched: list[str] = []

            # Check keywords for relevant languages
            langs_to_check = ["vi", "en"] if lang == "auto" else [lang]

            for lang_key in langs_to_check:
                for kw in keywords.get(lang_key, []):
                    if self._keyword_matches(kw, desc_lower):
                        matched.append(kw)

            scores[domain] = (len(matched), matched)

        # Get best match
        best_domain = max(scores, key=lambda d: scores[d][0])
        count, matched = scores[best_domain]

        # Calculate confidence (3+ matches = 100% confidence)
        confidence = min(1.0, count / 3) if count > 0 else 0.0

        # If no matches, return general domain
        if count == 0:
            return DomainResult(
                domain="general",
                confidence=0.0,
                matched_keywords=[],
                detected_language=detected_lang,
            )

        return DomainResult(
            domain=best_domain,
            confidence=confidence,
            matched_keywords=matched,
            detected_language=detected_lang,
        )

    def _detect_language(self, text: str) -> str:
        """
        Detect if text is Vietnamese or English.

        Uses presence of Vietnamese diacritics as indicator.

        Args:
            text: Input text to analyze

        Returns:
            "vi" for Vietnamese, "en" for English
        """
        # Vietnamese diacritics pattern
        vietnamese_pattern = r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]"

        if re.search(vietnamese_pattern, text):
            return "vi"

        # Check for common Vietnamese words without diacritics
        vietnamese_words = [
            "nha hang",
            "cua hang",
            "nhan vien",
            "khach hang",
            "don hang",
            "san pham",
            "quan ly",
        ]
        for word in vietnamese_words:
            if word in text:
                return "vi"

        return "en"

    def _keyword_matches(self, keyword: str, text: str) -> bool:
        """
        Check if keyword matches in text.

        Uses word boundary matching for better accuracy.

        Args:
            keyword: Keyword to search for
            text: Text to search in

        Returns:
            True if keyword found, False otherwise
        """
        # For multi-word keywords, use simple substring match
        if " " in keyword:
            return keyword in text

        # For single words, use word boundary matching
        pattern = rf"\b{re.escape(keyword)}\b"
        return bool(re.search(pattern, text, re.IGNORECASE))

    def get_domain_description(self, domain: str, lang: str = "vi") -> str:
        """
        Get description for a domain.

        Args:
            domain: Domain name
            lang: Language for description

        Returns:
            Domain description string
        """
        descriptions = {
            "restaurant": {
                "vi": "Ứng dụng quản lý nhà hàng/quán ăn",
                "en": "Restaurant management application",
            },
            "ecommerce": {
                "vi": "Ứng dụng thương mại điện tử",
                "en": "E-commerce application",
            },
            "hrm": {
                "vi": "Ứng dụng quản lý nhân sự",
                "en": "Human Resource Management application",
            },
            "crm": {
                "vi": "Ứng dụng quản lý quan hệ khách hàng",
                "en": "Customer Relationship Management application",
            },
            "inventory": {
                "vi": "Ứng dụng quản lý kho",
                "en": "Inventory management application",
            },
            "education": {
                "vi": "Ứng dụng quản lý giáo dục",
                "en": "Education management application",
            },
            "healthcare": {
                "vi": "Ứng dụng quản lý y tế",
                "en": "Healthcare management application",
            },
            "general": {
                "vi": "Ứng dụng tổng quát",
                "en": "General application",
            },
        }

        return descriptions.get(domain, descriptions["general"]).get(lang, "")

    def list_supported_domains(self) -> list[str]:
        """
        Get list of supported domains.

        Returns:
            List of domain names
        """
        return list(self.domain_keywords.keys())
