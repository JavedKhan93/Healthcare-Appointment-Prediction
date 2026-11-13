"""
Threshold Analysis and Probability Calibration Analysis for MORROW.

Evaluates decision thresholds on the VALIDATION dataset to balance
precision, recall, and illustrative operational costs (false positive = $5,
false negative = $50).

Generates calibration curve, ROC curve, PR curve, and threshold charts.

Usage:
    python -m ml.training.threshold_analysis
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import (
    precision_recall_curve,
    roc_curve,
    auc,
    average_precision_score,
    roc_auc_score,
    brier_score_loss,
    confusion_matrix,
)
from sklearn.calibration import calibration_curve

from ml.config import (
    MODEL_ARTIFACT_PATH,
    METRICS_DIR,
    FIGURES_DIR,
    FALSE_POSITIVE_COST,
    FALSE_NEGATIVE_COST,
    THRESHOLD_CANDIDATES,
)
from ml.features.build_features import build_features


def compute_quantile_calibration(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 5) -> dict:
    """
    Compute quantile-binned calibration statistics safely.
    Handles duplicate quantile bin boundaries and insufficient unique probabilities.
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_proba_arr = np.asarray(y_proba, dtype=float)

    if len(y_proba_arr) == 0:
        return {
            "n_bins_requested": n_bins,
            "n_bins_actual": 0,
            "mean_predicted": [],
            "fraction_positives": [],
            "bin_counts": [],
            "bin_ranges": [],
        }

    unique_probs = np.unique(y_proba_arr)
    if len(unique_probs) < 2:
        p_val = round(float(unique_probs[0]), 4)
        return {
            "n_bins_requested": n_bins,
            "n_bins_actual": 1,
            "mean_predicted": [round(float(np.mean(y_proba_arr)), 4)],
            "fraction_positives": [round(float(np.mean(y_true_arr)), 4)],
            "bin_counts": [int(len(y_proba_arr))],
            "bin_ranges": [f"[{p_val:.4f}, {p_val:.4f}]"],
        }

    # Attempt quantile binning, dropping duplicate edges safely
    try:
        bin_ids, edges = pd.qcut(
            y_proba_arr, q=n_bins, labels=False, duplicates="drop", retbins=True
        )
    except ValueError:
        # Fallback to single bin if edges cannot be separated
        return {
            "n_bins_requested": n_bins,
            "n_bins_actual": 1,
            "mean_predicted": [round(float(np.mean(y_proba_arr)), 4)],
            "fraction_positives": [round(float(np.mean(y_true_arr)), 4)],
            "bin_counts": [int(len(y_proba_arr))],
            "bin_ranges": [f"[{float(y_proba_arr.min()):.4f}, {float(y_proba_arr.max()):.4f}]"],
        }

    mean_predicted = []
    fraction_positives = []
    bin_counts = []
    bin_ranges = []

    for b in range(len(edges) - 1):
        mask = bin_ids == b
        count = int(np.sum(mask))
        if count == 0:
            continue
        mean_predicted.append(round(float(np.mean(y_proba_arr[mask])), 4))
        fraction_positives.append(round(float(np.mean(y_true_arr[mask])), 4))
        bin_counts.append(count)
        bin_ranges.append(f"[{float(edges[b]):.4f}, {float(edges[b + 1]):.4f}]")

    return {
        "n_bins_requested": n_bins,
        "n_bins_actual": len(bin_counts),
        "mean_predicted": mean_predicted,
        "fraction_positives": fraction_positives,
        "bin_counts": bin_counts,
        "bin_ranges": bin_ranges,
    }


