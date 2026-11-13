"""
Database Management Layer for MORROW.

Connects to MongoDB using PyMongo with automatic index creation and idempotent seeding.
Provides graceful fallback mechanisms if MongoDB is offline, ensuring reliable API service.
"""
import os
import json
import uuid
from datetime import datetime
import pandas as pd
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING

from backend.config import Config

_CLIENT = None
_DB = None
_IS_CONNECTED = False

# Fallback in-memory storage for predictions when MongoDB is offline
_LOCAL_PREDICTIONS = []
_LOCAL_APPOINTMENTS_CACHE = None


def get_db():
    """Return active MongoDB database instance, or None if unavailable."""
    global _DB
    return _DB


def is_mongodb_connected():
    """Return True if MongoDB connection is active."""
    global _IS_CONNECTED
    return _IS_CONNECTED


def ping_mongodb() -> dict:
    """
    Execute a live MongoDB ping check and return connectivity status & collection counts.
    """
    global _CLIENT, _DB, _IS_CONNECTED
    if _CLIENT is None or _DB is None:
        # Attempt reconnection in case MongoDB started after Flask
        try:
            _CLIENT = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=500,
                connectTimeoutMS=500,
            )
            _CLIENT.admin.command("ping")
            _DB = _CLIENT[Config.MONGODB_DATABASE]
            _IS_CONNECTED = True
            _setup_indexes(_DB)
            seed_database(_DB)
        except Exception as e:
            _IS_CONNECTED = False
            _CLIENT = None
            _DB = None
            return {"connected": False, "error": str(e)}

    try:
        _CLIENT.admin.command("ping")
        _IS_CONNECTED = True
        collections = _DB.list_collection_names()
        return {
            "connected": True,
            "collections": collections,
            "appointments_count": _DB.appointments.count_documents({}),
            "prediction_logs_count": _DB.prediction_logs.count_documents({}),
        }
    except Exception as e:
        _IS_CONNECTED = False
        _CLIENT = None
        _DB = None
        return {"connected": False, "error": str(e)}


def init_db(app=None):
    """
    Initialize MongoDB client, check connectivity, and setup collections & indexes.
    """
    global _CLIENT, _DB, _IS_CONNECTED

    uri = Config.MONGODB_URI
    db_name = Config.MONGODB_DATABASE

    try:
        _CLIENT = MongoClient(uri, serverSelectionTimeoutMS=1000, connectTimeoutMS=1000)
        # Verify connection
        _CLIENT.admin.command("ping")
        _DB = _CLIENT[db_name]
        _IS_CONNECTED = True
        print(f"✓ Connected to MongoDB database: '{db_name}' at {uri}")

        # Setup indexes
        _setup_indexes(_DB)

        # Idempotent seed
        seed_database(_DB)

    except Exception as e:
        _IS_CONNECTED = False
        _CLIENT = None
        _DB = None
        print(f"! Notice: MongoDB is not available ({e}). Using local high-performance fallback store.")
        # Preload local appointments cache
        _load_local_appointments()

    return _DB


def _setup_indexes(db):
    """Create optimal database indexes."""
    try:
        # Appointments indexes
        db.appointments.create_index([("appointment_id", ASCENDING)], unique=True)
        db.appointments.create_index([("booking_created_at", ASCENDING)])
        db.appointments.create_index([("appointment_datetime", ASCENDING)])
        db.appointments.create_index([("booking_channel", ASCENDING)])
        db.appointments.create_index([("no_show", ASCENDING)])

        # Prediction logs indexes
        db.prediction_logs.create_index([("prediction_id", ASCENDING)], unique=True)
        db.prediction_logs.create_index([("created_at", DESCENDING)])

        print("✓ MongoDB indexes established.")
    except Exception as e:
        print(f"! Warning creating indexes: {e}")


