"""
=========================================================================
Vietnamese Domain Prompts - Templates for Vietnamese SME
SDLC Orchestrator - Sprint 52

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 Implementation
Authority: Backend Team + CTO Approved

Purpose:
- Vietnamese domain-specific prompts for AI code generation
- Pre-built entity templates for common business domains
- Localized field names and descriptions
- Production-ready templates for Vietnam SME market

Supported Domains:
- restaurant: Nhà hàng, quán ăn, cafe
- ecommerce: Thương mại điện tử, cửa hàng online
- hrm: Quản lý nhân sự (Human Resource Management)
- crm: Quản lý khách hàng (Customer Relationship Management)
- inventory: Quản lý kho, tồn kho
- education: Giáo dục, đào tạo
- healthcare: Y tế, bệnh viện, phòng khám

References:
- docs/02-design/14-Technical-Specs/Vietnamese-Domain-Templates.md
=========================================================================
"""

from typing import Optional


# ============================================================================
# System Prompts
# ============================================================================

SYSTEM_PROMPT_VI = """
Bạn là AI Assistant của SDLC Orchestrator - hệ thống quản lý vòng đời phát triển phần mềm.

Nhiệm vụ: Phân tích mô tả từ người dùng và tạo AppBlueprint phù hợp.

Quy tắc quan trọng:
1. Xác định domain kinh doanh (restaurant, ecommerce, hrm, crm, inventory, education, healthcare)
2. Đề xuất các modules và entities phù hợp với nghiệp vụ Việt Nam
3. Tạo tên app dạng snake_case từ mô tả (ví dụ: pho24_restaurant, vinshop_ecommerce)
4. Luôn trả về JSON hợp lệ theo schema AppBlueprint
5. Sử dụng tiếng Anh cho tên biến/entity, tiếng Việt cho mô tả

Lưu ý đặc thù Việt Nam:
- Thanh toán: VNPay, Momo, ZaloPay, COD (tiền mặt khi nhận hàng)
- Vận chuyển: Giao Hàng Nhanh, Giao Hàng Tiết Kiệm, Viettel Post
- Thuế VAT: 10% cho hầu hết sản phẩm
- Định dạng số điện thoại: +84 hoặc 0xxx
- Định dạng tiền tệ: VND (đồng Việt Nam)
"""

SYSTEM_PROMPT_EN = """
You are an AI Assistant for SDLC Orchestrator - a software development lifecycle management system.

Your task: Analyze user descriptions and generate appropriate AppBlueprints.

Important rules:
1. Identify business domain (restaurant, ecommerce, hrm, crm, inventory, education, healthcare)
2. Suggest modules and entities appropriate for the business
3. Create app names in snake_case from description
4. Always return valid JSON following AppBlueprint schema
5. Use English for variable/entity names

Output format:
- Follow SDLC Orchestrator AppBlueprint schema
- Include all required fields
- Generate production-ready entity definitions
"""


# ============================================================================
# Domain-Specific Prompts (Vietnamese)
# ============================================================================

