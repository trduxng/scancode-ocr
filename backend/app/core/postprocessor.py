"""
postprocessor.py — Xử lý hậu kỳ kết quả OCR

Các bước:
1. Confidence filtering — loại bỏ kết quả confidence thấp
2. Character correction — sửa lỗi ký tự phổ biến trên kim loại
3. De-duplication — loại bỏ text trùng lặp từ overlapping boxes
4. Sorting — sắp xếp theo vị trí (top-to-bottom, left-to-right)
5. Regex validation — kiểm tra format serial number/mã sản phẩm
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from app.core.ocr_engine import OcrDetection, OcrResult
from app.config import settings

logger = logging.getLogger(__name__)


# === Character Correction Maps ===
CHAR_CORRECTION_MAP: Dict[str, str] = {
    "O": "0", "I": "1", "l": "1", "S": "5",
    "B": "8", "G": "6", "Z": "2", "D": "0",
    "|": "1", "!": "1",
}

CHAR_CORRECTION_MAP_ALPHA: Dict[str, str] = {
    "0": "O", "1": "I", "5": "S", "8": "B", "6": "G", "2": "Z",
}


@dataclass
class PostprocessingConfig:
    """Cấu hình post-processing"""
    confidence_threshold: float = settings.confidence_threshold
    enable_char_correction: bool = settings.enable_char_correction
    enable_deduplication: bool = settings.enable_deduplication
    iou_threshold: float = 0.5
    regex_patterns: List[str] = field(default_factory=list)


@dataclass
class PostprocessedResult:
    """Kết quả sau post-processing"""
    detections: List[OcrDetection]
    removed_count: int = 0
    corrected_count: int = 0
    original_texts: Dict[int, str] = field(default_factory=dict)


class OcrPostprocessor:
    """
    Post-processor cho kết quả OCR trên bề mặt kim loại.
    Pipeline: Filter → Correct → Deduplicate → Sort → Validate
    """

    def process(
        self,
        ocr_result: OcrResult,
        config: Optional[PostprocessingConfig] = None
    ) -> PostprocessedResult:
        """Chạy toàn bộ post-processing pipeline."""
        try:
            if config is None:
                config = PostprocessingConfig()

            detections = list(ocr_result.detections)
            removed_count = 0
            corrected_count = 0
            original_texts = {}

            # Bước 1: Confidence Filtering
            before_count = len(detections)
            detections = self._filterByConfidence(detections, config.confidence_threshold)
            removed_count += before_count - len(detections)
            logger.debug(f"Confidence filter: {before_count} → {len(detections)}")

            # Bước 2: Character Correction
            if config.enable_char_correction:
                detections, corrected, originals = self._correctCharacters(detections)
                corrected_count = corrected
                original_texts = originals
                if corrected > 0:
                    logger.debug(f"Character correction: {corrected} texts corrected")

            # Bước 3: De-duplication
            if config.enable_deduplication:
                before_count = len(detections)
                detections = self._deduplicateDetections(detections, config.iou_threshold)
                removed_count += before_count - len(detections)
                logger.debug(f"Deduplication: {before_count} → {len(detections)}")

            # Bước 4: Sort by Position
            detections = self._sortByPosition(detections)

            # Bước 5: Regex Validation
            if config.regex_patterns:
                detections = self._validateRegex(detections, config.regex_patterns)

            return PostprocessedResult(
                detections=detections,
                removed_count=removed_count,
                corrected_count=corrected_count,
                original_texts=original_texts
            )

        except Exception as e:
            logger.error(f"Post-processing failed: {str(e)}")
            raise

    def _filterByConfidence(
        self,
        detections: List[OcrDetection],
        threshold: float
    ) -> List[OcrDetection]:
        """Loại bỏ detections có confidence thấp."""
        return [d for d in detections if d.confidence >= threshold]

    def _correctCharacters(
        self,
        detections: List[OcrDetection]
    ) -> Tuple[List[OcrDetection], int, Dict[int, str]]:
        """Sửa lỗi ký tự phổ biến trên kim loại dựa trên ngữ cảnh."""
        corrected_count = 0
        original_texts = {}
        corrected_detections = []

        for i, det in enumerate(detections):
            original_text = det.text
            corrected_text = self._correctText(original_text)

            if corrected_text != original_text:
                corrected_count += 1
                original_texts[i] = original_text
                corrected_detections.append(OcrDetection(
                    text=corrected_text,
                    confidence=det.confidence,
                    bounding_box=det.bounding_box,
                    position=det.position
                ))
            else:
                corrected_detections.append(det)

        return corrected_detections, corrected_count, original_texts

    def _correctText(self, text: str) -> str:
        """Sửa từng ký tự dựa trên ngữ cảnh (segment phần lớn là số vs chữ)."""
        if not text:
            return text

        segments = re.split(r'([-\s./\\])', text)
        corrected_segments = []

        for segment in segments:
            if not segment or segment in '-./\\ ':
                corrected_segments.append(segment)
                continue

            num_digits = sum(1 for c in segment if c.isdigit())
            num_alpha = sum(1 for c in segment if c.isalpha())

            if num_digits > num_alpha and num_alpha <= 2:
                # Segment chủ yếu là số → sửa chữ cái thành số
                corrected = ""
                for c in segment:
                    if c.upper() in CHAR_CORRECTION_MAP:
                        corrected += CHAR_CORRECTION_MAP[c.upper()]
                    else:
                        corrected += c
                corrected_segments.append(corrected)
            elif num_alpha > num_digits and num_digits <= 1:
                # Segment chủ yếu là chữ → sửa số thành chữ
                corrected = ""
                for c in segment:
                    if c in CHAR_CORRECTION_MAP_ALPHA:
                        corrected += CHAR_CORRECTION_MAP_ALPHA[c]
                    else:
                        corrected += c
                corrected_segments.append(corrected)
            else:
                corrected_segments.append(segment)

        return "".join(corrected_segments)

    def _deduplicateDetections(
        self,
        detections: List[OcrDetection],
        iou_threshold: float
    ) -> List[OcrDetection]:
        """Loại bỏ text trùng lặp từ overlapping bounding boxes (giữ confidence cao nhất)."""
        if len(detections) <= 1:
            return detections

        sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
        keep = []
        removed_indices = set()

        for i, det_i in enumerate(sorted_dets):
            if i in removed_indices:
                continue
            keep.append(det_i)

            for j in range(i + 1, len(sorted_dets)):
                if j in removed_indices:
                    continue
                iou = self._calculateIou(det_i.bounding_box, sorted_dets[j].bounding_box)
                if iou > iou_threshold:
                    removed_indices.add(j)

        return keep

    def _calculateIou(
        self,
        box1: List[List[float]],
        box2: List[List[float]]
    ) -> float:
        """Tính IoU giữa 2 bounding boxes (chuyển 4-point → axis-aligned rect)."""
        try:
            x1_min = min(p[0] for p in box1)
            y1_min = min(p[1] for p in box1)
            x1_max = max(p[0] for p in box1)
            y1_max = max(p[1] for p in box1)

            x2_min = min(p[0] for p in box2)
            y2_min = min(p[1] for p in box2)
            x2_max = max(p[0] for p in box2)
            y2_max = max(p[1] for p in box2)

            inter_x_min = max(x1_min, x2_min)
            inter_y_min = max(y1_min, y2_min)
            inter_x_max = min(x1_max, x2_max)
            inter_y_max = min(y1_max, y2_max)

            if inter_x_min >= inter_x_max or inter_y_min >= inter_y_max:
                return 0.0

            intersection = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
            area1 = (x1_max - x1_min) * (y1_max - y1_min)
            area2 = (x2_max - x2_min) * (y2_max - y2_min)
            union = area1 + area2 - intersection

            if union <= 0:
                return 0.0

            return intersection / union

        except (IndexError, TypeError, ZeroDivisionError):
            return 0.0

    def _sortByPosition(self, detections: List[OcrDetection]) -> List[OcrDetection]:
        """Sắp xếp detections theo reading order (top-to-bottom, left-to-right)."""
        if len(detections) <= 1:
            return detections

        line_threshold = 20
        sorted_by_y = sorted(detections, key=lambda d: d.position[1])

        lines = []
        current_line = [sorted_by_y[0]]
        current_y = sorted_by_y[0].position[1]

        for det in sorted_by_y[1:]:
            if abs(det.position[1] - current_y) <= line_threshold:
                current_line.append(det)
            else:
                lines.append(current_line)
                current_line = [det]
                current_y = det.position[1]
        lines.append(current_line)

        result = []
        for line in lines:
            sorted_line = sorted(line, key=lambda d: d.position[0])
            result.extend(sorted_line)

        return result

    def _validateRegex(
        self,
        detections: List[OcrDetection],
        patterns: List[str]
    ) -> List[OcrDetection]:
        """Validate text against regex patterns — chỉ giữ lại text match."""
        if not patterns:
            return detections

        compiled_patterns = []
        for pattern in patterns:
            try:
                compiled_patterns.append(re.compile(pattern))
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {str(e)}")
                continue

        if not compiled_patterns:
            return detections

        validated = []
        for det in detections:
            for pattern in compiled_patterns:
                if pattern.search(det.text):
                    validated.append(det)
                    break

        return validated
