import React, { useState, useEffect } from 'react';
import Header from '../components/layout/Header';
import StatusBadge from '../components/common/StatusBadge';
import { submitPrediction, fetchPredictionHistory } from '../api/api';
import { formatProbability, formatDate, formatChannel } from '../utils/formatters';

const INITIAL_FORM = {
  booking_lead_days: 14,
  appointment_weekday: 0,
  appointment_hour: 10,
  booking_hour: 9,
  booking_channel: 'online',
  prior_appointments_count: 3,
  prior_no_show_count: 1,
  prior_cancellations_count: 0,
  prior_no_show_rate: 0.33,
  days_since_last_appointment: 45,
};

export default function PredictionDesk() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [validationError, setValidationError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const loadHistory = async () => {
    try {
      const data = await fetchPredictionHistory(10, 0);
      setHistory(data.predictions || []);
    } catch {
      // Non-blocking for initial desk render
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleChange = (field, value) => {
    setValidationError(null);
    setApiError(null);

    setForm((prev) => {
      const updated = { ...prev, [field]: value };

      // Enforce documented first-time appointment convention & auto-sync rate
      if (field === 'prior_appointments_count' && Number(value) === 0) {
        updated.prior_no_show_count = 0;
        updated.prior_cancellations_count = 0;
        updated.prior_no_show_rate = 0;
        updated.days_since_last_appointment = 0;
      } else if (field === 'prior_appointments_count' || field === 'prior_no_show_count') {
        const appts = Number(field === 'prior_appointments_count' ? value : prev.prior_appointments_count);
        const noshows = Number(field === 'prior_no_show_count' ? value : prev.prior_no_show_count);
        if (appts > 0 && noshows >= 0 && noshows <= appts) {
          updated.prior_no_show_rate = Number((noshows / appts).toFixed(4));
        } else if (appts === 0) {
          updated.prior_no_show_rate = 0;
        }
      }
      return updated;
    });
  };

  const applyPreset = (type) => {
    setValidationError(null);
    setApiError(null);
    if (type === 'first') {
      setForm({
        booking_lead_days: 10,
        appointment_weekday: 1,
        appointment_hour: 11,
        booking_hour: 10,
        booking_channel: 'online',
        prior_appointments_count: 0,
        prior_no_show_count: 0,
        prior_cancellations_count: 0,
        prior_no_show_rate: 0.0,
        days_since_last_appointment: 0,
      });
    } else if (type === 'low') {
      setForm({
        booking_lead_days: 4,
        appointment_weekday: 2,
        appointment_hour: 10,
        booking_hour: 11,
        booking_channel: 'in_person',
        prior_appointments_count: 8,
        prior_no_show_count: 0,
        prior_cancellations_count: 0,
        prior_no_show_rate: 0.0,
        days_since_last_appointment: 28,
      });
    } else if (type === 'high') {
      setForm({
        booking_lead_days: 72,
        appointment_weekday: 4,
        appointment_hour: 18,
        booking_hour: 21,
        booking_channel: 'online',
        prior_appointments_count: 5,
        prior_no_show_count: 3,
        prior_cancellations_count: 1,
        prior_no_show_rate: 0.6,
        days_since_last_appointment: 210,
      });
    }
  };

  const validateClientForm = () => {
    const lead = Number(form.booking_lead_days);
    const apptHr = Number(form.appointment_hour);
    const bookHr = Number(form.booking_hour);
    const appts = Number(form.prior_appointments_count);
    const noshows = Number(form.prior_no_show_count);
    const cancels = Number(form.prior_cancellations_count);
    const rate = Number(form.prior_no_show_rate);
    const gap = Number(form.days_since_last_appointment);

    if (lead < 0 || lead > 365) return 'Booking lead days must be between 0 and 365.';
    if (apptHr < 6 || apptHr > 21) return 'Appointment hour must be between 6 and 21.';
    if (bookHr < 0 || bookHr > 23) return 'Booking hour must be between 0 and 23.';
    if (appts < 0 || noshows < 0 || cancels < 0 || gap < 0) return 'Historical counts and days cannot be negative.';
    if (noshows > appts) return 'Prior no-show count cannot exceed prior appointments count.';
    if (cancels > appts) return 'Prior cancellations count cannot exceed prior appointments count.';
    if (noshows + cancels > appts) return 'Prior no-shows plus cancellations cannot exceed prior appointments count.';
    if (appts === 0 && (noshows !== 0 || cancels !== 0 || rate !== 0 || gap !== 0)) {
      return 'For first-time appointments (prior appointments = 0), prior no-shows, cancellations, rate, and days since last must all be 0.';
    }
    if (appts > 0 && Math.abs(rate - noshows / appts) > 0.02) {
      return `Prior no-show rate must match prior no-shows / prior appointments (${(noshows / appts).toFixed(4)}).`;
    }
    if (rate < 0 || rate > 1) return 'Prior no-show rate must be between 0.0 and 1.0.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errMsg = validateClientForm();
    if (errMsg) {
      setValidationError(errMsg);
      return;
    }

    setSubmitting(true);
    setApiError(null);

    try {
      const payload = {
        booking_lead_days: Number(form.booking_lead_days),
        appointment_weekday: Number(form.appointment_weekday),
        appointment_hour: Number(form.appointment_hour),
        booking_hour: Number(form.booking_hour),
        booking_channel: form.booking_channel,
        prior_appointments_count: Number(form.prior_appointments_count),
        prior_no_show_count: Number(form.prior_no_show_count),
        prior_cancellations_count: Number(form.prior_cancellations_count),
        prior_no_show_rate: Number(form.prior_no_show_rate),
        days_since_last_appointment: Number(form.days_since_last_appointment),
      };

      const data = await submitPrediction(payload);
      setResult(data);
      loadHistory();
    } catch (err) {
      setApiError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const thresholdPct = result ? (result.selected_threshold * 100).toFixed(0) : 15;
  const probPct = result ? (result.no_show_probability * 100).toFixed(1) : 0;

  return (
    <div>
      <Header
        category="PREDICT"
        title="No-Show Prediction"
        description="Enter booking details to estimate no-show risk."
      />

      <div className="page-body">
        <div className="grid-form-result">
          {/* Left Column: Input Form */}
          <div className="ledger-panel" style={{ minWidth: 0 }}>
            <div className="ledger-panel-header">
              <div>
                <div className="ledger-panel-title">Appointment Details</div>
                <div className="ledger-panel-subtitle">Enter all required details.</div>
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '0.35rem 0.7rem', fontSize: '0.84rem' }}
                  onClick={() => applyPreset('first')}
                >
                  First Visit Example
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '0.35rem 0.7rem', fontSize: '0.84rem' }}
                  onClick={() => applyPreset('low')}
                >
                  Lower Risk Example
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '0.35rem 0.7rem', fontSize: '0.84rem' }}
                  onClick={() => applyPreset('high')}
                >
                  Higher Risk Example
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label" htmlFor="booking_lead_days">
                    Booking Lead Days
                  </label>
                  <input
                    id="booking_lead_days"
                    type="number"
                    min="0"
                    max="365"
                    className="form-control"
                    value={form.booking_lead_days}
                    onChange={(e) => handleChange('booking_lead_days', e.target.value)}
                    required
                  />
                  <span className="form-hint">Days between booking &amp; appointment (0–365)</span>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="booking_channel">
                    Booking Channel
                  </label>
                  <select
                    id="booking_channel"
                    className="form-control"
                    value={form.booking_channel}
                    onChange={(e) => handleChange('booking_channel', e.target.value)}
                  >
                    <option value="online">Online Portal</option>
                    <option value="phone">Telephone Desk</option>
                    <option value="in_person">In-Person Reception</option>
                  </select>
                  <span className="form-hint">Channel used to create reservation</span>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="appointment_weekday">
                    Appointment Weekday
                  </label>
                  <select
                    id="appointment_weekday"
                    className="form-control"
                    value={form.appointment_weekday}
                    onChange={(e) => handleChange('appointment_weekday', e.target.value)}
                  >
                    <option value={0}>Monday</option>
                    <option value={1}>Tuesday</option>
                    <option value={2}>Wednesday</option>
                    <option value={3}>Thursday</option>
                    <option value={4}>Friday</option>
                    <option value={5}>Saturday</option>
                    <option value={6}>Sunday</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="appointment_hour">
                    Appointment Hour (24h)
                  </label>
                  <input
                    id="appointment_hour"
                    type="number"
                    min="6"
                    max="21"
                    className="form-control"
                    value={form.appointment_hour}
                    onChange={(e) => handleChange('appointment_hour', e.target.value)}
                    required
                  />
                  <span className="form-hint">Clinic operational hour (6–21)</span>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="booking_hour">
                    Booking Hour (24h)
                  </label>
                  <input
                    id="booking_hour"
                    type="number"
                    min="0"
                    max="23"
                    className="form-control"
                    value={form.booking_hour}
                    onChange={(e) => handleChange('booking_hour', e.target.value)}
                    required
                  />
                  <span className="form-hint">Hour booking was placed (0–23)</span>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="days_since_last_appointment">
                    Days Since Prior Appointment
                  </label>
                  <input
                    id="days_since_last_appointment"
                    type="number"
                    min="0"
                    max="3650"
                    className="form-control"
                    value={form.days_since_last_appointment}
                    onChange={(e) => handleChange('days_since_last_appointment', e.target.value)}
                    required
                  />
                  <span className="form-hint">0 for first-time scheduled visits</span>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="prior_appointments_count">
                    Prior Appointments Count
                  </label>
                  <input
                    id="prior_appointments_count"
                    type="number"
                    min="0"
                    max="200"
                    className="form-control"
                    value={form.prior_appointments_count}
                    onChange={(e) => handleChange('prior_appointments_count', e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="prior_no_show_count">
                    Prior No-Show Count
                  </label>
                  <input
                    id="prior_no_show_count"
                    type="number"
                    min="0"
                    max="200"
                    className="form-control"
                    value={form.prior_no_show_count}
                    onChange={(e) => handleChange('prior_no_show_count', e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="prior_cancellations_count">
                    Prior Cancellations Count
                  </label>
                  <input
                    id="prior_cancellations_count"
                    type="number"
                    min="0"
                    max="200"
                    className="form-control"
                    value={form.prior_cancellations_count}
                    onChange={(e) => handleChange('prior_cancellations_count', e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="prior_no_show_rate">
                    Prior No-Show Rate (0.0 – 1.0)
                  </label>
                  <input
                    id="prior_no_show_rate"
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    className="form-control"
                    value={form.prior_no_show_rate}
                    onChange={(e) => handleChange('prior_no_show_rate', e.target.value)}
                    required
                  />
                  <span className="form-hint">Auto-computed from counts above</span>
                </div>
              </div>

              {validationError && (
                <div className="editorial-callout alert" style={{ marginTop: '1rem' }}>
                  <strong>Validation Error:</strong> {validationError}
                </div>
              )}

              {apiError && (
                <div className="editorial-callout alert" style={{ marginTop: '1rem' }}>
                  <strong>Server Error:</strong> {apiError}
                </div>
              )}

              <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Running Inference...' : 'Predict No-Show Risk'}
                </button>
              </div>
            </form>
          </div>

          {/* Right Column: Inference Output */}
          <div className="ledger-panel" style={{ minWidth: 0 }}>
            <div className="ledger-panel-header">
              <div className="ledger-panel-title">Prediction Result</div>
              {result && <StatusBadge status={result.risk_level} label={`RISK: ${result.risk_level}`} />}
            </div>

            {!result ? (
              <div style={{ padding: '2rem 0', textAlign: 'center', color: 'var(--color-ink-muted)' }}>
                <p>Complete the form to see your prediction.</p>
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div>
                    <div className="stat-label">Estimated No-Show Probability</div>
                    <div
                      style={{
                        fontSize: '2.75rem',
                        fontWeight: 700,
                        color:
                          result.predicted_class === 1
                            ? 'var(--color-terracotta)'
                            : 'var(--color-teal-deep)',
                      }}
                    >
                      {formatProbability(result.no_show_probability)}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div className="stat-label">Classification</div>
                    <div style={{ marginTop: '0.25rem' }}>
                      <StatusBadge status={result.predicted_outcome} />
                    </div>
                  </div>
                </div>

                {/* Probability Meter with Threshold Marker */}
                <div style={{ margin: '1.1rem 0' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '0.94rem',
                      fontWeight: 700,
                      color: 'var(--color-ink-primary)',
                      marginBottom: '0.4rem',
                      letterSpacing: '0.01em',
                    }}
                  >
                    <span>0% (Attended)</span>
                    <span>Threshold: {thresholdPct}%</span>
                    <span>100% (No-Show)</span>
                  </div>
                  <div className="prob-meter-track">
                    <div
                      className="prob-meter-fill"
                      style={{
                        width: `${Math.min(100, Math.max(0, probPct))}%`,
                        backgroundColor:
                          result.predicted_class === 1
                            ? 'var(--color-terracotta)'
                            : 'var(--color-sage)',
                      }}
                    />
                    <div
                      className="prob-meter-threshold"
                      style={{ left: `${thresholdPct}%` }}
                      title={`Selected Operational Threshold: ${result.selected_threshold}`}
                    />
                  </div>
                </div>

                <hr className="ledger-rule" />

                <div style={{ marginBottom: '0.9rem' }}>
                  <div className="stat-label">Operational Guidance</div>
                  <p style={{ marginTop: '0.35rem', fontWeight: 700, fontSize: '1.05rem', color: 'var(--color-ink-primary)', lineHeight: 1.5 }}>
                    {result.operational_suggestion}
                  </p>
                </div>

                {result.context_notes && result.context_notes.length > 0 && (
                  <div style={{ marginBottom: '0.9rem' }}>
                    <div className="stat-label">Notable Input Characteristics</div>
                    <ul style={{ paddingLeft: '1.25rem', marginTop: '0.35rem', fontSize: '0.98rem', fontWeight: 600, color: 'var(--color-ink-primary)' }}>
                      {result.context_notes.map((note, idx) => (
                        <li key={idx} style={{ marginBottom: '0.25rem' }}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div
                  style={{
                    fontSize: '0.95rem',
                    fontWeight: 600,
                    color: 'var(--color-ink-primary)',
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '0.55rem',
                    marginTop: '0.9rem',
                    padding: '0.75rem 0.95rem',
                    backgroundColor: 'var(--color-paper-alt)',
                    border: '1.5px solid var(--color-border-strong)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <div>
                    <strong style={{ color: 'var(--color-ink-primary)' }}>Model:</strong> {result.model_name}
                  </div>
                  <div>
                    <strong style={{ color: 'var(--color-ink-primary)' }}>Version:</strong> v{result.model_version}
                  </div>
                  <div>
                    <strong style={{ color: 'var(--color-ink-primary)' }}>Threshold:</strong> {result.selected_threshold}
                  </div>
                  <div>
                    <strong style={{ color: 'var(--color-ink-primary)' }}>Log ID:</strong> {result.prediction_id || 'Recorded'}
                  </div>
                </div>

                {/* Mandatory Exact Disclaimer */}
                <div className="editorial-callout warning" style={{ marginTop: '1rem', fontSize: '0.96rem', fontWeight: 500, lineHeight: 1.55 }}>
                  <strong style={{ fontWeight: 700 }}>Experimental Notice:</strong> This prediction is an estimate generated from synthetic data. It is not a guarantee that an appointment will be missed. Staff must review the details before taking action.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Prediction History Table */}
        <div className="ledger-panel">
          <div className="ledger-panel-header">
            <div className="ledger-panel-title">Recent Predictions</div>
            <div className="ledger-panel-subtitle">Recorded prediction history</div>
          </div>
          {history.length === 0 ? (
            <p style={{ color: 'var(--color-ink-muted)', fontStyle: 'italic' }}>
              No predictions recorded yet. Submit the form above to see your prediction here.
            </p>
          ) : (
            <div className="table-container">
              <table className="ledger-table">
                <thead>
                  <tr>
                    <th>Log ID</th>
                    <th>Timestamp</th>
                    <th>Channel</th>
                    <th className="num-col">Lead Days</th>
                    <th className="num-col">Prior No-Show %</th>
                    <th className="num-col">Est. Probability</th>
                    <th>Outcome</th>
                    <th>Risk Tier</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item, idx) => (
                    <tr key={item.prediction_id || idx}>
                      <td style={{ fontWeight: 700 }}>{item.prediction_id}</td>
                      <td>{formatDate(item.created_at)}</td>
                      <td>{formatChannel(item.input_features?.booking_channel)}</td>
                      <td className="num-col">{item.input_features?.booking_lead_days}d</td>
                      <td className="num-col">
                        {formatProbability(item.input_features?.prior_no_show_rate, 0)}
                      </td>
                      <td className="num-col" style={{ fontWeight: 700 }}>
                        {formatProbability(item.no_show_probability)}
                      </td>
                      <td>
                        <StatusBadge status={item.predicted_outcome} />
                      </td>
                      <td>
                        <StatusBadge status={item.risk_level} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

