"""
schemas.py — Pydantic models cho API request/response
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from app.config import MetalTextType


# ============================
# Request Models
# ============================

class PreprocessingOptions(BaseModel):
    """Tùy chọn preprocessing — gửi từ frontend."""
    clahe_clip_limit: Optional[float] = Field(default=None, ge=0.5, le=10.0)
    blur_kernel_size: Optional[int] = Field(default=None, ge=1, le=15)
    adaptive_block_size: Optional[int] = Field(default=None, ge=3, le=51)
    adaptive_c: Optional[int] = Field(default=None, ge=0, le=20)
    morph_kernel_size: Optional[int] = Field(default=None, ge=1, le=15)
    enable_clahe: bool = True
    enable_blur: bool = True
    enable_morphology: bool = True
    enable_threshold: bool = True
    enable_cleanup: bool = True


class ScanRequest(BaseModel):
    """Request body cho /api/ocr/scan endpoint."""
    metal_type: MetalTextType = Field(default=MetalTextType.AUTO)
    language: str = Field(default="en")
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    preprocessing: Optional[PreprocessingOptions] = None
    enable_char_correction: bool = Field(default=True)
    regex_patterns: List[str] = Field(default=[])
    return_preprocessed: bool = Field(default=False)


# ============================
# Response Models
# ============================

class BoundingBox(BaseModel):
    """Bounding box 4 điểm cho 1 text detection"""
    points: List[List[float]] = Field(description="4 góc: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]")


class DetectionResult(BaseModel):
    """Kết quả 1 text detection"""
    text: str
    confidence: float
    bounding_box: BoundingBox
    position: Dict[str, float]
    original_text: Optional[str] = None


class ProcessingMetadata(BaseModel):
    """Metadata về quá trình xử lý"""
    processing_time_ms: float
    preprocessing_time_ms: float = 0.0
    ocr_time_ms: float = 0.0
    postprocessing_time_ms: float = 0.0
    metal_type_detected: str
    image_size: Dict[str, int]
    preprocessing_steps: List[str]
    language: str
    detections_removed: int = 0
    detections_corrected: int = 0


class ScanResponse(BaseModel):
    """Response cho /api/ocr/scan"""
    success: bool = True
    results: List[DetectionResult] = []
    metadata: ProcessingMetadata
    preprocessed_image: Optional[str] = None


class BatchScanResponse(BaseModel):
    """Response cho /api/ocr/batch"""
    success: bool = True
    total_images: int = 0
    total_detections: int = 0
    total_processing_time_ms: float = 0.0
    results: List[ScanResponse] = []


class PreprocessPreviewResponse(BaseModel):
    """Response cho /api/ocr/preprocess-preview"""
    success: bool = True
    original_image: str
    strategies: Dict[str, str]
    auto_detected_type: str


class LanguageInfo(BaseModel):
    """Thông tin 1 ngôn ngữ"""
    code: str
    name: str
    loaded: bool = False


class LanguagesResponse(BaseModel):
    """Response cho /api/ocr/languages"""
    languages: List[LanguageInfo] = []


class HealthResponse(BaseModel):
    """Response cho /api/health"""
    status: str = "ok"
    version: str
    gpu_available: bool = False
    ocr_ready: bool = False
    loaded_languages: List[str] = []


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
