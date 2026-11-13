import pandas as pd
from ml.config import MODEL_FEATURES, TARGET_COLUMN
from ml.features.build_features import load_cleaned_data, chronological_split, build_features

def test_chronological_split_ordering():
    df = load_cleaned_data()
    df_train, df_val, df_test, split_info = chronological_split(df)

    # Strictly chronological ordering: train <= val <= test
    assert df_train["booking_created_at"].max() <= df_val["booking_created_at"].min()
    assert df_val["booking_created_at"].max() <= df_test["booking_created_at"].min()

    # Exact record counts add up
    assert len(df_train) + len(df_val) + len(df_test) == len(df)
    assert split_info["train"]["count"] == len(df_train)
    assert split_info["validation"]["count"] == len(df_val)
    assert split_info["test"]["count"] == len(df_test)

def test_no_target_or_future_leakage_in_features():
    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor, _ = build_features()
    assert list(X_train.columns) == MODEL_FEATURES
    assert TARGET_COLUMN not in X_train.columns
    assert "booking_created_at" not in X_train.columns
    assert "appointment_datetime" not in X_train.columns
    assert "appointment_id" not in X_train.columns
    assert "patient_key" not in X_train.columns

    # Preprocessor handles missing values cleanly
    X_val_transformed = preprocessor.transform(X_val)
    assert not pd.DataFrame(X_val_transformed).isnull().any().any()

