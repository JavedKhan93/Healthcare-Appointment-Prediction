"""
ML Configuration for MORROW Hospital No-Show Prediction.

Central configuration module containing all constants, feature schemas,
file paths, and model parameters used across the ML pipeline.
"""
import os

# ─── Random Seed ───────────────────────────────────────────────────────
RANDOM_SEED = 42

# ─── Paths ─────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")
MODELS_DIR = os.path.join(ARTIFACTS_DIR, "models")
METRICS_DIR = os.path.join(ARTIFACTS_DIR, "metrics")
FIGURES_DIR = os.path.join(ARTIFACTS_DIR, "figures")

RAW_DATA_PATH = os.path.join(DATA_RAW_DIR, "synthetic_appointments_raw.csv")
CLEANED_DATA_PATH = os.path.join(DATA_PROCESSED_DIR, "synthetic_appointments_cleaned.csv")
MODEL_ARTIFACT_PATH = os.path.join(MODELS_DIR, "no_show_pipeline.joblib")

# ─── Dataset Generation ───────────────────────────────────────────────
NUM_PATIENTS = 2500
NUM_APPOINTMENTS = 10000
DATE_START = "2023-01-01"
DATE_END = "2024-12-31"

# ─── Booking Channels ─────────────────────────────────────────────────
BOOKING_CHANNELS = ["online", "phone", "in_person"]

# ─── Feature Schema ───────────────────────────────────────────────────
# These are the model input features (prediction-time available)
MODEL_FEATURES = [
    "booking_lead_days",
    "appointment_weekday",
    "appointment_hour",
    "booking_hour",
    "booking_channel",
    "prior_appointments_count",
    "prior_no_show_count",
    "prior_cancellations_count",
    "prior_no_show_rate",
    "days_since_last_appointment",
]

# Numerical features for preprocessing
NUMERICAL_FEATURES = [
    "booking_lead_days",
    "appointment_weekday",
    "appointment_hour",
    "booking_hour",
    "prior_appointments_count",
    "prior_no_show_count",
    "prior_cancellations_count",
    "prior_no_show_rate",
    "days_since_last_appointment",
]

# Categorical features for preprocessing
CATEGORICAL_FEATURES = [
    "booking_channel",
]

# Target column
TARGET_COLUMN = "no_show"

# Record identifier
ID_COLUMN = "appointment_id"

# Timestamp columns (for chronological splitting, not model features)
TIMESTAMP_COLUMNS = ["booking_created_at", "appointment_datetime"]

# ─── All Dataset Columns ──────────────────────────────────────────────
ALL_COLUMNS = [
    "appointment_id",
    "booking_created_at",
    "appointment_datetime",
    "booking_lead_days",
    "appointment_weekday",
    "appointment_hour",
    "booking_hour",
    "booking_channel",
    "prior_appointments_count",
    "prior_no_show_count",
    "prior_cancellations_count",
    "prior_no_show_rate",
    "days_since_last_appointment",
    "no_show",
]

# ─── Chronological Split Ratios ───────────────────────────────────────
TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

# ─── Model Parameters ─────────────────────────────────────────────────
LOGISTIC_REGRESSION_PARAMS = {
    "C": 1.0,
    "class_weight": "balanced",
    "max_iter": 1000,
    "random_state": RANDOM_SEED,
    "solver": "lbfgs",
}

RANDOM_FOREST_PARAMS = {
    "n_estimators": 200,
    "max_depth": 12,
    "min_samples_leaf": 10,
    "class_weight": "balanced_subsample",
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
}

HISTGB_PARAMS = {
    "learning_rate": 0.05,
    "max_iter": 300,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 0.1,
    "random_state": RANDOM_SEED,
}

# ─── Threshold Candidates ─────────────────────────────────────────────
THRESHOLD_CANDIDATES = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70]

# ─── Business Cost Assumptions (Illustrative) ─────────────────────────
# Cost of sending an unnecessary reminder (false positive)
FALSE_POSITIVE_COST = 5.0   # £/$5 operational cost
# Cost of missing a no-show that could have been flagged (false negative)
FALSE_NEGATIVE_COST = 50.0  # £/$50 lost slot + rescheduling

# ─── Validation Ranges for Inference Inputs ────────────────────────────
FEATURE_VALIDATION = {
    "booking_lead_days": {"min": 0, "max": 365, "type": "int"},
    "appointment_weekday": {"min": 0, "max": 6, "type": "int"},
    "appointment_hour": {"min": 6, "max": 21, "type": "int"},
    "booking_hour": {"min": 0, "max": 23, "type": "int"},
    "booking_channel": {"values": BOOKING_CHANNELS, "type": "str"},
    "prior_appointments_count": {"min": 0, "max": 200, "type": "int"},
    "prior_no_show_count": {"min": 0, "max": 200, "type": "int"},
    "prior_cancellations_count": {"min": 0, "max": 200, "type": "int"},
    "prior_no_show_rate": {"min": 0.0, "max": 1.0, "type": "float"},
    "days_since_last_appointment": {"min": 0, "max": 3650, "type": "int"},
}

# ─── Model Metadata ───────────────────────────────────────────────────
MODEL_NAME = "MORROW No-Show Predictor"
MODEL_VERSION = "1.0.0"

