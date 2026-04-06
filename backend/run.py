"""
run.py — Script khởi động ScanCode-OCR server

Usage:
    python run.py                    # Default: 0.0.0.0:8000
    python run.py --port 8080        # Custom port
    python run.py --reload           # Auto-reload khi code thay đổi
"""

import argparse
import uvicorn

from app.config import settings


def main():
    """Khởi động Uvicorn server"""
    parser = argparse.ArgumentParser(description="ScanCode-OCR Server")
    parser.add_argument("--host", default=settings.host, help="Host address")
    parser.add_argument("--port", type=int, default=settings.port, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")

    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    main()
