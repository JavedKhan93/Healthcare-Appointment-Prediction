"""
Real-Time Inference Engine for MORROW.

Loads the saved ML artifact (preprocessing pipeline + calibrated model),
validates incoming appointment features, generates calibrated probabilities,
applies the decision threshold, and produces an operational risk indicator.

Usage:
    python -m ml.inference.predict
"""
import os
import joblib
import pandas as pd
import numpy as np

from ml.config import (
    MODEL_ARTIFACT_PATH,
    MODEL_FEATURES,
    FEATURE_VALIDATION,
    BOOKING_CHANNELS,
)

_CACHED_ARTIFACT = None


def load_model(artifact_path: str = MODEL_ARTIFACT_PATH) -> dict:
    """Load model artifact from disk or return cached version."""
    global _CACHED_ARTIFACT
    if _CACHED_ARTIFACT is not None:
        return _CACHED_ARTIFACT

    if not os.path.exists(artifact_path):
        raise FileNotFoundError(
            f"Model artifact not found at '{artifact_path}'. "
            "Please run the training pipeline first: python -m ml.training.train"
        )

    _CACHED_ARTIFACT = joblib.load(artifact_path)
    return _CACHED_ARTIFACT


def validate_input(data: dict) -> tuple[dict, list[str]]:
    """
    Validate inference payload against feature schema and allowable ranges.

    Returns:
        (cleaned_dict, error_list)
    """
    cleaned = {}
    errors = []

    for feature in MODEL_FEATURES:
        if feature not in data or data[feature] is None or data[feature] == "":
            errors.append(f"Missing required feature: '{feature}'")
            continue

        val = data[feature]
        rule = FEATURE_VALIDATION.get(feature, {})
        expected_type = rule.get("type")

        try:
            if expected_type == "int":
                if isinstance(val, bool) or (isinstance(val, float) and not val.is_integer()):
                    raise ValueError("Expected integer")
                parsed = int(val)
                if "min" in rule and parsed < rule["min"]:
                    errors.append(f"Field '{feature}' ({parsed}) cannot be less than {rule['min']}")
                if "max" in rule and parsed > rule["max"]:
                    errors.append(f"Field '{feature}' ({parsed}) cannot be greater than {rule['max']}")
                cleaned[feature] = parsed

            elif expected_type == "float":
                if isinstance(val, bool):
                    raise ValueError("Expected float")
                parsed = float(val)
                if "min" in rule and parsed < rule["min"]:
                    errors.append(f"Field '{feature}' ({parsed}) cannot be less than {rule['min']}")
                if "max" in rule and parsed > rule["max"]:
                    errors.append(f"Field '{feature}' ({parsed}) cannot be greater than {rule['max']}")
                cleaned[feature] = parsed

            elif expected_type == "str":
                parsed = str(val).strip().lower()
                allowed = rule.get("values", BOOKING_CHANNELS)
                if parsed not in allowed:
                    errors.append(f"Field '{feature}' ('{parsed}') must be one of: {allowed}")
                cleaned[feature] = parsed

            else:
                cleaned[feature] = val

        except (ValueError, TypeError):
            errors.append(f"Field '{feature}' must be a valid {expected_type}, got '{val}'")

    # Semantic cross-validation against documented historical rules
    has_hist = all(
        k in cleaned
        for k in (
            "prior_appointments_count",
            "prior_no_show_count",
            "prior_cancellations_count",
            "prior_no_show_rate",
            "days_since_last_appointment",
        )
    )
    if has_hist:
        appts = cleaned["prior_appointments_count"]
        noshows = cleaned["prior_no_show_count"]
        cancels = cleaned["prior_cancellations_count"]
        rate = cleaned["prior_no_show_rate"]
        days_last = cleaned["days_since_last_appointment"]

        if noshows > appts:
            errors.append("prior_no_show_count cannot exceed prior_appointments_count")
        if cancels > appts:
            errors.append("prior_cancellations_count cannot exceed prior_appointments_count")
        if noshows + cancels > appts:
            errors.append("prior_no_show_count + prior_cancellations_count cannot exceed prior_appointments_count")

        if appts == 0:
            if noshows != 0 or cancels != 0 or abs(rate) > 1e-6 or days_last != 0:
                errors.append(
                    "First-time appointment convention (prior_appointments_count = 0) requires "
                    "prior_no_show_count = 0, prior_cancellations_count = 0, prior_no_show_rate = 0.0, "
                    "and days_since_last_appointment = 0"
                )
        else:
            expected_rate = noshows / appts
            if abs(rate - expected_rate) > 0.02:
                errors.append(
                    f"prior_no_show_rate ({rate:.4f}) is inconsistent with prior_no_show_count / prior_appointments_count ({expected_rate:.4f})"
                )

    return cleaned, errors


