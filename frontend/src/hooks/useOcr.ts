/**
 * useOcr.ts — Custom hook quản lý OCR workflow
 * Quản lý: upload, scan/batch, progress, error handling.
 */

import { useState, useCallback, useRef } from 'react';
import type {
  ScanParams,
  ScanResponse,
  BatchScanResponse,
  ProcessingStatus,
  UploadedFile,
} from '../types';
import { DEFAULT_SCAN_PARAMS } from '../types';
import { scanImage, scanBatch } from '../services/api';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

interface UseOcrReturn {
  status: ProcessingStatus;
  uploadedFile: UploadedFile | null;
  batchFiles: UploadedFile[];
  result: ScanResponse | null;
  batchResult: BatchScanResponse | null;
  error: string | null;
  uploadProgress: number;
  scanParams: ScanParams;
  handleFileSelect: (files: FileList | File[]) => void;
  handleBatchSelect: (files: FileList | File[]) => void;
  removeBatchFile: (id: string) => void;
  clearAll: () => void;
  startScan: () => Promise<void>;
  startBatchScan: () => Promise<void>;
  setScanParams: (params: Partial<ScanParams>) => void;
  setResult: (result: ScanResponse | null) => void;
}

export function useOcr(): UseOcrReturn {
  const [status, setStatus] = useState<ProcessingStatus>('idle');
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [batchFiles, setBatchFiles] = useState<UploadedFile[]>([]);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [batchResult, setBatchResult] = useState<BatchScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [scanParams, setScanParamsState] = useState<ScanParams>(DEFAULT_SCAN_PARAMS);

  const blobUrlsRef = useRef<string[]>([]);

  const cleanupBlobUrls = useCallback(() => {
    blobUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    blobUrlsRef.current = [];
  }, []);

  const createUploadedFile = useCallback((file: File): UploadedFile => {
    const previewUrl = URL.createObjectURL(file);
    blobUrlsRef.current.push(previewUrl);
    return { file, previewUrl, id: generateId() };
  }, []);

  const handleFileSelect = useCallback((files: FileList | File[]) => {
    try {
      const fileArray = Array.from(files);
      if (fileArray.length === 0) return;

      if (uploadedFile) {
        URL.revokeObjectURL(uploadedFile.previewUrl);
      }

      const file = fileArray[0];
      setUploadedFile(createUploadedFile(file));
      setResult(null);
      setError(null);
      setStatus('idle');
      setUploadProgress(0);
    } catch (err) {
      setError(`Failed to load file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [uploadedFile, createUploadedFile]);

  const handleBatchSelect = useCallback((files: FileList | File[]) => {
    try {
      const fileArray = Array.from(files);
      if (fileArray.length === 0) return;

      const newFiles = fileArray.map(createUploadedFile);
      setBatchFiles((prev) => [...prev, ...newFiles]);
      setBatchResult(null);
      setError(null);
    } catch (err) {
      setError(`Failed to load files: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [createUploadedFile]);

  const removeBatchFile = useCallback((id: string) => {
    setBatchFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file) {
        URL.revokeObjectURL(file.previewUrl);
      }
      return prev.filter((f) => f.id !== id);
    });
  }, []);

  const clearAll = useCallback(() => {
    cleanupBlobUrls();
    if (uploadedFile) {
      URL.revokeObjectURL(uploadedFile.previewUrl);
    }
    setUploadedFile(null);
    setBatchFiles([]);
    setResult(null);
    setBatchResult(null);
    setError(null);
    setStatus('idle');
    setUploadProgress(0);
  }, [uploadedFile, cleanupBlobUrls]);

  const startScan = useCallback(async () => {
    if (!uploadedFile) {
      setError('No image selected');
      return;
    }

    try {
      setStatus('uploading');
      setError(null);
      setUploadProgress(0);

      const scanResult = await scanImage(
        uploadedFile.file,
        scanParams,
        (percent) => {
          setUploadProgress(percent);
          if (percent >= 100) {
            setStatus('scanning');
          }
        },
      );

      setResult(scanResult);
      setStatus('done');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Scan failed';
      setError(message);
      setStatus('error');
    }
  }, [uploadedFile, scanParams]);

  const startBatchScan = useCallback(async () => {
    if (batchFiles.length === 0) {
      setError('No images selected for batch');
      return;
    }

    try {
      setStatus('scanning');
      setError(null);

      const files = batchFiles.map((f) => f.file);
      const batchRes = await scanBatch(files, scanParams);

      setBatchResult(batchRes);
      setStatus('done');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Batch scan failed';
      setError(message);
      setStatus('error');
    }
  }, [batchFiles, scanParams]);

  const setScanParams = useCallback((params: Partial<ScanParams>) => {
    setScanParamsState((prev) => ({ ...prev, ...params }));
  }, []);

  return {
    status, uploadedFile, batchFiles, result, batchResult,
    error, uploadProgress, scanParams,
    handleFileSelect, handleBatchSelect, removeBatchFile,
    clearAll, startScan, startBatchScan, setScanParams, setResult,
  };
}
