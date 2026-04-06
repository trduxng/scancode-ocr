/**
 * api.ts — API Client Service
 * Handles all HTTP communication with the FastAPI backend.
 */

import type {
  ScanResponse,
  BatchScanResponse,
  PreprocessPreviewResponse,
  LanguageInfo,
  HealthResponse,
  ScanParams,
  PreprocessingOptions,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Tạo FormData từ file và scan parameters */
function buildScanFormData(file: File, params: ScanParams): FormData {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('metal_type', params.metalType);
  formData.append('language', params.language);
  formData.append('confidence_threshold', params.confidenceThreshold.toString());
  formData.append('enable_char_correction', params.enableCharCorrection.toString());
  formData.append('return_preprocessed', params.returnPreprocessed.toString());

  if (params.preprocessingOptions) {
    formData.append('preprocessing_options', JSON.stringify(params.preprocessingOptions));
  }

  return formData;
}

/** Xử lý response từ API */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.error || errorMessage;
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(errorMessage);
  }
  return response.json() as Promise<T>;
}

/** Scan 1 ảnh — POST /api/ocr/scan */
export async function scanImage(
  file: File,
  params: ScanParams,
  onProgress?: (percent: number) => void,
): Promise<ScanResponse> {
  try {
    const formData = buildScanFormData(file, params);

    // XMLHttpRequest cho upload progress tracking
    if (onProgress) {
      return new Promise<ScanResponse>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE}/api/ocr/scan`);

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent);
          }
        };

        xhr.onload = () => {
          try {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(JSON.parse(xhr.responseText));
            } else {
              const errorData = JSON.parse(xhr.responseText);
              reject(new Error(errorData.detail || `HTTP ${xhr.status}`));
            }
          } catch (e) {
            reject(new Error(`Failed to parse response: ${xhr.statusText}`));
          }
        };

        xhr.onerror = () => reject(new Error('Network error'));
        xhr.ontimeout = () => reject(new Error('Request timeout'));
        xhr.timeout = 120000;

        xhr.send(formData);
      });
    }

    const response = await fetch(`${API_BASE}/api/ocr/scan`, {
      method: 'POST',
      body: formData,
    });

    return handleResponse<ScanResponse>(response);

  } catch (error) {
    console.error('Scan failed:', error);
    throw error;
  }
}

/** Batch scan — POST /api/ocr/batch */
export async function scanBatch(
  files: File[],
  params: ScanParams,
): Promise<BatchScanResponse> {
  try {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('images', file);
    });

    formData.append('metal_type', params.metalType);
    formData.append('language', params.language);
    formData.append('confidence_threshold', params.confidenceThreshold.toString());
    formData.append('enable_char_correction', params.enableCharCorrection.toString());

    const response = await fetch(`${API_BASE}/api/ocr/batch`, {
      method: 'POST',
      body: formData,
    });

    return handleResponse<BatchScanResponse>(response);

  } catch (error) {
    console.error('Batch scan failed:', error);
    throw error;
  }
}

/** Preview preprocessing — POST /api/ocr/preprocess-preview */
export async function getPreprocessPreview(
  file: File,
  options?: PreprocessingOptions,
): Promise<PreprocessPreviewResponse> {
  try {
    const formData = new FormData();
    formData.append('image', file);

    if (options) {
      formData.append('preprocessing_options', JSON.stringify(options));
    }

    const response = await fetch(`${API_BASE}/api/ocr/preprocess-preview`, {
      method: 'POST',
      body: formData,
    });

    return handleResponse<PreprocessPreviewResponse>(response);

  } catch (error) {
    console.error('Preview failed:', error);
    throw error;
  }
}

/** Get supported languages — GET /api/ocr/languages */
export async function getLanguages(): Promise<LanguageInfo[]> {
  try {
    const response = await fetch(`${API_BASE}/api/ocr/languages`);
    const data = await handleResponse<{ languages: LanguageInfo[] }>(response);
    return data.languages;
  } catch (error) {
    console.error('Failed to fetch languages:', error);
    throw error;
  }
}

/** Health check — GET /api/health */
export async function checkHealth(): Promise<HealthResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    return handleResponse<HealthResponse>(response);
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
}
