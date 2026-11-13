"""
Health and Status Routes for MORROW.
"""
from flask import Blueprint, jsonify
from backend.database import ping_mongodb, Config
from backend.services.model_service import get_model_artifact
from backend.utils.serializers import success_response

health_bp = Blueprint("health_bp", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Returns system operational health: backend, live MongoDB ping, and ML artifact status.
    """
    artifact = get_model_artifact()
    ping_info = ping_mongodb()
    mongo_ok = ping_info.get("connected", False)

    data = {
        "service": "MORROW Backend API",
        "status": "operational",
        "mongodb": {
            "connected": mongo_ok,
            "database": Config.MONGODB_DATABASE,
            "mode": "mongodb" if mongo_ok else "offline_fallback",
            "collections": ping_info.get("collections", []),
            "appointments_count": ping_info.get("appointments_count"),
            "prediction_logs_count": ping_info.get("prediction_logs_count"),
            "error": ping_info.get("error") if not mongo_ok else None,
        },
        "model_artifact": {
            "loaded": artifact is not None,
            "model_name": artifact.get("model_name") if artifact else None,
            "model_version": artifact.get("model_version") if artifact else None,
            "selected_threshold": artifact.get("selected_threshold") if artifact else None,
        },
    }

    payload, code = success_response(data=data, message="System is operational")
    return jsonify(payload), code

