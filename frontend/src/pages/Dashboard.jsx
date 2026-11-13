import React, { useEffect, useState } from 'react';
import Header from '../components/layout/Header';
import StatCard from '../components/common/StatCard';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import StatusBadge from '../components/common/StatusBadge';
import DoughnutChart from '../components/charts/DoughnutChart';
import BarChart from '../components/charts/BarChart';
import CombinedBarLineChart from '../components/charts/CombinedBarLineChart';
import { fetchDashboardSummary, fetchDashboardTrends } from '../api/api';
import { scrollToSection } from '../utils/navigation';
import {
  formatNumber,
  formatPercentage,
  formatProbability,
  formatDate,
  formatChannel,
} from '../utils/formatters';

export default function Dashboard({ onNavigate }) {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumData, trendData] = await Promise.all([
        fetchDashboardSummary(),
        fetchDashboardTrends(),
      ]);
      setSummary(sumData);
      setTrends(trendData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div>
      <Header
        category="OVERVIEW"
        badge="Synthetic Data"
        title="Hospital Appointment Overview"
        description="View attendance, no-show trends and recent predictions."
        rightContent={
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => (onNavigate ? onNavigate('predict') : scrollToSection('predict'))}
          >
            Make a Prediction
          </button>
        }
      />

      <div className="page-body">
        {loading && <LoadingState message="Loading appointment overview..." />}
        {error && <ErrorState message={error} onRetry={loadData} />}

        {!loading && !error && summary && trends && (
          <>
            {/* Top KPI Blocks */}
            <div className="grid-4">
              <StatCard
                label="Total Appointments"
                value={formatNumber(summary.total_appointments)}
                note="Appointments in the dataset"
                accent="teal"
              />
              <StatCard
                label="Attended Appointments"
                value={formatNumber(summary.attended_appointments)}
                note="Attended appointments"
                accent="sage"
              />
              <StatCard
                label="No-Show Occurrences"
                value={formatNumber(summary.no_show_appointments)}
                note="Missed appointments"
                accent="terracotta"
              />
              <StatCard
                label="Overall No-Show Rate"
                value={formatPercentage(summary.no_show_rate_percent)}
                note={`${formatNumber(summary.total_predictions_logged)} predictions recorded`}
                accent="ochre"
              />
            </div>

            {/* Asymmetric Primary Charts */}
            <div className="grid-asymmetric">
              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">No-Show Rate by Appointment Weekday</div>
                  <div className="ledger-panel-subtitle">Missed appointment rate (%)</div>
                </div>
                <BarChart
                  labels={trends.by_weekday.map((d) => d.day_name)}
                  datasets={[
                    {
                      label: 'No-Show Rate (%)',
                      data: trends.by_weekday.map((d) => d.rate),
                      backgroundColor: '#1F5A57',
                      borderColor: '#174543',
                      borderWidth: 1,
                    },
                  ]}
                  yLabel="No-Show Rate (%)"
                />
              </div>

              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">Attendance Distribution</div>
                  <div className="ledger-panel-subtitle">Attendance breakdown</div>
                </div>
                <DoughnutChart
                  labels={[
                    `Attended (${formatNumber(trends.attendance_distribution.attended)})`,
                    `No-Show (${formatNumber(trends.attendance_distribution.no_show)})`,
                  ]}
                  dataValues={[
                    trends.attendance_distribution.attended,
                    trends.attendance_distribution.no_show,
                  ]}
                  colors={['#8D9E8F', '#A85D48']}
                />
              </div>
            </div>

            {/* Secondary Trends: Channel + Combined Hourly Chart */}
            <div className="grid-2">
              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">No-Show Rate by Booking Channel</div>
                  <div className="ledger-panel-subtitle">Missed rate by channel</div>
                </div>
                <BarChart
                  labels={trends.by_channel.map((c) => formatChannel(c.channel))}
                  datasets={[
                    {
                      label: 'No-Show Rate (%)',
                      data: trends.by_channel.map((c) => c.rate),
                      backgroundColor: ['#1F5A57', '#A85D48', '#C19345'],
                      borderWidth: 1,
                    },
                  ]}
                  yLabel="No-Show Rate (%)"
                  height={250}
                />
              </div>

              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">Hourly Appointment Volume &amp; No-Show Rate</div>
                  <div className="ledger-panel-subtitle">Hourly volume and missed rate</div>
                </div>
                <CombinedBarLineChart
                  labels={trends.by_hour.map((h) => h.label)}
                  barLabel="Appointment Volume"
                  barData={trends.by_hour.map((h) => h.total)}
                  lineLabel="No-Show Rate (%)"
                  lineData={trends.by_hour.map((h) => h.rate)}
                  leftAxisLabel="Total Appointments"
                  rightAxisLabel="No-Show Rate (%)"
                  height={250}
                />
              </div>
            </div>

            {/* Activity Over Time */}
            {trends.by_month && trends.by_month.length > 0 && (
              <div className="ledger-panel" style={{ marginBottom: '1.5rem' }}>
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">Appointment Activity Over Time (Monthly)</div>
                  <div className="ledger-panel-subtitle">Monthly volume and missed rate</div>
                </div>
                <CombinedBarLineChart
                  labels={trends.by_month.map((m) => m.month)}
                  barLabel="Monthly Appointments"
                  barData={trends.by_month.map((m) => m.total)}
                  lineLabel="Monthly No-Show Rate (%)"
                  lineData={trends.by_month.map((m) => m.rate)}
                  leftAxisLabel="Appointment Count"
                  rightAxisLabel="No-Show Rate (%)"
                  height={240}
                />
              </div>
            )}

            {/* Recent Appointments & Recent Predictions */}
            <div className="grid-2">
              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">Recent Appointments</div>
                  <a
                    href="#appointments"
                    onClick={(e) => {
                      e.preventDefault();
                      scrollToSection('appointments');
                    }}
                    style={{ fontSize: '0.9rem' }}
                  >
                    View all appointments &rarr;
                  </a>
                </div>
                {summary.recent_appointments && summary.recent_appointments.length > 0 ? (
                  <div className="table-container">
                    <table className="ledger-table">
                      <thead>
                        <tr>
                          <th>Appointment ID</th>
                          <th>Scheduled Date</th>
                          <th>Channel</th>
                          <th>Outcome</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.recent_appointments.map((appt) => (
                          <tr key={appt.appointment_id}>
                            <td style={{ fontWeight: 700, color: 'var(--color-teal-deep)' }}>
                              {appt.appointment_id}
                            </td>
                            <td>{formatDate(appt.appointment_datetime)}</td>
                            <td>{formatChannel(appt.booking_channel)}</td>
                            <td>
                              <StatusBadge status={appt.no_show} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p style={{ color: 'var(--color-ink-muted)', fontStyle: 'italic' }}>
                    No appointment records available.
                  </p>
                )}
              </div>

              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">Recent Predictions</div>
                  <a
                    href="#predict"
                    onClick={(e) => {
                      e.preventDefault();
                      scrollToSection('predict');
                    }}
                    style={{ fontSize: '0.9rem' }}
                  >
                    Make prediction &rarr;
                  </a>
                </div>
                {summary.recent_predictions && summary.recent_predictions.length > 0 ? (
                  <div className="table-container">
                    <table className="ledger-table">
                      <thead>
                        <tr>
                          <th>Log ID</th>
                          <th>Channel</th>
                          <th className="num-col">Prob.</th>
                          <th>Outcome</th>
                          <th>Risk</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.recent_predictions.map((p, idx) => (
                          <tr key={p.prediction_id || idx}>
                            <td style={{ fontWeight: 700 }}>{p.prediction_id || '—'}</td>
                            <td>{formatChannel(p.input_features?.booking_channel)}</td>
                            <td className="num-col" style={{ fontWeight: 700 }}>
                              {formatProbability(p.no_show_probability)}
                            </td>
                            <td>
                              <StatusBadge status={p.predicted_outcome} />
                            </td>
                            <td>
                              <StatusBadge status={p.risk_level} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p style={{ color: 'var(--color-ink-muted)', fontStyle: 'italic' }}>
                    No predictions recorded yet. Use the Prediction Desk to test an appointment.
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