DOMAIN_PROMPTS: dict[str, str] = {
    "restaurant": """
Tạo ứng dụng quản lý nhà hàng với các tính năng:

📋 Quản lý thực đơn:
- Món ăn (tên, giá, hình ảnh, mô tả, thời gian chế biến)
- Danh mục (khai vị, món chính, tráng miệng, đồ uống)
- Combo/Set menu (gói món ăn giảm giá)
- Giá theo thời gian (happy hour, cuối tuần)

🪑 Đặt bàn online:
- Chọn bàn theo sơ đồ
- Chọn thời gian (ngày, giờ, số người)
- Xác nhận qua SMS/Zalo
- Lịch sử đặt bàn

🛒 Quản lý đơn hàng:
- Gọi món từ khách (dine-in)
- Đơn mang về (takeaway)
- Đơn giao hàng (delivery)
- Trạng thái đơn hàng real-time

💰 Thanh toán & Hóa đơn:
- Tiền mặt, thẻ, VNPay, Momo
- Hóa đơn VAT
- Tip/Boa phục vụ
- Tách bill/Gộp bill

👨‍🍳 Quản lý nhân viên:
- Phục vụ, bếp, thu ngân, quản lý
- Ca làm việc
- KPI nhân viên

📊 Báo cáo doanh thu:
- Theo ngày/tuần/tháng/năm
- Top món bán chạy
- Thống kê khách hàng
    """,

    "ecommerce": """
Tạo ứng dụng thương mại điện tử với các tính năng:

🛍️ Danh mục sản phẩm:
- Phân loại đa cấp (danh mục cha-con)
- Tìm kiếm sản phẩm
- Lọc theo giá, thương hiệu, đánh giá
- Sản phẩm biến thể (màu sắc, kích thước)

🛒 Giỏ hàng & Checkout:
- Thêm/xóa/cập nhật số lượng
- Mã giảm giá (voucher, coupon)
- Tính phí ship theo khu vực
- Lưu giỏ hàng (cho khách đăng nhập)

💳 Thanh toán đa dạng:
- VNPay, Momo, ZaloPay
- Thẻ ATM/Visa/Master
- COD (thanh toán khi nhận hàng)
- Trả góp (cho đơn lớn)

📦 Quản lý đơn hàng:
- Trạng thái đơn: chờ xác nhận, đang xử lý, đang giao, hoàn thành
- Theo dõi vận chuyển (GHN, GHTK, Viettel Post)
- Hoàn hàng/Đổi trả
- Lịch sử mua hàng

👤 Quản lý khách hàng:
- Đăng ký/Đăng nhập (email, SĐT, Facebook, Google)
- Điểm tích lũy (loyalty points)
- Danh sách yêu thích
- Địa chỉ giao hàng

📊 Báo cáo & Thống kê:
- Doanh số theo ngày/tháng
- Sản phẩm bán chạy
- Khách hàng VIP
- Tồn kho cảnh báo
    """,

    "hrm": """
Tạo ứng dụng quản lý nhân sự (HRM) với các tính năng:

👥 Hồ sơ nhân viên:
- Thông tin cá nhân (CMND/CCCD, địa chỉ, SĐT)
- Thông tin công việc (phòng ban, chức vụ, ngày vào)
- Hợp đồng lao động (loại, thời hạn, mức lương)
- Bằng cấp, chứng chỉ

⏰ Chấm công:
- Check-in/Check-out (vân tay, khuôn mặt, GPS)
- Tính giờ làm việc
- Làm thêm giờ (overtime)
- Đi muộn/Về sớm

📝 Nghỉ phép:
- Đơn xin nghỉ (phép năm, ốm, việc riêng)
- Quy trình duyệt đơn
- Số ngày phép còn lại
- Lịch nghỉ toàn công ty

💰 Bảng lương:
- Lương cơ bản + Phụ cấp
- Thưởng (KPI, lễ, Tết)
- Khấu trừ (BHXH, BHYT, thuế TNCN)
- Phiếu lương hàng tháng

📊 Đánh giá hiệu suất:
- KPI theo phòng ban
- Đánh giá 360 độ
- Mục tiêu OKR
- Xếp hạng nhân viên

🏢 Tổ chức:
- Sơ đồ tổ chức (org chart)
- Phòng ban, đơn vị
- Cấp bậc, chức vụ
    """,

    "crm": """
Tạo ứng dụng CRM (Quản lý quan hệ khách hàng) với các tính năng:

👤 Quản lý khách hàng:
- Thông tin liên hệ (tên, SĐT, email, công ty)
- Phân loại khách (tiềm năng, mới, VIP)
- Lịch sử tương tác
- Ghi chú, tags

📊 Pipeline bán hàng:
- Lead (khách tiềm năng)
- Opportunity (cơ hội)
- Stages (giai đoạn: tiếp cận → tư vấn → báo giá → đàm phán → chốt)
- Dự báo doanh số

📞 Hoạt động Sales:
- Gọi điện (log cuộc gọi)
- Email (mẫu email, theo dõi mở)
- Meeting (lịch hẹn, nhắc nhở)
- Ghi chú hoạt động

💼 Báo giá & Hợp đồng:
- Tạo báo giá (products, giá, chiết khấu)
- Phê duyệt báo giá
- Chuyển báo giá → Hợp đồng
- Theo dõi hợp đồng

📈 Báo cáo:
- Doanh số theo nhân viên/team
- Tỷ lệ chuyển đổi (conversion rate)
- Thời gian chốt deal trung bình
- Hiệu suất nguồn lead

👨‍💼 Nhân viên Sales:
- Phân công khách hàng
- KPI sales
- Bảng xếp hạng
    """,

    "inventory": """
Tạo ứng dụng quản lý kho với các tính năng:

📦 Quản lý hàng hóa:
- Mã sản phẩm (SKU), tên, đơn vị tính
- Giá nhập, giá bán
- Hình ảnh sản phẩm
- Barcode/QR code

🔄 Nhập kho:
- Phiếu nhập kho
- Nhà cung cấp
- Số lượng, đơn giá
- Ngày nhập, lô hàng

📤 Xuất kho:
- Phiếu xuất kho
- Lý do xuất (bán, chuyển kho, hủy)
- Số lượng xuất
- Ngày xuất

📊 Tồn kho:
- Số lượng tồn theo kho
- Cảnh báo tồn thấp
- Định mức tồn (min/max)
- Báo cáo tồn kho

📋 Kiểm kê:
- Phiếu kiểm kê định kỳ
- So sánh thực tế vs hệ thống
- Xử lý chênh lệch
- Lịch sử kiểm kê

🏭 Đa kho:
- Quản lý nhiều kho
- Chuyển kho nội bộ
- Theo dõi vị trí trong kho

🚚 Nhà cung cấp:
- Danh sách nhà cung cấp
- Công nợ nhà cung cấp
- Lịch sử nhập hàng
    """,

    "education": """
Tạo ứng dụng quản lý giáo dục với các tính năng:

👨‍🎓 Quản lý học viên:
- Thông tin cá nhân (họ tên, ngày sinh, CMND)
- Phụ huynh/Người liên hệ
- Lớp học, khóa học
- Học phí, công nợ

👩‍🏫 Quản lý giáo viên:
- Thông tin cá nhân
- Chuyên môn, bằng cấp
- Lịch dạy
- Lương, thưởng

📚 Khóa học & Lớp:
- Danh mục khóa học
- Lịch học (ngày, giờ, phòng)
- Học phí khóa học
- Số lượng học viên tối đa

📝 Điểm số & Đánh giá:
- Điểm bài tập, bài kiểm tra
- Điểm trung bình
- Xếp loại học lực
- Nhận xét của giáo viên

💰 Học phí:
- Thu học phí
- Giảm giá (học bổng, anh em)
- Công nợ học viên
- Hóa đơn thu tiền

📊 Báo cáo:
- Thống kê học viên
- Doanh thu học phí
- Hiệu suất giáo viên
- Tỷ lệ nghỉ học
    """,

    "healthcare": """
Tạo ứng dụng quản lý y tế với các tính năng:

👤 Hồ sơ bệnh nhân:
- Thông tin cá nhân (CMND, BHYT)
- Tiền sử bệnh án
- Dị ứng thuốc
- Người liên hệ khẩn cấp

👨‍⚕️ Quản lý bác sĩ:
- Thông tin bác sĩ
- Chuyên khoa
- Lịch làm việc
- Phòng khám

📅 Đặt lịch khám:
- Đặt lịch online
- Chọn bác sĩ, chuyên khoa
- Xác nhận qua SMS
- Nhắc nhở trước giờ khám

🩺 Khám bệnh:
- Triệu chứng, chẩn đoán
- Đơn thuốc (kê đơn điện tử)
- Chỉ định xét nghiệm
- Toa thuốc

💊 Quản lý thuốc:
- Danh mục thuốc
- Tồn kho thuốc
- Xuất thuốc theo đơn
- Cảnh báo hết hạn

💰 Viện phí:
- Phí khám
- Phí xét nghiệm
- Phí thuốc
- Thanh toán BHYT

📊 Báo cáo:
- Số lượt khám
- Doanh thu theo ngày
- Top bệnh phổ biến
- Hiệu suất bác sĩ
    """,
}


