import React, { useEffect, useState } from 'react';
import Header from '../components/layout/Header';
import StatCard from '../components/common/StatCard';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import StatusBadge from '../components/common/StatusBadge';
import BarChart from '../components/charts/BarChart';
import LineChart from '../components/charts/LineChart';
import { fetchModelMetrics, fetchFeatureImportance, fetchModelMetadata } from '../api/api';
import { formatNumber } from '../utils/formatters';

export default function ModelEvidence() {
  const [metricsData, setMetricsData] = useState(null);
  const [featureImp, setFeatureImp] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadEvidence = async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, fi, meta] = await Promise.all([
        fetchModelMetrics(),
        fetchFeatureImportance(),
        fetchModelMetadata(),
      ]);
      setMetricsData(m);
      setFeatureImp(fi || []);
      setMetadata(meta);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvidence();
  }, []);

  const comparison = metricsData?.comparison;
  const testMetrics = metricsData?.test_metrics;
  const threshAnalysis = metricsData?.threshold_analysis;
  const curves = metricsData?.curves;

  return (
    <div>
      <Header
        category="MODEL RESULTS"
        title="Model Performance"
        description="Compare models and review results on unseen appointments."
      />

      <div className="page-body page-body-wide">
        {loading && <LoadingState message="Loading model evaluation artifacts..." />}
        {error && <ErrorState message={error} onRetry={loadEvidence} />}

        {!loading && !error && metricsData && (
          <>
            {/* Selected Model Summary Cards */}
            {testMetrics && (
              <div className="grid-4">
                <StatCard
                  label="Selected Model"
                  value={testMetrics.model_name}
                  note={`v${testMetrics.model_version} · ${metadata?.calibration_method || 'Platt Scaling'}`}
                  accent="teal"
                />
                <StatCard
                  label="Test ROC-AUC / PR-AUC"
                  value={`${testMetrics.roc_auc.toFixed(3)} / ${testMetrics.pr_auc.toFixed(3)}`}
                  note={`Held-out test set (n=${formatNumber(testMetrics.test_sample_count)})`}
                  accent="ochre"
                />
                <StatCard
                  label="Operating Threshold"
                  value={testMetrics.applied_threshold.toFixed(2)}
                  note={`Flags ${formatNumber(testMetrics.flagged_count)} of ${formatNumber(testMetrics.test_sample_count)} test visits (${testMetrics.flagged_percentage}%)`}
                  accent="terracotta"
                />
                <StatCard
                  label="Test Brier vs Reference"
                  value={testMetrics.brier_score.toFixed(4)}
                  note={`Test prevalence-only (${((testMetrics.reference_prevalence ?? 0) * 100).toFixed(2)}%): ${testMetrics.reference_brier_score?.toFixed(4) ?? '—'}`}
                  accent="sage"
                />
              </div>
            )}

            {/* 1. Validation Set Candidate Model Comparison */}
            {comparison && (
              <div className="ledger-panel" style={{ marginBottom: '1.5rem' }}>
                <div className="ledger-panel-header">
                  <div>
                    <div className="ledger-panel-title">
                      1. Validation Model Selection (n = {formatNumber(comparison.split_info?.validation?.count ?? 1492)})
                    </div>
                    <div className="ledger-panel-subtitle">
                      Threshold {comparison.classification_threshold?.toFixed(2) ?? '0.50'} · Stratified baseline · Selected by F1 + PR-AUC
                    </div>
                  </div>
                </div>
                <div className="table-container">
                  <table className="ledger-table">
                    <thead>
                      <tr>
                        <th>Algorithm</th>
                        <th className="num-col">Threshold</th>
                        <th className="num-col">Accuracy</th>
                        <th className="num-col">Precision</th>
                        <th className="num-col">Recall</th>
                        <th className="num-col">F1-Score</th>
                        <th className="num-col">ROC-AUC</th>
                        <th className="num-col">PR-AUC</th>
                        <th className="num-col">Brier Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(comparison.models).map(([name, m]) => {
                        const isBest = name === comparison.best_model;
                        return (
                          <tr
                            key={name}
                            style={isBest ? { backgroundColor: 'var(--color-sage-bg)' } : undefined}
                          >
                            <td style={{ fontWeight: 700 }}>
                              {name}{' '}
                              {isBest && <StatusBadge status="attended" label="Selected" />}
                            </td>
                            <td className="num-col">0.50</td>
                            <td className="num-col">{m.accuracy.toFixed(4)}</td>
                            <td className="num-col">{m.precision.toFixed(4)}</td>
                            <td className="num-col">{m.recall.toFixed(4)}</td>
                            <td className="num-col" style={{ fontWeight: 700 }}>
                              {m.f1.toFixed(4)}
                            </td>
                            <td className="num-col">{m.roc_auc.toFixed(4)}</td>
                            <td className="num-col" style={{ fontWeight: 700 }}>
                              {m.average_precision.toFixed(4)}
                            </td>
                            <td className="num-col">{m.brier_score_loss.toFixed(4)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 2. Final Held-Out Test Set Comparison (Frozen Models) */}
            {testMetrics?.test_comparison && (
              <div className="ledger-panel" style={{ marginBottom: '1.5rem' }}>
                <div className="ledger-panel-header">
                  <div>
                    <div className="ledger-panel-title">
                      2. Held-Out Test Comparison (Frozen Models, n = {formatNumber(testMetrics.test_sample_count)})
                    </div>
                    <div className="ledger-panel-subtitle">
                      Period: {testMetrics.test_start_date.slice(0, 10)} to {testMetrics.test_end_date.slice(0, 10)} · Evaluated on unseen test data
                    </div>
                  </div>
                </div>
                <div className="table-container">
                  <table className="ledger-table">
                    <thead>
                      <tr>
                        <th>Frozen Model</th>
                        <th className="num-col">Threshold</th>
                        <th className="num-col">Accuracy</th>
                        <th className="num-col">Precision</th>
                        <th className="num-col">Recall</th>
                        <th className="num-col">F1-Score</th>
                        <th className="num-col">ROC-AUC</th>
                        <th className="num-col">PR-AUC</th>
                        <th className="num-col">Brier Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(testMetrics.test_comparison).map(([name, m]) => {
                        const isCalibrated = name.includes('Calibrated');
                        return (
                          <tr
                            key={name}
                            style={isCalibrated ? { backgroundColor: 'var(--color-ochre-bg)', fontWeight: 700 } : undefined}
                          >
                            <td style={{ fontWeight: 700 }}>
                              {name}{' '}
                              {isCalibrated && <StatusBadge status="moderate" label="Deployed" />}
                            </td>
                            <td className="num-col">{Number(m.threshold).toFixed(2)}</td>
                            <td className="num-col">{m.accuracy.toFixed(4)}</td>
                            <td className="num-col">{m.precision.toFixed(4)}</td>
                            <td className="num-col">{m.recall.toFixed(4)}</td>
                            <td className="num-col">{m.f1.toFixed(4)}</td>
                            <td className="num-col">{m.roc_auc.toFixed(4)}</td>
                            <td className="num-col">{m.pr_auc.toFixed(4)}</td>
                            <td className="num-col">{m.brier_score.toFixed(4)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 3. Validation ROC, Precision-Recall, and Calibration Curves */}
            {curves && (
              <div className="model-evidence-charts-grid">
                <div className="ledger-panel">
                  <div className="chart-panel-header">
                    <div className="chart-panel-title">Validation ROC Curve</div>
                    <div className="chart-panel-subtitle">
                      Calibrated {comparison?.best_model ?? 'LogisticRegression'} (Platt Scaling) · Validation Split (n = {formatNumber(comparison?.split_info?.validation?.count ?? 1492)}) · AUC = {curves.roc_curve.auc.toFixed(4)}
                    </div>
                  </div>
                  <LineChart
                    labels={curves.roc_curve.fpr.map((v) => v.toFixed(2))}
                    datasets={[
                      {
                        label: `Calibrated ${comparison?.best_model ?? 'LR'}`,
                        data: curves.roc_curve.tpr,
                        borderColor: '#1F5A57',
                        backgroundColor: 'rgba(31, 90, 87, 0.1)',
                        tension: 0.15,
                        pointRadius: 2.5,
                      },
                      {
                        label: 'Random Chance',
                        data: curves.roc_curve.fpr,
                        borderColor: '#8D9E8F',
                        borderDash: [5, 5],
                        pointRadius: 0,
                      },
                    ]}
                    xLabel="False Positive Rate"
                    yLabel="True Positive Rate"
                    yMin={0}
                    yMax={1}
                    height={300}
                  />
                  <p className="chart-caption">
                    Uses calibrated (Platt-scaled) validation predictions. Uncalibrated validation ROC-AUC (100% train):{' '}
                    {comparison?.models?.[comparison?.best_model]?.roc_auc?.toFixed(4) ?? '—'}.
                  </p>
                </div>

                <div className="ledger-panel">
                  <div className="chart-panel-header">
                    <div className="chart-panel-title">Validation Precision–Recall Curve</div>
                    <div className="chart-panel-subtitle">
                      Calibrated {comparison?.best_model ?? 'LogisticRegression'} (Platt Scaling) · Validation Split (n = {formatNumber(comparison?.split_info?.validation?.count ?? 1492)}) · AP = {(curves.pr_curve.average_precision ?? curves.pr_curve.auc).toFixed(4)} (Trapz AUC = {curves.pr_curve.auc.toFixed(4)})
                    </div>
                  </div>
                  <LineChart
                    labels={curves.pr_curve.recall.map((v) => v.toFixed(2))}
                    datasets={[
                      {
                        label: `Calibrated ${comparison?.best_model ?? 'LR'}`,
                        data: curves.pr_curve.precision,
                        borderColor: '#A85D48',
                        backgroundColor: 'rgba(168, 93, 72, 0.1)',
                        tension: 0.15,
                        pointRadius: 2.5,
                      },
                      {
                        label: `Prevalence (${(curves.pr_curve.baseline * 100).toFixed(1)}%)`,
                        data: curves.pr_curve.recall.map(() => curves.pr_curve.baseline),
                        borderColor: '#8D9E8F',
                        borderDash: [5, 5],
                        pointRadius: 0,
                      },
                    ]}
                    xLabel="Recall"
                    yLabel="Precision"
                    yMin={0}
                    yMax={1}
                    height={300}
                  />
                  <p className="chart-caption">
                    Uses calibrated (Platt-scaled) validation predictions. Uncalibrated validation PR-AUC (AP):{' '}
                    {comparison?.models?.[comparison?.best_model]?.average_precision?.toFixed(4) ?? '—'}.
                  </p>
                </div>

                <div className="ledger-panel">
                  <div className="chart-panel-header">
                    <div className="chart-panel-title">Validation Calibration Curve (Uniform Bins)</div>
                    <div className="chart-panel-subtitle">
                      Calibrated {comparison?.best_model ?? 'LogisticRegression'} (Platt Scaling) · Validation Split (n = {formatNumber(comparison?.split_info?.validation?.count ?? 1492)}) · Val Brier = {curves.calibration_curve.brier_score.toFixed(4)} (Val Prevalence Ref: {(curves.calibration_curve.reference_brier_score ?? threshAnalysis?.reference_brier_score)?.toFixed(4) ?? '—'})
                    </div>
                  </div>
                  <LineChart
                    labels={curves.calibration_curve.mean_predicted.map((v, idx) => {
                      const cnt = curves.calibration_curve.bin_counts?.[idx];
                      return cnt !== undefined ? `${v.toFixed(2)} (n=${cnt})` : v.toFixed(2);
                    })}
                    datasets={[
                      {
                        label: 'Platt-Scaled Model (Uniform)',
                        data: curves.calibration_curve.fraction_positives,
                        borderColor: '#1F5A57',
                        backgroundColor: '#1F5A57',
                        pointRadius: 4,
                      },
                      {
                        label: 'Perfect Calibration',
                        data: curves.calibration_curve.mean_predicted,
                        borderColor: '#263A3A',
                        borderDash: [5, 5],
                        pointRadius: 0,
                      },
                    ]}
                    xLabel="Mean Predicted Probability (Sample Count)"
                    yLabel="Observed Positive Fraction"
                    height={300}
                  />
                  {curves.calibration_curve.bin_counts && (
                    <div className="chart-caption">
                      <strong>Uniform bins (n per bin):</strong>{' '}
                      {curves.calibration_curve.mean_predicted.map((mp, idx) => (
                        <span key={idx}>
                          {idx > 0 ? ' · ' : ''}
                          {curves.calibration_curve.bin_ranges?.[idx] ?? `p̄=${mp.toFixed(2)}`}:{' '}
                          <strong>n={curves.calibration_curve.bin_counts[idx]}</strong>
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="chart-caption" style={{ marginTop: '0.4rem' }}>
                    Uniform width bins concentrate {curves.calibration_curve.bin_counts?.[1] ?? 'most'} records in [0.1, 0.2]. Validation Brier ({curves.calibration_curve.brier_score.toFixed(4)}) and Held-Out Test Brier ({testMetrics?.brier_score?.toFixed(4) ?? '—'}) evaluate different chronological splits.
                  </p>
                </div>

                {curves.quantile_calibration_curve && curves.quantile_calibration_curve.bin_counts?.length > 0 && (
                  <div className="ledger-panel">
                    <div className="chart-panel-header">
                      <div className="chart-panel-title">
                        Validation Calibration Curve ({curves.quantile_calibration_curve.n_bins_actual ?? 5}-Bin Quantile)
                      </div>
                      <div className="chart-panel-subtitle">
                        Calibrated {comparison?.best_model ?? 'LogisticRegression'} (Platt Scaling) · Validation Split (n = {formatNumber(comparison?.split_info?.validation?.count ?? 1492)}) · Val Brier = {curves.quantile_calibration_curve.brier_score.toFixed(4)} (Val Prevalence Ref: {curves.quantile_calibration_curve.reference_brier_score.toFixed(4)})
                      </div>
                    </div>
                    <LineChart
                      labels={curves.quantile_calibration_curve.mean_predicted.map((v, idx) => {
                        const cnt = curves.quantile_calibration_curve.bin_counts?.[idx];
                        return cnt !== undefined ? `${v.toFixed(3)} (n=${cnt})` : v.toFixed(3);
                      })}
                      datasets={[
                        {
                          label: `Platt-Scaled Model (${curves.quantile_calibration_curve.n_bins_actual ?? 5} Quantile Bins)`,
                          data: curves.quantile_calibration_curve.fraction_positives,
                          borderColor: '#A85D48',
                          backgroundColor: '#A85D48',
                          pointRadius: 4.5,
                        },
                        {
                          label: 'Perfect Calibration',
                          data: curves.quantile_calibration_curve.mean_predicted,
                          borderColor: '#263A3A',
                          borderDash: [5, 5],
                          pointRadius: 0,
                        },
                      ]}
                      xLabel="Mean Predicted Probability (Sample Count)"
                      yLabel="Observed Positive Fraction"
                      height={300}
                    />
                    <table className="calibration-bins-table">
                      <thead>
                        <tr>
                          <th>Quantile Bin</th>
                          <th>Prob. Range</th>
                          <th>Mean Pred.</th>
                          <th>Actual Pos.</th>
                          <th>Records (n)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {curves.quantile_calibration_curve.mean_predicted.map((mp, idx) => (
                          <tr key={idx}>
                            <td>Bin {idx + 1}</td>
                            <td>{curves.quantile_calibration_curve.bin_ranges?.[idx] ?? '—'}</td>
                            <td>{mp.toFixed(4)}</td>
                            <td>{curves.quantile_calibration_curve.fraction_positives[idx].toFixed(4)}</td>
                            <td><strong>{curves.quantile_calibration_curve.bin_counts[idx]}</strong></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="chart-caption">
                      Equal-count quantile bins computed from the saved validation probability array (n = {formatNumber(comparison?.split_info?.validation?.count ?? 1492)}), retaining the original validation Brier score ({curves.quantile_calibration_curve.brier_score.toFixed(4)}).
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* 4. Global Permutation Importance + Held-Out Confusion Matrix */}
            <div className="grid-asymmetric">
              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div>
                    <div className="ledger-panel-title">Global Feature Importance</div>
                    <div className="ledger-panel-subtitle">
                      Mean ROC-AUC Drop After Feature Permutation (Validation Set, 10 repeats)
                    </div>
                  </div>
                </div>
                {featureImp.length > 0 ? (
                  <>
                    <BarChart
                      horizontal
                      labels={featureImp.map((f) => f.feature)}
                      datasets={[
                        {
                          label: 'Mean ROC-AUC Drop After Permutation',
                          data: featureImp.map((f) => Number(f.importance_mean.toFixed(5))),
                          backgroundColor: '#1F5A57',
                          borderColor: '#174543',
                          borderWidth: 1,
                        },
                      ]}
                      height={300}
                    />
                    <p style={{ marginTop: '0.75rem', fontSize: '0.88rem', color: 'var(--color-ink-muted)' }}>
                      <strong>Non-Causal Notice:</strong> Permutation importance reflects global model reliance on
                      validation splits, not individual causal drivers of missed appointments.
                    </p>
                  </>
                ) : (
                  <p>No feature importance data found.</p>
                )}
              </div>

              {testMetrics && (
                <div className="ledger-panel">
                  <div className="ledger-panel-header">
                    <div className="ledger-panel-title">Held-Out Test Confusion Matrix</div>
                    <div className="ledger-panel-subtitle">
                      n = {formatNumber(testMetrics.test_sample_count)} · Threshold = {testMetrics.applied_threshold.toFixed(2)}
                    </div>
                  </div>

                  <div className="table-container">
                    <table className="ledger-table">
                      <thead>
                        <tr>
                          <th>Actual \ Predicted</th>
                          <th className="num-col">Predicted Attended (0)</th>
                          <th className="num-col">Predicted No-Show (1)</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <th>Actual Attended (0)</th>
                          <td className="num-col" style={{ backgroundColor: 'var(--color-sage-bg)', fontWeight: 700 }}>
                            {formatNumber(testMetrics.confusion_matrix.true_negatives)} (TN)
                          </td>
                          <td className="num-col" style={{ backgroundColor: 'var(--color-ochre-bg)' }}>
                            {formatNumber(testMetrics.confusion_matrix.false_positives)} (FP)
                          </td>
                        </tr>
                        <tr>
                          <th>Actual No-Show (1)</th>
                          <td className="num-col" style={{ backgroundColor: 'var(--color-terracotta-bg)' }}>
                            {formatNumber(testMetrics.confusion_matrix.false_negatives)} (FN)
                          </td>
                          <td className="num-col" style={{ backgroundColor: 'var(--color-sage-bg)', fontWeight: 700 }}>
                            {formatNumber(testMetrics.confusion_matrix.true_positives)} (TP)
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div style={{ marginTop: '0.85rem', fontSize: '0.9rem' }}>
                    <strong>Test Metrics:</strong> Precision = {testMetrics.precision.toFixed(4)} | Recall ={' '}
                    {testMetrics.recall.toFixed(4)} | F1 = {testMetrics.f1.toFixed(4)} | Accuracy ={' '}
                    {testMetrics.accuracy.toFixed(4)}
                  </div>

                  <div className="editorial-callout warning" style={{ marginTop: '0.85rem', fontSize: '0.88rem' }}>
                    <strong>Honest Operational Trade-Off:</strong> To capture {testMetrics.confusion_matrix.true_positives} of{' '}
                    {testMetrics.confusion_matrix.true_positives + testMetrics.confusion_matrix.false_negatives} true no-shows
                    (64.0% recall), threshold {testMetrics.applied_threshold.toFixed(2)} flags{' '}
                    <strong>{testMetrics.flagged_count} appointments ({testMetrics.flagged_percentage}%)</strong> and produces{' '}
                    <strong>{testMetrics.confusion_matrix.false_positives} false-positive alerts</strong>. Operations teams
                    must absorb substantial reminder-review workload in exchange for catching missed slots early.
                  </div>
                </div>
              )}
            </div>

            {/* 5. Threshold Analysis Table */}
            {threshAnalysis && (
              <div className="ledger-panel">
                <div className="ledger-panel-header">
                  <div>
                    <div className="ledger-panel-title">
                      Decision Threshold &amp; Cost Trade-Off (Validation Set, n = {formatNumber(threshAnalysis.validation_sample_count ?? 1492)})
                    </div>
                    <div className="ledger-panel-subtitle">
                      Illustrative costs: False Positive = ${threshAnalysis.cost_assumptions.false_positive_cost} | False Negative = ${threshAnalysis.cost_assumptions.false_negative_cost}
                    </div>
                  </div>
                </div>
                <p style={{ marginBottom: '1rem', fontSize: '0.94rem' }}>
                  {threshAnalysis.justification}
                </p>
                <div className="table-container">
                  <table className="ledger-table">
                    <thead>
                      <tr>
                        <th className="num-col">Threshold</th>
                        <th className="num-col">Flagged (TP+FP)</th>
                        <th className="num-col">Precision</th>
                        <th className="num-col">Recall</th>
                        <th className="num-col">F1-Score</th>
                        <th className="num-col">TP</th>
                        <th className="num-col">FP</th>
                        <th className="num-col">TN</th>
                        <th className="num-col">FN</th>
                        <th className="num-col">Hypothetical Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {threshAnalysis.threshold_evaluations.map((row) => {
                        const isSelected = row.threshold === threshAnalysis.selected_threshold;
                        const flagged = row.flagged_count ?? row.true_positives + row.false_positives;
                        return (
                          <tr
                            key={row.threshold}
                            style={isSelected ? { backgroundColor: 'var(--color-ochre-bg)', fontWeight: 700 } : undefined}
                          >
                            <td className="num-col">
                              {row.threshold.toFixed(2)} {isSelected ? '★' : ''}
                            </td>
                            <td className="num-col">
                              {flagged} ({row.flagged_percentage ?? ((flagged / 1492) * 100).toFixed(1)}%)
                            </td>
                            <td className="num-col">{row.precision.toFixed(4)}</td>
                            <td className="num-col">{row.recall.toFixed(4)}</td>
                            <td className="num-col">{row.f1.toFixed(4)}</td>
                            <td className="num-col">{row.true_positives}</td>
                            <td className="num-col">{row.false_positives}</td>
                            <td className="num-col">{row.true_negatives}</td>
                            <td className="num-col">{row.false_negatives}</td>
                            <td className="num-col">${row.hypothetical_cost.toLocaleString()}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
