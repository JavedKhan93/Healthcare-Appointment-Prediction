import React from 'react';

export default function StatCard({ label, value, note, accent = 'teal' }) {
  const accentClass = accent === 'teal' ? '' : `accent-${accent}`;
  return (
    <div className={`stat-block ${accentClass}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {note && <div className="stat-note">{note}</div>}
    </div>
  );
}

