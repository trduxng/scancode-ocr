"""
config.py — Cấu hình ứng dụng ScanCode-OCR

Sử dụng Pydantic Settings để quản lý environment variables
và default values cho toàn bộ backend.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from enum import Enum


class MetalTextType(str, Enum):
    """
    Các loại text trên bề mặt kim loại — mỗi loại cần chiến lược
    preprocessing khác nhau.
    """
    ENGRAVED = "engraved"           # Khắc chìm — chữ thấp hơn bề mặt
    STAMPED = "stamped"             # Dập nổi — chữ cao hơn bề mặt
    DOT_PEEN = "dot_peen"           # Chấm điểm — text tạo từ các dots
    LASER_ETCHED = "laser_etched"   # Khắc laser — tạo vết trên bề mặt
    AUTO = "auto"                   # Tự động phát hiện loại text


class Settings(BaseSettings):
    """
    Cấu hình chính của ứng dụng.
    Có thể override bằng file .env hoặc environment variables.
    """

    # === Server Settings ===
    app_name: str = "ScanCode-OCR"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # === CORS Settings ===
    # Cho phép frontend gọi API từ domain khác
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    )

    # === GPU/CUDA Settings ===
    cuda_visible_devices: str = "0"           # GPU index để sử dụng
    use_gpu: bool = True                      # Bật/tắt GPU acceleration

    # === OCR Settings ===
    ocr_languages: List[str] = Field(
        default=["en", "ru"]                  # English + Russian
    )
    default_language: str = "en"
    use_angle_cls: bool = True                # Phát hiện text xoay/nghiêng
    ocr_det_limit_side_len: int = 960         # Giới hạn kích thước ảnh cho detection
    ocr_show_log: bool = False                # Tắt log PaddleOCR verbose

    # === Preprocessing Defaults ===
    default_metal_type: MetalTextType = MetalTextType.AUTO
    clahe_clip_limit: float = 2.0             # CLAHE contrast limit
    clahe_tile_grid_size: int = 8             # CLAHE tile grid (8x8)
    blur_kernel_size: int = 3                 # Kích thước kernel blur
    adaptive_block_size: int = 11             # Block size cho adaptive threshold
    adaptive_c: int = 2                       # Constant trừ đi trong adaptive threshold
    morph_kernel_size: int = 5                # Kích thước kernel morphological operations

    # === Post-processing Settings ===
    confidence_threshold: float = 0.6         # Ngưỡng confidence tối thiểu
    enable_char_correction: bool = True       # Bật sửa lỗi ký tự O↔0, I↔1...
    enable_deduplication: bool = True          # Bật loại bỏ text trùng lặp

    # === Image Upload Settings ===
    max_image_size_mb: int = 20               # Kích thước file tối đa (MB)
    max_batch_size: int = 10                  # Số ảnh tối đa trong batch
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"]
    )

    # === File Storage ===
    temp_dir: str = "temp_uploads"            # Thư mục lưu file tạm

    model_config = {
        "env_prefix": "SCANCODE_",            # Prefix cho env vars: SCANCODE_USE_GPU=true
        "env_file": ".env",
        "case_sensitive": False,
    }


# Singleton settings instance — import từ bất kỳ module nào
settings = Settings()
