"""
Appointment Records Routes for MORROW.

Provides paginated search, deterministic sorting, date/channel/outcome filtering,
and single-record retrieval for appointment ledger records from MongoDB.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
import pandas as pd
from backend.database import get_db, is_mongodb_connected, get_appointments_df
from backend.utils.serializers import success_response, error_response

appointment_bp = Blueprint("appointment_bp", __name__)

ALLOWED_SORT_COLUMNS = {
    "appointment_id",
    "booking_created_at",
    "appointment_datetime",
    "booking_lead_days",
    "booking_channel",
    "prior_appointments_count",
    "prior_no_show_rate",
    "no_show",
}


@appointment_bp.route("/appointments", methods=["GET"])
def list_appointments():
    """
    Paginated appointment ledger query.
    Query parameters:
      - page: int (default 1)
      - per_page: int (default 20, max 100)
      - search: string (matches appointment_id)
      - booking_channel: string
      - no_show: int (0 or 1)
      - start_date: YYYY-MM-DD (filters appointment_datetime >= start_date)
      - end_date: YYYY-MM-DD (filters appointment_datetime <= end_date 23:59:59)
      - sort_by: string (default appointment_datetime)
      - sort_order: asc | desc (default desc)
    Always uses appointment_id as a deterministic secondary sort key.
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
        search = request.args.get("search", "").strip()
        channel = request.args.get("booking_channel", "").strip()
        no_show_arg = request.args.get("no_show", "").strip()
        start_date_arg = request.args.get("start_date", "").strip()
        end_date_arg = request.args.get("end_date", "").strip()
        sort_by = request.args.get("sort_by", "appointment_datetime").strip()
        if sort_by not in ALLOWED_SORT_COLUMNS:
            sort_by = "appointment_datetime"
        sort_order = request.args.get("sort_order", "desc").lower()

        start_dt = datetime.fromisoformat(start_date_arg) if start_date_arg else None
        end_dt = (
            datetime.fromisoformat(f"{end_date_arg}T23:59:59")
            if end_date_arg and "T" not in end_date_arg
            else (datetime.fromisoformat(end_date_arg) if end_date_arg else None)
        )

        db = get_db()
        if is_mongodb_connected() and db is not None:
            query = {}
            if search:
                query["appointment_id"] = {"$regex": search, "$options": "i"}
            if channel:
                query["booking_channel"] = channel
            if no_show_arg in ("0", "1"):
                query["no_show"] = int(no_show_arg)
            if start_dt or end_dt:
                dt_filter = {}
                if start_dt:
                    dt_filter["$gte"] = start_dt
                if end_dt:
                    dt_filter["$lte"] = end_dt
                query["appointment_datetime"] = dt_filter

            order_dir = -1 if sort_order == "desc" else 1
            total_records = db.appointments.count_documents(query)

            skip = (page - 1) * per_page
            sort_spec = [(sort_by, order_dir)]
            if sort_by != "appointment_id":
                sort_spec.append(("appointment_id", order_dir))

            cursor = (
                db.appointments.find(query)
                .sort(sort_spec)
                .skip(skip)
                .limit(per_page)
            )
            items = list(cursor)

            data = {
                "source": "mongodb",
                "items": items,
                "pagination": {
                    "total": total_records,
                    "page": page,
                    "per_page": per_page,
                    "pages": max(1, (total_records + per_page - 1) // per_page),
                },
            }
            payload, code = success_response(data=data)
            return jsonify(payload), code

        # Fallback using DataFrame when MongoDB is offline
        df = get_appointments_df()
        if df.empty:
            data = {"source": "offline_empty", "items": [], "pagination": {"total": 0, "page": page, "per_page": per_page, "pages": 1}}
            payload, code = success_response(data=data)
            return jsonify(payload), code

        filtered = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(filtered["appointment_datetime"]):
            filtered["appointment_datetime"] = pd.to_datetime(filtered["appointment_datetime"])

        if search:
            filtered = filtered[filtered["appointment_id"].str.contains(search, case=False, na=False)]
        if channel:
            filtered = filtered[filtered["booking_channel"] == channel]
        if no_show_arg in ("0", "1"):
            filtered = filtered[filtered["no_show"] == int(no_show_arg)]
        if start_dt:
            filtered = filtered[filtered["appointment_datetime"] >= pd.Timestamp(start_dt)]
        if end_dt:
            filtered = filtered[filtered["appointment_datetime"] <= pd.Timestamp(end_dt)]

        ascending = sort_order != "desc"
        if sort_by != "appointment_id":
            filtered = filtered.sort_values(
                by=[sort_by, "appointment_id"],
                ascending=[ascending, ascending],
                na_position="last",
            )
        else:
            filtered = filtered.sort_values(by="appointment_id", ascending=ascending)

        total_records = len(filtered)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        sliced = filtered.iloc[start_idx:end_idx]

        items = sliced.to_dict(orient="records")

        data = {
            "source": "offline_fallback",
            "items": items,
            "pagination": {
                "total": total_records,
                "page": page,
                "per_page": per_page,
                "pages": max(1, (total_records + per_page - 1) // per_page),
            },
        }
        payload, code = success_response(data=data)
        return jsonify(payload), code

    except Exception as e:
        payload, code = error_response(message=f"Failed to query appointments: {e}", status_code=500)
        return jsonify(payload), code


@appointment_bp.route("/appointments/<appointment_id>", methods=["GET"])
def get_appointment(appointment_id):
    """Retrieve single appointment record by appointment_id."""
    try:
        db = get_db()
        if is_mongodb_connected() and db is not None:
            doc = db.appointments.find_one({"appointment_id": appointment_id})
            if doc:
                payload, code = success_response(data=doc)
                return jsonify(payload), code

        # Fallback
        df = get_appointments_df()
        match = df[df["appointment_id"] == appointment_id]
        if not match.empty:
            doc = match.iloc[0].to_dict()
            payload, code = success_response(data=doc)
            return jsonify(payload), code

        payload, code = error_response(message=f"Appointment '{appointment_id}' not found", status_code=404)
        return jsonify(payload), code

    except Exception as e:
        payload, code = error_response(message=f"Error retrieving appointment: {e}", status_code=500)
        return jsonify(payload), code

