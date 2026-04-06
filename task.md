# ScanCode-OCR — Task Tracker

## Phase 1: Backend Core

### Setup
- [x] Tạo project structure (backend/app/...)
- [x] Tạo requirements.txt (paddlepaddle-gpu cu121, paddleocr, fastapi, opencv...)
- [ ] Tạo virtual environment Python 3.10
- [ ] Cài đặt dependencies

### Core Modules
- [x] `config.py` — Settings & environment variables
- [x] `preprocessor.py` — OpenCV preprocessing pipeline (CLAHE, morphology, adaptive threshold...)
- [x] `ocr_engine.py` — PaddleOCR singleton wrapper (GPU, en+ru, angle cls)
- [x] `postprocessor.py` — Regex cleanup, confidence filtering, char correction
- [x] `schemas.py` — Pydantic request/response models
- [x] `image_utils.py` — Image I/O helpers (base64, resize, format convert)

### API Layer
- [x] `routes.py` — POST /scan, /batch, /preprocess-preview, GET /languages, /health
- [x] `main.py` — FastAPI app, CORS, startup event, error handling
- [x] `run.py` — Server startup script

### Testing
- [ ] Test backend API manually (cần cài dependencies trước)

---

## Phase 2: Frontend

### Setup
- [x] Init Vite + React + TypeScript project
- [x] Setup design system (CSS tokens, dark theme, typography)

### Components
- [x] `Header.tsx` — Logo, title, server health status
- [x] `ImageUpload.tsx` — Drag & drop + file picker + camera (webcam + external)
- [x] `OcrResults.tsx` — Text results + confidence bars + bbox overlay + copy/export
- [x] `SettingsPanel.tsx` — Metal type, language, preprocessing params
- [x] `App.tsx` — Main app layout + batch results display

### Integration
- [x] `api.ts` — API client service (scan, batch, preview, health)
- [x] `useOcr.ts` — Custom hook managing OCR workflow
- [x] TypeScript types mirroring backend schemas
- [x] ✅ Frontend build passes (`npm run build`)

---

## Phase 3: Polish
- [x] Error handling & error banner
- [x] Animations (scan line, fade-in, floating icon, spinner)
- [x] Export results (JSON, CSV, TXT, clipboard)
- [x] Update README.md
- [x] Update .gitignore
- [ ] Manual verification (cần backend running)
