import React, { useEffect, useState } from 'react';
import Header from '../components/layout/Header';
import StatCard from '../components/common/StatCard';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import StatusBadge from '../components/common/StatusBadge';
import BarChart from '../components/charts/BarChart';
import { fetchDataQuality } from '../api/api';
import { formatNumber, formatDate } from '../utils/formatters';

const DATA_DICTIONARY = [
  { name: 'appointment_id', type: 'String', available: 'Identifier', desc: 'Unique synthetic identifier (e.g., APT-000001).' },
  { name: 'booking_created_at', type: 'Datetime', available: 'Split Only', desc: 'Timestamp when appointment was booked. Used solely for chronological splitting.' },
  { name: 'appointment_datetime', type: 'Datetime', available: 'Reference', desc: 'Scheduled date and time of the appointment.' },
  { name: 'booking_lead_days', type: 'Integer', available: 'Yes (Feature)', desc: 'Days elapsed between booking creation and scheduled appointment.' },
  { name: 'appointment_weekday', type: 'Integer (0–6)', available: 'Yes (Feature)', desc: 'Day of week of appointment (0=Monday, 6=Sunday).' },
  { name: 'appointment_hour', type: 'Integer (6–21)', available: 'Yes (Feature)', desc: 'Scheduled hour of the appointment.' },
  { name: 'booking_hour', type: 'Integer (0–23)', available: 'Yes (Feature)', desc: 'Hour of day when reservation was placed.' },
  { name: 'booking_channel', type: 'Categorical', available: 'Yes (Feature)', desc: 'Channel used: online, phone, or in_person.' },
  { name: 'prior_appointments_count', type: 'Integer', available: 'Yes (Feature)', desc: 'Count of previous completed appointments prior to this booking.' },
  { name: 'prior_no_show_count', type: 'Integer', available: 'Yes (Feature)', desc: 'Count of historical missed appointments.' },
  { name: 'prior_cancellations_count', type: 'Integer', available: 'Yes (Feature)', desc: 'Count of prior cancelled bookings.' },
  { name: 'prior_no_show_rate', type: 'Float (0–1)', available: 'Yes (Feature)', desc: 'Ratio of prior no-shows to prior appointments.' },
  { name: 'days_since_last_appointment', type: 'Integer', available: 'Yes (Feature)', desc: 'Days elapsed since previous scheduled appointment (0 if first).' },
  { name: 'no_show', type: 'Binary (0/1)', available: 'Target (Prohibited)', desc: 'Outcome label: 0 = Attended, 1 = No-Show. Never permitted as inference input.' },
];

