"""
preprocessor.py — Pipeline xử lý ảnh bề mặt kim loại

Đây là module QUAN TRỌNG NHẤT trong hệ thống. Pipeline xử lý ảnh
trước khi đưa vào OCR engine, giải quyết các vấn đề đặc thù của
bề mặt kim loại: glare, low contrast, surface noise, uneven lighting.

Chiến lược preprocessing khác nhau cho mỗi loại text:
- Engraved (khắc chìm): Black-Hat morphology
- Stamped (dập nổi): Top-Hat morphology
- Dot-peen (chấm điểm): Morphological Closing + Dilation
- Laser etching: High-pass filter (Laplacian)
- Auto: Phân tích histogram để tự chọn chiến lược
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.config import MetalTextType, settings

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingParams:
    """
    Tham số preprocessing — có thể tùy chỉnh từ API request.
    Mặc định lấy từ config.
    """
    metal_type: MetalTextType = MetalTextType.AUTO

    # CLAHE parameters
    clahe_clip_limit: float = settings.clahe_clip_limit
    clahe_tile_grid_size: int = settings.clahe_tile_grid_size

    # Blur parameters
    blur_kernel_size: int = settings.blur_kernel_size

    # Adaptive threshold parameters
    adaptive_block_size: int = settings.adaptive_block_size
    adaptive_c: int = settings.adaptive_c

    # Morphological operation parameters
    morph_kernel_size: int = settings.morph_kernel_size

    # Bật/tắt từng bước
    enable_clahe: bool = True
    enable_blur: bool = True
    enable_morphology: bool = True
    enable_threshold: bool = True
    enable_cleanup: bool = True


@dataclass
class PreprocessingResult:
    """Kết quả của preprocessing pipeline"""
    processed_image: np.ndarray                     # Ảnh đã xử lý
    original_image: np.ndarray                      # Ảnh gốc (grayscale)
    steps_applied: List[str] = field(default_factory=list)  # Các bước đã áp dụng
    metal_type_detected: MetalTextType = MetalTextType.AUTO
    intermediate_images: Dict[str, np.ndarray] = field(default_factory=dict)  # Ảnh trung gian (debug)


class MetalSurfacePreprocessor:
    """
    Pipeline xử lý ảnh bề mặt kim loại cho OCR.

    Pipeline gồm 6 bước chính:
    1. Grayscale Conversion — loại bỏ color noise
    2. CLAHE — tăng contrast cục bộ
    3. Noise Reduction — loại bỏ grain, vết xước
    4. Morphological Operations — tách text khỏi nền
    5. Adaptive Thresholding — binarize cho bề mặt sáng không đều
    6. Final Cleanup — kết nối nét đứt, loại bỏ noise nhỏ
    """

    def preprocess(
        self,
        image: np.ndarray,
        params: Optional[PreprocessingParams] = None,
        keep_intermediates: bool = False
    ) -> PreprocessingResult:
        """
        Chạy toàn bộ preprocessing pipeline.

        Args:
            image: Ảnh đầu vào (BGR format từ OpenCV)
            params: Tham số preprocessing tùy chỉnh
            keep_intermediates: Lưu ảnh trung gian cho debug/preview

        Returns:
            PreprocessingResult chứa ảnh đã xử lý và metadata
        """
        try:
            if params is None:
                params = PreprocessingParams()

            steps_applied = []
            intermediates = {}

            # === Bước 1: Grayscale Conversion ===
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                steps_applied.append("grayscale")
            else:
                gray = image.copy()

            original_gray = gray.copy()
            if keep_intermediates:
                intermediates["grayscale"] = gray.copy()

            # === Bước 2: CLAHE ===
            if params.enable_clahe:
                gray = self._applyClahe(gray, params)
                steps_applied.append("clahe")
                if keep_intermediates:
                    intermediates["clahe"] = gray.copy()

            # === Bước 3: Noise Reduction ===
            if params.enable_blur:
                gray = self._applyNoiseReduction(gray, params)
                steps_applied.append("noise_reduction")
                if keep_intermediates:
                    intermediates["noise_reduction"] = gray.copy()

            # === Bước 4: Phát hiện loại text (nếu AUTO) ===
            metal_type = params.metal_type
            if metal_type == MetalTextType.AUTO:
                metal_type = self._detectMetalTextType(gray)
                logger.info(f"Auto-detected metal text type: {metal_type.value}")

            # === Bước 5: Morphological Operations ===
            if params.enable_morphology:
                gray = self._applyMorphology(gray, metal_type, params)
                steps_applied.append(f"morphology_{metal_type.value}")
                if keep_intermediates:
                    intermediates["morphology"] = gray.copy()

            # === Bước 6: Adaptive Thresholding ===
            if params.enable_threshold:
                gray = self._applyAdaptiveThreshold(gray, params)
                steps_applied.append("adaptive_threshold")
                if keep_intermediates:
                    intermediates["adaptive_threshold"] = gray.copy()

            # === Bước 7: Final Cleanup ===
            if params.enable_cleanup:
                gray = self._applyFinalCleanup(gray, params)
                steps_applied.append("final_cleanup")
                if keep_intermediates:
                    intermediates["final_cleanup"] = gray.copy()

            return PreprocessingResult(
                processed_image=gray,
                original_image=original_gray,
                steps_applied=steps_applied,
                metal_type_detected=metal_type,
                intermediate_images=intermediates
            )

        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}")
            raise

    def _applyClahe(self, image: np.ndarray, params: PreprocessingParams) -> np.ndarray:
        """
        Áp dụng CLAHE — Contrast Limited Adaptive Histogram Equalization.
        Tăng contrast CỤC BỘ — vital cho bề mặt kim loại với ánh sáng không đều.
        """
        clahe = cv2.createCLAHE(
            clipLimit=params.clahe_clip_limit,
            tileGridSize=(params.clahe_tile_grid_size, params.clahe_tile_grid_size)
        )
        return clahe.apply(image)

    def _applyNoiseReduction(self, image: np.ndarray, params: PreprocessingParams) -> np.ndarray:
        """
        Giảm noise bề mặt kim loại.
        Dùng Median Blur thay vì Gaussian vì bảo toàn edges tốt hơn.
        """
        kernel_size = params.blur_kernel_size
        # Đảm bảo kernel size là số lẻ
        if kernel_size % 2 == 0:
            kernel_size += 1
        return cv2.medianBlur(image, kernel_size)

    def _detectMetalTextType(self, image: np.ndarray) -> MetalTextType:
        """
        Tự động phát hiện loại text trên kim loại dựa trên phân tích ảnh.
        Sử dụng: edge density, histogram analysis, connected components.
        """
        # Tính edge density bằng Canny
        edges = cv2.Canny(image, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size

        # Tính histogram
        hist = cv2.calcHist([image], [0], None, [256], [0, 256])
        hist_normalized = hist.flatten() / hist.sum()

        # Tìm connected components
        _, binary_temp = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        num_components, labels, stats, _ = cv2.connectedComponentsWithStats(binary_temp)

        # Phân tích kích thước components (bỏ background — component 0)
        if num_components > 1:
            component_areas = stats[1:, cv2.CC_STAT_AREA]
            mean_area = np.mean(component_areas)
            area_std = np.std(component_areas)

            # Dot-peen: Nhiều components nhỏ, kích thước đều nhau
            if num_components > 50 and mean_area < 100 and area_std < mean_area * 0.5:
                return MetalTextType.DOT_PEEN

        # Laser etched: Edge density cao, contrast thấp
        hist_std = np.std(hist_normalized)
        if edge_density > 0.15 and hist_std < 0.01:
            return MetalTextType.LASER_ETCHED

        # Engraved: Contrast thấp, edges trung bình
        if edge_density < 0.08:
            return MetalTextType.ENGRAVED

        # Default: Stamped (contrast cao nhất, phổ biến nhất)
        return MetalTextType.STAMPED

    def _applyMorphology(
        self,
        image: np.ndarray,
        metal_type: MetalTextType,
        params: PreprocessingParams
    ) -> np.ndarray:
        """
        Áp dụng morphological operations tùy theo loại text trên kim loại.
        - Engraved: Black-Hat (tách chữ tối trên nền sáng)
        - Stamped: Top-Hat (tách chữ sáng trên nền tối)
        - Dot-peen: Closing để nối dots → Dilation
        - Laser etched: Laplacian high-pass filter
        """
        kernel_size = params.morph_kernel_size
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (kernel_size, kernel_size)
        )

        if metal_type == MetalTextType.ENGRAVED:
            # Black-Hat Transform — tách phần tử TỐI hơn nền
            result = cv2.morphologyEx(image, cv2.MORPH_BLACKHAT, kernel)
            result = cv2.bitwise_not(result)
            return result

        elif metal_type == MetalTextType.STAMPED:
            # Top-Hat Transform — tách phần tử SÁNG hơn nền
            result = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)
            return result

        elif metal_type == MetalTextType.DOT_PEEN:
            # Closing + Dilation để nối các dots thành nét liền
            large_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            result = cv2.morphologyEx(image, cv2.MORPH_CLOSE, large_kernel)
            small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            result = cv2.dilate(result, small_kernel, iterations=1)
            return result

        elif metal_type == MetalTextType.LASER_ETCHED:
            # High-Pass Filter (Laplacian)
            laplacian = cv2.Laplacian(image, cv2.CV_64F, ksize=3)
            result = np.uint8(np.absolute(laplacian))
            result = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX)
            return result

        else:
            # Fallback: Top-Hat chung
            result = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)
            return result

    def _applyAdaptiveThreshold(self, image: np.ndarray, params: PreprocessingParams) -> np.ndarray:
        """
        Adaptive Thresholding — binarize ảnh cho bề mặt sáng không đều.
        Dùng Gaussian weighted mean cho kết quả mượt hơn.
        """
        block_size = params.adaptive_block_size
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3

        return cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,
            params.adaptive_c
        )

    def _applyFinalCleanup(self, image: np.ndarray, params: PreprocessingParams) -> np.ndarray:
        """
        Bước cleanup cuối cùng.
        Opening: loại bỏ noise nhỏ. Closing: kết nối nét đứt.
        """
        small_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        result = cv2.morphologyEx(image, cv2.MORPH_OPEN, small_kernel, iterations=1)
        result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, small_kernel, iterations=1)
        return result

    def previewAllStrategies(
        self,
        image: np.ndarray,
        params: Optional[PreprocessingParams] = None
    ) -> Dict[str, np.ndarray]:
        """
        Chạy preprocessing với TẤT CẢ strategies và trả về kết quả.
        Dùng cho debug/preview trên frontend.
        """
        if params is None:
            params = PreprocessingParams()

        results = {}
        for metal_type in MetalTextType:
            if metal_type == MetalTextType.AUTO:
                continue
            try:
                strategy_params = PreprocessingParams(
                    metal_type=metal_type,
                    clahe_clip_limit=params.clahe_clip_limit,
                    clahe_tile_grid_size=params.clahe_tile_grid_size,
                    blur_kernel_size=params.blur_kernel_size,
                    adaptive_block_size=params.adaptive_block_size,
                    adaptive_c=params.adaptive_c,
                    morph_kernel_size=params.morph_kernel_size
                )
                result = self.preprocess(image, strategy_params)
                results[metal_type.value] = result.processed_image
            except Exception as e:
                logger.warning(f"Strategy {metal_type.value} failed: {str(e)}")
                continue

        return results
