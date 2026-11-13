"""End-to-end API verification script for MORROW."""
import requests
import json
import sys

BASE = "http://localhost:5000/api/v1"

def main():
    errors = []

    # 1. Health check
    print("=== HEALTH CHECK ===")
    r = requests.get(f"{BASE}/health")
    h = r.json()["data"]
    print(json.dumps(h, indent=2))
    mongo_ok = h["mongodb"]["connected"]
    print(f"MongoDB Connected: {mongo_ok}")
    if not mongo_ok:
        errors.append("MongoDB NOT connected")

    # 2. Dashboard summary
    print("\n=== DASHBOARD SUMMARY ===")
    r = requests.get(f"{BASE}/dashboard/summary")
    d = r.json()["data"]
    print(f"Total appointments: {d['total_appointments']}")
    print(f"Attended: {d['attended_appointments']}")
    print(f"No-show: {d['no_show_appointments']}")
    print(f"No-show rate: {d['no_show_rate_percent']}%")
    print(f"Predictions logged: {d['total_predictions_logged']}")
    if d["total_appointments"] != 9950:
        errors.append(f"Expected 9950 appointments, got {d['total_appointments']}")

    # 3. Dashboard trends
    print("\n=== DASHBOARD TRENDS ===")
    r = requests.get(f"{BASE}/dashboard/trends")
    t = r.json()["data"]
    print(f"Source: {t['source']}")
    print(f"Weekdays: {len(t['by_weekday'])}")
    print(f"Channels: {len(t['by_channel'])}")
    print(f"Hours: {len(t['by_hour'])}")
    print(f"Months: {len(t['by_month'])}")
    if t["source"] != "mongodb":
        errors.append(f"Dashboard trends source is '{t['source']}', expected 'mongodb'")

    # 4. Appointments pagination
    print("\n=== APPOINTMENTS (page 1, 5 per page) ===")
    r = requests.get(f"{BASE}/appointments?page=1&per_page=5")
    a = r.json()["data"]
    print(f"Source: {a['source']}")
    print(f"Total: {a['pagination']['total']}")
    print(f"Pages: {a['pagination']['pages']}")
    print(f"Items on page: {len(a['items'])}")
    if a["source"] != "mongodb":
        errors.append(f"Appointments source is '{a['source']}', expected 'mongodb'")

    # 5. Appointments search
    print("\n=== APPOINTMENTS SEARCH ===")
    r = requests.get(f"{BASE}/appointments?search=APT-00001&per_page=5")
    a = r.json()["data"]
    print(f"Search results: {a['pagination']['total']}")
    if a["pagination"]["total"] == 0:
        errors.append("Search returned 0 results for APT-00001")

    # 6. Submit prediction
    print("\n=== PREDICTION SUBMISSION ===")
    pred_payload = {
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
    r = requests.post(f"{BASE}/predictions", json=pred_payload)
    p = r.json()
    print(f"Status: {p['status']}")
    pred_data = p["data"]
    print(f"No-Show Probability: {pred_data['no_show_probability']}")
    print(f"Predicted Outcome: {pred_data['predicted_outcome']}")
    print(f"Threshold: {pred_data['selected_threshold']}")
    print(f"Risk Level: {pred_data['risk_level']}")
    print(f"Model: {pred_data['model_name']} v{pred_data['model_version']}")
    print(f"Prediction ID: {pred_data['prediction_id']}")
    if pred_data["selected_threshold"] != 0.15:
        errors.append(f"Threshold is {pred_data['selected_threshold']}, expected 0.15")
    if pred_data["model_name"] != "LogisticRegression":
        errors.append(f"Model is {pred_data['model_name']}, expected LogisticRegression")

    # 7. Verify prediction in MongoDB
    print("\n=== PREDICTION HISTORY (verify persistence) ===")
    r = requests.get(f"{BASE}/predictions/history?limit=5")
    hist = r.json()["data"]
    print(f"Predictions in DB: {hist['count']}")
    if hist["predictions"]:
        latest = hist["predictions"][0]
        print(f"Latest prediction ID: {latest['prediction_id']}")
        print(f"Latest probability: {latest['no_show_probability']}")
    if hist["count"] < 1:
        errors.append("No predictions found after submission")

    # 8. Model metrics
    print("\n=== MODEL METRICS ===")
    r = requests.get(f"{BASE}/model/metrics")
    m = r.json()["data"]
    tm = m["test_metrics"]
    cv = m["curves"]
    print(f"Test Brier: {tm['brier_score']}")
    print(f"Test ROC-AUC: {tm['roc_auc']}")
    print(f"Test PR-AUC: {tm['pr_auc']}")
    print(f"Validation ROC-AUC (curves): {cv['roc_curve']['auc']}")
    print(f"Validation PR-AUC (curves): {cv['pr_curve']['auc']}")
    print(f"Calibration Brier (curves): {cv['calibration_curve']['brier_score']}")
    print(f"Bin counts: {cv['calibration_curve'].get('bin_counts', 'N/A')}")
    print(f"Test comparison models: {list(tm['test_comparison'].keys())}")
    
    # Verify all 4+1 models in test comparison
    expected_test_models = {"DummyClassifier", "LogisticRegression", "RandomForest", "HistGradientBoosting"}
    actual_test_models = set(tm["test_comparison"].keys())
    for em in expected_test_models:
        if em not in actual_test_models:
            errors.append(f"Missing test comparison model: {em}")

    # 9. Model metadata
    print("\n=== MODEL METADATA ===")
    r = requests.get(f"{BASE}/model/metadata")
    meta = r.json()["data"]
    print(f"Model: {meta['model_name']}")
    print(f"Version: {meta['model_version']}")
    print(f"Threshold: {meta['selected_threshold']}")
    print(f"Calibration: {meta['calibration_method']}")

    # 10. Feature importance
    print("\n=== FEATURE IMPORTANCE ===")
    r = requests.get(f"{BASE}/model/feature-importance")
    fi = r.json()["data"]
    print(f"Features: {len(fi)}")
    if fi:
        print(f"Top feature: {fi[0]['feature']} ({fi[0]['importance_mean']:.5f})")

    # 11. Data quality
    print("\n=== DATA QUALITY ===")
    r = requests.get(f"{BASE}/data-quality")
    dq = r.json()["data"]
    print(f"Initial records: {dq['initial_record_count']}")
    print(f"Final records: {dq['final_record_count']}")
    print(f"Records removed: {dq['records_removed']}")
    print(f"Duplicate feature rows: {dq['duplicate_feature_rows_removed']}")
    print(f"Duplicate IDs: {dq['duplicate_appointment_ids_removed']}")
    print(f"Bad timestamps: {dq['removed_impossible_timestamps']}")
    print(f"Negative counts set to NaN: {dq['negative_counts_set_to_nan']}")
    
    # Verify cleaning reconciliation
    expected_removed = dq["duplicate_feature_rows_removed"] + dq["duplicate_appointment_ids_removed"] + dq["removed_impossible_timestamps"]
    if expected_removed != dq["records_removed"]:
        errors.append(f"Cleaning reconciliation: {expected_removed} != {dq['records_removed']}")
    if dq["initial_record_count"] - dq["records_removed"] != dq["final_record_count"]:
        errors.append(f"Record count mismatch: {dq['initial_record_count']} - {dq['records_removed']} != {dq['final_record_count']}")

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("ALL API ENDPOINT TESTS PASSED ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()