def seed_database(db=None):
    """
    Idempotent database seeding.
    Populates appointments collection from cleaned dataset only if collection is empty.
    """
    if db is None:
        db = _DB

    if db is None or not _IS_CONNECTED:
        print("Skipping MongoDB seed: Database not connected.")
        return

    try:
        count = db.appointments.count_documents({})
        if count == 0:
            csv_path = Config.CLEANED_DATA_PATH
            if not os.path.exists(csv_path):
                print(f"Cleaned dataset not found at '{csv_path}'. Cannot seed.")
            else:
                print(f"Seeding MongoDB from: {csv_path}...")
                df = pd.read_csv(csv_path, parse_dates=["booking_created_at", "appointment_datetime"])

                records = df.to_dict(orient="records")
                for rec in records:
                    # Ensure proper datetime objects and native Python None for NaN
                    for k, v in list(rec.items()):
                        if pd.isna(v):
                            rec[k] = None
                    if isinstance(rec["booking_created_at"], pd.Timestamp):
                        rec["booking_created_at"] = rec["booking_created_at"].to_pydatetime()
                    if isinstance(rec["appointment_datetime"], pd.Timestamp):
                        rec["appointment_datetime"] = rec["appointment_datetime"].to_pydatetime()

                db.appointments.insert_many(records, ordered=False)
                print(f"✓ Successfully seeded {len(records)} appointment records into MongoDB.")
        else:
            print(f"MongoDB already contains {count} appointment records. Skipping appointment seeding.")

        # Idempotently seed/upsert model metadata
        meta_path = os.path.join(Config.METRICS_DIR, "model_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            db.model_metadata.update_one(
                {"model_name": meta.get("model_name"), "model_version": meta.get("model_version")},
                {"$set": meta},
                upsert=True,
            )

        # Idempotently seed/upsert latest data quality report
        dq_path = os.path.join(Config.METRICS_DIR, "data_quality_report.json")
        if os.path.exists(dq_path):
            with open(dq_path, "r") as f:
                dq = json.load(f)
            db.data_quality_reports.update_one(
                {"generated_at": dq.get("generated_at")},
                {"$set": dq},
                upsert=True,
            )

    except Exception as e:
        print(f"! Error during database seeding: {e}")


def _load_local_appointments():
    """Load local dataframe for fallback mode."""
    global _LOCAL_APPOINTMENTS_CACHE
    csv_path = Config.CLEANED_DATA_PATH
    if os.path.exists(csv_path):
        _LOCAL_APPOINTMENTS_CACHE = pd.read_csv(
            csv_path, parse_dates=["booking_created_at", "appointment_datetime"]
        )
        print(f"✓ Loaded {len(_LOCAL_APPOINTMENTS_CACHE)} records into local fallback cache.")


def save_prediction_log(log_entry: dict):
    """Save prediction log to MongoDB or local storage."""
    log_entry["created_at"] = datetime.now()
    if "prediction_id" not in log_entry:
        log_entry["prediction_id"] = f"PRD-{uuid.uuid4().hex[:8].upper()}"

    if _IS_CONNECTED and _DB is not None:
        try:
            _DB.prediction_logs.insert_one(log_entry)
            return log_entry
        except Exception as e:
            print(f"! Failed to save prediction to MongoDB: {e}")

    # Fallback storage
    _LOCAL_PREDICTIONS.insert(0, log_entry)
    # Keep up to 500 in memory
    if len(_LOCAL_PREDICTIONS) > 500:
        _LOCAL_PREDICTIONS.pop()

    return log_entry


def get_prediction_logs(limit: int = 50, skip: int = 0):
    """Retrieve historical prediction logs."""
    if _IS_CONNECTED and _DB is not None:
        try:
            cursor = _DB.prediction_logs.find().sort("created_at", DESCENDING).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"! Error querying MongoDB prediction logs: {e}")

    # Fallback
    return _LOCAL_PREDICTIONS[skip : skip + limit]


def get_prediction_logs_count() -> int:
    """Return total number of logged predictions."""
    if _IS_CONNECTED and _DB is not None:
        try:
            return int(_DB.prediction_logs.count_documents({}))
        except Exception:
            pass
    return len(_LOCAL_PREDICTIONS)


def get_appointments_df():
    """Retrieve full appointments DataFrame (from MongoDB when connected, or CSV fallback)."""
    global _LOCAL_APPOINTMENTS_CACHE
    if _IS_CONNECTED and _DB is not None:
        try:
            cursor = _DB.appointments.find({}, {"_id": 0})
            df = pd.DataFrame(list(cursor))
            return df
        except Exception as e:
            print(f"! Error fetching appointments from MongoDB: {e}")

    if _LOCAL_APPOINTMENTS_CACHE is not None:
        return _LOCAL_APPOINTMENTS_CACHE

    csv_path = Config.CLEANED_DATA_PATH
    if os.path.exists(csv_path):
        _LOCAL_APPOINTMENTS_CACHE = pd.read_csv(
            csv_path, parse_dates=["booking_created_at", "appointment_datetime"]
        )
        return _LOCAL_APPOINTMENTS_CACHE

    return pd.DataFrame()