# ============================================================================
# Entity Templates
# ============================================================================

ENTITY_TEMPLATES: dict[str, dict] = {
    # Restaurant entities
    "menu_item": {
        "name": "MenuItem",
        "description_vi": "Món ăn trong thực đơn",
        "fields": [
            {"name": "name", "type": "string", "required": True, "description_vi": "Tên món ăn"},
            {"name": "description", "type": "text", "required": False, "description_vi": "Mô tả món"},
            {"name": "price", "type": "decimal", "required": True, "description_vi": "Giá bán (VND)"},
            {"name": "image_url", "type": "string", "required": False, "description_vi": "URL hình ảnh"},
            {"name": "category_id", "type": "uuid", "required": True, "description_vi": "Danh mục"},
            {"name": "prep_time_minutes", "type": "integer", "required": False, "description_vi": "Thời gian chế biến (phút)"},
            {"name": "is_available", "type": "boolean", "required": True, "description_vi": "Còn phục vụ"},
            {"name": "is_featured", "type": "boolean", "required": False, "description_vi": "Món nổi bật"},
        ],
    },
    "reservation": {
        "name": "Reservation",
        "description_vi": "Đặt bàn",
        "fields": [
            {"name": "customer_name", "type": "string", "required": True, "description_vi": "Tên khách"},
            {"name": "phone", "type": "string", "required": True, "description_vi": "Số điện thoại"},
            {"name": "table_id", "type": "uuid", "required": True, "description_vi": "Bàn đặt"},
            {"name": "reservation_date", "type": "date", "required": True, "description_vi": "Ngày đặt"},
            {"name": "reservation_time", "type": "time", "required": True, "description_vi": "Giờ đặt"},
            {"name": "party_size", "type": "integer", "required": True, "description_vi": "Số người"},
            {"name": "status", "type": "enum", "required": True, "description_vi": "Trạng thái", "values": ["pending", "confirmed", "cancelled", "completed"]},
            {"name": "notes", "type": "text", "required": False, "description_vi": "Ghi chú"},
        ],
    },

    # E-commerce entities
    "product": {
        "name": "Product",
        "description_vi": "Sản phẩm",
        "fields": [
            {"name": "sku", "type": "string", "required": True, "description_vi": "Mã sản phẩm"},
            {"name": "name", "type": "string", "required": True, "description_vi": "Tên sản phẩm"},
            {"name": "description", "type": "text", "required": False, "description_vi": "Mô tả"},
            {"name": "price", "type": "decimal", "required": True, "description_vi": "Giá bán (VND)"},
            {"name": "compare_price", "type": "decimal", "required": False, "description_vi": "Giá gốc (VND)"},
            {"name": "category_id", "type": "uuid", "required": True, "description_vi": "Danh mục"},
            {"name": "brand_id", "type": "uuid", "required": False, "description_vi": "Thương hiệu"},
            {"name": "stock_quantity", "type": "integer", "required": True, "description_vi": "Số lượng tồn"},
            {"name": "is_active", "type": "boolean", "required": True, "description_vi": "Đang bán"},
        ],
    },
    "order": {
        "name": "Order",
        "description_vi": "Đơn hàng",
        "fields": [
            {"name": "order_number", "type": "string", "required": True, "description_vi": "Mã đơn hàng"},
            {"name": "customer_id", "type": "uuid", "required": True, "description_vi": "Khách hàng"},
            {"name": "subtotal", "type": "decimal", "required": True, "description_vi": "Tạm tính (VND)"},
            {"name": "discount_amount", "type": "decimal", "required": False, "description_vi": "Giảm giá (VND)"},
            {"name": "shipping_fee", "type": "decimal", "required": True, "description_vi": "Phí ship (VND)"},
            {"name": "total", "type": "decimal", "required": True, "description_vi": "Tổng cộng (VND)"},
            {"name": "status", "type": "enum", "required": True, "description_vi": "Trạng thái", "values": ["pending", "confirmed", "processing", "shipping", "delivered", "cancelled"]},
            {"name": "payment_method", "type": "enum", "required": True, "description_vi": "Phương thức thanh toán", "values": ["cod", "vnpay", "momo", "zalopay", "bank_transfer"]},
            {"name": "payment_status", "type": "enum", "required": True, "description_vi": "Trạng thái thanh toán", "values": ["pending", "paid", "refunded"]},
            {"name": "shipping_address", "type": "text", "required": True, "description_vi": "Địa chỉ giao"},
        ],
    },

    # HRM entities
    "employee": {
        "name": "Employee",
        "description_vi": "Nhân viên",
        "fields": [
            {"name": "employee_code", "type": "string", "required": True, "description_vi": "Mã nhân viên"},
            {"name": "full_name", "type": "string", "required": True, "description_vi": "Họ và tên"},
            {"name": "email", "type": "email", "required": True, "description_vi": "Email"},
            {"name": "phone", "type": "string", "required": True, "description_vi": "Số điện thoại"},
            {"name": "id_card", "type": "string", "required": True, "description_vi": "CMND/CCCD"},
            {"name": "department_id", "type": "uuid", "required": True, "description_vi": "Phòng ban"},
            {"name": "position_id", "type": "uuid", "required": True, "description_vi": "Chức vụ"},
            {"name": "hire_date", "type": "date", "required": True, "description_vi": "Ngày vào làm"},
            {"name": "base_salary", "type": "decimal", "required": True, "description_vi": "Lương cơ bản (VND)"},
            {"name": "status", "type": "enum", "required": True, "description_vi": "Trạng thái", "values": ["active", "on_leave", "terminated"]},
        ],
    },
    "attendance": {
        "name": "Attendance",
        "description_vi": "Chấm công",
        "fields": [
            {"name": "employee_id", "type": "uuid", "required": True, "description_vi": "Nhân viên"},
            {"name": "date", "type": "date", "required": True, "description_vi": "Ngày"},
            {"name": "check_in", "type": "datetime", "required": False, "description_vi": "Giờ vào"},
            {"name": "check_out", "type": "datetime", "required": False, "description_vi": "Giờ ra"},
            {"name": "work_hours", "type": "decimal", "required": False, "description_vi": "Số giờ làm"},
            {"name": "overtime_hours", "type": "decimal", "required": False, "description_vi": "Giờ tăng ca"},
            {"name": "status", "type": "enum", "required": True, "description_vi": "Trạng thái", "values": ["present", "absent", "late", "half_day", "leave"]},
        ],
    },

    # CRM entities
    "customer": {
        "name": "Customer",
        "description_vi": "Khách hàng",
        "fields": [
            {"name": "name", "type": "string", "required": True, "description_vi": "Tên khách hàng"},
            {"name": "email", "type": "email", "required": False, "description_vi": "Email"},
            {"name": "phone", "type": "string", "required": True, "description_vi": "Số điện thoại"},
            {"name": "company", "type": "string", "required": False, "description_vi": "Công ty"},
            {"name": "address", "type": "text", "required": False, "description_vi": "Địa chỉ"},
            {"name": "source", "type": "enum", "required": False, "description_vi": "Nguồn", "values": ["website", "facebook", "referral", "cold_call", "event"]},
            {"name": "type", "type": "enum", "required": True, "description_vi": "Loại khách", "values": ["lead", "prospect", "customer", "vip"]},
            {"name": "assigned_to", "type": "uuid", "required": False, "description_vi": "Nhân viên phụ trách"},
        ],
    },
    "deal": {
        "name": "Deal",
        "description_vi": "Cơ hội kinh doanh",
        "fields": [
            {"name": "title", "type": "string", "required": True, "description_vi": "Tên deal"},
            {"name": "customer_id", "type": "uuid", "required": True, "description_vi": "Khách hàng"},
            {"name": "value", "type": "decimal", "required": True, "description_vi": "Giá trị (VND)"},
            {"name": "stage", "type": "enum", "required": True, "description_vi": "Giai đoạn", "values": ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]},
            {"name": "probability", "type": "integer", "required": False, "description_vi": "Xác suất thắng (%)"},
            {"name": "expected_close_date", "type": "date", "required": False, "description_vi": "Ngày dự kiến chốt"},
            {"name": "assigned_to", "type": "uuid", "required": True, "description_vi": "Nhân viên sales"},
        ],
    },

    # Inventory entities
    "inventory_item": {
        "name": "InventoryItem",
        "description_vi": "Hàng hóa trong kho",
        "fields": [
            {"name": "sku", "type": "string", "required": True, "description_vi": "Mã hàng"},
            {"name": "name", "type": "string", "required": True, "description_vi": "Tên hàng"},
            {"name": "unit", "type": "string", "required": True, "description_vi": "Đơn vị tính"},
            {"name": "cost_price", "type": "decimal", "required": True, "description_vi": "Giá nhập (VND)"},
            {"name": "sell_price", "type": "decimal", "required": False, "description_vi": "Giá bán (VND)"},
            {"name": "quantity", "type": "integer", "required": True, "description_vi": "Số lượng tồn"},
            {"name": "min_quantity", "type": "integer", "required": False, "description_vi": "Tồn tối thiểu"},
            {"name": "max_quantity", "type": "integer", "required": False, "description_vi": "Tồn tối đa"},
            {"name": "warehouse_id", "type": "uuid", "required": True, "description_vi": "Kho"},
        ],
    },
    "stock_movement": {
        "name": "StockMovement",
        "description_vi": "Phiếu xuất nhập kho",
        "fields": [
            {"name": "movement_number", "type": "string", "required": True, "description_vi": "Số phiếu"},
            {"name": "type", "type": "enum", "required": True, "description_vi": "Loại phiếu", "values": ["in", "out", "transfer", "adjustment"]},
            {"name": "item_id", "type": "uuid", "required": True, "description_vi": "Hàng hóa"},
            {"name": "quantity", "type": "integer", "required": True, "description_vi": "Số lượng"},
            {"name": "unit_cost", "type": "decimal", "required": False, "description_vi": "Đơn giá (VND)"},
            {"name": "from_warehouse_id", "type": "uuid", "required": False, "description_vi": "Từ kho"},
            {"name": "to_warehouse_id", "type": "uuid", "required": False, "description_vi": "Đến kho"},
            {"name": "supplier_id", "type": "uuid", "required": False, "description_vi": "Nhà cung cấp"},
            {"name": "notes", "type": "text", "required": False, "description_vi": "Ghi chú"},
        ],
    },
}


