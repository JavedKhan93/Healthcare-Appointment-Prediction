"""
Model Evaluation and Explainability Routes for MORROW.
"""
from flask import Blueprint, jsonify
from backend.services.model_service import (
    get_model_metrics,
    get_feature_importance,
    get_model_metadata,
)
from backend.utils.serializers import success_response, error_response

model_bp = Blueprint("model_bp", __name__)


@model_bp.route("/model/metrics", methods=["GET"])
def metrics():
    """Returns genuine model comparison and held-out test evaluation metrics."""
    try:
        data = get_model_metrics()
        payload, code = success_response(data=data)
        return jsonify(payload), code
    except Exception as e:
        payload, code = error_response(message=f"Failed to fetch model metrics: {e}", status_code=500)
        return jsonify(payload), code


@model_bp.route("/model/feature-importance", methods=["GET"])
def feature_importance():
    """Returns global permutation feature importance table."""
    try:
        data = get_feature_importance()
        payload, code = success_response(data=data)
        return jsonify(payload), code
    except Exception as e:
        payload, code = error_response(message=f"Failed to fetch feature importance: {e}", status_code=500)
        return jsonify(payload), code


@model_bp.route("/model/metadata", methods=["GET"])
def metadata():
    """Returns model metadata, version, schema, and threshold configuration."""
    try:
        data = get_model_metadata()
        payload, code = success_response(data=data)
        return jsonify(payload), code
    except Exception as e:
        payload, code = error_response(message=f"Failed to fetch model metadata: {e}", status_code=500)
        return jsonify(payload), code