def analyze_thresholds():
    os.makedirs(METRICS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    print("Loading model artifact...")
    artifact = joblib.load(MODEL_ARTIFACT_PATH)
    pipeline = artifact["pipeline"]
    model_name = artifact.get("model_name", "Classifier")

    print("Loading validation dataset...")
    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, split_info = (
        build_features()
    )

    y_val_proba = pipeline.predict_proba(X_val)[:, 1]

    # Store validation prediction array for reproducible metric audit
    val_preds_path = os.path.join(METRICS_DIR, "validation_predictions.npz")
    np.savez(val_preds_path, y_true=y_val, y_proba=y_val_proba)
    val_preds = np.load(val_preds_path)
    y_val_arr = val_preds["y_true"]
    y_val_proba_arr = val_preds["y_proba"]

    # Evaluate candidates
    threshold_results = []
    min_cost = float("inf")
    best_thresh = 0.50

    for t in THRESHOLD_CANDIDATES:
        y_pred = (y_val_proba >= t).astype(int)
        tp = int(np.sum((y_val == 1) & (y_pred == 1)))
        fp = int(np.sum((y_val == 0) & (y_pred == 1)))
        tn = int(np.sum((y_val == 0) & (y_pred == 0)))
        fn = int(np.sum((y_val == 1) & (y_pred == 0)))

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float((2 * prec * rec) / (prec + rec)) if (prec + rec) > 0 else 0.0
        cost = float((fp * FALSE_POSITIVE_COST) + (fn * FALSE_NEGATIVE_COST))

        flagged = tp + fp
        res = {
            "threshold": round(t, 2),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "flagged_count": flagged,
            "flagged_percentage": round(flagged / len(y_val) * 100, 2),
            "hypothetical_cost": round(cost, 2),
        }
        threshold_results.append(res)

        if cost < min_cost:
            min_cost = cost
            best_thresh = t

    brier = float(brier_score_loss(y_val_arr, y_val_proba_arr))
    val_prevalence = float(np.mean(y_val_arr))
    ref_brier = float(brier_score_loss(y_val_arr, np.full_like(y_val_proba_arr, val_prevalence)))

    analysis_data = {
        "model_name": model_name,
        "calibration_method": artifact.get("calibration_method", "sigmoid (Platt scaling)"),
        "evaluation_split": "validation",
        "validation_sample_count": len(y_val_arr),
        "selected_threshold": best_thresh,
        "min_validation_cost": min_cost,
        "brier_score": round(brier, 4),
        "reference_brier_score": round(ref_brier, 4),
        "reference_prevalence": round(val_prevalence, 4),
        "cost_assumptions": {
            "false_positive_cost": FALSE_POSITIVE_COST,
            "false_negative_cost": FALSE_NEGATIVE_COST,
        },
        "threshold_evaluations": threshold_results,
        "justification": (
            f"Threshold {best_thresh:.2f} was selected on validation data (n={len(y_val)}) because it minimizes "
            f"the illustrative operational cost (${min_cost:.2f}) assuming False Positive = ${FALSE_POSITIVE_COST:.2f} "
            f"and False Negative = ${FALSE_NEGATIVE_COST:.2f}. These are hypothetical modeling assumptions, not measured "
            f"hospital financial figures. At t={best_thresh:.2f}, {next(r['flagged_count'] for r in threshold_results if r['threshold']==best_thresh)} "
            f"of {len(y_val)} appointments are flagged, generating substantial false-positive review workload."
        ),
    }

    out_json = os.path.join(METRICS_DIR, "threshold_analysis.json")
    with open(out_json, "w") as f:
        json.dump(analysis_data, f, indent=2)
    print(f"Saved threshold analysis to: {out_json}")

    # ── 1. Threshold Performance Plot ─────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(10, 6))
    thresholds = [r["threshold"] for r in threshold_results]
    f1_scores = [r["f1"] for r in threshold_results]
    precisions = [r["precision"] for r in threshold_results]
    recalls = [r["recall"] for r in threshold_results]
    costs = [r["hypothetical_cost"] for r in threshold_results]

    ax1.plot(thresholds, precisions, label="Precision", color="#1F5A57", marker="o", linewidth=2)
    ax1.plot(thresholds, recalls, label="Recall", color="#A85D48", marker="s", linewidth=2)
    ax1.plot(thresholds, f1_scores, label="F1-Score", color="#C19345", marker="^", linewidth=2)
    ax1.axvline(best_thresh, color="#263A3A", linestyle="--", alpha=0.7, label=f"Selected ({best_thresh:.2f})")
    ax1.set_xlabel("Decision Threshold", fontsize=12)
    ax1.set_ylabel("Score", fontsize=12)
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(thresholds, costs, label="Operational Cost ($)", color="#8D9E8F", linestyle=":", linewidth=2)
    ax2.set_ylabel("Hypothetical Cost ($)", fontsize=12, color="#8D9E8F")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right")

    plt.title("Threshold vs. Performance & Operational Cost", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "threshold_analysis.png"), dpi=150)
    plt.close()
    print("  ✓ threshold_analysis.png")

    # ── 2. ROC Curve ──────────────────────────────────────────────────
    fpr, tpr, _ = roc_curve(y_val_arr, y_val_proba_arr)
    roc_auc = float(roc_auc_score(y_val_arr, y_val_proba_arr))

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color="#1F5A57", lw=2, label=f"ROC curve (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="#263A3A", linestyle="--", alpha=0.5, label="Chance")
    plt.xlabel("False Positive Rate", fontsize=12)
    plt.ylabel("True Positive Rate", fontsize=12)
    plt.title(f"Validation ROC Curve — Calibrated {model_name}", fontsize=14)
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "roc_curve.png"), dpi=150)
    plt.close()
    print("  ✓ roc_curve.png")

    # ── 3. Precision-Recall Curve ─────────────────────────────────────
    prec_curve, rec_curve, _ = precision_recall_curve(y_val_arr, y_val_proba_arr)
    pr_auc = float(auc(rec_curve, prec_curve))
    pr_ap = float(average_precision_score(y_val_arr, y_val_proba_arr))

    plt.figure(figsize=(8, 6))
    plt.plot(rec_curve, prec_curve, color="#A85D48", lw=2, label=f"PR curve (AP = {pr_ap:.4f}, AUC = {pr_auc:.4f})")
    plt.xlabel("Recall", fontsize=12)
    plt.ylabel("Precision", fontsize=12)
    plt.title(f"Validation Precision-Recall Curve — Calibrated {model_name}", fontsize=14)
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "precision_recall_curve.png"), dpi=150)
    plt.close()
    print("  ✓ precision_recall_curve.png")

    # ── 4. Calibration Curve ──────────────────────────────────────────
    prob_true, prob_pred = calibration_curve(y_val_arr, y_val_proba_arr, n_bins=10)

    # Match sklearn calibration_curve exact binning (np.searchsorted)
    bin_edges = np.linspace(0.0, 1.0, 10 + 1)
    binids = np.searchsorted(bin_edges[1:-1], y_val_proba_arr)
    bin_counts_all = np.bincount(binids, minlength=10)
    non_empty_bins = np.nonzero(bin_counts_all)[0]
    cal_bin_counts = bin_counts_all[non_empty_bins].tolist()
    cal_bin_ranges = [f"[{bin_edges[i]:.1f}, {bin_edges[i+1]:.1f}]" for i in non_empty_bins]

    plt.figure(figsize=(8, 6))
    plt.plot(prob_pred, prob_true, marker="o", color="#1F5A57", lw=2, label="Calibrated Model")
    plt.plot([0, 1], [0, 1], linestyle="--", color="#263A3A", alpha=0.5, label="Perfect Calibration")
    plt.xlabel("Mean Predicted Probability", fontsize=12)
    plt.ylabel("Fraction of Positives (Empirical)", fontsize=12)
    plt.title(f"Validation Calibration Curve — Calibrated {model_name} (Brier={brier:.4f})", fontsize=14)
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "calibration_curve.png"), dpi=150)
    plt.close()
    print("  ✓ calibration_curve.png")

    # ── 4b. Quantile Calibration Curve (5 bins) ──────────────────────
    q_cal = compute_quantile_calibration(y_val_arr, y_val_proba_arr, n_bins=5)

    plt.figure(figsize=(8, 6))
    plt.plot(
        q_cal["mean_predicted"],
        q_cal["fraction_positives"],
        marker="s",
        color="#A85D48",
        lw=2,
        label=f"Quantile-Binned Model ({q_cal['n_bins_actual']} bins)",
    )
    plt.plot([0, 1], [0, 1], linestyle="--", color="#263A3A", alpha=0.5, label="Perfect Calibration")
    plt.xlabel("Mean Predicted Probability", fontsize=12)
    plt.ylabel("Fraction of Positives (Empirical)", fontsize=12)
    plt.title(f"Validation Quantile Calibration Curve (5 Bins) — Calibrated {model_name} (Brier={brier:.4f})", fontsize=13)
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "calibration_curve_quantile.png"), dpi=150)
    plt.close()
    print("  ✓ calibration_curve_quantile.png")

    # ── 5. Export Structured Curves JSON for Interactive Frontend ─────
    grid = np.linspace(0.0, 1.0, 21)
    roc_tpr_interp = np.interp(grid, fpr, tpr)
    roc_tpr_interp[0] = 0.0
    roc_tpr_interp[-1] = 1.0

    rec_rev = rec_curve[::-1]
    prec_rev = prec_curve[::-1]
    pr_prec_interp = np.interp(grid, rec_rev, prec_rev)

    curves_data = {
        "model_name": model_name,
        "calibration_method": artifact.get("calibration_method", "sigmoid (Platt scaling)"),
        "evaluation_split": "validation",
        "sample_count": int(len(y_val_arr)),
        "roc_curve": {
            "auc": round(roc_auc, 4),
            "fpr": [round(float(x), 2) for x in grid],
            "tpr": [round(float(y), 4) for y in roc_tpr_interp],
        },
        "pr_curve": {
            "auc": round(pr_auc, 4),
            "average_precision": round(pr_ap, 4),
            "baseline": round(val_prevalence, 4),
            "recall": [round(float(x), 2) for x in grid],
            "precision": [round(float(y), 4) for y in pr_prec_interp],
        },
        "calibration_curve": {
            "brier_score": round(brier, 4),
            "reference_brier_score": round(ref_brier, 4),
            "reference_prevalence": round(val_prevalence, 4),
            "mean_predicted": [round(float(x), 4) for x in prob_pred],
            "fraction_positives": [round(float(y), 4) for y in prob_true],
            "bin_counts": cal_bin_counts,
            "bin_ranges": cal_bin_ranges,
        },
        "quantile_calibration_curve": {
            "brier_score": round(brier, 4),
            "reference_brier_score": round(ref_brier, 4),
            "reference_prevalence": round(val_prevalence, 4),
            **q_cal,
        },
    }
    curves_json = os.path.join(METRICS_DIR, "model_curves.json")
    with open(curves_json, "w") as f:
        json.dump(curves_data, f, indent=2)
    print(f"Saved interactive model curves to: {curves_json}")

    # Update artifact only if selected threshold changed
    if artifact.get("selected_threshold") != best_thresh:
        artifact["selected_threshold"] = best_thresh
        joblib.dump(artifact, MODEL_ARTIFACT_PATH)
        print(f"Updated artifact with validated threshold {best_thresh:.2f}")
    else:
        print(f"Verified saved artifact threshold remains {best_thresh:.2f} (model untouched)")


def main():
    print("=" * 60)
    print("MORROW — Threshold and Calibration Analysis")
    print("=" * 60)
    analyze_thresholds()


if __name__ == "__main__":
    main()

