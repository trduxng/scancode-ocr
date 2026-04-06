# ScanCode-OCR — Task Tracker

## Phase 1: Backend Core

### Setup

- [ ] Tạo project structure (backend/app/...)
- [ ] Tạo requirements.txt (paddlepaddle-gpu cu121, paddleocr, fastapi, opencv...)
- [ ] Tạo virtual environment Python 3.10
- [ ] Cài đặt dependencies

### Core Modules

- [ ] `config.py` — Settings & environment variables
- [ ] `preprocessor.py` — OpenCV preprocessing pipeline (CLAHE, morphology, adaptive threshold...)
- [ ] `ocr_engine.py` — PaddleOCR singleton wrapper (GPU, en+ru, angle cls)
- [ ] `postprocessor.py` — Regex cleanup, confidence filtering, char correction
- [ ] `schemas.py` — Pydantic request/response models
- [ ] `image_utils.py` — Image I/O helpers (base64, resize, format convert)

### API Layer

- [ ] `routes.py` — POST /scan, /batch, /preprocess-preview, GET /languages, /health
- [ ] `main.py` — FastAPI app, CORS, startup event, error handling
- [ ] `run.py` — Server startup script

### Testing

- [ ] Test backend API manually (cần cài dependencies trước)

---

## Phase 2: Frontend

### Setup

- [ ] Init Vite + React + TypeScript project
- [ ] Setup design system (CSS tokens, dark theme, typography)

### Components

- [ ] `Header.tsx` — Logo, title, server health status
- [ ] `ImageUpload.tsx` — Drag & drop + file picker + camera (webcam + external)
- [ ] `OcrResults.tsx` — Text results + confidence bars + bbox overlay + copy/export
- [ ] `SettingsPanel.tsx` — Metal type, language, preprocessing params
- [ ] `App.tsx` — Main app layout + batch results display

### Integration

- [ ] `api.ts` — API client service (scan, batch, preview, health)
- [ ] `useOcr.ts` — Custom hook managing OCR workflow
- [ ] TypeScript types mirroring backend schemas
- [ ] ✅ Frontend build passes (`npm run build`)

---

## Phase 3: Polish

- [ ] Error handling & error banner
- [ ] Animations (scan line, fade-in, floating icon, spinner)
- [ ] Export results (JSON, CSV, TXT, clipboard)
- [ ] Update README.md
- [ ] Update .gitignore
- [ ] Manual verification (cần backend running)
