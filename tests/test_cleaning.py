import pandas as pd
import numpy as np
from ml.config import BOOKING_CHANNELS, RANDOM_SEED
from ml.data.generate_synthetic_data import generate_synthetic_data, inject_quality_issues
from ml.data.clean_dataset import clean_dataset

def test_cleaning_removes_duplicates_and_bad_timestamps():
    df_clean_base = generate_synthetic_data(n_patients=200, n_appointments=800, seed=RANDOM_SEED)
    df_raw = inject_quality_issues(df_clean_base, seed=RANDOM_SEED)

    df_cleaned, report = clean_dataset(df_raw)

    assert report["duplicate_count"] > 0
    assert report["impossible_timestamps"] > 0
    assert report["negative_counts_set_to_nan"] > 0
    assert report["final_record_count"] < report["initial_record_count"]
    assert report["initial_record_count"] - report["records_removed"] == report["final_record_count"]
    assert (
        report["duplicate_feature_rows_removed"]
        + report["duplicate_appointment_ids_removed"]
        + report["removed_impossible_timestamps"]
        + report["invalid_target_removed"]
        == report["records_removed"]
    )

    # Check post-clean invariants
    assert (df_cleaned["booking_created_at"] < df_cleaned["appointment_datetime"]).all()
    assert df_cleaned["appointment_id"].is_unique
    assert set(df_cleaned["booking_channel"].dropna().unique()).issubset(set(BOOKING_CHANNELS))
    assert (df_cleaned["prior_no_show_count"].dropna() >= 0).all()
    assert (df_cleaned["prior_cancellations_count"].dropna() >= 0).all()

def test_cleaning_preserves_missing_for_pipeline():
    df_clean_base = generate_synthetic_data(n_patients=200, n_appointments=800, seed=RANDOM_SEED)
    df_raw = inject_quality_issues(df_clean_base, seed=RANDOM_SEED)
    df_cleaned, _ = clean_dataset(df_raw)
    # Missing numerical/categorical values should still exist for train-fold SimpleImputer
    assert df_cleaned.isnull().sum().sum() > 0

