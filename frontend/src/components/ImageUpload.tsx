/**
 * ImageUpload.tsx — Drag & Drop Upload Component
 * Supports: drag & drop, file picker, camera capture (webcam + external).
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import type { UploadedFile, ProcessingStatus } from '../types';
import './ImageUpload.css';

interface ImageUploadProps {
  onFileSelect: (files: FileList | File[]) => void;
  onBatchSelect?: (files: FileList | File[]) => void;
  uploadedFile: UploadedFile | null;
  batchFiles?: UploadedFile[];
  onRemoveBatchFile?: (id: string) => void;
  onClear: () => void;
  status: ProcessingStatus;
  uploadProgress: number;
  mode: 'single' | 'batch';
}

export function ImageUpload({
  onFileSelect, onBatchSelect, uploadedFile, batchFiles = [],
  onRemoveBatchFile, onClear, status, uploadProgress, mode,
}: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [availableCameras, setAvailableCameras] = useState<MediaDeviceInfo[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string>('');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const isProcessing = status === 'uploading' || status === 'scanning' || status === 'preprocessing';

  // Detect available cameras
  useEffect(() => {
    const detectCameras = async () => {
      try {
        const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
        tempStream.getTracks().forEach((t) => t.stop());

        const devices = await navigator.mediaDevices.enumerateDevices();
        const cameras = devices.filter((d) => d.kind === 'videoinput');
        setAvailableCameras(cameras);
        if (cameras.length > 0) { setSelectedCameraId(cameras[0].deviceId); }
      } catch { /* Camera không khả dụng */ }
    };
    detectCameras();
  }, []);

  // Cleanup camera stream
  useEffect(() => {
    return () => {
      if (cameraStream) { cameraStream.getTracks().forEach((track) => track.stop()); }
    };
  }, [cameraStream]);

  // Drag & Drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }, []);
  const handleDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      if (mode === 'batch' && onBatchSelect) { onBatchSelect(files); } else { onFileSelect(files); }
    }
  }, [mode, onFileSelect, onBatchSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      if (mode === 'batch' && onBatchSelect) { onBatchSelect(files); } else { onFileSelect(files); }
    }
    e.target.value = '';
  }, [mode, onFileSelect, onBatchSelect]);

  // Camera handlers
  const openCamera = useCallback(async () => {
    try {
      const constraints: MediaStreamConstraints = {
        video: selectedCameraId ? { deviceId: { exact: selectedCameraId } } : true,
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setCameraStream(stream);
      setShowCamera(true);
      if (videoRef.current) { videoRef.current.srcObject = stream; }
    } catch (err) { console.error('Camera access failed:', err); }
  }, [selectedCameraId]);

  const closeCamera = useCallback(() => {
    if (cameraStream) { cameraStream.getTracks().forEach((track) => track.stop()); setCameraStream(null); }
    setShowCamera(false);
  }, [cameraStream]);

  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `capture-${Date.now()}.png`, { type: 'image/png' });
        onFileSelect([file]);
        closeCamera();
      }
    }, 'image/png');
  }, [onFileSelect, closeCamera]);

  useEffect(() => {
    if (videoRef.current && cameraStream) { videoRef.current.srcObject = cameraStream; }
  }, [cameraStream, showCamera]);

  const hasFile = mode === 'single' ? !!uploadedFile : batchFiles.length > 0;

  return (
    <div className="upload-container" id="upload-section">
      {/* Camera Modal */}
      {showCamera && (
        <div className="camera-modal" id="camera-modal">
          <div className="camera-content glass">
            <div className="camera-header">
              <h3>📷 Camera Capture</h3>
              {availableCameras.length > 1 && (
                <select className="camera-select" value={selectedCameraId}
                  onChange={(e) => { setSelectedCameraId(e.target.value); closeCamera(); setTimeout(() => openCamera(), 100); }}>
                  {availableCameras.map((cam, i) => (
                    <option key={cam.deviceId} value={cam.deviceId}>{cam.label || `Camera ${i + 1}`}</option>
                  ))}
                </select>
              )}
              <button className="camera-close-btn" onClick={closeCamera}>✕</button>
            </div>
            <div className="camera-preview">
              <video ref={videoRef} autoPlay playsInline muted />
              <div className="camera-scan-overlay"><div className="camera-scan-line" /></div>
            </div>
            <div className="camera-actions">
              <button className="btn btn-primary btn-capture" onClick={capturePhoto}>
                <span className="capture-icon">⊙</span> Capture
              </button>
            </div>
          </div>
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Drop Zone */}
      {!hasFile ? (
        <div className={`drop-zone ${isDragging ? 'dragging' : ''}`} id="drop-zone"
          onDragEnter={handleDragEnter} onDragLeave={handleDragLeave} onDragOver={handleDragOver} onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}>
          <input ref={fileInputRef} type="file" accept="image/*" multiple={mode === 'batch'}
            onChange={handleFileInput} className="file-input-hidden" id="file-input" />
          <div className="drop-zone-content">
            <div className="drop-icon">
              <svg viewBox="0 0 64 64" fill="none">
                <rect x="8" y="12" width="48" height="40" rx="6" stroke="currentColor" strokeWidth="2" opacity="0.6" />
                <path d="M20 36 L28 28 L36 36 L40 32 L52 44 H12 Z" fill="currentColor" opacity="0.2" />
                <circle cx="24" cy="24" r="4" fill="currentColor" opacity="0.3" />
                <path d="M32 4 V16 M26 10 L32 4 L38 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <p className="drop-text">{isDragging ? 'Drop image here!' : 'Drag & drop metal surface image'}</p>
            <p className="drop-hint">or click to browse · JPG, PNG, BMP, TIFF · Max 20MB</p>
            {availableCameras.length > 0 && (
              <button className="btn btn-glass camera-btn" onClick={(e) => { e.stopPropagation(); openCamera(); }}>
                📷 Capture from Camera
                {availableCameras.length > 1 && (<span className="camera-count">({availableCameras.length} cameras)</span>)}
              </button>
            )}
          </div>
        </div>
      ) : mode === 'single' && uploadedFile ? (
        <div className="preview-container" id="image-preview">
          <div className="preview-image-wrapper">
            <img src={uploadedFile.previewUrl} alt="Metal surface" className="preview-image" />
            {isProcessing && (<div className="scan-overlay"><div className="scan-line" /></div>)}
            {status === 'uploading' && (<div className="upload-progress"><div className="upload-progress-bar" style={{ width: `${uploadProgress}%` }} /></div>)}
          </div>
          <div className="preview-info">
            <span className="preview-filename">{uploadedFile.file.name}</span>
            <span className="preview-size">{(uploadedFile.file.size / 1024 / 1024).toFixed(2)} MB</span>
            <button className="btn btn-ghost btn-sm clear-btn" onClick={onClear} disabled={isProcessing}>✕ Clear</button>
          </div>
        </div>
      ) : mode === 'batch' && batchFiles.length > 0 ? (
        <div className="batch-container" id="batch-preview">
          <div className="batch-header">
            <span className="batch-count">{batchFiles.length} images selected</span>
            <div className="batch-actions">
              <button className="btn btn-glass btn-sm" onClick={() => fileInputRef.current?.click()} disabled={isProcessing}>+ Add More</button>
              <button className="btn btn-ghost btn-sm" onClick={onClear} disabled={isProcessing}>Clear All</button>
            </div>
          </div>
          <input ref={fileInputRef} type="file" accept="image/*" multiple onChange={handleFileInput} className="file-input-hidden" />
          <div className="batch-grid">
            {batchFiles.map((f) => (
              <div key={f.id} className="batch-item">
                <img src={f.previewUrl} alt={f.file.name} className="batch-thumbnail" />
                <span className="batch-item-name">{f.file.name}</span>
                <button className="batch-item-remove" onClick={() => onRemoveBatchFile?.(f.id)} disabled={isProcessing}>✕</button>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
