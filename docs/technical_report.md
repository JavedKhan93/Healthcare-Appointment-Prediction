# Technical Report — MORROW Hospital Appointment No-Show Prediction System

**Organization:** ALGIONS AI LABS PRIVATE LIMITED  
**Project Title:** MORROW — Appointment Operations & No-Show Intelligence  
**Date:** November 2026  

---

## 1. Introduction
Outpatient clinic scheduling depends heavily on predictable patient attendance. Missed appointments without advance notice ("no-shows") cause unrecovered clinician capacity, extended patient waitlists, and elevated administrative overhead. **MORROW** is an end-to-end machine learning operations system built to estimate the probability of non-attendance at the exact time of booking.

## 2. Problem Statement
Given booking-time operational features for a scheduled hospital appointment, estimate the probability $P(\text{no\_show} = 1 \mid X) \in [0, 1]$ and assign an actionable administrative classification (`0 = Attended`, `1 = No-Show`) using an operating threshold calibrated to asymmetric hospital costs.

## 3. Objectives
1. Generate a realistic, reproducible synthetic hospital appointment dataset (`random_seed = 42`) free of real patient data.
2. Implement an automated data cleaning and audit pipeline preventing train/test imputation leakage.
3. Build and compare four Scikit-learn classification pipelines across strict chronological splits.
4. Calibrate output probabilities using chronological Platt scaling (`CalibratedClassifierCV`) and select an operating threshold using validation operational costs.
5. Deploy the serialized ML artifact (`no_show_pipeline.joblib`) inside a production-structured Flask REST API backed by MongoDB (`morrow_hospital`) and an accessible React 18 frontend.

## 4. Dataset Description
The cleaned dataset (`data/processed/synthetic_appointments_cleaned.csv`) contains **`9,950`** chronological appointment records spanning **`2022-10-04` to `2024-12-29`**, with an overall no-show rate of **`17.09%`** (`8,250` Attended, `1,700` No-Show).

## 5. Data Generation
Implemented in `ml/data/generate_synthetic_data.py`:
- Simulates `2,500` fictional longitudinal patient schedules (`9,955` clean appointments).
- Derives historical counts (`prior_appointments_count`, `prior_no_show_count`, `prior_cancellations_count`, `prior_no_show_rate`, `days_since_last_appointment`) strictly from earlier appointments.
- Strips temporary `patient_key` prior to export.
- Computes probabilistic outcomes combining latent patient propensity (`Beta(2,5)`), lead time, weekday, clinic hour, booking channel, prior history, and Gaussian noise (`Normal(0, 0.08)`), clipped to `[0.05, 0.65]`.
- Injects controlled anomalies (`50` duplicates, `48` missing values, `15` formatting discrepancies, `10` negative counts, `5` impossible timestamps) yielding `10,005` raw rows.

## 6. Data Cleaning
Implemented in `ml/data/clean_dataset.py` (`artifacts/metrics/data_quality_report.json`):
- **Initial Raw Rows:** `10,005`
- **Duplicates Removed (`50` total):** `49` exact feature-row duplicates + `1` duplicate `appointment_id` (modified duplicate copy)
- **Impossible Timestamps Removed (`booking_created_at >= appointment_datetime`):** `5`
- **Invalid Target Rows Removed:** `0`
- **Invalid Negative Counts Converted to Missing (`NaN`):** `10` (`5` in `prior_no_show_count`, `5` in `prior_cancellations_count`)
- **Categorical Standardization:** Normalized `booking_channel` variants (`ONLINE`, `telephone`, `in-person`) to `online`, `phone`, `in_person`.
- **Valid Outliers Preserved:** `2` records with `booking_lead_days > 120` and `328` records with `days_since_last_appointment > 365` were documented and retained.
- **Missing Values Preserved:** `58` post-cleaning `NaN` values across 7 columns were deliberately retained for training-fold imputation inside Scikit-learn pipelines.
- **Final Cleaned Rows (Exact Reconciliation):** `10,005 − 55 (49 + 1 + 5) = 9,950`.

## 7. Exploratory Data Analysis (EDA)
Implemented in `ml/eda/analyze_dataset.py` and `notebooks/01_data_exploration.ipynb`, generating 7 visualizations in `artifacts/figures/`:
- **Target Imbalance:** `82.91%` Attended (`8,250`) vs. `17.09%` No-Show (`1,700`).
- **Channel Distribution:** `online` (`3,577` / `35.9%`), `phone` (`3,201` / `32.2%`), `in_person` (`3,152` / `31.7%`).
- **Lead Time:** Mean `14.74` days (median `10.0`, max `126.0`).
- **Prior Appointments:** Mean `2.29` (median `2.0`, max `16.0`); mean `prior_no_show_rate` = `0.130`.

