"""
Data Quality and Cleaning Report Routes for MORROW.
"""
import os
import json
from flask import Blueprint, jsonify
from backend.config import Config
from backend.database import get_db, is_mongodb_connected
from backend.utils.serializers import success_response, error_response

data_quality_bp = Blueprint("data_quality_bp", __name__)


@data_quality_bp.route("/data-quality", methods=["GET"])
def get_data_quality():
    """
    Returns actual data quality and cleaning report metrics, including
    initial record counts, duplicates detected, missing values,
    impossible timestamps, records removed, and final counts.
    """
    try:
        # Check MongoDB first
        db = get_db()
        if is_mongodb_connected() and db is not None:
            doc = db.data_quality_reports.find_one({}, sort=[("_id", -1)])
            if doc:
                payload, code = success_response(data=doc)
                return jsonify(payload), code

        # Fallback to JSON artifact
        json_path = os.path.join(Config.METRICS_DIR, "data_quality_report.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                report = json.load(f)
            payload, code = success_response(data=report)
            return jsonify(payload), code

        payload, code = error_response(
            message="Data quality report artifact not found. Please run: python -m ml.data.clean_dataset",
            status_code=404,
        )
        return jsonify(payload), code

    except Exception as e:
        payload, code = error_response(message=f"Error retrieving data quality report: {e}", status_code=500)
        return jsonify(payload), code

