# System Architecture — MORROW

## 1. High-Level Data & Inference Architecture

```
+-----------------------------------------------------------------------------+
|                        OFFLINE REPRODUCIBLE ML PIPELINE                     |
|                                                                             |
|  [generate_synthetic_data.py] ---> data/raw/synthetic_appointments_raw.csv  |
|             |                                                               |
|             v                                                               |
|     [clean_dataset.py] ----------> data/processed/synthetic_..._cleaned.csv |
|             |                      artifacts/metrics/data_quality_report    |
|             v                                                               |
|     [build_features.py] ---------> Chronological Split (70 / 15 / 15)       |
|             |                      ColumnTransformer (Fit on Train ONLY)    |
|             v                                                               |
|  [compare_models.py] -> [train.py] -> [threshold_analysis.py] -> [evaluate] |
|                                        |                                    |
|                                        v                                    |
|                       artifacts/models/no_show_pipeline.joblib              |
|                       artifacts/metrics/*.json, *.csv & artifacts/figures/  |
+-----------------------------------------------------------------------------+
                                         |
                                         | Loaded ONCE at Backend Startup
                                         v
+-----------------------------------------------------------------------------+
|                           FLASK APPLICATION SERVER                          |
|                              (backend/run.py)                               |
|                                                                             |
|  Blueprints (/api/v1):                                                      |
|   ├── health_routes.py         (System & artifact verification)             |
|   ├── dashboard_routes.py      (KPI & trend aggregations)                   |
|   ├── appointment_routes.py    (Paginated search, sort & filter)            |
|   ├── prediction_routes.py     (Input validation -> ML Inference -> Log)    |
|   ├── model_routes.py          (Comparison, threshold, test metrics, FI)    |
|   └── data_quality_routes.py   (Cleaning & missing-value audit)             |
|                                                                             |
|  Data Layer (backend/database.py):                                          |
|   ├── Primary: MongoDB (`morrow_hospital` via PyMongo)                      |
|   │     Collections: appointments, prediction_logs,                         |
|   │                  model_metadata, data_quality_reports                   |
|   └── Fallback: In-memory & CSV cache if MongoDB daemon is unreachable      |
+-----------------------------------------------------------------------------+
                                         ^
                                         | HTTP JSON (Fetch API / Vite Proxy)
                                         v
+-----------------------------------------------------------------------------+
|                      REACT 18 + VITE FRONTEND CLIENT                        |
|                        (frontend/src/api/api.js)                            |
|                                                                             |
|   Pages (Clinical Archive Ledger Design System):                            |
|    1. Dashboard (/)                 4. Model Evidence (/model-evidence)     |
|    2. Appointment Register          5. Data Quality (/data-quality)         |
|    3. Prediction Desk (/predict)    6. Responsible Use (/responsible-use)   |
+-----------------------------------------------------------------------------+
```

---

## 2. Prediction Request Lifecycle

1. **Client Form Submission (`PredictionDesk.jsx`)**:
   - Operations staff enters the 10 booking-time features (lead days, weekday, hours, channel, prior appointment metrics).
   - Client-side validation checks bounds and cross-field constraints (`prior_no_show_count <= prior_appointments_count`).
2. **API Transport (`api.js`)**:
   - Dispatches `POST /api/v1/predictions` with JSON payload via Fetch API.
3. **Server Validation (`backend/utils/validation.py`)**:
   - Rejects prohibited target/future leakage keys (`no_show`, `actual_attendance`, etc.).
   - Enforces types and domain bounds defined in `ml/config.py`.
4. **Model Service (`backend/services/prediction_service.py` -> `ml/inference/predict.py`)**:
   - Invokes the cached `no_show_pipeline.joblib` loaded at Flask startup.
   - Applies the training-fitted `ColumnTransformer` (median imputation + standard scaling + one-hot encoding).
   - Computes calibrated probability (`predict_proba`) from the Platt-scaled Logistic Regression classifier.
   - Applies the validated decision threshold (`0.15`) to classify `0 (Attended)` or `1 (No-Show)` and assigns operational risk tier (`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`).
5. **Audit Persistence (`backend/database.py`)**:
   - Writes structured prediction log (input features, probability, class, threshold, model version, timestamp) to `prediction_logs` in MongoDB (or fallback store).
6. **UI Rendering**:
   - Displays calibrated probability meter, threshold line, risk tier badge, notable input characteristics, human-review disclaimer, and refreshes audit log table.

---

## 3. MongoDB Schema & Indexes (`morrow_hospital`)

- **`appointments`**: Cleaned synthetic historical appointments (`9,950` rows).
  - Indexes: `appointment_id` (Unique Ascending), `booking_created_at` (Asc), `appointment_datetime` (Asc), `booking_channel` (Asc), `no_show` (Asc).
- **`prediction_logs`**: Live inference requests logged from Prediction Desk / API.
  - Indexes: `prediction_id` (Unique Ascending), `created_at` (Descending).
- **`model_metadata`**: Active model details, training timestamp, threshold, cost assumptions, and feature schema.
- **`data_quality_reports`**: Before/after cleaning telemetry and outlier summary.

