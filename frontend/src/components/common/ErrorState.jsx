import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function ErrorState({ message = 'Unable to load records from the server.', onRetry }) {
  return (
    <div className="state-container state-error" role="alert">
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', fontWeight: 700 }}>
        <AlertCircle size={18} />
        <span>System Notice</span>
      </div>
      <p style={{ marginTop: '0.35rem' }}>{message}</p>
      {onRetry && (
        <button className="btn btn-secondary" style={{ marginTop: '0.75rem' }} onClick={onRetry}>
          Retry Connection
        </button>
      )}
    </div>
  );
}

