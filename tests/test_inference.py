import pytest
from ml.inference.predict import load_model, validate_input, predict

def test_load_model_succeeds():
    artifact = load_model()
    assert artifact is not None
    assert "pipeline" in artifact

def test_predict_valid_input():
    sample = {
        "booking_lead_days": 20,
        "appointment_weekday": 1,
        "appointment_hour": 10,
        "booking_hour": 9,
        "booking_channel": "online",
        "prior_appointments_count": 4,
        "prior_no_show_count": 1,
        "prior_cancellations_count": 0,
        "prior_no_show_rate": 0.25,
        "days_since_last_appointment": 30,
    }
    res = predict(sample)
    assert res["status"] == "success"
    assert 0.0 <= res["no_show_probability"] <= 1.0
    assert 0.0 <= res["attended_probability"] <= 1.0
    assert abs(res["no_show_probability"] + res["attended_probability"] - 1.0) < 1e-3
    assert res["predicted_class"] in [0, 1]
    assert res["risk_level"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]

def test_input_validation_catches_errors():
    bad_sample = {
        "booking_lead_days": -5,
        "appointment_weekday": 10,
        "appointment_hour": 10,
        "booking_hour": 9,
        "booking_channel": "invalid_channel",
        "prior_appointments_count": 2,
        "prior_no_show_count": 5,  # > prior_appointments_count
        "prior_cancellations_count": 0,
        "prior_no_show_rate": 0.5,
        "days_since_last_appointment": 10,
    }
    cleaned, errors = validate_input(bad_sample)
    assert len(errors) >= 3
    with pytest.raises(ValueError):
        predict(bad_sample)


def test_first_time_and_historical_consistency_validation():
    # First-time appointment convention (prior_appointments_count = 0)
    valid_first = {
        "booking_lead_days": 10,
        "appointment_weekday": 1,
        "appointment_hour": 10,
        "booking_hour": 9,
        "booking_channel": "online",
        "prior_appointments_count": 0,
        "prior_no_show_count": 0,
        "prior_cancellations_count": 0,
        "prior_no_show_rate": 0.0,
        "days_since_last_appointment": 0,
    }
    cleaned, errors = validate_input(valid_first)
    assert errors == []

    # Invalid first-time with nonzero days_since_last_appointment
    bad_first = dict(valid_first, days_since_last_appointment=30)
    _, errors_first = validate_input(bad_first)
    assert len(errors_first) >= 1

    # Invalid inconsistent prior_no_show_rate
    bad_rate = dict(valid_first, prior_appointments_count=4, prior_no_show_count=2, prior_no_show_rate=0.1, days_since_last_appointment=20)
    _, errors_rate = validate_input(bad_rate)
    assert any("inconsistent" in e for e in errors_rate)

    # Invalid no_show + cancellations > prior_appointments_count
    bad_sum = dict(valid_first, prior_appointments_count=3, prior_no_show_count=2, prior_cancellations_count=2, prior_no_show_rate=0.67, days_since_last_appointment=20)
    _, errors_sum = validate_input(bad_sum)
    assert len(errors_sum) >= 1

