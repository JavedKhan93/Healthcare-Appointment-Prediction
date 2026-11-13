/**
 * Formatting helpers for MORROW Hospital Operations Ledger.
 */

export function formatNumber(val) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return Number(val).toLocaleString();
}

export function formatPercentage(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${Number(val).toFixed(decimals)}%`;
}

export function formatProbability(prob, decimals = 1) {
  if (prob === null || prob === undefined || isNaN(prob)) return '—';
  return `${(Number(prob) * 100).toFixed(decimals)}%`;
}

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr);
    return d.toLocaleString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return String(dateStr);
  }
}

export function formatChannel(channel) {
  if (!channel) return 'Unknown';
  const map = {
    online: 'Online Portal',
    phone: 'Telephone Desk',
    in_person: 'In-Person Reception',
  };
  return map[channel] || channel;
}

export function formatWeekday(idx) {
  const days = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
  ];
  return days[idx] !== undefined ? days[idx] : String(idx);
}

