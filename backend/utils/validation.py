"""
Input Validation for Prediction and Query Payloads.
"""
from ml.inference.predict import validate_input

def validate_prediction_input(data):
    """
    Validates prediction payload against model schema.
    Returns (cleaned_dict, errors_list).
    """
    if not isinstance(data, dict):
        return None, ["Request body must be a valid JSON object"]
    
    # Reject prohibited fields (target leakage / post-appointment data)
    forbidden_keys = ["no_show", "actual_attendance", "post_appointment_notes"]
    leaks = [k for k in forbidden_keys if k in data]
    if leaks:
        return None, [f"Target or post-appointment field '{k}' is strictly prohibited as input" for k in leaks]
    
    return validate_input(data)

