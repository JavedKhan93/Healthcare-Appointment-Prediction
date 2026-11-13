from datetime import datetime
from bson import ObjectId
from backend.utils.serializers import serialize_doc
from backend.utils.validation import validate_prediction_input

def test_mongodb_document_serialization():
    oid = ObjectId()
    now = datetime(2026, 1, 15, 10, 30, 0)
    doc = {
        "_id": oid,
        "created_at": now,
        "nested": {"ref_id": oid, "list": [now]},
        "value": 42,
    }
    serialized = serialize_doc(doc)
    assert serialized["id"] == str(oid)
    assert "_id" not in serialized
    assert serialized["created_at"] == "2026-01-15T10:30:00"
    assert serialized["nested"]["ref_id"] == str(oid)
    assert serialized["nested"]["list"][0] == "2026-01-15T10:30:00"
    assert serialized["value"] == 42

def test_validation_rejects_prohibited_leakage():
    payload = {
        "booking_lead_days": 10,
        "appointment_weekday": 2,
        "appointment_hour": 10,
        "booking_hour": 8,
        "booking_channel": "online",
        "prior_appointments_count": 1,
        "prior_no_show_count": 0,
        "prior_cancellations_count": 0,
        "prior_no_show_rate": 0.0,
        "days_since_last_appointment": 20,
        "no_show": 0,
    }
    cleaned, errors = validate_prediction_input(payload)
    assert cleaned is None
    assert len(errors) == 1
    assert "prohibited" in errors[0].lower()

