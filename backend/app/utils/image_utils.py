"""
image_utils.py — Tiện ích xử lý ảnh

Các helper functions cho: đọc ảnh từ upload bytes,
encode/decode base64, resize ảnh, validate file format.
"""

import cv2
import base64
import numpy as np
import logging
from typing import Optional, Tuple
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def readImageFromBytes(image_bytes: bytes) -> np.ndarray:
    """Đọc ảnh từ bytes (upload file) thành numpy array (BGR)."""
    try:
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Cannot decode image from bytes")

        return image

    except Exception as e:
        logger.error(f"Failed to read image from bytes: {str(e)}")
        raise ValueError(f"Invalid image data: {str(e)}")


def encodeImageToBase64(image: np.ndarray, format: str = ".png") -> str:
    """Encode ảnh (numpy array) thành base64 string."""
    try:
        success, buffer = cv2.imencode(format, image)
        if not success:
            raise ValueError(f"Failed to encode image to {format}")

        return base64.b64encode(buffer).decode("utf-8")

    except Exception as e:
        logger.error(f"Failed to encode image to base64: {str(e)}")
        raise


def decodeBase64ToImage(base64_string: str) -> np.ndarray:
    """Decode base64 string thành numpy array."""
    try:
        image_data = base64.b64decode(base64_string)
        return readImageFromBytes(image_data)
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {str(e)}")
        raise ValueError(f"Invalid base64 image data: {str(e)}")


def resizeImage(
    image: np.ndarray,
    max_side: int = 1920,
    keep_aspect_ratio: bool = True
) -> np.ndarray:
    """Resize ảnh nếu quá lớn để tối ưu performance."""
    h, w = image.shape[:2]
    max_dim = max(h, w)

    if max_dim <= max_side:
        return image

    if keep_aspect_ratio:
        scale = max_side / max_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
    else:
        new_w = max_side
        new_h = max_side

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    logger.debug(f"Image resized: ({w}x{h}) → ({new_w}x{new_h})")
    return resized


def validateImageFile(
    filename: str,
    file_size: int
) -> Tuple[bool, Optional[str]]:
    """Validate file upload (extension + size)."""
    # Kiểm tra extension
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        return False, f"Unsupported file format: {ext}. Allowed: {settings.allowed_extensions}"

    # Kiểm tra file size
    max_size_bytes = settings.max_image_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File too large: {file_size / 1024 / 1024:.1f}MB. Max: {settings.max_image_size_mb}MB"

    return True, None


def getImageDimensions(image: np.ndarray) -> Tuple[int, int]:
    """Lấy kích thước ảnh (width, height)."""
    if len(image.shape) == 3:
        h, w = image.shape[:2]
    else:
        h, w = image.shape
    return w, h
