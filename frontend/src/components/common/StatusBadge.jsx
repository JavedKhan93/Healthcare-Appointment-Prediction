import React from 'react';

export default function StatusBadge({ status, label }) {
  const normalized = String(status).toLowerCase();

  let badgeClass = 'badge-neutral';
  let text = label || status;

  if (normalized === '0' || normalized === 'attended' || normalized === 'low') {
    badgeClass = 'badge-attended';
    if (!label) text = normalized === '0' ? 'Attended' : status;
  } else if (normalized === '1' || normalized === 'no-show' || normalized === 'high' || normalized === 'very_high') {
    badgeClass = 'badge-noshow';
    if (!label) text = normalized === '1' ? 'No-Show' : status;
  } else if (normalized === 'moderate' || normalized === 'review') {
    badgeClass = 'badge-moderate';
  }

  return <span className={`badge ${badgeClass}`}>{text}</span>;
}

