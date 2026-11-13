"""
Backend Configuration for MORROW Hospital No-Show Intelligence.
"""
import os
from dotenv import load_dotenv

# Load .env if present
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

class Config:
    PROJECT_ROOT = PROJECT_ROOT
    SECRET_KEY = os.getenv("SECRET_KEY", "morrow_hospital_secret_key_dev_2026")
    
    # MongoDB Config
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "morrow_hospital")
    
    # Server Config
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")
    
    # Artifact paths
    ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")
    MODEL_PATH = os.path.join(ARTIFACTS_DIR, "models", "no_show_pipeline.joblib")
    METRICS_DIR = os.path.join(ARTIFACTS_DIR, "metrics")
    FIGURES_DIR = os.path.join(ARTIFACTS_DIR, "figures")
    
    # Data paths
    CLEANED_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "synthetic_appointments_cleaned.csv")
    RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "synthetic_appointments_raw.csv")

