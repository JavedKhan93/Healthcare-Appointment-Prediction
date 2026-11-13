"""
Model Service for MORROW.

Manages loading, caching, and serving model artifacts, metrics, and metadata.
Loads the model ONCE on startup.
"""
import os
import json
import pandas as pd
from backend.config import Config
from ml.inference.predict import load_model

_LOADED_ARTIFACT = None


def init_model():
    """Load model artifact on startup and cache it."""
    global _LOADED_ARTIFACT
    try:
        _LOADED_ARTIFACT = load_model(Config.MODEL_PATH)
        print(f"✓ ML Model artifact loaded successfully: {_LOADED_ARTIFACT.get('model_name')} (v{_LOADED_ARTIFACT.get('model_version')})")
    except Exception as e:
        print(f"! Warning: Failed to load ML model artifact: {e}")
        _LOADED_ARTIFACT = None
    return _LOADED_ARTIFACT


def get_model_artifact():
    """Return the cached model artifact or load if needed."""
    global _LOADED_ARTIFACT
    if _LOADED_ARTIFACT is None:
        _LOADED_ARTIFACT = init_model()
    return _LOADED_ARTIFACT


def get_model_metrics():
    """Retrieve model comparison, test metrics, and threshold analysis."""
    metrics = {}
    
    # Model comparison
    comp_file = os.path.join(Config.METRICS_DIR, "model_comparison.json")
    if os.path.exists(comp_file):
        with open(comp_file, "r") as f:
            metrics["comparison"] = json.load(f)
            
    # Test metrics
    test_file = os.path.join(Config.METRICS_DIR, "test_metrics.json")
    if os.path.exists(test_file):
        with open(test_file, "r") as f:
            metrics["test_metrics"] = json.load(f)
            
    # Threshold analysis
    thresh_file = os.path.join(Config.METRICS_DIR, "threshold_analysis.json")
    if os.path.exists(thresh_file):
        with open(thresh_file, "r") as f:
            metrics["threshold_analysis"] = json.load(f)

    # Interactive curve points (ROC, PR, Calibration)
    curves_file = os.path.join(Config.METRICS_DIR, "model_curves.json")
    if os.path.exists(curves_file):
        with open(curves_file, "r") as f:
            metrics["curves"] = json.load(f)

    return metrics


def get_feature_importance():
    """Retrieve global permutation feature importance table."""
    feat_file = os.path.join(Config.METRICS_DIR, "feature_importance.csv")
    if os.path.exists(feat_file):
        df = pd.read_csv(feat_file)
        return df.to_dict(orient="records")
    return []


def get_model_metadata():
    """Retrieve model metadata."""
    artifact = get_model_artifact()
    meta_file = os.path.join(Config.METRICS_DIR, "model_metadata.json")
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            data = json.load(f)
            return data
    if artifact:
        return {
            "model_name": artifact.get("model_name"),
            "model_version": artifact.get("model_version"),
            "selected_threshold": artifact.get("selected_threshold"),
            "feature_schema": artifact.get("feature_schema"),
            "training_timestamp": artifact.get("training_timestamp"),
        }
    return {}

