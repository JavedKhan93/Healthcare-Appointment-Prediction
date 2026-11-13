"""
Real-Time Prediction Routes for MORROW.
"""
from flask import Blueprint, request, jsonify
from backend.services.prediction_service import process_prediction, list_predictions
from backend.utils.serializers import success_response, error_response

prediction_bp = Blueprint("prediction_bp", __name__)


@prediction_bp.route("/predictions", methods=["POST"])
def make_prediction():
    """
    Generate calibrated no-show probability estimate from appointment features.
    """
    if not request.is_json:
        payload, code = error_response(message="Request content-type must be application/json", status_code=415)
        return jsonify(payload), code

    data = request.get_json()
    appointment_id = data.get("appointment_id")

    result = process_prediction(data, appointment_id=appointment_id)
    if not result.get("success"):
        payload, code = error_response(
            message="Prediction validation error",
            errors=result.get("errors"),
            status_code=400,
        )
        return jsonify(payload), code

    payload, code = success_response(
        data=result["data"],
        message="Prediction successfully generated",
        status_code=201,
    )
    return jsonify(payload), code


@prediction_bp.route("/predictions/history", methods=["GET"])
def history():
    """Retrieve recent prediction history."""
    try:
        limit = min(100, max(1, int(request.args.get("limit", 20))))
        skip = max(0, int(request.args.get("skip", 0)))

        records = list_predictions(limit=limit, skip=skip)
        payload, code = success_response(data={"predictions": records, "count": len(records)})
        return jsonify(payload), code
    except Exception as e:
        payload, code = error_response(message=f"Failed to fetch prediction history: {e}", status_code=500)
        return jsonify(payload), code

