/**
 * OcrResults.tsx — OCR Results Display
 * Text results + confidence bars + bounding box overlay + copy/export.
 */

import { useState, useMemo } from 'react';
import type { ScanResponse } from '../types';
import './OcrResults.css';

interface OcrResultsProps {
  result: ScanResponse;
  originalImageUrl?: string;
}

export function OcrResults({ result, originalImageUrl }: OcrResultsProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [showPreprocessed, setShowPreprocessed] = useState(false);

  const allText = useMemo(() => result.results.map((r) => r.text).join('\n'), [result.results]);

  const copyToClipboard = async (text: string, index?: number) => {
    try {
      await navigator.clipboard.writeText(text);
      if (index !== undefined) { setCopiedIndex(index); setTimeout(() => setCopiedIndex(null), 2000); }
    } catch (err) { console.error('Copy failed:', err); }
  };

  const exportResults = (format: 'json' | 'csv' | 'text') => {
    let content: string; let filename: string; let mimeType: string;
    if (format === 'json') {
      content = JSON.stringify(result, null, 2); filename = 'ocr-results.json'; mimeType = 'application/json';
    } else if (format === 'csv') {
      const header = 'Text,Confidence,Position X,Position Y\n';
      const rows = result.results.map((r) => `"${r.text}",${r.confidence},${r.position.x},${r.position.y}`).join('\n');
      content = header + rows; filename = 'ocr-results.csv'; mimeType = 'text/csv';
    } else {
      content = allText; filename = 'ocr-results.txt'; mimeType = 'text/plain';
    }
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return 'var(--color-success)';
    if (confidence >= 0.7) return 'var(--color-primary)';
    if (confidence >= 0.5) return 'var(--color-warning)';
    return 'var(--color-error)';
  };

  return (
    <div className="results-container animate-fade-in-up" id="results-section">
      {/* Image with Bounding Boxes */}
      {(originalImageUrl || result.preprocessed_image) && (
        <div className="results-image-section">
          <div className="results-image-header">
            <h3>🖼️ Detection Results</h3>
            {result.preprocessed_image && (
              <button className="btn btn-glass btn-sm" onClick={() => setShowPreprocessed(!showPreprocessed)}>
                {showPreprocessed ? '📷 Original' : '⚙️ Preprocessed'}
              </button>
            )}
          </div>
          <div className="results-image-wrapper">
            {showPreprocessed && result.preprocessed_image ? (
              <img src={`data:image/png;base64,${result.preprocessed_image}`} alt="Preprocessed" className="results-image" />
            ) : originalImageUrl ? (
              <img src={originalImageUrl} alt="Original" className="results-image" />
            ) : null}

            {!showPreprocessed && originalImageUrl && result.results.length > 0 && (
              <svg className="bbox-overlay" viewBox={`0 0 ${result.metadata.image_size.width} ${result.metadata.image_size.height}`}>
                {result.results.map((det, i) => {
                  const points = det.bounding_box.points;
                  const pathD = `M ${points[0][0]},${points[0][1]} L ${points[1][0]},${points[1][1]} L ${points[2][0]},${points[2][1]} L ${points[3][0]},${points[3][1]} Z`;
                  const isHovered = hoveredIndex === i;
                  return (
                    <g key={i}>
                      <path d={pathD}
                        fill={isHovered ? 'rgba(59, 130, 246, 0.2)' : 'rgba(59, 130, 246, 0.08)'}
                        stroke={isHovered ? 'var(--color-secondary)' : 'var(--color-primary)'}
                        strokeWidth={isHovered ? 3 : 2} className="bbox-path"
                        onMouseEnter={() => setHoveredIndex(i)} onMouseLeave={() => setHoveredIndex(null)} />
                      {isHovered && (
                        <text x={points[0][0]} y={points[0][1] - 6} fill="var(--color-secondary)"
                          fontSize="14" fontWeight="600" fontFamily="var(--font-mono)">{det.text}</text>
                      )}
                    </g>
                  );
                })}
              </svg>
            )}
          </div>
        </div>
      )}

      {/* Metadata Summary */}
      <div className="results-meta glass">
        <div className="meta-grid">
          <div className="meta-item"><span className="meta-label">⏱️ Total Time</span><span className="meta-value">{result.metadata.processing_time_ms.toFixed(0)}ms</span></div>
          <div className="meta-item"><span className="meta-label">🔍 Pre-process</span><span className="meta-value">{result.metadata.preprocessing_time_ms.toFixed(0)}ms</span></div>
          <div className="meta-item"><span className="meta-label">🧠 OCR Inference</span><span className="meta-value">{result.metadata.ocr_time_ms.toFixed(0)}ms</span></div>
          <div className="meta-item"><span className="meta-label">⚙️ Metal Type</span><span className="meta-value capitalize">{result.metadata.metal_type_detected}</span></div>
          <div className="meta-item"><span className="meta-label">📐 Image Size</span><span className="meta-value">{result.metadata.image_size.width}×{result.metadata.image_size.height}</span></div>
          <div className="meta-item"><span className="meta-label">📝 Detections</span><span className="meta-value">{result.results.length}</span></div>
        </div>
        {result.metadata.preprocessing_steps.length > 0 && (
          <div className="meta-steps">
            <span className="meta-label">Pipeline: </span>
            {result.metadata.preprocessing_steps.map((step, i) => (<span key={i} className="step-badge">{step}</span>))}
          </div>
        )}
      </div>

      {/* Text Results Table */}
      {result.results.length > 0 ? (
        <div className="results-table-wrapper">
          <div className="results-table-header">
            <h3>📋 Extracted Text ({result.results.length})</h3>
            <div className="results-actions">
              <button className="btn btn-glass btn-sm" onClick={() => copyToClipboard(allText)}>📋 Copy All</button>
              <button className="btn btn-glass btn-sm" onClick={() => exportResults('json')}>📄 JSON</button>
              <button className="btn btn-glass btn-sm" onClick={() => exportResults('csv')}>📊 CSV</button>
              <button className="btn btn-glass btn-sm" onClick={() => exportResults('text')}>📝 TXT</button>
            </div>
          </div>
          <div className="results-list">
            {result.results.map((det, i) => (
              <div key={i} className={`result-row ${hoveredIndex === i ? 'highlighted' : ''}`}
                onMouseEnter={() => setHoveredIndex(i)} onMouseLeave={() => setHoveredIndex(null)} id={`result-row-${i}`}>
                <div className="result-index">#{i + 1}</div>
                <div className="result-text-col">
                  <span className="result-text">{det.text}</span>
                  {det.original_text && (<span className="result-original">was: <s>{det.original_text}</s></span>)}
                </div>
                <div className="result-confidence">
                  <div className="confidence-bar-bg">
                    <div className="confidence-bar-fill" style={{ width: `${det.confidence * 100}%`, backgroundColor: getConfidenceColor(det.confidence) }} />
                  </div>
                  <span className="confidence-value">{(det.confidence * 100).toFixed(1)}%</span>
                </div>
                <button className="btn btn-ghost btn-sm copy-row-btn" onClick={() => copyToClipboard(det.text, i)}>
                  {copiedIndex === i ? '✓' : '📋'}
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="results-empty glass">
          <div className="empty-icon">🔍</div>
          <p className="empty-text">No text detected</p>
          <p className="empty-hint">Try adjusting preprocessing settings or use a different metal type strategy</p>
        </div>
      )}
    </div>
  );
}
