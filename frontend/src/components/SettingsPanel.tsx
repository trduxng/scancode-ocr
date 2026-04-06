import type { ScanParams, MetalTextType } from '../types';
import './SettingsPanel.css';

interface SettingsPanelProps {
  params: ScanParams;
  onChange: (params: Partial<ScanParams>) => void;
}

export function SettingsPanel({ params, onChange }: SettingsPanelProps) {
  return (
    <div className="settings-panel glass">
      <h3 className="settings-title">⚙️ Processing Settings</h3>
      
      <div className="setting-group">
        <label>Metal / Text Type</label>
        <select 
          value={params.metalType || 'auto'} 
          onChange={(e) => onChange({ metalType: e.target.value as MetalTextType })}
        >
          <option value="auto">Auto Detect</option>
          <option value="engraved">Engraved / Lasered</option>
          <option value="stamped">Stamped / Embossed</option>
          <option value="dot_peen">Dot-peen</option>
          <option value="laser_etched">Laser Etched</option>
        </select>
        <span className="setting-desc">Adjusts preprocessing for surface texture</span>
      </div>

      <div className="setting-group">
        <label>Language</label>
        <select 
          value={params.language || 'en'} 
          onChange={(e) => onChange({ language: e.target.value })}
        >
          <option value="en">English (Alphanumeric)</option>
          <option value="vi">Vietnamese</option>
        </select>
        <span className="setting-desc">Primary language for text recognition</span>
      </div>

      <div className="setting-group checkbox-group">
        <label>
          <input 
            type="checkbox" 
            checked={params.preprocessingOptions?.enable_clahe ?? true}
            onChange={(e) => onChange({ 
              preprocessingOptions: { 
                ...params.preprocessingOptions, 
                enable_clahe: e.target.checked 
              } 
            })}
          />
          Enhance Contrast (CLAHE)
        </label>
      </div>

      <div className="setting-group checkbox-group">
        <label>
          <input 
            type="checkbox" 
            checked={params.enableCharCorrection ?? true}
            onChange={(e) => onChange({ enableCharCorrection: e.target.checked })}
          />
          Enable Char Correction
        </label>
      </div>
    </div>
  );
}
