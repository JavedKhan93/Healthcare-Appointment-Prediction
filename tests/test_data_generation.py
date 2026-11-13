import pandas as pd
import pytest
from ml.config import ALL_COLUMNS, BOOKING_CHANNELS, RANDOM_SEED
from ml.data.generate_synthetic_data import generate_synthetic_data, inject_quality_issues

def test_synthetic_data_reproducibility():
    df1 = generate_synthetic_data(n_patients=50, n_appointments=200, seed=RANDOM_SEED)
    df2 = generate_synthetic_data(n_patients=50, n_appointments=200, seed=RANDOM_SEED)
    # Check deterministic outcomes and distributions match
    assert len(df1) == len(df2)
    assert list(df1.columns) == ALL_COLUMNS
    assert df1["no_show"].equals(df2["no_show"])
    assert df1["booking_lead_days"].equals(df2["booking_lead_days"])

def test_synthetic_data_schema_and_ranges():
    df = generate_synthetic_data(n_patients=100, n_appointments=400, seed=RANDOM_SEED)
    assert set(df.columns) == set(ALL_COLUMNS)
    assert "patient_key" not in df.columns
    assert df["no_show"].isin([0, 1]).all()
    assert df["booking_channel"].isin(BOOKING_CHANNELS).all()
    assert (df["booking_lead_days"] >= 0).all()
    assert (df["prior_appointments_count"] >= 0).all()
    assert (df["prior_no_show_count"] <= df["prior_appointments_count"]).all()
    assert (df["booking_created_at"] < df["appointment_datetime"]).all()

def test_quality_issue_injection():
    df_clean = generate_synthetic_data(n_patients=200, n_appointments=800, seed=RANDOM_SEED)
    df_raw = inject_quality_issues(df_clean, seed=RANDOM_SEED)
    assert len(df_raw) > len(df_clean)  # Duplicates added
    assert df_raw.isnull().sum().sum() > 0  # Missing values injected
    assert (df_raw["booking_created_at"] >= df_raw["appointment_datetime"]).sum() > 0  # Bad timestamps