## 8. Feature Engineering
Implemented in `ml/features/build_features.py`:
- **10 Exact Prediction-Time Features:** `booking_lead_days`, `appointment_weekday`, `appointment_hour`, `booking_hour`, `booking_channel`, `prior_appointments_count`, `prior_no_show_count`, `prior_cancellations_count`, `prior_no_show_rate`, `days_since_last_appointment`.
- **Preprocessing (`ColumnTransformer`):**
  - Numerical (9 features): `SimpleImputer(strategy="median")` $\rightarrow$ `StandardScaler()`
  - Categorical (`booking_channel`): `SimpleImputer(strategy="most_frequent")` $\rightarrow$ `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`
  - Produces `12` dense transformed features, fitted strictly on the training split.

## 9. Leakage Prevention
- `no_show`, post-appointment status, timestamps (`booking_created_at`, `appointment_datetime`), `appointment_id`, and internal `patient_key` are completely excluded from `MODEL_FEATURES`.
- Backend validation (`backend/utils/validation.py`) explicitly rejects any inference request containing `no_show` or post-appointment fields with HTTP `400`.
- Imputers and scalers are never fitted on validation or test rows.

## 10. Chronological Split Strategy
Sorted strictly ascending by `booking_created_at`:
- **Training Split (70%):** `6,965` records (`2022-10-04 14:10:00` to `2024-05-11 19:50:00`, no-show rate `16.50%`)
- **Validation Split (15%):** `1,492` records (`2024-05-11 21:40:00` to `2024-08-29 18:40:00`, no-show rate `18.30%`)
- **Test Split (15%):** `1,493` records (`2024-08-29 19:30:00` to `2024-12-29 18:00:00`, no-show rate `18.62%`)

## 11. Baseline Model
`DummyClassifier(strategy="stratified", random_state=42)` establishes the minimum performance floor on validation: Accuracy `0.7084`, F1 `0.1808`, ROC-AUC `0.5018`, PR-AUC `0.1835`.

## 12. Candidate Models
1. **DummyClassifier** (`strategy="stratified"`)
2. **LogisticRegression** (`C=1.0`, `class_weight="balanced"`, `max_iter=1000`, `solver="lbfgs"`)
3. **RandomForestClassifier** (`n_estimators=200`, `max_depth=12`, `min_samples_leaf=10`, `class_weight="balanced_subsample"`)
4. **HistGradientBoostingClassifier** (`learning_rate=0.05`, `max_iter=300`, `max_leaf_nodes=31`, `min_samples_leaf=20`, `l2_regularization=0.1`)

## 13. Model Comparison (Validation Set)
| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Brier |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| DummyClassifier | 0.7084 | 0.1860 | 0.1758 | 0.1808 | 0.5018 | 0.1835 | 0.2916 |
| **LogisticRegression** ★ | 0.6025 | 0.2232 | 0.4725 | **0.3032** | **0.5804** | **0.2384** | 0.2369 |
| RandomForest | 0.7239 | 0.2296 | 0.2161 | 0.2226 | 0.5570 | 0.2167 | 0.1982 |
| HistGradientBoosting | 0.8103 | 0.2727 | 0.0220 | 0.0407 | 0.5474 | 0.2199 | 0.1563 |

**Selection Justification:** `LogisticRegression` achieved the highest validation F1 (`0.3032`), ROC-AUC (`0.5804`), and PR-AUC (`0.2384`) while maintaining full linear interpretability. `HistGradientBoosting` without sample weighting collapsed to predicting the majority class (`Recall = 0.0220`).

## 14. Held-Out Test Evaluation & Frozen Model Comparison
Evaluated strictly once on `1,493` held-out chronological test appointments (`2024-08-29` to `2024-12-29`) after freezing model selection, calibration, and thresholding:

| Frozen Model | Threshold | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Brier |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| DummyClassifier (`stratified`) | 0.50 | 0.7173 | 0.2209 | 0.2050 | 0.2127 | 0.5198 | 0.1933 | 0.2827 |
| LogisticRegression (Uncalibrated) | 0.50 | 0.6330 | 0.2472 | 0.4748 | 0.3251 | 0.6067 | 0.2547 | 0.2339 |
| RandomForest | 0.50 | 0.7314 | 0.2140 | 0.1655 | 0.1866 | 0.5867 | 0.2352 | 0.1921 |
| HistGradientBoosting | 0.50 | 0.8091 | 0.2667 | 0.0144 | 0.0273 | 0.5688 | 0.2393 | 0.1560 |
| **LogisticRegression (Calibrated, Selected)** | **0.15** | **0.5325** | **0.2294** | **0.6403** | **0.3378** | **0.6044** | **0.2530** | **0.1498** |

- **Held-Out Confusion Matrix (Calibrated Selected, t=0.15):** `TN = 617`, `FP = 598`, `FN = 100`, `TP = 178` (`Total = 1,493`).
- **Operational Workload Note:** Flagging `776` (`51.98%`) of test appointments yields `64.03%` recall while generating `598` false-positive alerts that administrative staff must review.

