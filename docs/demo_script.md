# 3–5 Minute Demonstration Script — MORROW

**Target Duration:** ~4 minutes  
**Setup Before Recording:** Ensure Flask backend (`.\scripts\start_backend.ps1`) and React frontend (`.\scripts\start_frontend.ps1`) are running, with the browser open to `http://localhost:5173`.

---

## [0:00 – 0:45] 1. Project Overview & Design Philosophy
- **Visual:** Start on **Operations Overview (`/`)**.
- **Narration:**
  - *"Hello, this is MORROW — Appointment Operations & No-Show Intelligence, built for the ALGIONS AI LABS internship assessment."*
  - *"Hospitals lose clinical capacity when patients miss appointments without advance warning. MORROW provides operations staff with a calibrated probability estimate at booking time so they can decide if a courteous reminder call is warranted—strictly without clinical predictions or automated cancellations."*
  - *"Notice the Clinical Archive Ledger UI: warm paper `#F3F0E6` background, deep teal `#1F5A57` navigation, Times New Roman editorial typography, and live Chart.js visualizations populated from the Flask API."*

## [0:45 – 1:35] 2. Dataset, Data Quality & EDA
- **Visual:** Navigate to **Data Quality (`/data-quality`)** and **Appointment Register (`/appointments`)**.
- **Narration:**
  - *"Every record in MORROW comes from our reproducible synthetic simulation (`random_seed=42`). We deliberately injected controlled anomalies into 10,005 raw rows—49 duplicates, 5 impossible timestamps, 10 negative counts, and 48 missing values."*
  - *"The cleaning pipeline removes duplicates and impossible timestamps to produce 9,950 valid records, while preserving imputable NaNs so Scikit-learn fits imputers strictly inside training folds."*
  - *"In the Appointment Register, staff can search, filter by channel or outcome, sort, and inspect any individual appointment's booking-time metadata."*

## [1:35 – 2:30] 3. Model Comparison, Calibration & Thresholding
- **Visual:** Navigate to **Model Evidence (`/model-evidence`)**.
- **Narration:**
  - *"We split the data chronologically 70/15/15 by `booking_created_at` to guarantee zero future leakage."*
  - *"On the validation set, we compared DummyClassifier, LogisticRegression, RandomForest, and HistGradientBoosting. Logistic Regression led on validation F1 (`0.3032`), ROC-AUC (`0.5804`), and PR-AUC (`0.2384`)."*
  - *"We applied chronological Platt scaling (`CalibratedClassifierCV`) on the final 20% of training data, lowering test Brier score to `0.1498`. Then, using an asymmetric cost ratio—$5 for a reminder review vs $50 for a missed slot—validation cost analysis selected threshold `0.15`, achieving `64.03%` recall and cutting estimated operational cost by 40%."*

## [2:30 – 3:45] 4. Live Prediction & Audit History
- **Visual:** Navigate to **Prediction Desk (`/predict`)**.
- **Narration:**
  - *"Now let's submit a live prediction through the Prediction Desk, which calls our Flask API and loads the serialized `no_show_pipeline.joblib` artifact."*
  - Click **"Low-Risk Sample"**, then click **"Predict No-Show Risk"**. Point out ~7.0% probability (`Attended`, `LOW` risk).
  - Click **"Elevated-Risk Sample"**, then click **"Predict No-Show Risk"**.
  - *"For this profile—72-day lead time, 3 prior no-shows out of 5 appointments—the pipeline returns a calibrated probability well above the `0.15` threshold, classifying it as `No-Show` with `VERY_HIGH` operational risk and flagging notable factors."*
  - Scroll down to show the newly logged record in the **Prediction Audit Log**.

## [3:45 – 4:15] 5. Limitations & Responsible Use
- **Visual:** Navigate to **Responsible Use (`/responsible-use`)**.
- **Narration:**
  - *"Finally, MORROW communicates uncertainty honestly. Because real-world attendance involves unforeseen emergencies and our data is synthetic, ROC-AUC is `0.6044`. Every output displays a mandatory experimental disclaimer and requires human review before any administrative outreach. Thank you."*

