import React from 'react';

export default function LoadingState({ message = 'Retrieving archive records...' }) {
  return (
    <div className="state-container" role="status" aria-live="polite">
      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-ink-primary)' }}>
        Loading
      </div>
      <p style={{ marginTop: '0.25rem' }}>{message}</p>
    </div>
  );
}

