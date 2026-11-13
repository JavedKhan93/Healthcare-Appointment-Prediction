"""
Dashboard Aggregation Service for MORROW.

Computes operational KPIs and trends across appointments and predictions.
Uses MongoDB aggregations or fallback DataFrame calculations.
"""
import pandas as pd
from backend.database import (
    get_db,
    is_mongodb_connected,
    get_appointments_df,
    get_prediction_logs,
    get_prediction_logs_count,
)


def get_dashboard_summary():
    """
    Computes top-level KPIs: total appointments, attended, no-shows,
    no-show rate, recent appointment activity, and recent predictions count.
    """
    db = get_db()
    if is_mongodb_connected() and db is not None:
        try:
            total = db.appointments.count_documents({})
            no_show = db.appointments.count_documents({"no_show": 1})
            attended = db.appointments.count_documents({"no_show": 0})
            recent_preds = list(db.prediction_logs.find().sort("created_at", -1).limit(5))
            recent_appts = list(db.appointments.find({}, {"_id": 0}).sort("appointment_datetime", -1).limit(5))
            pred_count = db.prediction_logs.count_documents({})

            rate = (no_show / total * 100) if total > 0 else 0.0

            return {
                "total_appointments": total,
                "attended_appointments": attended,
                "no_show_appointments": no_show,
                "no_show_rate_percent": round(rate, 2),
                "total_predictions_logged": pred_count,
                "recent_predictions": recent_preds,
                "recent_appointments": recent_appts,
            }
        except Exception as e:
            print(f"! Error in MongoDB dashboard summary: {e}")

    # Fallback using DataFrame
    df = get_appointments_df()
    if df.empty:
        return {
            "total_appointments": 0,
            "attended_appointments": 0,
            "no_show_appointments": 0,
            "no_show_rate_percent": 0.0,
            "total_predictions_logged": 0,
            "recent_predictions": [],
            "recent_appointments": [],
        }

    total = len(df)
    no_show = int((df["no_show"] == 1).sum())
    attended = int((df["no_show"] == 0).sum())
    rate = (no_show / total * 100) if total > 0 else 0.0
    recent_preds = get_prediction_logs(limit=5)
    pred_count = get_prediction_logs_count()
    recent_appts = df.sort_values("appointment_datetime", ascending=False).head(5).to_dict(orient="records")

    return {
        "total_appointments": total,
        "attended_appointments": attended,
        "no_show_appointments": no_show,
        "no_show_rate_percent": round(rate, 2),
        "total_predictions_logged": pred_count,
        "recent_predictions": recent_preds,
        "recent_appointments": recent_appts,
    }


