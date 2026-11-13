"""
Dashboard and KPI Routes for MORROW.
"""
from flask import Blueprint, jsonify
from backend.services.dashboard_service import get_dashboard_summary, get_dashboard_trends
from backend.utils.serializers import success_response, error_response

dashboard_bp = Blueprint("dashboard_bp", __name__)

@dashboard_bp.route("/dashboard/summary", methods=["GET"])
def summary():
    """Returns top-level KPIs and summary counts."""
    try:
        data = get_dashboard_summary()
        payload, code = success_response(data=data)
        return jsonify(payload), code
    except Exception as e:
        payload, code = error_response(message=f"Failed to load summary: {e}", status_code=500)
        return jsonify(payload), code

@dashboard_bp.route("/dashboard/trends", methods=["GET"])
def trends():
    """Returns chart aggregation trends."""
    try:
        data = get_dashboard_trends()
        payload, code = success_response(data=data)
        return jsonify(payload), code
    except Exception as e:
        payload, code = error_response(message=f"Failed to load trends: {e}", status_code=500)
        return jsonify(payload), code