# ============================================================================
# Helper Functions
# ============================================================================


def get_domain_prompt(domain: str, lang: str = "vi") -> str:
    """
    Get the prompt for a specific domain.

    Args:
        domain: Business domain key
        lang: Language ("vi" or "en")

    Returns:
        Domain-specific prompt string
    """
    if lang == "en":
        return DOMAIN_PROMPTS.get(domain, "General application.")

    return DOMAIN_PROMPTS.get(domain, "Ứng dụng tổng quát.")


def get_entity_template(entity_key: str) -> Optional[dict]:
    """
    Get entity template by key.

    Args:
        entity_key: Template key (e.g., "menu_item", "product")

    Returns:
        Entity template dictionary or None
    """
    return ENTITY_TEMPLATES.get(entity_key)


def get_all_entity_templates_for_domain(domain: str) -> list[dict]:
    """
    Get all entity templates relevant to a domain.

    Args:
        domain: Business domain key

    Returns:
        List of entity templates
    """
    domain_entities = {
        "restaurant": ["menu_item", "reservation"],
        "ecommerce": ["product", "order"],
        "hrm": ["employee", "attendance"],
        "crm": ["customer", "deal"],
        "inventory": ["inventory_item", "stock_movement"],
        "education": [],  # Uses custom entities
        "healthcare": [],  # Uses custom entities
    }

    entity_keys = domain_entities.get(domain, [])
    return [ENTITY_TEMPLATES[key] for key in entity_keys if key in ENTITY_TEMPLATES]
