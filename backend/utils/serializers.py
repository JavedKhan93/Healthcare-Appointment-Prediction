"""
Serialization Helpers for MongoDB documents, datetimes, and API JSON responses.
"""
import math
from datetime import datetime, date
from bson import ObjectId
import numpy as np


def _serialize_scalar(val):
    if val is None:
        return None
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if val != val:  # catches pandas NaT / NaN
        return None
    return val


def serialize_doc(doc):
    """Recursively convert MongoDB/Pandas document into strict RFC-8259 JSON-serializable object."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if k == "_id" and isinstance(v, ObjectId):
                result["id"] = str(v)
            elif isinstance(v, (dict, list)):
                result[k] = serialize_doc(v)
            else:
                result[k] = _serialize_scalar(v)
        return result
    return _serialize_scalar(doc)

def success_response(data=None, message=None, status_code=200):
    """Standard success response payload."""
    payload = {"status": "success"}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = serialize_doc(data)
    return payload, status_code

def error_response(message="An error occurred", errors=None, status_code=400):
    """Standard error response payload."""
    payload = {"status": "error", "message": message}
    if errors is not None:
        payload["errors"] = errors
    return payload, status_code

