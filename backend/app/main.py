"""
main.py — FastAPI Application Entry Point

Cấu hình: CORS, startup event, error handling, API router.
"""

import os
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import router as api_router
from app.core.ocr_engine import OcrEngine

# === Logging Configuration ===
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def createApp() -> FastAPI:
    """Factory function tạo FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "🔍 ScanCode-OCR — Web API đọc text trên bề mặt kim loại.\n\n"
            "Hỗ trợ: Engraved, Stamped, Dot-peen, Laser Etched text.\n"
            "Engine: PaddleOCR PP-OCRv5 + GPU acceleration.\n"
            "Preprocessing: OpenCV pipeline tối ưu cho kim loại."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # === CORS Middleware ===
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # === Request Logging Middleware ===
    @app.middleware("http")
    async def logRequests(request: Request, call_next):
        """Log mỗi request với thời gian xử lý"""
        start_time = time.time()
        response = await call_next(request)
        elapsed = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.0f}ms)"
        )
        return response

    # === Global Exception Handler ===
    @app.exception_handler(Exception)
    async def globalExceptionHandler(request: Request, exc: Exception):
        """Catch-all error handler — trả về JSON thay vì HTML"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred",
            },
        )

    # === Startup Event ===
    @app.on_event("startup")
    async def startupEvent():
        """Pre-load PaddleOCR models khi server start."""
        logger.info("=" * 60)
        logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
        logger.info("=" * 60)

        os.environ["CUDA_VISIBLE_DEVICES"] = settings.cuda_visible_devices
        logger.info(f"CUDA_VISIBLE_DEVICES: {settings.cuda_visible_devices}")

        logger.info("Loading OCR models (this may take a moment on first run)...")
        try:
            start = time.time()
            engine = OcrEngine.getInstance()
            elapsed = time.time() - start
            logger.info(f"✅ OCR engine ready in {elapsed:.1f}s")
            logger.info(f"   Languages loaded: {engine.getLoadedLanguages()}")
            logger.info(f"   GPU: {settings.use_gpu}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCR engine: {str(e)}")
            logger.warning("Server will start without OCR — fix the error and restart")

        logger.info("=" * 60)
        logger.info(f"📡 API docs: http://{settings.host}:{settings.port}/docs")
        logger.info(f"📡 Health:   http://{settings.host}:{settings.port}/api/health")
        logger.info("=" * 60)

    # === Shutdown Event ===
    @app.on_event("shutdown")
    async def shutdownEvent():
        """Cleanup khi server shutdown"""
        logger.info("Shutting down ScanCode-OCR...")

    # === Register Routes ===
    app.include_router(api_router)

    # === Root Endpoint ===
    @app.get("/")
    async def root():
        """Root endpoint — redirect to docs"""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


# Tạo app instance — được import bởi uvicorn
app = createApp()
