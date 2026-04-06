/**
 * types/index.ts — TypeScript type definitions
 * Mirror backend Pydantic schemas.
 */

// === Enums ===
export type MetalTextType = 'auto' | 'engraved' | 'stamped' | 'dot_peen' | 'laser_etched';
export type ProcessingStatus = 'idle' | 'uploading' | 'preprocessing' | 'scanning' | 'done' | 'error';

// === Request Types ===
export interface PreprocessingOptions {
  clahe_clip_limit?: number;
  blur_kernel_size?: number;
  adaptive_block_size?: number;
  adaptive_c?: number;
  morph_kernel_size?: number;
  enable_clahe?: boolean;
  enable_blur?: boolean;
  enable_morphology?: boolean;
  enable_threshold?: boolean;
  enable_cleanup?: boolean;
}

export interface ScanParams {
  metalType: MetalTextType;
  language: string;
  confidenceThreshold: number;
  enableCharCorrection: boolean;
  returnPreprocessed: boolean;
  preprocessingOptions?: PreprocessingOptions;
}

// === Response Types ===
export interface BoundingBox {
  points: number[][];
}

export interface DetectionResult {
  text: string;
  confidence: number;
  bounding_box: BoundingBox;
  position: { x: number; y: number };
  original_text?: string | null;
}

export interface ProcessingMetadata {
  processing_time_ms: number;
  preprocessing_time_ms: number;
  ocr_time_ms: number;
  postprocessing_time_ms: number;
  metal_type_detected: string;
  image_size: { width: number; height: number };
  preprocessing_steps: string[];
  language: string;
  detections_removed: number;
  detections_corrected: number;
}

export interface ScanResponse {
  success: boolean;
  results: DetectionResult[];
  metadata: ProcessingMetadata;
  preprocessed_image?: string | null;
}

export interface BatchScanResponse {
  success: boolean;
  total_images: number;
  total_detections: number;
  total_processing_time_ms: number;
  results: ScanResponse[];
}

export interface PreprocessPreviewResponse {
  success: boolean;
  original_image: string;
  strategies: Record<string, string>;
  auto_detected_type: string;
}

export interface LanguageInfo {
  code: string;
  name: string;
  loaded: boolean;
}

export interface HealthResponse {
  status: string;
  version: string;
  gpu_available: boolean;
  ocr_ready: boolean;
  loaded_languages: string[];
}

// === UI State Types ===
export interface UploadedFile {
  file: File;
  previewUrl: string;
  id: string;
}

export interface BatchItem {
  uploadedFile: UploadedFile;
  result?: ScanResponse;
  status: ProcessingStatus;
  error?: string;
}

export interface AppState {
  uploadedFiles: UploadedFile[];
  scanParams: ScanParams;
  currentResult: ScanResponse | null;
  batchResults: BatchItem[];
  status: ProcessingStatus;
  error: string | null;
  activeTab: 'single' | 'batch';
}

// === Default Values ===
export const DEFAULT_SCAN_PARAMS: ScanParams = {
  metalType: 'auto',
  language: 'en',
  confidenceThreshold: 0.6,
  enableCharCorrection: true,
  returnPreprocessed: true,
  preprocessingOptions: {
    clahe_clip_limit: 2.0,
    blur_kernel_size: 3,
    adaptive_block_size: 11,
    adaptive_c: 2,
    morph_kernel_size: 5,
    enable_clahe: true,
    enable_blur: true,
    enable_morphology: true,
    enable_threshold: true,
    enable_cleanup: true,
  },
};

export const METAL_TYPE_LABELS: Record<MetalTextType, string> = {
  auto: '🔄 Auto Detect',
  engraved: '🔨 Engraved (Khắc chìm)',
  stamped: '⚙️ Stamped (Dập nổi)',
  dot_peen: '⬤ Dot-Peen (Chấm điểm)',
  laser_etched: '✨ Laser Etched (Khắc laser)',
};

export const METAL_TYPE_DESCRIPTIONS: Record<MetalTextType, string> = {
  auto: 'Automatically detect text type based on image analysis',
  engraved: 'Text carved below the surface — uses Black-Hat morphology',
  stamped: 'Text raised above the surface — uses Top-Hat morphology',
  dot_peen: 'Text made of small dots — uses morphological Closing',
  laser_etched: 'Text etched by laser — uses high-pass filter',
};
