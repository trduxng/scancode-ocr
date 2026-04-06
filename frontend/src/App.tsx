import { useState } from 'react';
import { Header } from './components/Header';
import { ImageUpload } from './components/ImageUpload';
import { OcrResults } from './components/OcrResults';
import { SettingsPanel } from './components/SettingsPanel';
import { useOcr } from './hooks/useOcr';
import './App.css';

export default function App() {
  const ocr = useOcr();
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single');
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="app-container">
      <Header />
      
      <main className="main-content">
        <div className="toolbar">
          <div className="tabs">
            <button 
              className={`tab-btn ${activeTab === 'single' ? 'active' : ''}`}
              onClick={() => setActiveTab('single')}
            >
              Single Image
            </button>
            <button 
              className={`tab-btn ${activeTab === 'batch' ? 'active' : ''}`}
              onClick={() => setActiveTab('batch')}
            >
              Batch Processing
            </button>
          </div>
          <button 
            className="btn btn-outline"
            onClick={() => setShowSettings(!showSettings)}
          >
            ⚙️ Settings
          </button>
        </div>

        <div className="content-grid">
          <div className="left-panel">
            <ImageUpload 
              mode={activeTab}
              onFileSelect={ocr.handleFileSelect}
              onBatchSelect={ocr.handleBatchSelect}
              uploadedFile={ocr.uploadedFile}
              batchFiles={ocr.batchFiles}
              onRemoveBatchFile={ocr.removeBatchFile}
              onClear={ocr.clearAll}
              status={ocr.status}
              uploadProgress={ocr.uploadProgress}
            />

            <div className="action-panel">
              <button 
                className="btn btn-primary btn-large btn-scan"
                onClick={activeTab === 'single' ? ocr.startScan : ocr.startBatchScan}
                disabled={
                  ocr.status === 'uploading' || 
                  ocr.status === 'scanning' || 
                  (activeTab === 'single' ? !ocr.uploadedFile : ocr.batchFiles.length === 0)
                }
              >
                {ocr.status === 'scanning' ? 'Scanning...' : 'Start Scan'}
              </button>
              {ocr.error && <p className="error-text">❌ {ocr.error}</p>}
            </div>
            
            {showSettings && (
              <SettingsPanel 
                params={ocr.scanParams} 
                onChange={ocr.setScanParams} 
              />
            )}
          </div>

          <div className="right-panel">
            {activeTab === 'single' && ocr.result && (
              <OcrResults 
                result={ocr.result} 
                originalImageUrl={ocr.uploadedFile?.previewUrl} 
              />
            )}
            {activeTab === 'batch' && ocr.batchResult && (
              <div className="batch-results">
                <h3>Batch Results</h3>
                <p>Processed {ocr.batchResult.total_images} images successfully.</p>
                <div className="batch-list">
                    {ocr.batchResult.results.map((res, idx) => (
                         <div key={idx} className="batch-res-item">
                            <h4>Image {idx + 1}</h4>
                            {res.success ? (
                              <pre>{res.results.map(r => r.text).join('\n') || 'No text detected'}</pre>
                            ) : (
                              <p className="error-text">Failed</p>
                            )}
                         </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
