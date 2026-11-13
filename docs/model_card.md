# Model Card — MORROW No-Show Predictor

## 1. Model Details
- **Model Name:** MORROW No-Show Predictor (`LogisticRegression` with Scikit-learn Preprocessing & Platt Calibration)
- **Version:** `1.0.0`
- **Task:** Binary Classification + Calibrated Probability Estimation (`0 = Attended`, `1 = No-Show`)
- **Primary Artifact:** `artifacts/models/no_show_pipeline.joblib`
- **Training Seed:** `42`

---

## 2. Intended Use & Scope
- **Intended Users:** Hospital administrative and scheduling operations personnel.
- **Intended Use:** Estimate appointment no-show probability at booking time to inform human review or optional courtesy reminder prioritization.
- **Out-of-Scope Uses:**
  - Clinical diagnosis, triage, disease severity estimation, or treatment planning.
  - Automated appointment cancellation, slot overbooking without oversight, or punitive denial of care.

---

## 3. Training & Evaluation Data
- **Source:** Synthetic hospital appointment dataset generated via `ml/data/generate_synthetic_data.py` (`9,950` cleaned rows).
- **Split Strategy:** Strict chronological ordering by `booking_created_at`:
  - **Training Set (70%):** `6,965` records (`2022-10-04` to `2024-05-11`, no-show rate `16.50%`)
    - Initial 80% (`5,572`) used to fit base `LogisticRegression` (`C=1.0`, `class_weight="balanced"`)
    - Final 20% (`1,393`) reserved chronologically for `CalibratedClassifierCV(method="sigmoid")`
  - **Validation Set (15%):** `1,492` records (`2024-05-11` to `2024-08-29`, no-show rate `18.30%`) — used for model comparison & cost thresholding.
  - **Held-Out Test Set (15%):** `1,493` records (`2024-08-29` to `2024-12-29`, no-show rate `18.62%`) — evaluated once.

---

## 4. Quantitative Performance

### Candidate Model Comparison (Validation Set)
| Model | F1-Score | ROC-AUC | PR-AUC | Brier Score |
| :--- | :---: | :---: | :---: | :---: |
| DummyClassifier (Stratified) | 0.1808 | 0.5018 | 0.1835 | 0.2916 |
| **LogisticRegression (Selected)** | **0.3032** | **0.5804** | **0.2384** | 0.2369 |
| RandomForest | 0.2226 | 0.5570 | 0.2167 | 0.1982 |
| HistGradientBoosting | 0.0407 | 0.5474 | 0.2199 | 0.1563 |

### Held-Out Test Set Performance (Threshold = `0.15`)
- **ROC-AUC:** `0.6044`
- **PR-AUC (Average Precision):** `0.2530`
- **Brier Score:** `0.1498` (vs. prevalence-only reference Brier `0.1520`)
- **Recall:** `0.6403` (`178` / `278` no-shows flagged; `776` total flagged = `51.98%`)
- **Precision:** `0.2294`
- **F1-Score:** `0.3378`
- **Accuracy:** `0.5325`
- **Confusion Matrix:** `TN=617`, `FP=598`, `FN=100`, `TP=178` (with `598` false-positive alerts requiring operational review)

---

## 5. Threshold & Calibration Rationale
After Platt scaling (`sigmoid`) maps probabilities to the empirical ~17% base rate, predicted probabilities cluster between `0.04` and `0.51`. Using an illustrative cost matrix (**False Positive = \$5.00** reminder review cost vs. **False Negative = \$50.00** lost clinical slot), evaluating candidate thresholds `[0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70]` on the validation set showed that **`0.15`** minimizes total operational cost (`$8,195.00` on validation; `$7,990.00` on test vs. `$13,410.00` at threshold `0.30`).

---

## 6. Ethical Considerations & Limitations
- Moderate discrimination (`ROC-AUC = 0.6044`) accurately reflects intrinsic real-world unpredictability and overlapping synthetic classes.
- Model outputs are probabilistic estimates requiring human operational judgment.