export default function DataQuality() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadQuality = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDataQuality();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuality();
  }, []);

  const dupFeat = report?.duplicate_feature_rows_removed ?? report?.duplicate_count ?? 0;
  const dupId = report?.duplicate_appointment_ids_removed ?? 0;
  const badTs = report?.removed_impossible_timestamps ?? report?.impossible_timestamps ?? 0;
  const totalDup = report?.duplicate_count ?? dupFeat + dupId;

  return (
    <div>
      <Header
        category="DATA QUALITY"
        title="Data Quality"
        description="Review the dataset and see how records were cleaned."
      />

      <div className="page-body">
        {loading && <LoadingState message="Loading data quality audit report..." />}
        {error && <ErrorState message={error} onRetry={loadQuality} />}

        {!loading && !error && report && (
          <>
            <div className="grid-4">
              <StatCard
                label="Raw Records"
                value={formatNumber(report.initial_record_count)}
                note="Initial synthetic records"
                accent="teal"
              />
              <StatCard
                label="Cleaned Records"
                value={formatNumber(report.final_record_count)}
                note="After duplicate and error removal"
                accent="sage"
              />
              <StatCard
                label="Total Records Removed"
                value={formatNumber(report.records_removed)}
                note={`${dupFeat} duplicates + ${dupId} ID + ${badTs} timestamps`}
                accent="terracotta"
              />
              <StatCard
                label="Negative Counts Masked"
                value={formatNumber(report.negative_counts_set_to_nan)}
                note="Converted to missing values"
                accent="ochre"
              />
            </div>

            {/* Before vs After Comparison Chart + Reconciliation Callout */}
            <div className="ledger-panel" style={{ marginBottom: '1.5rem' }}>
              <div className="ledger-panel-header">
                <div className="ledger-panel-title">Before vs. After Cleaning Reconciliation</div>
                <div className="ledger-panel-subtitle">
                  Summary of anomaly removal
                </div>
              </div>
              <div className="grid-2" style={{ marginBottom: 0, alignItems: 'center' }}>
                <BarChart
                  labels={[
                    'Total Records',
                    'Duplicates Present',
                    'Impossible Timestamps',
                    'Negative Counts',
                  ]}
                  datasets={[
                    {
                      label: 'Before Cleaning (Raw)',
                      data: [
                        report.initial_record_count,
                        totalDup,
                        badTs,
                        report.negative_counts,
                      ],
                      backgroundColor: '#A85D48',
                    },
                    {
                      label: 'After Cleaning (Processed)',
                      data: [report.final_record_count, 0, 0, 0],
                      backgroundColor: '#1F5A57',
                    },
                  ]}
                  height={210}
                />
                <div className="editorial-callout" style={{ margin: 0 }}>
                  <strong>Exact Record Count Reconciliation:</strong>
                  <ul style={{ paddingLeft: '1.25rem', marginTop: '0.45rem', lineHeight: 1.65 }}>
                    <li>Initial raw records: <strong>{formatNumber(report.initial_record_count)}</strong></li>
                    <li>Exact feature-row duplicates removed: <strong>{dupFeat}</strong></li>
                    <li>Duplicate <code>appointment_id</code> (modified duplicate copy) removed: <strong>{dupId}</strong></li>
                    <li>Impossible timestamps removed (<code>booking_created_at &ge; appointment_datetime</code>): <strong>{badTs}</strong></li>
                    <li>Total removed: <strong>{dupFeat} + {dupId} + {badTs} = {report.records_removed}</strong></li>
                    <li>Final cleaned dataset: <strong>{formatNumber(report.final_record_count)}</strong></li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="grid-2">
              {/* Cleaning Actions & Outliers */}
              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">Cleaning Actions &amp; Outlier Audit</div>
                  <div className="ledger-panel-subtitle">Rule-based cleaning steps</div>
                </div>
                <table className="ledger-table">
                  <thead>
                    <tr>
                      <th>Validation Check</th>
                      <th className="num-col">Detected</th>
                      <th>Resolution</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Exact Feature-Row Duplicates</td>
                      <td className="num-col">{dupFeat}</td>
                      <td>Removed duplicate rows</td>
                    </tr>
                    <tr>
                      <td>Duplicate Appointment IDs (Modified Copies)</td>
                      <td className="num-col">{dupId}</td>
                      <td>Removed duplicate IDs, keeping first entry</td>
                    </tr>
                    <tr>
                      <td>Impossible Timestamps (Booked &ge; Appt)</td>
                      <td className="num-col">{badTs}</td>
                      <td>Removed invalid records</td>
                    </tr>
                    <tr>
                      <td>Invalid Negative Historical Counts</td>
                      <td className="num-col">{report.negative_counts}</td>
                      <td>Converted to missing values; imputed during model training</td>
                    </tr>
                    <tr>
                      <td>Inconsistent Channel Formatting</td>
                      <td className="num-col">Standardized</td>
                      <td>Normalized to online, phone, in_person</td>
                    </tr>
                    <tr>
                      <td>Valid Outliers: Lead Days &gt; 120</td>
                      <td className="num-col">{report.outlier_observations?.booking_lead_days_gt_120 ?? 0}</td>
                      <td>Kept (valid long lead time)</td>
                    </tr>
                    <tr>
                      <td>Valid Outliers: Gap &gt; 365 Days</td>
                      <td className="num-col">{report.outlier_observations?.days_since_last_gt_365 ?? 0}</td>
                      <td>Kept (valid returning visit gap)</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Missing Values Breakdown */}
              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div className="ledger-panel-title">Missing Values Profile</div>
                  <div className="ledger-panel-subtitle">Missing values are handled during model training.</div>
                </div>
                <p style={{ fontSize: '0.92rem', color: 'var(--color-ink-muted)', marginBottom: '0.75rem' }}>
                  Missing values are preserved in the cleaned dataset and imputed only on training folds to prevent data leakage. Post-clean counts include the 10 negative counts converted to missing values.
                </p>
                <table className="ledger-table">
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th className="num-col">Raw Missing</th>
                      <th className="num-col">Post-Clean Missing</th>
                      <th>Data Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(report.final_data_types || {}).map(([col, dtype]) => {
                      const rawMiss = report.missing_values?.[col]?.count || 0;
                      const finalMiss = report.final_missing_values?.[col]?.count || 0;
                      return (
                        <tr key={col}>
                          <td style={{ fontWeight: 700 }}>{col}</td>
                          <td className="num-col">{rawMiss}</td>
                          <td className="num-col">{finalMiss}</td>
                          <td>
                            <code>{dtype}</code>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Data Dictionary */}
            <div className="ledger-panel">
              <div className="ledger-panel-header">
                <div className="ledger-panel-title">Dataset Data Dictionary</div>
                <div className="ledger-panel-subtitle">Column definitions and availability</div>
              </div>
              <div className="table-container">
                <table className="ledger-table">
                  <thead>
                    <tr>
                      <th>Column Name</th>
                      <th>Data Type</th>
                      <th>Prediction-Time Status</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {DATA_DICTIONARY.map((col) => (
                      <tr key={col.name}>
                        <td style={{ fontWeight: 700 }}>{col.name}</td>
                        <td>
                          <code>{col.type}</code>
                        </td>
                        <td>
                          <StatusBadge
                            status={
                              col.available.includes('Feature')
                                ? 'attended'
                                : col.available.includes('Prohibited')
                                ? 'noshow'
                                : 'moderate'
                            }
                            label={col.available}
                          />
                        </td>
                        <td>{col.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
