/**
 * Header.tsx — App header component
 * Logo, tên app, và server health status indicator.
 */

import { useState, useEffect } from 'react';
import type { HealthResponse } from '../types';
import { checkHealth } from '../services/api';
import './Header.css';

export function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
      } catch {
        setHealth(null);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="header" id="app-header">
      <div className="header-content">
        <div className="header-brand">
          <div className="header-logo">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="4" width="12" height="3" rx="1.5" fill="url(#grad1)" />
              <rect x="4" y="10" width="8" height="3" rx="1.5" fill="url(#grad1)" opacity="0.8" />
              <rect x="4" y="16" width="14" height="3" rx="1.5" fill="url(#grad1)" />
              <rect x="4" y="22" width="6" height="3" rx="1.5" fill="url(#grad1)" opacity="0.6" />
              <rect x="4" y="28" width="11" height="3" rx="1.5" fill="url(#grad1)" opacity="0.8" />
              <rect x="4" y="34" width="9" height="3" rx="1.5" fill="url(#grad1)" />
              <rect x="22" y="2" width="2" height="36" rx="1" fill="url(#grad2)" className="scan-line-icon" />
              <path d="M28 8 L36 8" stroke="url(#grad1)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
              <path d="M26 16 L36 16" stroke="url(#grad1)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
              <path d="M27 24 L36 24" stroke="url(#grad1)" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
              <path d="M28 32 L36 32" stroke="url(#grad1)" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
              <defs>
                <linearGradient id="grad1" x1="0" y1="0" x2="40" y2="40">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
                <linearGradient id="grad2" x1="0" y1="0" x2="0" y2="40">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="50%" stopColor="#06b6d4" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <div className="header-title-group">
            <h1 className="header-title">ScanCode-OCR</h1>
            <p className="header-subtitle">Metal Surface Text Recognition</p>
          </div>
        </div>

        <div className="header-status">
          <div className={`status-dot ${health?.status === 'ok' ? 'online' : 'offline'}`} />
          <div className="status-info">
            <span className="status-label">
              {health?.status === 'ok' ? 'Server Online' : 'Server Offline'}
            </span>
            {health && (
              <span className="status-detail">
                {health.gpu_available ? '🎮 GPU' : '💻 CPU'}
                {' · '}
                v{health.version}
                {health.loaded_languages.length > 0 && (
                  <> · {health.loaded_languages.join(', ').toUpperCase()}</>
                )}
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
