"""
Prediction Service for MORROW.

Validates input, runs inference using cached pipeline, stores prediction logs,
and generates structured operational risk profiles.
"""
import uuid
from backend.services.model_service import get_model_artifact
from backend.utils.validation import validate_prediction_input
from backend.database import save_prediction_log, get_prediction_logs
from ml.inference.predict import predict as run_ml_prediction

def process_prediction(input_data: dict, appointment_id: str = None) -> dict:
    """
    Validate input, invoke ML pipeline, record in history, and return result.
    """
    cleaned_input, errors = validate_prediction_input(input_data)
    if errors:
        return {"success": False, "errors": errors}

    artifact = get_model_artifact()
    if artifact is None:
        return {
            "success": False,
            "errors": ["Model pipeline artifact is not loaded on the server. Please check artifacts/models/."],
        }

    # Run genuine model prediction
    prediction_result = run_ml_prediction(cleaned_input, artifact)

    # Attach optional appointment ID
    if appointment_id:
        prediction_result["appointment_id"] = appointment_id

    # Store prediction log in database
    log_entry = {
        "prediction_id": f"PRD-{uuid.uuid4().hex[:8].upper()}",
        "appointment_id": appointment_id,
        "input_features": cleaned_input,
        "no_show_probability": prediction_result["no_show_probability"],
        "attended_probability": prediction_result["attended_probability"],
        "predicted_class": prediction_result["predicted_class"],
        "predicted_outcome": prediction_result["predicted_outcome"],
        "selected_threshold": prediction_result["selected_threshold"],
        "risk_level": prediction_result["risk_level"],
        "operational_suggestion": prediction_result["operational_suggestion"],
        "context_notes": prediction_result["context_notes"],
        "model_name": prediction_result["model_name"],
        "model_version": prediction_result["model_version"],
    }
    
    saved_log = save_prediction_log(log_entry)
    prediction_result["prediction_id"] = saved_log.get("prediction_id")
    prediction_result["created_at"] = saved_log.get("created_at")

    return {"success": True, "data": prediction_result}


def list_predictions(limit: int = 50, skip: int = 0) -> list:
    """Retrieve historical prediction records."""
    return get_prediction_logs(limit=limit, skip=skip)

