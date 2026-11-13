"""
Final Model Evaluation on Held-Out Test Set for MORROW.

Evaluates the saved pipeline on the un-shuffled chronological TEST set
using the operating threshold chosen during validation.

Generates confusion matrix plot and saves test_metrics.json.

Usage:
    python -m ml.training.evaluate
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    classification_report,
)

from ml.config import (
    MODEL_ARTIFACT_PATH,
    METRICS_DIR,
    FIGURES_DIR,
    FALSE_POSITIVE_COST,
    FALSE_NEGATIVE_COST,
)
from ml.features.build_features import build_features
from ml.training.compare_models import get_models, evaluate_model


def evaluate_test_set():
    os.makedirs(METRICS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    print("Loading saved model pipeline...")
    artifact = joblib.load(MODEL_ARTIFACT_PATH)
    pipeline = artifact["pipeline"]
    model_name = artifact.get("model_name", "Classifier")
    threshold = artifact.get("selected_threshold", 0.50)

    print("Loading test data...")
    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, split_info = (
        build_features()
    )

    y_test_proba = pipeline.predict_proba(X_test)[:, 1]

    # Store held-out test prediction array for reproducible metric audit
    test_preds_path = os.path.join(METRICS_DIR, "test_predictions.npz")
    np.savez(test_preds_path, y_true=y_test, y_proba=y_test_proba)
    test_preds = np.load(test_preds_path)
    y_test_arr = test_preds["y_true"]
    y_test_proba_arr = test_preds["y_proba"]

    y_test_pred = (y_test_proba_arr >= threshold).astype(int)

    cm = confusion_matrix(y_test_arr, y_test_pred)
    tn, fp, fn, tp = cm.ravel()

    acc = float(accuracy_score(y_test_arr, y_test_pred))
    prec = float(precision_score(y_test_arr, y_test_pred, zero_division=0))
    rec = float(recall_score(y_test_arr, y_test_pred, zero_division=0))
    f1 = float(f1_score(y_test_arr, y_test_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test_arr, y_test_proba_arr))
    pr_auc = float(average_precision_score(y_test_arr, y_test_proba_arr))
    brier = float(brier_score_loss(y_test_arr, y_test_proba_arr))
    test_prevalence = float(np.mean(y_test_arr))
    ref_brier = float(brier_score_loss(y_test_arr, np.full_like(y_test_proba_arr, test_prevalence)))

    cost = float((fp * FALSE_POSITIVE_COST) + (fn * FALSE_NEGATIVE_COST))
    flagged_count = int(tp + fp)

    report_dict = classification_report(y_test_arr, y_test_pred, output_dict=True, zero_division=0)

    # Evaluate all frozen candidate models on the held-out test set for comparison
    # (No tuning or selection is performed on test results)
    print("Evaluating all frozen baseline & candidate models on held-out test set...")
    frozen_models = get_models()
    test_comparison = {}
    for name, candidate_pipe in frozen_models.items():
        candidate_pipe.fit(X_train, y_train)
        m = evaluate_model(candidate_pipe, X_test, y_test)
        test_comparison[name] = {
            "threshold": 0.50,
            "accuracy": round(m["accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
            "roc_auc": round(m["roc_auc"], 4),
            "pr_auc": round(m["average_precision"], 4),
            "brier_score": round(m["brier_score_loss"], 4),
        }

    test_comparison[f"{model_name} (Calibrated, Selected)"] = {
        "threshold": threshold,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
    }

    test_metrics = {
        "model_name": model_name,
        "model_version": artifact.get("model_version", "1.0.0"),
        "evaluation_dataset": "held-out chronological test set",
        "test_sample_count": len(y_test_arr),
        "test_start_date": split_info["test"]["start_date"],
        "test_end_date": split_info["test"]["end_date"],
        "applied_threshold": threshold,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "reference_brier_score": round(ref_brier, 4),
        "reference_prevalence": round(test_prevalence, 4),
        "flagged_count": flagged_count,
        "flagged_percentage": round(flagged_count / len(y_test_arr) * 100, 2),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "operational_cost": round(cost, 2),
        "classification_report": report_dict,
        "test_comparison": test_comparison,
    }

    out_json = os.path.join(METRICS_DIR, "test_metrics.json")
    with open(out_json, "w") as f:
        json.dump(test_metrics, f, indent=2)
    print(f"Saved test metrics to: {out_json}")

    # Plot Confusion Matrix
    plt.figure(figsize=(7, 6))
    cm_display = np.array([[tn, fp], [fn, tp]])
    sns.heatmap(
        cm_display,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Predicted Attended", "Predicted No-Show"],
        yticklabels=["Actual Attended", "Actual No-Show"],
        cbar=False,
    )
    plt.title(f"Test Confusion Matrix ({model_name}, Threshold={threshold:.2f})", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "confusion_matrix.png"), dpi=150)
    plt.close()
    print("  ✓ confusion_matrix.png")

    print("\n" + "─" * 60)
    print("HELD-OUT TEST SET EVALUATION SUMMARY")
    print("─" * 60)
    print(f"  Model:       {model_name}")
    print(f"  Threshold:   {threshold:.2f}")
    print(f"  Accuracy:    {acc:.4f}")
    print(f"  Precision:   {prec:.4f}")
    print(f"  Recall:      {rec:.4f}")
    print(f"  F1-Score:    {f1:.4f}")
    print(f"  ROC-AUC:     {roc_auc:.4f}")
    print(f"  PR-AUC:      {pr_auc:.4f}")
    print(f"  Brier Score: {brier:.4f}")
    print(f"  TP: {tp} | FP: {fp} | TN: {tn} | FN: {fn}")
    print(f"  Estimated Test Cost: ${cost:.2f}")
    print("─" * 60)

    return test_metrics


def main():
    print("=" * 60)
    print("MORROW — Final Model Test Set Evaluation")
    print("=" * 60)
    evaluate_test_set()


if __name__ == "__main__":
    main()

