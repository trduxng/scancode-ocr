# ScanCode-OCR 🔍

> **AI-Powered OCR for Metal Surfaces** — Đọc text trên bề mặt kim loại sử dụng PaddleOCR + OpenCV

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-PP--OCRv5-green.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)

---

## ✨ Features

- 🔨 **Engraved Text** — Đọc chữ khắc chìm trên kim loại (Black-Hat morphology)
- ⚙️ **Stamped Text** — Đọc chữ dập nổi (Top-Hat morphology)
- ⬤ **Dot-Peen Marking** — Đọc chữ tạo từ chấm điểm (Morphological Closing)
- ✨ **Laser Etching** — Đọc chữ khắc laser (High-pass filter)
- 🔄 **Auto Detection** — Tự động phát hiện loại text
- 🎮 **GPU Acceleration** — NVIDIA CUDA cho inference nhanh
- 📷 **Camera Capture** — Chụp trực tiếp từ webcam/camera ngoài
- 📚 **Batch Processing** — Xử lý nhiều ảnh cùng lúc
- 🌐 **Multi-language** — English + Russian

## 🏗️ Architecture

```
Frontend (React + Vite)  ──→  Backend (FastAPI)  ──→  PaddleOCR (GPU)
     │                              │
     │                              ├── Preprocessing (OpenCV)
     │                              │   ├── CLAHE
     │                              │   ├── Noise Reduction
     │                              │   ├── Morphological Ops
     │                              │   ├── Adaptive Threshold
     │                              │   └── Final Cleanup
     │                              │
     │                              └── Post-processing
     │                                  ├── Confidence Filter
     │                                  ├── Character Correction
     │                                  ├── De-duplication
     │                                  └── Sorting
     │
     └── Results Display
         ├── Bounding Box Overlay
         ├── Confidence Bars
         └── Export (JSON/CSV/TXT)
```

## 🚀 Quick Start

### Prerequisites

- Python ≥ 3.10
- Node.js ≥ 18
- NVIDIA GPU + CUDA 12.1

### Backend Setup

```bash
# Tạo virtual environment
cd backend
python -m venv venv
venv\Scripts\activate  # Windows

# Cài dependencies
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu121/
pip install -r requirements.txt

# Chạy server
python run.py
```

Server sẽ chạy tại `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend sẽ chạy tại `http://localhost:5173`

## 📡 API Reference

| Endpoint                      | Method | Description                      |
| :---------------------------- | :----- | :------------------------------- |
| `/api/ocr/scan`               | POST   | OCR 1 ảnh                        |
| `/api/ocr/batch`              | POST   | OCR nhiều ảnh                    |
| `/api/ocr/preprocess-preview` | POST   | Preview preprocessing strategies |
| `/api/ocr/languages`          | GET    | Ngôn ngữ hỗ trợ                  |
| `/api/health`                 | GET    | Health check                     |

## 🔧 Configuration

Tạo file `.env` trong `backend/`:

```env
SCANCODE_USE_GPU=true
SCANCODE_CUDA_VISIBLE_DEVICES=0
SCANCODE_DEFAULT_LANGUAGE=en
SCANCODE_CONFIDENCE_THRESHOLD=0.6
SCANCODE_MAX_IMAGE_SIZE_MB=20
SCANCODE_MAX_BATCH_SIZE=10
```

## 📄 License

MIT