## 15. Probability Calibration
Because `class_weight="balanced"` inflates raw predicted probabilities toward `0.50`, `CalibratedClassifierCV(method="sigmoid")` (Platt scaling) was fitted using an explicit chronological `80/20` split within training data (`5,572` fit / `1,393` calibration rows; zero test data used). This reduced validation Brier score from `0.2369` (uncalibrated) to **`0.1480`** (vs. prevalence-only reference Brier **`0.1498`**), and achieved **`0.1498`** on the held-out test set (vs. prevalence-only reference Brier **`0.1520`**). Because the synthetic target is dominated by overlapping uncertainty, a modest Brier reduction over the base prevalence must always be read alongside the reliability diagram and ROC-AUC (`0.6044`).

## 16. Threshold Analysis
Using illustrative asymmetric operational costs (**FP = \$5.00** unnecessary reminder review vs. **FN = \$50.00** missed clinic slot):

| Threshold | Precision | Recall | F1-Score | TP | FP | TN | FN | Operational Cost |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.15 ★** | 0.2114 | **0.6374** | **0.3175** | 174 | 649 | 570 | 99 | **\$8,195.00** |
| 0.20 | 0.2892 | 0.2161 | 0.2474 | 59 | 145 | 1074 | 214 | \$11,425.00 |
| 0.25 | 0.3036 | 0.0623 | 0.1033 | 17 | 39 | 1180 | 256 | \$12,995.00 |
| 0.30 | 0.2857 | 0.0220 | 0.0408 | 6 | 15 | 1204 | 267 | \$13,425.00 |
| 0.40 | 0.3333 | 0.0037 | 0.0072 | 1 | 2 | 1217 | 272 | \$13,610.00 |
| 0.50 | 1.0000 | 0.0037 | 0.0073 | 1 | 0 | 1219 | 272 | \$13,600.00 |
| 0.60 / 0.70 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1219 | 273 | \$13,650.00 |

Threshold `0.15` reduces validation operational cost by **40.0%** compared to `0.50` (`$8,195` vs. `$13,600`) and yielded `$7,990.00` on held-out test data.

## 17. Error Analysis & Real Prediction Walkthrough
- **True Positive Walkthrough (Test Record):** `booking_lead_days=4`, `appointment_weekday=0`, `appointment_hour=18`, `booking_channel='in_person'`, `prior_appointments_count=5`, `prior_no_show_count=4`, `prior_no_show_rate=0.80`, `days_since_last_appointment=315`. Output probability = **`0.3937`** (`>= 0.15`, `VERY_HIGH`, actual = `1`). Historical non-attendance streak drove high risk score.
- **False Negative Walkthrough (Test Record):** `booking_lead_days=79`, `appointment_weekday=6`, `appointment_hour=17`, `prior_appointments_count=1`, `prior_no_show_count=0`, `prior_no_show_rate=0.0`, `days_since_last_appointment=682`. Output probability = **`0.1361`** (`< 0.15`, `LOW`, actual = `1`). Despite a long 79-day booking lead time and 682-day gap, having `0` prior missed visits kept the calibrated linear risk score below threshold, demonstrating why unmeasured real-world volatility causes irreducible error.

## 18. Explainability (Permutation Importance)
Calculated via 10 repeats of `permutation_importance` on the validation set (`artifacts/metrics/feature_importance.csv`):
1. `prior_no_show_count`: `0.1046` ($\pm 0.0092$)
2. `prior_cancellations_count`: `0.0158` ($\pm 0.0061$)
3. `prior_appointments_count`: `0.0147` ($\pm 0.0144$)
4. `booking_channel`: `0.0041` ($\pm 0.0031$)
5. `prior_no_show_rate`: `0.0031` ($\pm 0.0058$)

*Note: Global permutation importance measures aggregate predictive signal across the validation cohort, not causal factors for individual patients.*

## 19. Application Architecture
Three-tier modular stack: Offline ML pipeline (`ml/`) $\rightarrow$ Flask REST API (`backend/`) $\rightarrow$ React 18 + Vite UI (`frontend/`). See `docs/architecture.md`.

## 20. MongoDB Design
Database `morrow_hospital` with PyMongo collections (`appointments`, `prediction_logs`, `model_metadata`, `data_quality_reports`), unique `appointment_id` and `prediction_id` indexes, idempotent seeding, and graceful local CSV fallback when offline.

## 21. API Implementation
Blueprints under `/api/v1` returning standardized `{status, data/message}` payloads with strict schema validation, ObjectId/datetime serialization, and single-startup model caching.

## 22. Limitations
- Synthetic dataset does not replicate clinic-specific seasonal peaks or clinical specialty effects.
- Moderate ROC-AUC (`0.6044`) confirms scheduling metadata alone cannot predict acute life events.
- Cost assumptions (`$5` vs `$50`) are illustrative and must be calibrated per hospital budget.

## 23. Responsible Use
MORROW strictly prohibits clinical diagnosis predictions, automated cancellations, or unsupervised SMS outreach. All risk indicators require human administrative review.

## 24. Conclusion
MORROW successfully delivers a full-stack, leakage-free, calibrated, and rigorously tested appointment operations decision-support system adhering to all engineering, statistical, and ethical guidelines.

