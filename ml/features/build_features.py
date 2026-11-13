"""
Feature Engineering Module for MORROW.

Loads the cleaned dataset, performs a chronological train/val/test split,
and builds sklearn preprocessing pipelines.

Usage:
    python -m ml.features.build_features
"""
import os
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from ml.config import (
    CLEANED_DATA_PATH,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    TARGET_COLUMN,
    TRAIN_RATIO,
    VALIDATION_RATIO,
    RANDOM_SEED,
)


def load_cleaned_data(path: str = CLEANED_DATA_PATH) -> pd.DataFrame:
    """Load the cleaned CSV with parsed timestamps."""
    df = pd.read_csv(path, parse_dates=["booking_created_at", "appointment_datetime"])
    df = df.sort_values("booking_created_at").reset_index(drop=True)
    print(f"Loaded {len(df)} cleaned records from {path}")
    return df


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VALIDATION_RATIO,
) -> tuple:
    """
    Split the dataset chronologically by booking_created_at.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned dataset sorted by booking_created_at.
    train_ratio : float
        Fraction for training (default 0.70).
    val_ratio : float
        Fraction for validation (default 0.15).

    Returns
    -------
    (df_train, df_val, df_test, split_info)
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    split_info = {
        "total_records": n,
        "train": {
            "count": len(df_train),
            "start_date": str(df_train["booking_created_at"].min()),
            "end_date": str(df_train["booking_created_at"].max()),
            "no_show_rate": float(df_train[TARGET_COLUMN].mean()),
        },
        "validation": {
            "count": len(df_val),
            "start_date": str(df_val["booking_created_at"].min()),
            "end_date": str(df_val["booking_created_at"].max()),
            "no_show_rate": float(df_val[TARGET_COLUMN].mean()),
        },
        "test": {
            "count": len(df_test),
            "start_date": str(df_test["booking_created_at"].min()),
            "end_date": str(df_test["booking_created_at"].max()),
            "no_show_rate": float(df_test[TARGET_COLUMN].mean()),
        },
    }

    return df_train, df_val, df_test, split_info


def build_preprocessor() -> ColumnTransformer:
    """
    Build a ColumnTransformer with:
      - Numerical: SimpleImputer(median) → StandardScaler
      - Categorical: SimpleImputer(most_frequent) → OneHotEncoder(sparse_output=False)
    """
    numerical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_pipeline, NUMERICAL_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    return preprocessor


def build_features(
    data_path: str = CLEANED_DATA_PATH,
) -> tuple:
    """
    Full feature engineering pipeline.

    Returns
    -------
    (X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, split_info)
    """
    df = load_cleaned_data(data_path)

    # Chronological split
    df_train, df_val, df_test, split_info = chronological_split(df)

    # Extract features and target
    X_train = df_train[MODEL_FEATURES]
    X_val = df_val[MODEL_FEATURES]
    X_test = df_test[MODEL_FEATURES]

    y_train = df_train[TARGET_COLUMN].values
    y_val = df_val[TARGET_COLUMN].values
    y_test = df_test[TARGET_COLUMN].values

    # Build and fit preprocessor on training data ONLY
    preprocessor = build_preprocessor()
    preprocessor.fit(X_train)

    print(f"\nPreprocessor fitted on {len(X_train)} training samples")
    print(f"Transformed feature count: {preprocessor.transform(X_train[:1]).shape[1]}")

    return X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, split_info


def main():
    """Print split summary."""
    print("=" * 60)
    print("MORROW — Feature Engineering")
    print("=" * 60)

    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, split_info = (
        build_features()
    )

    print("\n" + "─" * 50)
    print("Chronological Split Summary:")
    print("─" * 50)
    for split_name in ["train", "validation", "test"]:
        info = split_info[split_name]
        print(f"\n  {split_name.upper()}:")
        print(f"    Records:      {info['count']}")
        print(f"    Date range:   {info['start_date']}  →  {info['end_date']}")
        print(f"    No-show rate: {info['no_show_rate']:.2%}")

    print(f"\n  Total records: {split_info['total_records']}")
    print("─" * 50)


if __name__ == "__main__":
    main()
