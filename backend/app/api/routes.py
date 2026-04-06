"""
routes.py — API Endpoints cho ScanCode-OCR

Endpoints:
- POST /api/ocr/scan              — OCR 1 ảnh
- POST /api/ocr/batch             — OCR nhiều ảnh (batch)
- POST /api/ocr/preprocess-preview — Preview preprocessing strategies
- GET  /api/ocr/languages         — Danh sách ngôn ngữ hỗ trợ
- GET  /api/health                — Health check
"""

import time
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.config import MetalTextType, settings
from app.core.preprocessor import MetalSurfacePreprocessor, PreprocessingParams
from app.core.ocr_engine import OcrEngine
from app.core.postprocessor import OcrPostprocessor, PostprocessingConfig
from app.models.schemas import (
    ScanResponse,
    BatchScanResponse,
    PreprocessPreviewResponse,
    LanguagesResponse,
    LanguageInfo,
    HealthResponse,
    ErrorResponse,
    DetectionResult,
    BoundingBox,
    ProcessingMetadata,
)
from app.utils.image_utils import (
    readImageFromBytes,
    encodeImageToBase64,
    resizeImage,
    validateImageFile,
    getImageDimensions,
)

logger = logging.getLogger(__name__)

# Tạo router
router = APIRouter(prefix="/api", tags=["OCR"])

# Khởi tạo các components
preprocessor = MetalSurfacePreprocessor()
postprocessor = OcrPostprocessor()

# Language display names
LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian (Русский)",
    "ch": "Chinese (中文)",
    "japan": "Japanese (日本語)",
    "korean": "Korean (한국어)",
    "fr": "French (Français)",
    "german": "German (Deutsch)",
    "es": "Spanish (Español)",
}


