import React from 'react';

export default function EmptyState({ title = 'No Records Found', message = 'Adjust search or filter parameters to inspect ledger entries.' }) {
  return (
    <div className="state-container">
      <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--color-ink-primary)' }}>
        {title}
      </div>
      <p style={{ marginTop: '0.25rem' }}>{message}</p>
    </div>
  );
}

