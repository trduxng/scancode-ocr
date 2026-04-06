# ScanCode-OCR — Implementation Walkthrough

## Overview

Đã xây dựng **full-stack web application** cho OCR trên bề mặt kim loại, bao gồm:

- **Backend**: FastAPI + OpenCV preprocessing pipeline + PaddleOCR PP-OCRv5 (GPU)
- **Frontend**: React + Vite + TypeScript với dark theme glassmorphism UI

---

## Backend Architecture

### Core Pipeline: Image → Preprocess → OCR → Postprocess → Results

```mermaid
graph LR
    A[Upload Image] --> B[Grayscale]
    B --> C[CLAHE]
    C --> D[Noise Reduction]
    D --> E[Morphological Ops]
    E --> F[Adaptive Threshold]
    F --> G[Final Cleanup]
    G --> H[PaddleOCR]
    H --> I[Post-processing]
    I --> J[JSON Response]
```

### Files Created

#### Config & Models
- [config.py](file:///d:/Code/project/scancode-ocr/backend/app/config.py) — Pydantic Settings (GPU, OCR, preprocessing defaults)
- [schemas.py](file:///d:/Code/project/scancode-ocr/backend/app/models/schemas.py) — Request/Response Pydantic models

#### Core Processing
- [preprocessor.py](file:///d:/Code/project/scancode-ocr/backend/app/core/preprocessor.py) — 6-step OpenCV pipeline with **4 metal-specific strategies**:
  - **Engraved**: Black-Hat morphology (tách chữ tối trên nền sáng)
  - **Stamped**: Top-Hat morphology (tách chữ sáng trên nền tối)
  - **Dot-peen**: Morphological Closing (nối dots) + Dilation
  - **Laser etched**: Laplacian high-pass filter
  - **Auto**: Phân tích histogram + edge density + connected components

- [ocr_engine.py](file:///d:/Code/project/scancode-ocr/backend/app/core/ocr_engine.py) — PaddleOCR singleton (en + ru, GPU, angle classification, batch)

- [postprocessor.py](file:///d:/Code/project/scancode-ocr/backend/app/core/postprocessor.py) — Confidence filtering, character correction (O↔0, I↔1), IoU de-duplication, reading-order sorting, regex validation

#### API Layer
- [routes.py](file:///d:/Code/project/scancode-ocr/backend/app/api/routes.py) — 5 endpoints: scan, batch, preprocess-preview, languages, health
- [main.py](file:///d:/Code/project/scancode-ocr/backend/app/main.py) — FastAPI app with CORS, logging, model preloading

---

## Frontend Architecture

### Dark Theme Glassmorphism UI

| Feature | Implementation |
|:---|:---|
| **Design System** | CSS custom properties, Inter font, gradient accents |
| **Upload** | Drag & drop + file picker + camera capture (multi-camera) |
| **Results** | SVG bounding box overlay, confidence bars, copy/export |
| **Settings** | Metal type grid, language select, range sliders, toggle switches |
| **Batch** | Multi-file grid, batch results with per-image breakdown |
| **Animations** | Scan line, fade-in, floating icon, spinner, hover effects |

### Files Created

- [index.css](file:///d:/Code/project/scancode-ocr/frontend/src/index.css) — Design tokens, animations, scrollbar, selection styles
- [App.tsx](file:///d:/Code/project/scancode-ocr/frontend/src/App.tsx) + [App.css](file:///d:/Code/project/scancode-ocr/frontend/src/App.css) — 2-column layout, tab switcher, empty state
- [Header.tsx](file:///d:/Code/project/scancode-ocr/frontend/src/components/Header.tsx) — Animated logo + health status
- [ImageUpload.tsx](file:///d:/Code/project/scancode-ocr/frontend/src/components/ImageUpload.tsx) — Upload + camera
- [OcrResults.tsx](file:///d:/Code/project/scancode-ocr/frontend/src/components/OcrResults.tsx) — Results + bbox overlay
- [SettingsPanel.tsx](file:///d:/Code/project/scancode-ocr/frontend/src/components/SettingsPanel.tsx) — All OCR settings
- [api.ts](file:///d:/Code/project/scancode-ocr/frontend/src/services/api.ts) — API client with upload progress
- [useOcr.ts](file:///d:/Code/project/scancode-ocr/frontend/src/hooks/useOcr.ts) — State management hook

---

## Verification

| Check | Status |
|:---|:---|
| Frontend TypeScript compile | ✅ Pass |
| Frontend production build | ✅ Pass (1.48s) |
| Frontend dev server | ✅ Runs on :5173 |
| Backend code structure | ✅ Complete |
| Backend venv + deps | ⏳ Needs manual setup |

---

## Next Steps

1. **Setup Python venv** và cài dependencies:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu121/
   pip install -r requirements.txt
   ```

2. **Start backend**: `python run.py`

3. **Test**: Mở `http://localhost:5173/`, upload ảnh kim loại, và scan
