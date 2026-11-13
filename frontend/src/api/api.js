/**
 * Centralized API Client for MORROW Flask Backend.
 * Uses native Fetch API against VITE_API_BASE_URL.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  let response;
  try {
    response = await fetch(url, config);
  } catch (err) {
    throw new Error(`Network error: Cannot connect to MORROW backend (${err.message})`);
  }

  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`Invalid response format from server (HTTP ${response.status})`);
  }

  if (!response.ok || body.status === 'error') {
    const errMsg = body.errors
      ? `${body.message}: ${body.errors.join(', ')}`
      : body.message || `Server error (${response.status})`;
    throw new Error(errMsg);
  }

  return body.data;
}

export function fetchHealth() {
  return request('/health');
}

export function fetchDashboardSummary() {
  return request('/dashboard/summary');
}

export function fetchDashboardTrends() {
  return request('/dashboard/trends');
}

export function fetchAppointments(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      query.set(k, v);
    }
  });
  return request(`/appointments?${query.toString()}`);
}

export function fetchAppointment(appointmentId) {
  return request(`/appointments/${encodeURIComponent(appointmentId)}`);
}

export function submitPrediction(payload) {
  return request('/predictions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchPredictionHistory(limit = 20, skip = 0) {
  return request(`/predictions/history?limit=${limit}&skip=${skip}`);
}

export function fetchModelMetrics() {
  return request('/model/metrics');
}

export function fetchFeatureImportance() {
  return request('/model/feature-importance');
}

export function fetchModelMetadata() {
  return request('/model/metadata');
}

export function fetchDataQuality() {
  return request('/data-quality');
}

