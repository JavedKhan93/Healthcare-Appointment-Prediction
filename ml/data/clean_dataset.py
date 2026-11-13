"""
Data Cleaning Pipeline for MORROW.

Loads the raw synthetic CSV, validates and cleans it, produces a
data-quality report, and saves the cleaned dataset.

Usage:
    python -m ml.data.clean_dataset
"""
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

from ml.config import (
    RAW_DATA_PATH,
    CLEANED_DATA_PATH,
    DATA_PROCESSED_DIR,
    METRICS_DIR,
    ALL_COLUMNS,
    BOOKING_CHANNELS,
    TARGET_COLUMN,
    ID_COLUMN,
)


def load_raw_data(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw CSV file."""
    df = pd.read_csv(path, parse_dates=["booking_created_at", "appointment_datetime"])
    print(f"Loaded {len(df)} records from {path}")
    return df


def validate_columns(df: pd.DataFrame) -> dict:
    """Check that expected columns are present."""
    expected = set(ALL_COLUMNS)
    actual = set(df.columns)
    missing = expected - actual
    extra = actual - expected
    return {"missing_columns": list(missing), "extra_columns": list(extra)}


def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Identify and flag duplicate records."""
    # Duplicates based on all columns except appointment_id
    feature_cols = [c for c in df.columns if c != ID_COLUMN]
    is_dup = df.duplicated(subset=feature_cols, keep="first")
    n_dups = is_dup.sum()
    print(f"Found {n_dups} duplicate records")
    return is_dup


def check_missing(df: pd.DataFrame) -> dict:
    """Report missing values per column."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    report = {}
    for col in df.columns:
        if missing[col] > 0:
            report[col] = {"count": int(missing[col]), "percentage": float(missing_pct[col])}
    return report


def validate_timestamps(df: pd.DataFrame) -> pd.Series:
    """
    Flag records where booking_created_at >= appointment_datetime
    (impossible: you can't book after the appointment).
    """
    invalid = df["booking_created_at"] >= df["appointment_datetime"]
    n_invalid = invalid.sum()
    print(f"Found {n_invalid} records with impossible timestamps")
    return invalid


def validate_non_negative(df: pd.DataFrame) -> pd.Series:
    """Flag records with negative counts."""
    count_cols = [
        "prior_appointments_count",
        "prior_no_show_count",
        "prior_cancellations_count",
    ]
    invalid = pd.Series(False, index=df.index)
    for col in count_cols:
        col_invalid = df[col] < 0
        if col_invalid.any():
            print(f"  {col}: {col_invalid.sum()} negative values")
            invalid = invalid | col_invalid
    return invalid


def validate_historical_relationships(df: pd.DataFrame) -> pd.Series:
    """
    Flag records where prior_no_show_count > prior_appointments_count.
    """
    invalid = pd.Series(False, index=df.index)
    mask = df["prior_no_show_count"] > df["prior_appointments_count"]
    mask = mask & df["prior_no_show_count"].notna() & df["prior_appointments_count"].notna()
    mask = mask & (df["prior_no_show_count"] >= 0) & (df["prior_appointments_count"] >= 0)
    if mask.any():
        print(f"  {mask.sum()} records where prior_no_show_count > prior_appointments_count")
    invalid = invalid | mask
    return invalid


def standardize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize booking_channel values to standard lowercase."""
    channel_map = {
        "online": "online", "Online": "online", "ONLINE": "online", "on-line": "online",
        "phone": "phone", "Phone": "phone", "PHONE": "phone", "telephone": "phone",
        "in_person": "in_person", "In_Person": "in_person", "IN_PERSON": "in_person",
        "in-person": "in_person", "walk_in": "in_person",
    }
    original_unique = df["booking_channel"].dropna().unique().tolist()
    df["booking_channel"] = df["booking_channel"].map(channel_map)
    cleaned_unique = df["booking_channel"].dropna().unique().tolist()
    print(f"Standardized booking_channel: {original_unique} → {cleaned_unique}")
    return df


def analyze_outliers(df: pd.DataFrame) -> dict:
    """
    Identify unusual but potentially valid observations.
    Do NOT remove these — document them.
    """
    outlier_info = {}

    # Booking lead days > 120
    long_lead = (df["booking_lead_days"] > 120).sum()
    outlier_info["booking_lead_days_gt_120"] = int(long_lead)

    # Prior appointments > 20
    high_prior = (df["prior_appointments_count"] > 20).sum()
    outlier_info["prior_appointments_gt_20"] = int(high_prior)

    # Days since last > 365
    long_gap = (df["days_since_last_appointment"] > 365).sum()
    outlier_info["days_since_last_gt_365"] = int(long_gap)

    return outlier_info


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Full cleaning pipeline.

    Returns
    -------
    (cleaned_df, quality_report)
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "initial_record_count": len(df),
    }

    print("\n── Column Validation ──")
    col_check = validate_columns(df)
    report["column_validation"] = col_check

    print("\n── Duplicate Detection ──")
    is_dup = check_duplicates(df)
    report["duplicate_feature_rows_removed"] = int(is_dup.sum())

    print("\n── Missing Value Analysis ──")
    missing_report = check_missing(df)
    report["missing_values"] = missing_report
    print(f"  Total columns with missing: {len(missing_report)}")

    print("\n── Timestamp Validation ──")
    invalid_ts = validate_timestamps(df)
    report["impossible_timestamps"] = int(invalid_ts.sum())

    print("\n── Non-Negative Validation ──")
    invalid_neg = validate_non_negative(df)
    report["negative_counts"] = int(invalid_neg.sum())

    print("\n── Historical Relationship Validation ──")
    invalid_hist = validate_historical_relationships(df)
    report["invalid_historical_relationships"] = int(invalid_hist.sum())

    # ── Remove duplicates ─────────────────────────────────────────────
    df_clean = df[~is_dup].copy()
    print(f"\nRemoved {is_dup.sum()} exact feature-row duplicates → {len(df_clean)} records")

    # ── Remove impossible timestamps ──────────────────────────────────
    invalid_ts_clean = validate_timestamps(df_clean)
    df_clean = df_clean[~invalid_ts_clean].copy()
    report["removed_impossible_timestamps"] = int(invalid_ts_clean.sum())
    print(f"Removed {invalid_ts_clean.sum()} impossible timestamp records → {len(df_clean)} records")

    # ── Fix negative counts (set to NaN for later imputation) ─────────
    count_cols = ["prior_no_show_count", "prior_cancellations_count",
                  "prior_appointments_count"]
    neg_fixed = 0
    for col in count_cols:
        mask = df_clean[col] < 0
        neg_fixed += mask.sum()
        df_clean.loc[mask, col] = np.nan
    report["negative_counts_set_to_nan"] = int(neg_fixed)
    print(f"Converted {neg_fixed} invalid negative counts to missing (NaN)")

    # ── Standardize categories ────────────────────────────────────────
    print("\n── Category Standardization ──")
    df_clean = standardize_categories(df_clean)

    # ── Validate target ───────────────────────────────────────────────
    valid_target = df_clean[TARGET_COLUMN].isin([0, 1])
    invalid_target = (~valid_target).sum()
    if invalid_target > 0:
        df_clean = df_clean[valid_target].copy()
        print(f"Removed {invalid_target} records with invalid target")
    report["invalid_target_removed"] = int(invalid_target)

    # ── Ensure appointment_id is unique after cleaning ────────────────
    dup_id_mask = df_clean[ID_COLUMN].duplicated(keep="first")
    dup_id_count = int(dup_id_mask.sum())
    if dup_id_count > 0:
        df_clean = df_clean[~dup_id_mask].copy()
        print(f"Removed {dup_id_count} duplicate appointment_id record(s) (modified duplicate rows) → {len(df_clean)} records")
    report["duplicate_appointment_ids_removed"] = dup_id_count
    report["duplicate_count"] = report["duplicate_feature_rows_removed"] + dup_id_count

    # ── Outlier Analysis (documented, not removed) ────────────────────
    print("\n── Outlier Analysis ──")
    outlier_info = analyze_outliers(df_clean)
    report["outlier_observations"] = outlier_info
    for k, v in outlier_info.items():
        print(f"  {k}: {v}")

    # ── Final Missing Values After Cleaning ───────────────────────────
    final_missing = check_missing(df_clean)
    report["final_missing_values"] = final_missing

    # ── Final Report ──────────────────────────────────────────────────
    report["final_record_count"] = len(df_clean)
    report["records_removed"] = report["initial_record_count"] - len(df_clean)
    report["final_data_types"] = {col: str(dtype) for col, dtype in df_clean.dtypes.items()}
    report["target_distribution"] = {
        "attended": int((df_clean[TARGET_COLUMN] == 0).sum()),
        "no_show": int((df_clean[TARGET_COLUMN] == 1).sum()),
        "no_show_rate": float(round(df_clean[TARGET_COLUMN].mean(), 4)),
    }

    # Sort by booking date for chronological ordering
    df_clean = df_clean.sort_values("booking_created_at").reset_index(drop=True)

    return df_clean, report


def main():
    """Run the cleaning pipeline and save results."""
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    os.makedirs(METRICS_DIR, exist_ok=True)

    print("=" * 60)
    print("MORROW — Data Cleaning Pipeline")
    print("=" * 60)

    # Load raw data
    df_raw = load_raw_data()

    # Clean
    df_clean, report = clean_dataset(df_raw)

    # Save cleaned dataset
    df_clean.to_csv(CLEANED_DATA_PATH, index=False)
    print(f"\nSaved cleaned dataset to: {CLEANED_DATA_PATH}")
    print(f"Final cleaned records: {len(df_clean)}")

    # Save quality report
    report_path = os.path.join(METRICS_DIR, "data_quality_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Saved quality report to: {report_path}")

    print("\n" + "─" * 40)
    print("Cleaning Summary:")
    print(f"  Initial:  {report['initial_record_count']}")
    print(f"  Removed:  {report['records_removed']}")
    print(f"  Final:    {report['final_record_count']}")
    print(f"  No-show:  {report['target_distribution']['no_show_rate']:.2%}")
    print("─" * 40)


if __name__ == "__main__":
    main()