def compute_risk_profile(probability: float, threshold: float) -> tuple[str, str]:
    """
    Determine risk tier and operational recommendation based on calibrated
    probability relative to the selected operating threshold and base rate (~17%).
    """
    if probability < threshold:
        risk_level = "LOW"
        suggestion = "Below operational threshold. Standard scheduling; no extra outreach needed."
    elif probability < 0.25:
        risk_level = "MODERATE"
        suggestion = "Above operational threshold. Standard confirmation reminder recommended."
    elif probability < 0.35:
        risk_level = "HIGH"
        suggestion = "Elevated non-attendance probability. Recommend administrative follow-up call or SMS verification."
    else:
        risk_level = "VERY_HIGH"
        suggestion = "Substantially elevated non-attendance probability (2x+ baseline). Recommend priority human review and confirmation."

    return risk_level, suggestion


def predict(input_data: dict, artifact: dict = None) -> dict:
    """
    Execute real-time model inference.

    Parameters:
        input_data: Dictionary of input features.
        artifact: Optional pre-loaded artifact.

    Returns:
        Structured prediction output dictionary.
    """
    if artifact is None:
        artifact = load_model()

    cleaned_features, errors = validate_input(input_data)
    if errors:
        raise ValueError(f"Input validation failed: {'; '.join(errors)}")

    pipeline = artifact["pipeline"]
    model_name = artifact.get("model_name", "MORROW Calibrated Estimator")
    model_version = artifact.get("model_version", "1.0.0")
    threshold = artifact.get("selected_threshold", 0.50)

    # Convert to DataFrame with schema order
    df_input = pd.DataFrame([cleaned_features])[MODEL_FEATURES]

    # Predict calibrated probability
    probabilities = pipeline.predict_proba(df_input)[0]
    prob_no_show = float(probabilities[1])
    prob_attended = float(probabilities[0])

    predicted_class = 1 if prob_no_show >= threshold else 0
    risk_level, suggestion = compute_risk_profile(prob_no_show, threshold)

    # Extract notable feature characteristics for operational context
    context_notes = []
    if cleaned_features.get("booking_lead_days", 0) > 30:
        context_notes.append(f"Extended lead time ({cleaned_features['booking_lead_days']} days)")
    if cleaned_features.get("prior_no_show_rate", 0) > 0.30:
        context_notes.append(f"Elevated prior no-show rate ({cleaned_features['prior_no_show_rate']:.0%})")
    if cleaned_features.get("prior_appointments_count", 0) == 0:
        context_notes.append("First-time hospital appointment")
    if cleaned_features.get("appointment_weekday") in [0, 4]:
        context_notes.append("Booked on a peak variance weekday")

    return {
        "status": "success",
        "no_show_probability": round(prob_no_show, 4),
        "attended_probability": round(prob_attended, 4),
        "predicted_class": predicted_class,
        "predicted_outcome": "No-Show" if predicted_class == 1 else "Attended",
        "selected_threshold": threshold,
        "risk_level": risk_level,
        "operational_suggestion": suggestion,
        "context_notes": context_notes,
        "model_name": model_name,
        "model_version": model_version,
        "input_features": cleaned_features,
        "disclaimer": (
            "This result is an experimental operational estimate generated using synthetic training data. "
            "It is not a guarantee that an appointment will be missed. Operational staff must review the "
            "information before taking administrative action."
        ),
    }


def main():
    print("=" * 60)
    print("MORROW — Inference Smoke Test")
    print("=" * 60)

    sample = {
        "booking_lead_days": 18,
        "appointment_weekday": 4,
        "appointment_hour": 10,
        "booking_hour": 9,
        "booking_channel": "online",
        "prior_appointments_count": 4,
        "prior_no_show_count": 1,
        "prior_cancellations_count": 0,
        "prior_no_show_rate": 0.25,
        "days_since_last_appointment": 45,
    }

    print("Submitting sample input:")
    for k, v in sample.items():
        print(f"  {k}: {v}")

    result = predict(sample)
    print("\nInference Output:")
    print(f"  No-Show Probability:   {result['no_show_probability']:.2%}")
    print(f"  Predicted Outcome:     {result['predicted_outcome']} (Class {result['predicted_class']})")
    print(f"  Operating Threshold:   {result['selected_threshold']:.2f}")
    print(f"  Operational Risk:      {result['risk_level']}")
    print(f"  Review Recommendation: {result['operational_suggestion']}")
    print(f"  Context Factors:       {result['context_notes']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
