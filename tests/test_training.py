import os
import json
import joblib
import numpy as np
from ml.config import MODEL_ARTIFACT_PATH, METRICS_DIR
from ml.training.threshold_analysis import compute_quantile_calibration

def test_model_artifact_exists_and_complete():
    assert os.path.exists(MODEL_ARTIFACT_PATH)
    artifact = joblib.load(MODEL_ARTIFACT_PATH)
    required_keys = [
        "pipeline",
        "model_name",
        "model_version",
        "selected_threshold",
        "feature_schema",
        "calibration_method",
        "random_seed",
    ]
    for key in required_keys:
        assert key in artifact, f"Missing key '{key}' in saved artifact"

    assert 0.0 < artifact["selected_threshold"] < 1.0

def test_evaluation_metrics_artifacts_exist():
    expected_files = [
        "data_quality_report.json",
        "model_comparison.json",
        "model_metadata.json",
        "threshold_analysis.json",
        "test_metrics.json",
        "feature_importance.csv",
    ]
    for fname in expected_files:
        fpath = os.path.join(METRICS_DIR, fname)
        assert os.path.exists(fpath), f"Missing metric artifact: {fpath}"

    with open(os.path.join(METRICS_DIR, "test_metrics.json"), "r") as f:
        test_m = json.load(f)
    assert 0.0 <= test_m["roc_auc"] <= 1.0
    assert 0.0 <= test_m["brier_score"] <= 1.0


def test_quantile_calibration_edge_cases_and_validation_consistency():
    # 1. Identical probabilities (insufficient unique values)
    y_true = np.array([0, 1, 0, 0, 1])
    y_const = np.full(5, 0.2)
    res_const = compute_quantile_calibration(y_true, y_const, n_bins=5)
    assert res_const["n_bins_actual"] == 1
    assert sum(res_const["bin_counts"]) == 5

    # 2. Duplicate quantile bin edges (many repeated values)
    y_rep = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.3, 0.4, 0.5])
    y_lbl = np.array([0, 0, 1, 0, 0, 0, 0, 1, 0, 1])
    res_dup = compute_quantile_calibration(y_lbl, y_rep, n_bins=5)
    assert 1 <= res_dup["n_bins_actual"] <= 5
    assert sum(res_dup["bin_counts"]) == len(y_lbl)

    # 3. Consistency between saved validation prediction array and model_curves.json
    val_preds = np.load(os.path.join(METRICS_DIR, "validation_predictions.npz"))
    with open(os.path.join(METRICS_DIR, "model_curves.json"), "r") as f:
        curves = json.load(f)

    q_cal = curves["quantile_calibration_curve"]
    assert q_cal["n_bins_actual"] == 5
    assert sum(q_cal["bin_counts"]) == len(val_preds["y_true"])
    assert curves["calibration_curve"]["brier_score"] == q_cal["brier_score"]
    assert sum(curves["calibration_curve"]["bin_counts"]) == len(val_preds["y_true"])


