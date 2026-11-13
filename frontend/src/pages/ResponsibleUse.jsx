import React from 'react';
import Header from '../components/layout/Header';

export default function ResponsibleUse() {
  return (
    <div>
      <Header
        category="RESPONSIBLE USE"
        title="Responsible Use"
        description="Understand what predictions can and cannot tell you."
      />

      <div className="page-body">
        <div className="editorial-callout alert" style={{ marginBottom: '1rem' }}>
          <strong>Experimental Prototype Notice:</strong> MORROW is an educational machine learning
          prototype trained using custom-generated synthetic appointment data. It has not been
          validated on real hospital appointment records.
        </div>

        <div className="editorial-callout warning" style={{ marginBottom: '1.5rem' }}>
          <strong>Mandatory Boundary:</strong> MORROW is strictly an administrative support tool.
          It must never be used to deny care, predict clinical outcomes, assess medical urgency, or
          automatically cancel appointments.
        </div>

        <div className="grid-2">
          <div className="ledger-panel">
            <div className="ledger-panel-header">
              <div className="ledger-panel-title">1. Synthetic Data &amp; Privacy</div>
            </div>
            <p style={{ marginBottom: '0.75rem' }}>
              All appointment records, attendance outcomes, and evaluation statistics in MORROW come
              from a reproducible synthetic simulation (<code>random_seed = 42</code>).
            </p>
            <p>
              No real patient records, personal identifiers, Protected Health Information (PHI), or
              external medical databases are used. Internal simulation keys are removed prior to
              export and are never included in model features.
            </p>
          </div>

          <div className="ledger-panel">
            <div className="ledger-panel-header">
              <div className="ledger-panel-title">2. Probability Uncertainty &amp; Limitations</div>
            </div>
            <p style={{ marginBottom: '0.75rem' }}>
              Predictions show statistical likelihoods, not certainties. Because real attendance
              depends on factors not captured in booking history (such as transit delays, sudden
              illness, or work changes), the model has modest discrimination (Test ROC-AUC ~0.60).
            </p>
            <p>
              Staff should treat an elevated score as a soft signal for optional courtesy outreach,
              not as proof that a patient will miss their visit.
            </p>
          </div>

          <div className="ledger-panel">
            <div className="ledger-panel-header">
              <div className="ledger-panel-title">3. Representativeness &amp; Potential Bias</div>
            </div>
            <p style={{ marginBottom: '0.75rem' }}>
              Synthetic rules do not reflect the demographic, socioeconomic, or regional factors
              found in real healthcare facilities. The model cannot be deployed in a clinical
              setting without local validation.
            </p>
            <p>
              In real hospitals, relying on past missed appointments can disproportionately flag
              patients facing transport or childcare barriers. Any follow-up should be supportive,
              never punitive.
            </p>
          </div>

          <div className="ledger-panel">
            <div className="ledger-panel-header">
              <div className="ledger-panel-title">4. Human Review &amp; Prohibited Actions</div>
            </div>
            <ul style={{ paddingLeft: '1.25rem', lineHeight: 1.7 }}>
              <li>
                <strong>Human Review Required:</strong> Staff review predictions alongside clinic
                schedules before making courtesy reminder calls.
              </li>
              <li>
                <strong>No Automated Actions:</strong> MORROW never cancels appointments, triggers
                automatic messages, or double-books schedules.
              </li>
              <li>
                <strong>No Clinical Scope:</strong> The model has no access to diagnoses, medical
                specialties, symptoms, or clinical urgency.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

