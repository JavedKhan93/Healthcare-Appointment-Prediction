"""
Model Comparison for MORROW.

Trains and evaluates multiple classifiers on the validation set.

Usage:
    python -m ml.training.compare_models
"""
import os
import json
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
)

from ml.config import (
    METRICS_DIR,
    RANDOM_SEED,
    LOGISTIC_REGRESSION_PARAMS,
    RANDOM_FOREST_PARAMS,
    HISTGB_PARAMS,
)
from ml.features.build_features import build_features, build_preprocessor


def _make_dense_preprocessor():
    """Build a preprocessor that always outputs dense arrays (for HistGradientBoosting)."""
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline as SkPipeline
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from ml.config import NUMERICAL_FEATURES, CATEGORICAL_FEATURES

    numerical_pipeline = SkPipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = SkPipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", numerical_pipeline, NUMERICAL_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def get_models() -> dict:
    """Return dict of model_name → sklearn Pipeline."""
    from ml.config import NUMERICAL_FEATURES, CATEGORICAL_FEATURES

    models = {
        "DummyClassifier": Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", DummyClassifier(strategy="stratified", random_state=RANDOM_SEED)),
        ]),
        "LogisticRegression": Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", LogisticRegression(**LOGISTIC_REGRESSION_PARAMS)),
        ]),
        "RandomForest": Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", RandomForestClassifier(**RANDOM_FOREST_PARAMS)),
        ]),
        "HistGradientBoosting": Pipeline([
            ("preprocessor", _make_dense_preprocessor()),
            ("classifier", HistGradientBoostingClassifier(**HISTGB_PARAMS)),
        ]),
    }
    return models


def evaluate_model(pipeline: Pipeline, X_val, y_val) -> dict:
    """Evaluate a fitted pipeline on validation data."""
    y_pred = pipeline.predict(X_val)
    y_proba = pipeline.predict_proba(X_val)[:, 1]

    cm = confusion_matrix(y_val, y_pred)

    return {
        "accuracy": float(accuracy_score(y_val, y_pred)),
        "precision": float(precision_score(y_val, y_pred, zero_division=0)),
        "recall": float(recall_score(y_val, y_pred, zero_division=0)),
        "f1": float(f1_score(y_val, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_val, y_proba)),
        "average_precision": float(average_precision_score(y_val, y_proba)),
        "brier_score_loss": float(brier_score_loss(y_val, y_proba)),
        "confusion_matrix": cm.tolist(),
    }


def compare_models() -> tuple:
    """
    Train and compare all models.

    Returns
    -------
    (results_dict, best_model_name)
    """
    print("Loading features...")
    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, split_info = (
        build_features()
    )

    models = get_models()
    results = {}

    for name, pipeline in models.items():
        print(f"\nTraining {name}...")
        pipeline.fit(X_train, y_train)
        metrics = evaluate_model(pipeline, X_val, y_val)
        results[name] = metrics
        print(f"  F1={metrics['f1']:.4f}  ROC-AUC={metrics['roc_auc']:.4f}  "
              f"PR-AUC={metrics['average_precision']:.4f}  Brier={metrics['brier_score_loss']:.4f}")

    # Determine best model by F1 + PR-AUC
    best_name = max(
        results,
        key=lambda n: results[n]["f1"] + results[n]["average_precision"],
    )

    return results, best_name, split_info


def main():
    """Run model comparison and save results."""
    os.makedirs(METRICS_DIR, exist_ok=True)

    print("=" * 60)
    print("MORROW — Model Comparison")
    print("=" * 60)

    results, best_name, split_info = compare_models()

    # Save results
    output = {
        "evaluation_dataset": "validation split",
        "classification_threshold": 0.50,
        "baseline_strategy": "DummyClassifier(strategy='stratified', random_state=42)",
        "split_info": split_info,
        "models": results,
        "best_model": best_name,
        "selection_criterion": "F1 + PR-AUC (average_precision)",
    }
    output_path = os.path.join(METRICS_DIR, "model_comparison.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved comparison to: {output_path}")

    # Print comparison table
    print("\n" + "─" * 90)
    print(f"{'Model':<25} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} "
          f"{'F1':>8} {'ROC-AUC':>9} {'PR-AUC':>9} {'Brier':>8}")
    print("─" * 90)
    for name, m in results.items():
        marker = " ★" if name == best_name else ""
        print(f"{name:<25} {m['accuracy']:>9.4f} {m['precision']:>10.4f} {m['recall']:>8.4f} "
              f"{m['f1']:>8.4f} {m['roc_auc']:>9.4f} {m['average_precision']:>9.4f} "
              f"{m['brier_score_loss']:>8.4f}{marker}")
    print("─" * 90)
    print(f"\n★ Best model: {best_name}")

    return results, best_name


if __name__ == "__main__":
    main()
