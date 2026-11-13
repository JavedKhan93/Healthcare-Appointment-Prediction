# Technical Interview Preparation — MORROW

## Business Problem & Scope
1. **Why predict appointment no-shows at booking time?**
   - Unfilled slots waste clinician time and delay access for waitlisted patients. Booking-time risk estimation allows administrative staff to prioritize supportive confirmation calls.
2. **Why exclude clinical diagnoses and automated cancellations?**
   - Predicting clinical urgency or auto-cancelling appointments poses patient-safety and ethical risks. MORROW is strictly an operations decision-support tool requiring human oversight.

## Dataset & Data Cleaning
3. **Why generate a synthetic dataset instead of scraping public hospital datasets?**
   - Avoids privacy/PHI compliance risks, ensures full control over feature availability at booking time, and lets us demonstrate a realistic data-cleaning pipeline on known controlled anomalies.
4. **How did you prevent patient history leakage during synthetic simulation?**
   - Patient trajectories were walked forward chronologically; `prior_no_show_count` and `prior_appointments_count` counted only earlier appointments. The internal `patient_key` was dropped before exporting.
5. **Why did you mask negative counts to `NaN` rather than imputing medians during cleaning?**
   - Computing global medians before the chronological train/val/test split leaks future distribution statistics into training. Keeping `NaN` values allows `SimpleImputer` inside the Scikit-learn `Pipeline` to fit strictly on training rows.
6. **How did you distinguish invalid data from valid outliers?**
   - Impossible relationships (`booking_created_at >= appointment_datetime`) and negative counts (`-1`) are physically impossible and were removed/masked. Valid extreme observations (`booking_lead_days > 120`, `days_since_last > 365`) were retained and logged.

## Machine Learning & Evaluation
7. **Why use a chronological split instead of a random `train_test_split`?**
   - Random splitting leaks future temporal trends into training and fails to test how the model generalizes to future appointment periods.
8. **How is class imbalance handled?**
   - The target is ~17.1% positive (`no_show=1`). We used `class_weight="balanced"` on Logistic Regression, `balanced_subsample` on Random Forest, evaluated PR-AUC alongside ROC-AUC, and calibrated threshold selection via asymmetric operational cost.
9. **Why didn't you select HistGradientBoosting if its accuracy was highest (81.03%)?**
   - Accuracy is misleading on imbalanced data: a model predicting almost all zeros gets ~82% accuracy with only `2.20%` recall (`F1 = 0.0407`). Logistic Regression achieved the highest F1 (`0.3032`), ROC-AUC (`0.5804`), and PR-AUC (`0.2384`).
10. **Why is Logistic Regression's ROC-AUC ~0.60 instead of 0.95?**
    - Real attendance outcomes involve unmeasured stochastic factors (illness, transit, work). Because our data generation adds realistic overlapping noise rather than deterministic shortcuts, `0.60` reflects honest predictive difficulty.
11. **What is probability calibration and how did you apply it without leakage?**
    - Calibration aligns predicted probabilities with empirical outcome frequencies. We used `CalibratedClassifierCV(method="sigmoid")` (Platt scaling) passing explicit chronological split indices (`80%` fit / `20%` calibration within training data), lowering test Brier score to `0.1498`.
12. **Why is the operating threshold `0.15` instead of `0.50`?**
    - After calibration onto a ~17% base rate, probabilities center around `0.17`. At `0.50`, recall collapses (`0.37%`). Given a `$50` missed-slot cost vs. `$5` reminder cost, `0.15` minimizes total validation cost (`$8,195`), improving test recall to `64.03%`.
13. **What is the difference between global permutation importance and local causal effects?**
    - Permutation importance (`prior_no_show_count = 0.1046`) shows how much shuffling a column degrades aggregate validation ROC-AUC. It reflects model reliance/correlation across the population, not what *causes* an individual patient to miss a visit.

## Backend, Database & Frontend Engineering
14. **Why load the Joblib artifact once at Flask startup?**
    - Deserializing the Scikit-learn pipeline per HTTP request adds latency and disk I/O overhead. Caching it at app startup enables millisecond inference.
15. **How does the MongoDB schema prevent duplicate seeding?**
    - `seed_database()` checks `appointments.count_documents({}) > 0` before inserting and enforces a unique index on `appointment_id`.
16. **How are MongoDB `ObjectId` and `datetime` objects handled in Flask JSON responses?**
    - `backend/utils/serializers.py` recursively converts `ObjectId` to strings (`id`) and `datetime` objects to ISO-8601 strings before calling `jsonify`.
17. **What happens if MongoDB is offline during evaluation?**
    - `backend/database.py` catches connection errors with a 2-second timeout, flags `mongodb.connected = false` on `/api/v1/health`, and automatically serves cleaned CSV data and in-memory prediction logging without crashing.
18. **How does the React frontend validate inputs and communicate with Flask?**
    - `PredictionDesk.jsx` validates domain ranges and cross-field constraints (`prior_no_show_count <= prior_appointments_count`), then dispatches native `fetch()` calls through `src/api/api.js` proxied by Vite (`/api/v1` $\rightarrow$ `http://127.0.0.1:5000`).

