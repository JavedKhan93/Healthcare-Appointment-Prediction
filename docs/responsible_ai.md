# Responsible AI & Governance Framework — MORROW

## 1. Privacy & Synthetic Provenance
- **Zero Patient Data:** MORROW uses exclusively synthetic data generated programmatically (`random_seed = 42`). No patient names, national IDs, addresses, or real clinical histories exist anywhere in the codebase or dataset.
- **Entity Isolation:** Simulated patient keys used solely to derive chronologically consistent prior counts are deleted prior to dataset export and are strictly barred from model training or inference.

## 2. Uncertainty & Calibration Honesty
- The target variable is inherently noisy; operational scheduling metadata cannot observe personal emergencies, sudden illness, or weather disruptions.
- Consequently, MORROW does not attempt to fabricate artificially inflated accuracy (`95%+`) via deterministic shortcuts. Instead, it communicates honest calibrated probabilities (`Brier = 0.1498`, `ROC-AUC = 0.6044`) and displays an explicit experimental disclaimer on every prediction.

## 3. Representativeness & Bias Risks
- **Non-Transferability:** Because synthetic patterns do not mirror specific clinic demographics or regional healthcare barriers, the artifact must not be deployed into production hospitals without retraining and local validation on governed clinical scheduling data.
- **Fairness Safeguard:** In real clinics, historical no-show rates correlate with socioeconomic barriers (e.g., lack of reliable transportation or shift work). Flagged appointments must be met with supportive administrative outreach (e.g., polite reminder calls or flexible rescheduling), never automated penalties or slot revocation.

## 4. Human-in-the-Loop Mandate
- **No Automated Cancellation:** MORROW has no integration with appointment cancellation APIs or automated SMS gateways.
- **No Clinical Scope:** MORROW has no access to clinical codes, diagnoses, or acuity scores and performs zero clinical risk assessment.
- **Human Review:** Every high-risk indicator (`MODERATE`, `HIGH`, `VERY_HIGH`) requires human administrative verification.

