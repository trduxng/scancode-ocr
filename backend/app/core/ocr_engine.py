"""
ocr_engine.py — PaddleOCR Engine Wrapper

Singleton wrapper cho PaddleOCR với GPU acceleration.
Model được load 1 lần khi khởi tạo và tái sử dụng cho mọi request.

Hỗ trợ:
- Multi-language: English (en) + Russian (ru)
- Angle classification: phát hiện text xoay/nghiêng
- GPU acceleration: NVIDIA CUDA
- Batch processing: xử lý nhiều ảnh cùng lúc
"""

import cv2
import numpy as np
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from paddleocr import PaddleOCR

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OcrDetection:
    """Một text detection duy nhất từ PaddleOCR."""
    text: str
    confidence: float
    bounding_box: List[List[float]]
    position: Tuple[float, float] = (0.0, 0.0)


@dataclass
class OcrResult:
    """Kết quả OCR hoàn chỉnh cho 1 ảnh."""
    detections: List[OcrDetection] = field(default_factory=list)
    processing_time_ms: float = 0.0
    language: str = "en"
    image_size: Tuple[int, int] = (0, 0)


class OcrEngine:
    """
    Singleton PaddleOCR wrapper.
    Quản lý nhiều PaddleOCR instances cho các ngôn ngữ khác nhau.
    """

    _instance: Optional["OcrEngine"] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern — chỉ tạo 1 instance duy nhất"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Khởi tạo OCR engines cho các ngôn ngữ đã cấu hình"""
        if self._initialized:
            return

        self._engines: Dict[str, PaddleOCR] = {}
        self._initialized = True

        logger.info("Initializing OCR Engine...")
        logger.info(f"GPU enabled: {settings.use_gpu}")
        logger.info(f"Languages: {settings.ocr_languages}")

        # Pre-load engines cho tất cả ngôn ngữ
        for lang in settings.ocr_languages:
            try:
                self._loadEngine(lang)
            except Exception as e:
                logger.error(f"Failed to load OCR engine for '{lang}': {str(e)}")

    def _loadEngine(self, language: str) -> PaddleOCR:
        """Load PaddleOCR engine cho 1 ngôn ngữ."""
        if language in self._engines:
            return self._engines[language]

        logger.info(f"Loading PaddleOCR model for language: {language}")
        start_time = time.time()

        try:
            engine = PaddleOCR(
                use_angle_cls=settings.use_angle_cls,
                lang=language,
                device='gpu' if settings.use_gpu else 'cpu',
                det_limit_side_len=settings.ocr_det_limit_side_len,
            )

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"OCR engine for '{language}' loaded in {elapsed:.0f}ms")

            self._engines[language] = engine
            return engine

        except Exception as e:
            logger.error(f"Failed to load OCR engine for '{language}': {str(e)}")
            raise RuntimeError(f"Cannot load OCR engine for language '{language}': {e}")

    @classmethod
    def getInstance(cls) -> "OcrEngine":
        """Lấy singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def recognize(
        self,
        image: np.ndarray,
        language: str = None
    ) -> OcrResult:
        """Chạy OCR trên 1 ảnh."""
        try:
            if language is None:
                language = settings.default_language

            engine = self._loadEngine(language)

            start_time = time.time()
            raw_results = engine.ocr(image)
            elapsed_ms = (time.time() - start_time) * 1000

            detections = self._parseResults(raw_results)

            if len(image.shape) == 3:
                h, w = image.shape[:2]
            else:
                h, w = image.shape

            return OcrResult(
                detections=detections,
                processing_time_ms=round(elapsed_ms, 2),
                language=language,
                image_size=(w, h)
            )

        except Exception as e:
            logger.error(f"OCR recognition failed: {str(e)}")
            raise

    def recognizeBatch(
        self,
        images: List[np.ndarray],
        language: str = None
    ) -> List[OcrResult]:
        """Chạy OCR trên nhiều ảnh (batch processing)."""
        results = []
        for i, image in enumerate(images):
            try:
                logger.info(f"Processing batch image {i + 1}/{len(images)}")
                result = self.recognize(image, language)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch image {i + 1} failed: {str(e)}")
                results.append(OcrResult(
                    detections=[],
                    processing_time_ms=0.0,
                    language=language or settings.default_language,
                    image_size=(0, 0)
                ))
        return results

    def _parseResults(self, raw_results: list) -> List[OcrDetection]:
        """Parse kết quả từ PaddleOCR raw format."""
        detections = []

        if raw_results is None:
            return detections

        for page_result in raw_results:
            if page_result is None:
                continue
            for line in page_result:
                try:
                    bbox = line[0]
                    text = line[1][0]
                    confidence = line[1][1]

                    center_x = sum(p[0] for p in bbox) / 4
                    center_y = sum(p[1] for p in bbox) / 4

                    detections.append(OcrDetection(
                        text=str(text),
                        confidence=float(confidence),
                        bounding_box=[[float(p[0]), float(p[1])] for p in bbox],
                        position=(center_x, center_y)
                    ))
                except (IndexError, TypeError, ValueError) as e:
                    logger.warning(f"Failed to parse OCR line: {str(e)}")
                    continue

        return detections

    def getAvailableLanguages(self) -> List[str]:
        """Trả về danh sách ngôn ngữ đã cấu hình"""
        return list(settings.ocr_languages)

    def getLoadedLanguages(self) -> List[str]:
        """Trả về danh sách ngôn ngữ đã load model"""
        return list(self._engines.keys())

    def isReady(self) -> bool:
        """Kiểm tra engine đã sẵn sàng"""
        return len(self._engines) > 0