@router.post("/ocr/scan", response_model=ScanResponse)
async def scanImage(
    image: UploadFile = File(..., description="Ảnh bề mặt kim loại"),
    metal_type: str = Form(default="auto"),
    language: str = Form(default="en"),
    confidence_threshold: float = Form(default=0.6),
    enable_char_correction: bool = Form(default=True),
    return_preprocessed: bool = Form(default=False),
    preprocessing_options: Optional[str] = Form(default=None),
):
    """OCR 1 ảnh bề mặt kim loại."""
    total_start = time.time()

    try:
        # Validate file upload
        is_valid, error_msg = validateImageFile(image.filename, image.size or 0)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Đọc ảnh từ upload bytes
        image_bytes = await image.read()
        img = readImageFromBytes(image_bytes)
        img = resizeImage(img, max_side=1920)

        # Parse preprocessing options
        preprocess_params = PreprocessingParams()
        preprocess_params.metal_type = MetalTextType(metal_type)

        if preprocessing_options:
            try:
                options = json.loads(preprocessing_options)
                if "clahe_clip_limit" in options:
                    preprocess_params.clahe_clip_limit = float(options["clahe_clip_limit"])
                if "blur_kernel_size" in options:
                    preprocess_params.blur_kernel_size = int(options["blur_kernel_size"])
                if "adaptive_block_size" in options:
                    preprocess_params.adaptive_block_size = int(options["adaptive_block_size"])
                if "adaptive_c" in options:
                    preprocess_params.adaptive_c = int(options["adaptive_c"])
                if "morph_kernel_size" in options:
                    preprocess_params.morph_kernel_size = int(options["morph_kernel_size"])
                for key in ["enable_clahe", "enable_blur", "enable_morphology", "enable_threshold", "enable_cleanup"]:
                    if key in options:
                        setattr(preprocess_params, key, bool(options[key]))
            except json.JSONDecodeError:
                logger.warning("Invalid preprocessing_options JSON, using defaults")

        # Preprocessing
        preprocess_start = time.time()
        preprocess_result = preprocessor.preprocess(
            img, preprocess_params, keep_intermediates=return_preprocessed
        )
        preprocess_time = (time.time() - preprocess_start) * 1000

        # OCR Inference
        ocr_start = time.time()
        ocr_engine = OcrEngine.getInstance()
        ocr_result = ocr_engine.recognize(preprocess_result.processed_image, language)
        ocr_time = (time.time() - ocr_start) * 1000

        # Post-processing
        postprocess_start = time.time()
        post_config = PostprocessingConfig(
            confidence_threshold=confidence_threshold,
            enable_char_correction=enable_char_correction,
        )
        post_result = postprocessor.process(ocr_result, post_config)
        postprocess_time = (time.time() - postprocess_start) * 1000

        # Build response
        total_time = (time.time() - total_start) * 1000
        w, h = getImageDimensions(img)

        detection_results = []
        for i, det in enumerate(post_result.detections):
            detection_results.append(DetectionResult(
                text=det.text,
                confidence=round(det.confidence, 4),
                bounding_box=BoundingBox(points=det.bounding_box),
                position={"x": round(det.position[0], 2), "y": round(det.position[1], 2)},
                original_text=post_result.original_texts.get(i)
            ))

        metadata = ProcessingMetadata(
            processing_time_ms=round(total_time, 2),
            preprocessing_time_ms=round(preprocess_time, 2),
            ocr_time_ms=round(ocr_time, 2),
            postprocessing_time_ms=round(postprocess_time, 2),
            metal_type_detected=preprocess_result.metal_type_detected.value,
            image_size={"width": w, "height": h},
            preprocessing_steps=preprocess_result.steps_applied,
            language=language,
            detections_removed=post_result.removed_count,
            detections_corrected=post_result.corrected_count,
        )

        preprocessed_b64 = None
        if return_preprocessed:
            preprocessed_b64 = encodeImageToBase64(preprocess_result.processed_image)

        return ScanResponse(
            success=True,
            results=detection_results,
            metadata=metadata,
            preprocessed_image=preprocessed_b64,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/ocr/batch", response_model=BatchScanResponse)
async def scanBatch(
    images: List[UploadFile] = File(..., description="Danh sách ảnh (tối đa 10)"),
    metal_type: str = Form(default="auto"),
    language: str = Form(default="en"),
    confidence_threshold: float = Form(default=0.6),
    enable_char_correction: bool = Form(default=True),
):
    """Batch OCR — xử lý nhiều ảnh cùng lúc."""
    try:
        if len(images) > settings.max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Too many images: {len(images)}. Max: {settings.max_batch_size}"
            )

        total_start = time.time()
        batch_results = []
        total_detections = 0

        for i, img_file in enumerate(images):
            logger.info(f"Processing batch image {i + 1}/{len(images)}: {img_file.filename}")

            try:
                is_valid, error_msg = validateImageFile(img_file.filename, img_file.size or 0)
                if not is_valid:
                    batch_results.append(ScanResponse(
                        success=False,
                        results=[],
                        metadata=ProcessingMetadata(
                            processing_time_ms=0,
                            metal_type_detected="error",
                            image_size={"width": 0, "height": 0},
                            preprocessing_steps=[],
                            language=language,
                        ),
                    ))
                    continue

                image_bytes = await img_file.read()
                img = readImageFromBytes(image_bytes)
                img = resizeImage(img, max_side=1920)

                preprocess_params = PreprocessingParams(metal_type=MetalTextType(metal_type))
                preprocess_result = preprocessor.preprocess(img, preprocess_params)

                ocr_engine = OcrEngine.getInstance()
                ocr_result = ocr_engine.recognize(preprocess_result.processed_image, language)

                post_config = PostprocessingConfig(
                    confidence_threshold=confidence_threshold,
                    enable_char_correction=enable_char_correction,
                )
                post_result = postprocessor.process(ocr_result, post_config)

                w, h = getImageDimensions(img)
                detection_results = [
                    DetectionResult(
                        text=det.text,
                        confidence=round(det.confidence, 4),
                        bounding_box=BoundingBox(points=det.bounding_box),
                        position={"x": round(det.position[0], 2), "y": round(det.position[1], 2)},
                        original_text=post_result.original_texts.get(j)
                    )
                    for j, det in enumerate(post_result.detections)
                ]

                total_detections += len(detection_results)

                batch_results.append(ScanResponse(
                    success=True,
                    results=detection_results,
                    metadata=ProcessingMetadata(
                        processing_time_ms=round(ocr_result.processing_time_ms, 2),
                        metal_type_detected=preprocess_result.metal_type_detected.value,
                        image_size={"width": w, "height": h},
                        preprocessing_steps=preprocess_result.steps_applied,
                        language=language,
                        detections_removed=post_result.removed_count,
                        detections_corrected=post_result.corrected_count,
                    ),
                ))

            except Exception as e:
                logger.error(f"Batch image {i + 1} failed: {str(e)}")
                batch_results.append(ScanResponse(
                    success=False,
                    results=[],
                    metadata=ProcessingMetadata(
                        processing_time_ms=0,
                        metal_type_detected="error",
                        image_size={"width": 0, "height": 0},
                        preprocessing_steps=[],
                        language=language,
                    ),
                ))

        total_time = (time.time() - total_start) * 1000

        return BatchScanResponse(
            success=True,
            total_images=len(images),
            total_detections=total_detections,
            total_processing_time_ms=round(total_time, 2),
            results=batch_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch scan failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.post("/ocr/preprocess-preview", response_model=PreprocessPreviewResponse)
async def preprocessPreview(
    image: UploadFile = File(...),
    preprocessing_options: Optional[str] = Form(default=None),
):
    """Preview tất cả preprocessing strategies trên 1 ảnh."""
    try:
        is_valid, error_msg = validateImageFile(image.filename, image.size or 0)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        image_bytes = await image.read()
        img = readImageFromBytes(image_bytes)
        img = resizeImage(img, max_side=1280)

        params = PreprocessingParams()
        if preprocessing_options:
            try:
                options = json.loads(preprocessing_options)
                for key, value in options.items():
                    if hasattr(params, key):
                        setattr(params, key, value)
            except json.JSONDecodeError:
                pass

        strategies = preprocessor.previewAllStrategies(img, params)
        auto_result = preprocessor.preprocess(img, PreprocessingParams(metal_type=MetalTextType.AUTO))

        import cv2
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        return PreprocessPreviewResponse(
            success=True,
            original_image=encodeImageToBase64(gray),
            strategies={k: encodeImageToBase64(v) for k, v in strategies.items()},
            auto_detected_type=auto_result.metal_type_detected.value,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preprocess preview failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/ocr/languages", response_model=LanguagesResponse)
async def getLanguages():
    """Danh sách ngôn ngữ được hỗ trợ."""
    try:
        ocr_engine = OcrEngine.getInstance()
        loaded = ocr_engine.getLoadedLanguages()

        languages = []
        for lang_code in settings.ocr_languages:
            languages.append(LanguageInfo(
                code=lang_code,
                name=LANGUAGE_NAMES.get(lang_code, lang_code),
                loaded=lang_code in loaded,
            ))

        return LanguagesResponse(languages=languages)

    except Exception as e:
        logger.error(f"Failed to get languages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def healthCheck():
    """Health check — kiểm tra trạng thái server, GPU, OCR engine."""
    try:
        gpu_available = False
        try:
            import paddle
            gpu_available = paddle.device.is_compiled_with_cuda()
        except ImportError:
            pass

        ocr_ready = False
        loaded_languages = []
        try:
            ocr_engine = OcrEngine.getInstance()
            ocr_ready = ocr_engine.isReady()
            loaded_languages = ocr_engine.getLoadedLanguages()
        except Exception:
            pass

        return HealthResponse(
            status="ok",
            version=settings.app_version,
            gpu_available=gpu_available,
            ocr_ready=ocr_ready,
            loaded_languages=loaded_languages,
        )

    except Exception as e:
        return HealthResponse(
            status="error",
            version=settings.app_version,
        )