def get_dashboard_trends():
    """
    Computes distribution and trend data for Chart.js visual components:
    - Attendance distribution
    - No-show rate by weekday (Mon-Sun)
    - No-show rate by booking channel
    - Hourly appointment volume and no-show rate
    - Monthly appointment activity over time

    Uses native MongoDB aggregation pipelines when connected, falling back to
    identical DataFrame aggregations only when MongoDB is offline.
    """
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    db = get_db()

    if is_mongodb_connected() and db is not None:
        try:
            # 1. Attendance distribution via MongoDB aggregation
            att_agg = list(db.appointments.aggregate([
                {"$group": {"_id": "$no_show", "count": {"$sum": 1}}}
            ]))
            att_map = {doc["_id"]: doc["count"] for doc in att_agg}
            attended_count = int(att_map.get(0, 0))
            noshow_count = int(att_map.get(1, 0))

            # 2. By weekday via MongoDB aggregation
            wd_agg = list(db.appointments.aggregate([
                {"$group": {
                    "_id": "$appointment_weekday",
                    "total": {"$sum": 1},
                    "no_shows": {"$sum": "$no_show"},
                }},
                {"$sort": {"_id": 1}},
            ]))
            wd_map = {doc["_id"]: doc for doc in wd_agg}
            by_weekday = []
            for d in range(7):
                doc = wd_map.get(d)
                total = int(doc["total"]) if doc else 0
                no_shows = int(doc["no_shows"]) if doc else 0
                rate = round((no_shows / total) * 100, 2) if total > 0 else 0.0
                by_weekday.append({
                    "day_index": d,
                    "day_name": day_names[d],
                    "total": total,
                    "no_shows": no_shows,
                    "rate": rate,
                })

            # 3. By booking channel via MongoDB aggregation
            ch_agg = list(db.appointments.aggregate([
                {"$match": {"booking_channel": {"$ne": None}}},
                {"$group": {
                    "_id": "$booking_channel",
                    "total": {"$sum": 1},
                    "no_shows": {"$sum": "$no_show"},
                }},
                {"$sort": {"_id": 1}},
            ]))
            by_channel = []
            for doc in ch_agg:
                total = int(doc["total"])
                no_shows = int(doc["no_shows"])
                rate = round((no_shows / total) * 100, 2) if total > 0 else 0.0
                by_channel.append({
                    "channel": str(doc["_id"]),
                    "total": total,
                    "no_shows": no_shows,
                    "rate": rate,
                })

            # 4. By appointment hour via MongoDB aggregation
            hr_agg = list(db.appointments.aggregate([
                {"$group": {
                    "_id": "$appointment_hour",
                    "total": {"$sum": 1},
                    "no_shows": {"$sum": "$no_show"},
                }},
                {"$sort": {"_id": 1}},
            ]))
            by_hour = []
            for doc in hr_agg:
                total = int(doc["total"])
                no_shows = int(doc["no_shows"])
                rate = round((no_shows / total) * 100, 2) if total > 0 else 0.0
                h = int(doc["_id"])
                by_hour.append({
                    "hour": h,
                    "label": f"{h:02d}:00",
                    "total": total,
                    "no_shows": no_shows,
                    "rate": rate,
                })

            # 5. Monthly activity over time via MongoDB aggregation
            mo_agg = list(db.appointments.aggregate([
                {"$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m", "date": "$appointment_datetime"}},
                    "total": {"$sum": 1},
                    "no_shows": {"$sum": "$no_show"},
                }},
                {"$sort": {"_id": 1}},
            ]))
            by_month = []
            for doc in mo_agg:
                total = int(doc["total"])
                no_shows = int(doc["no_shows"])
                rate = round((no_shows / total) * 100, 2) if total > 0 else 0.0
                by_month.append({
                    "month": str(doc["_id"]),
                    "total": total,
                    "no_shows": no_shows,
                    "rate": rate,
                })

            return {
                "source": "mongodb",
                "attendance_distribution": {
                    "attended": attended_count,
                    "no_show": noshow_count,
                    "total": attended_count + noshow_count,
                },
                "by_weekday": by_weekday,
                "by_channel": by_channel,
                "by_hour": by_hour,
                "by_month": by_month,
            }
        except Exception as e:
            print(f"! Error in MongoDB dashboard trends aggregation: {e}")

    # Fallback using DataFrame when MongoDB is offline
    df = get_appointments_df()
    if df.empty:
        return {
            "source": "offline_empty",
            "attendance_distribution": {"attended": 0, "no_show": 0, "total": 0},
            "by_weekday": [],
            "by_channel": [],
            "by_hour": [],
            "by_month": [],
        }

    if not pd.api.types.is_datetime64_any_dtype(df["booking_created_at"]):
        df["booking_created_at"] = pd.to_datetime(df["booking_created_at"])
    if not pd.api.types.is_datetime64_any_dtype(df["appointment_datetime"]):
        df["appointment_datetime"] = pd.to_datetime(df["appointment_datetime"])

    attended_count = int((df["no_show"] == 0).sum())
    noshow_count = int((df["no_show"] == 1).sum())

    weekday_summary = (
        df.groupby("appointment_weekday")
        .agg(total=("no_show", "count"), no_shows=("no_show", "sum"))
        .reset_index()
    )
    by_weekday = []
    for d in range(7):
        row = weekday_summary[weekday_summary["appointment_weekday"] == d]
        total = int(row["total"].iloc[0]) if not row.empty else 0
        no_shows = int(row["no_shows"].iloc[0]) if not row.empty else 0
        rate = round((no_shows / total) * 100, 2) if total > 0 else 0.0
        by_weekday.append({
            "day_index": d,
            "day_name": day_names[d],
            "total": total,
            "no_shows": no_shows,
            "rate": rate,
        })

    channel_summary = (
        df.dropna(subset=["booking_channel"])
        .groupby("booking_channel")
        .agg(total=("no_show", "count"), no_shows=("no_show", "sum"))
        .reset_index()
        .sort_values("booking_channel")
    )
    by_channel = []
    for _, r in channel_summary.iterrows():
        total = int(r["total"])
        no_shows = int(r["no_shows"])
        by_channel.append({
            "channel": str(r["booking_channel"]),
            "total": total,
            "no_shows": no_shows,
            "rate": round((no_shows / total) * 100, 2) if total > 0 else 0.0,
        })

    hour_summary = (
        df.groupby("appointment_hour")
        .agg(total=("no_show", "count"), no_shows=("no_show", "sum"))
        .reset_index()
        .sort_values("appointment_hour")
    )
    by_hour = []
    for _, r in hour_summary.iterrows():
        total = int(r["total"])
        no_shows = int(r["no_shows"])
        by_hour.append({
            "hour": int(r["appointment_hour"]),
            "label": f"{int(r['appointment_hour']):02d}:00",
            "total": total,
            "no_shows": no_shows,
            "rate": round((no_shows / total) * 100, 2) if total > 0 else 0.0,
        })

    df_mo = df.copy()
    df_mo["month"] = df_mo["appointment_datetime"].dt.strftime("%Y-%m")
    mo_summary = (
        df_mo.groupby("month")
        .agg(total=("no_show", "count"), no_shows=("no_show", "sum"))
        .reset_index()
        .sort_values("month")
    )
    by_month = []
    for _, r in mo_summary.iterrows():
        total = int(r["total"])
        no_shows = int(r["no_shows"])
        by_month.append({
            "month": str(r["month"]),
            "total": total,
            "no_shows": no_shows,
            "rate": round((no_shows / total) * 100, 2) if total > 0 else 0.0,
        })

    return {
        "source": "offline_fallback",
        "attendance_distribution": {
            "attended": attended_count,
            "no_show": noshow_count,
            "total": attended_count + noshow_count,
        },
        "by_weekday": by_weekday,
        "by_channel": by_channel,
        "by_hour": by_hour,
        "by_month": by_month,
    }

