import pytest
from backend.run import create_app

@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "success"
    assert body["data"]["model_artifact"]["loaded"] is True

def test_dashboard_endpoints(client):
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["total_appointments"] > 9000
    assert data["attended_appointments"] + data["no_show_appointments"] == data["total_appointments"]

    res_trends = client.get("/api/v1/dashboard/trends")
    assert res_trends.status_code == 200
    trends = res_trends.get_json()["data"]
    assert len(trends["by_weekday"]) == 7
    assert len(trends["by_channel"]) == 3
    assert len(trends["by_hour"]) > 0
    assert "total" in trends["by_hour"][0] and "rate" in trends["by_hour"][0]
    assert len(trends["by_month"]) > 0

def test_appointments_pagination_and_detail(client):
    res1 = client.get("/api/v1/appointments?page=1&per_page=10")
    res2 = client.get("/api/v1/appointments?page=2&per_page=10")
    assert res1.status_code == 200 and res2.status_code == 200
    items1 = res1.get_json()["data"]["items"]
    items2 = res2.get_json()["data"]["items"]
    assert len(items1) == 10 and len(items2) == 10
    ids1 = {r["appointment_id"] for r in items1}
    ids2 = {r["appointment_id"] for r in items2}
    assert ids1.isdisjoint(ids2)  # No duplicates across stable deterministic pagination

    # Date filter check
    res_date = client.get("/api/v1/appointments?start_date=2024-01-01&end_date=2024-06-30")
    assert res_date.status_code == 200
    assert res_date.get_json()["data"]["pagination"]["total"] > 0

    first_id = items1[0]["appointment_id"]
    res_single = client.get(f"/api/v1/appointments/{first_id}")
    assert res_single.status_code == 200
    assert res_single.get_json()["data"]["appointment_id"] == first_id

    res_404 = client.get("/api/v1/appointments/NON-EXISTENT-999")
    assert res_404.status_code == 404

def test_prediction_endpoint_valid_and_invalid(client):
    valid_payload = {
        "booking_lead_days": 25,
        "appointment_weekday": 4,
        "appointment_hour": 14,
        "booking_hour": 10,
        "booking_channel": "phone",
        "prior_appointments_count": 5,
        "prior_no_show_count": 2,
        "prior_cancellations_count": 1,
        "prior_no_show_rate": 0.4,
        "days_since_last_appointment": 60,
    }
    res = client.post("/api/v1/predictions", json=valid_payload)
    assert res.status_code == 201
    pred = res.get_json()["data"]
    assert 0.0 <= pred["no_show_probability"] <= 1.0
    assert pred["predicted_class"] in [0, 1]

    # Duplicate submission must generate a distinct prediction_id (no hash collision)
    res_dup = client.post("/api/v1/predictions", json=valid_payload)
    assert res_dup.status_code == 201
    assert res_dup.get_json()["data"]["prediction_id"] != pred["prediction_id"]

    # Verify history recorded
    hist_res = client.get("/api/v1/predictions/history")
    assert hist_res.status_code == 200
    assert hist_res.get_json()["data"]["count"] >= 2

    # Invalid payload containing target leakage field
    leak_payload = dict(valid_payload, no_show=1)
    res_leak = client.post("/api/v1/predictions", json=leak_payload)
    assert res_leak.status_code == 400

    # Invalid missing field
    res_bad = client.post("/api/v1/predictions", json={"booking_lead_days": 5})
    assert res_bad.status_code == 400

def test_model_and_quality_endpoints(client):
    res_metrics = client.get("/api/v1/model/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.get_json()["data"]
    assert "comparison" in metrics_data
    assert "test_metrics" in metrics_data
    assert "test_comparison" in metrics_data["test_metrics"]
    assert "curves" in metrics_data
    assert "reference_brier_score" in metrics_data["test_metrics"]

    res_fi = client.get("/api/v1/model/feature-importance")
    assert res_fi.status_code == 200
    assert len(res_fi.get_json()["data"]) == 10

    res_dq = client.get("/api/v1/data-quality")
    assert res_dq.status_code == 200
    assert res_dq.get_json()["data"]["final_record_count"] > 9000

