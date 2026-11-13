"""
Training and Probability Calibration Pipeline for MORROW.

Trains the selected model on training data with chronological calibration
(Platt scaling / sigmoid via CalibratedClassifierCV on a reserved later slice of training data).
Computes permutation feature importance and saves the complete model artifact.

Usage:
    python -m ml.training.train
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

from ml.config import (
    MODEL_ARTIFACT_PATH,
    METRICS_DIR,
    RANDOM_SEED,
    MODEL_NAME,
    MODEL_VERSION,
    MODEL_FEATURES,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    LOGISTIC_REGRESSION_PARAMS,
    RANDOM_FOREST_PARAMS,
    HISTGB_PARAMS,
    FALSE_POSITIVE_COST,
    FALSE_NEGATIVE_COST,
    THRESHOLD_CANDIDATES,
)
from ml.features.build_features import build_features, build_preprocessor


def get_base_classifier(model_name: str):
    """Instantiate base classifier based on selected name."""
    if model_name == "LogisticRegression":
        return LogisticRegression(**LOGISTIC_REGRESSION_PARAMS)
    elif model_name == "RandomForest":
        return RandomForestClassifier(**RANDOM_FOREST_PARAMS)
    elif model_name == "HistGradientBoosting":
        return HistGradientBoostingClassifier(**HISTGB_PARAMS)
    else:
        # Default to Logistic Regression
        return LogisticRegression(**LOGISTIC_REGRESSION_PARAMS)


def train_and_calibrate(model_name: str = None) -> tuple:
    """
    Train pipeline with chronological calibration.
    
    1. Load data and chronological splits.
    2. Split training data: first 80% for initial fitting, last 20% for calibration.
    3. Fit ColumnTransformer on training features.
    4. Fit CalibratedClassifierCV with custom chronological split index.
    5. Evaluate on validation set to determine optimal threshold.
    """
    # Check if compare_models selected a best model
    comp_path = os.path.join(METRICS_DIR, "model_comparison.json")
    if model_name is None:
        if os.path.exists(comp_path):
            with open(comp_path, "r") as f:
                comp = json.load(f)
                model_name = comp.get("best_model", "LogisticRegression")
        else:
            model_name = "LogisticRegression"

    print(f"Selected Model Architecture: {model_name}")

    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, split_info = (
        build_features()
    )

    n_train = len(X_train)
    fit_end = int(n_train * 0.80)
    train_indices = np.arange(0, fit_end)
    cal_indices = np.arange(fit_end, n_train)

    chronological_splits = [(train_indices, cal_indices)]
    print(f"Chronological calibration split: {len(train_indices)} fit samples, {len(cal_indices)} calibration samples")

    base_clf = get_base_classifier(model_name)
    calibrated_clf = CalibratedClassifierCV(
        estimator=base_clf,
        method="sigmoid",
        cv=chronological_splits,
    )

    full_pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", calibrated_clf),
    ])

    print("Fitting preprocessor and calibrated classifier...")
    full_pipeline.fit(X_train, y_train)
    print("Fitting complete.")

    # Determine optimal threshold on validation set
    y_val_proba = full_pipeline.predict_proba(X_val)[:, 1]
    best_thresh = 0.50
    min_cost = float("inf")
    best_f1 = 0.0

    threshold_results = []
    for t in THRESHOLD_CANDIDATES:
        y_pred = (y_val_proba >= t).astype(int)
        tp = int(np.sum((y_val == 1) & (y_pred == 1)))
        fp = int(np.sum((y_val == 0) & (y_pred == 1)))
        tn = int(np.sum((y_val == 0) & (y_pred == 0)))
        fn = int(np.sum((y_val == 1) & (y_pred == 0)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        cost = (fp * FALSE_POSITIVE_COST) + (fn * FALSE_NEGATIVE_COST)

        threshold_results.append({
            "threshold": round(t, 2),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "cost": round(cost, 2),
        })

        if cost < min_cost:
            min_cost = cost
            best_thresh = t
            best_f1 = f1

    print(f"\nOptimal operational threshold chosen on validation set: {best_thresh:.2f} (Total cost: ${min_cost:.2f}, F1: {best_f1:.4f})")

    # Compute Permutation Feature Importance
    print("Calculating permutation feature importance on validation set...")
    perm_importance = permutation_importance(
        full_pipeline, X_val, y_val,
        n_repeats=10,
        random_state=RANDOM_SEED,
        scoring="roc_auc",
        n_jobs=-1,
    )

    feature_importance_df = pd.DataFrame({
        "feature": MODEL_FEATURES,
        "importance_mean": perm_importance.importances_mean,
        "importance_std": perm_importance.importances_std,
    }).sort_values(by="importance_mean", ascending=False)

    feat_imp_path = os.path.join(METRICS_DIR, "feature_importance.csv")
    feature_importance_df.to_csv(feat_imp_path, index=False)
    print(f"Saved feature importance to: {feat_imp_path}")

    # Build Complete Artifact
    artifact = {
        "pipeline": full_pipeline,
        "model_name": model_name,
        "model_version": MODEL_VERSION,
        "selected_threshold": best_thresh,
        "calibration_method": "sigmoid (Platt scaling)",
        "training_timestamp": datetime.now().isoformat(),
        "random_seed": RANDOM_SEED,
        "feature_schema": MODEL_FEATURES,
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "training_records": len(X_train),
        "validation_records": len(X_val),
        "test_records": len(X_test),
        "training_config": {
            "false_positive_cost": FALSE_POSITIVE_COST,
            "false_negative_cost": FALSE_NEGATIVE_COST,
            "calibration_split": "80/20 chronological train",
        },
    }

    os.makedirs(os.path.dirname(MODEL_ARTIFACT_PATH), exist_ok=True)
    joblib.dump(artifact, MODEL_ARTIFACT_PATH)
    print(f"Saved model artifact to: {MODEL_ARTIFACT_PATH}")

    # Save model metadata JSON
    metadata = {
        "model_name": model_name,
        "model_version": MODEL_VERSION,
        "selected_threshold": best_thresh,
        "calibration_method": "sigmoid (Platt scaling)",
        "training_timestamp": artifact["training_timestamp"],
        "random_seed": RANDOM_SEED,
        "feature_schema": MODEL_FEATURES,
        "validation_records": len(X_val),
        "test_records": len(X_test),
        "cost_assumptions": {
            "false_positive_cost": FALSE_POSITIVE_COST,
            "false_negative_cost": FALSE_NEGATIVE_COST,
        },
        "optimal_validation_cost": min_cost,
    }
    meta_path = os.path.join(METRICS_DIR, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved model metadata to: {meta_path}")

    return artifact, threshold_results


def main():
    print("=" * 60)
    print("MORROW — Model Training and Calibration")
    print("=" * 60)
    train_and_calibrate()


if __name__ == "__main__":
    main()
