"""
Synthetic Hospital Appointment Dataset Generator for MORROW.

Generates ~10,000 fictional appointment records with realistic patterns.
The target (no_show) is generated probabilistically — no single feature
deterministically reveals it.

Dataset source: entirely synthetic.  No actual patient data is used.

Usage:
    python -m ml.data.generate_synthetic_data
"""
import os
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ml.config import (
    RANDOM_SEED,
    NUM_PATIENTS,
    NUM_APPOINTMENTS,
    DATE_START,
    DATE_END,
    BOOKING_CHANNELS,
    RAW_DATA_PATH,
    DATA_RAW_DIR,
)


def _patient_base_risk(rng: np.random.Generator) -> float:
    """Return a latent per-patient base no-show propensity in [0, 1]."""
    # Most patients are reliable; a minority have elevated risk
    return rng.beta(a=2, b=5)


def generate_synthetic_data(
    n_patients: int = NUM_PATIENTS,
    n_appointments: int = NUM_APPOINTMENTS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate a synthetic appointment dataset.

    The generation process:
    1.  Create a pool of fictional patients, each with a latent base risk.
    2.  For each patient, generate a sequence of appointments over time.
    3.  Historical features (prior_appointments_count, prior_no_show_count, etc.)
        are derived from the patient's earlier completed appointments.
    4.  The no-show probability for each appointment is a function of
        multiple features plus random noise, so no single feature is
        deterministic.
    5.  Controlled data-quality issues are injected into a small fraction
        of records.

    Parameters
    ----------
    n_patients : int
        Number of fictional patients.
    n_appointments : int
        Approximate total number of appointment records.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Raw synthetic dataset with controlled quality issues.
    """
    rng = np.random.default_rng(seed)

    start_date = pd.Timestamp(DATE_START)
    end_date = pd.Timestamp(DATE_END)
    date_range_days = (end_date - start_date).days

    # ── 1. Create patients ────────────────────────────────────────────
    patients = []
    for _ in range(n_patients):
        patients.append({
            "patient_key": str(uuid.uuid4()),
            "base_risk": _patient_base_risk(rng),
            "preferred_channel": rng.choice(
                BOOKING_CHANNELS, p=[0.50, 0.30, 0.20]
            ),
        })

    # How many appointments per patient (geometric-like distribution)
    appts_per_patient = rng.negative_binomial(n=3, p=0.4, size=n_patients) + 1
    total = appts_per_patient.sum()
    # Scale to approximate target
    scale = n_appointments / total
    appts_per_patient = np.maximum(
        1, np.round(appts_per_patient * scale).astype(int)
    )

    # ── 2. Generate appointment sequences ─────────────────────────────
    records = []
    for idx, pat in enumerate(patients):
        n_appts = int(appts_per_patient[idx])
        patient_key = pat["patient_key"]
        base_risk = pat["base_risk"]
        preferred_channel = pat["preferred_channel"]

        # Sort appointment times chronologically for this patient
        appt_offsets = sorted(rng.integers(0, date_range_days, size=n_appts))

        # Track history for this patient
        completed = 0
        no_shows = 0
        cancellations = 0
        last_appt_date = None

        for j, offset in enumerate(appt_offsets):
            appt_date = start_date + timedelta(days=int(offset))

            # Appointment hour (weighted toward business hours)
            hour_weights = np.zeros(24)
            for h in range(7, 20):
                hour_weights[h] = 1.0
            hour_weights[9:12] = 3.0   # Morning peak
            hour_weights[14:17] = 2.0  # Afternoon peak
            hour_weights /= hour_weights.sum()
            appt_hour = int(rng.choice(24, p=hour_weights))

            appt_datetime = appt_date.replace(
                hour=appt_hour, minute=int(rng.choice([0, 15, 30, 45]))
            )

            # Booking lead days (most 1-60, occasional longer)
            lead_days = int(rng.exponential(scale=14)) + 1
            lead_days = min(lead_days, 180)

            booking_datetime = appt_datetime - timedelta(days=lead_days)
            booking_hour = int(rng.integers(7, 22))
            booking_datetime = booking_datetime.replace(
                hour=booking_hour,
                minute=int(rng.choice([0, 10, 20, 30, 40, 50])),
            )

            # Booking channel (slight preference for patient's preferred)
            channel_probs = np.array([0.33, 0.33, 0.34])
            pref_idx = BOOKING_CHANNELS.index(preferred_channel)
            channel_probs[pref_idx] += 0.20
            channel_probs /= channel_probs.sum()
            channel = rng.choice(BOOKING_CHANNELS, p=channel_probs)

            # Historical features (from prior completed appointments)
            prior_appts = completed
            prior_no_shows = no_shows
            prior_cancels = cancellations
            prior_no_show_rate = (
                prior_no_shows / prior_appts if prior_appts > 0 else 0.0
            )

            if last_appt_date is not None:
                days_since_last = max(
                    0, (appt_date - last_appt_date).days
                )
            else:
                days_since_last = 0  # First appointment

            # ── Compute no-show probability ───────────────────────────
            # Base risk from patient profile
            prob = base_risk * 0.35

            # Lead time effect: very short or very long → higher risk
            if lead_days <= 2:
                prob += 0.05
            elif lead_days > 60:
                prob += rng.uniform(0.03, 0.10)

            # Day-of-week effect: Friday/Monday slightly higher
            weekday = appt_datetime.weekday()
            if weekday in (0, 4):  # Monday, Friday
                prob += 0.03
            elif weekday == 5:  # Saturday (rare)
                prob += 0.05

            # Time-of-day effect
            if appt_hour < 8 or appt_hour >= 18:
                prob += 0.04

            # Historical behaviour (strongest signal, but still noisy)
            if prior_appts >= 3:
                prob += prior_no_show_rate * 0.25

            # First-time patient effect
            if prior_appts == 0:
                prob += 0.05

            # Booking channel effect
            if channel == "online":
                prob += 0.02
            elif channel == "in_person":
                prob -= 0.02

            # Long gap since last appointment
            if days_since_last > 180 and prior_appts > 0:
                prob += 0.04

            # Random noise (ensures no deterministic rule)
            prob += rng.normal(0, 0.08)

            # Clamp to valid probability range
            prob = float(np.clip(prob, 0.05, 0.65))

            # Determine outcome
            no_show = int(rng.random() < prob)

            # Cancellation (separate from no-show; small fraction)
            is_cancelled = int(rng.random() < 0.05) if no_show == 0 else 0

            # Build record
            records.append({
                "appointment_id": f"APT-{len(records)+1:06d}",
                "patient_key": patient_key,  # will be removed later
                "booking_created_at": booking_datetime,
                "appointment_datetime": appt_datetime,
                "booking_lead_days": lead_days,
                "appointment_weekday": weekday,
                "appointment_hour": appt_hour,
                "booking_hour": booking_hour,
                "booking_channel": channel,
                "prior_appointments_count": prior_appts,
                "prior_no_show_count": prior_no_shows,
                "prior_cancellations_count": prior_cancels,
                "prior_no_show_rate": round(prior_no_show_rate, 4),
                "days_since_last_appointment": days_since_last,
                "no_show": no_show,
            })

            # Update patient history
            completed += 1
            if no_show == 1:
                no_shows += 1
            if is_cancelled:
                cancellations += 1
            last_appt_date = appt_date

    df = pd.DataFrame(records)

    # Remove internal patient key — must never be a model feature
    df = df.drop(columns=["patient_key"])

    # Sort by booking_created_at for chronological ordering
    df = df.sort_values("booking_created_at").reset_index(drop=True)

    # Re-assign sequential appointment IDs after sorting
    df["appointment_id"] = [f"APT-{i+1:06d}" for i in range(len(df))]

    print(f"Generated {len(df)} synthetic appointment records")
    print(f"No-show rate: {df['no_show'].mean():.2%}")
    print(f"Date range: {df['booking_created_at'].min()} to {df['booking_created_at'].max()}")

    return df


def inject_quality_issues(df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Inject controlled data-quality issues for cleaning demonstration.

    Issues introduced:
    1.  ~50 duplicate records
    2.  ~30 missing numerical values
    3.  ~20 missing categorical values
    4.  ~15 inconsistent category formatting
    5.  ~10 invalid negative historical counts
    6.  ~5  impossible timestamp relationships (booking after appointment)

    Parameters
    ----------
    df : pd.DataFrame
        Clean synthetic dataset.
    seed : int
        Random seed.

    Returns
    -------
    pd.DataFrame
        Dataset with controlled quality issues.
    """
    rng = np.random.default_rng(seed + 1)
    dirty = df.copy()
    n = len(dirty)

    # 1. Duplicate records (~50)
    dup_indices = rng.choice(n, size=50, replace=False)
    duplicates = dirty.iloc[dup_indices].copy()
    dirty = pd.concat([dirty, duplicates], ignore_index=True)
    print(f"Injected {len(duplicates)} duplicate records")

    # 2. Missing numerical values (~30)
    num_cols = [
        "booking_lead_days", "prior_appointments_count",
        "days_since_last_appointment", "prior_no_show_rate",
    ]
    for col in num_cols:
        miss_idx = rng.choice(len(dirty), size=7, replace=False)
        dirty.loc[miss_idx, col] = np.nan
    print("Injected ~28 missing numerical values")

    # 3. Missing categorical values (~20)
    miss_cat_idx = rng.choice(len(dirty), size=20, replace=False)
    dirty.loc[miss_cat_idx, "booking_channel"] = np.nan
    print("Injected 20 missing categorical values")

    # 4. Inconsistent category formatting (~15)
    format_idx = rng.choice(len(dirty), size=15, replace=False)
    format_map = {
        "online": ["Online", "ONLINE", "on-line"],
        "phone": ["Phone", "PHONE", "telephone"],
        "in_person": ["In_Person", "IN_PERSON", "in-person", "walk_in"],
    }
    for idx in format_idx:
        current = dirty.loc[idx, "booking_channel"]
        if pd.notna(current) and current in format_map:
            dirty.loc[idx, "booking_channel"] = rng.choice(format_map[current])
    print("Injected ~15 inconsistent category formats")

    # 5. Invalid negative counts (~10)
    neg_cols = ["prior_no_show_count", "prior_cancellations_count"]
    for col in neg_cols:
        neg_idx = rng.choice(len(dirty), size=5, replace=False)
        dirty.loc[neg_idx, col] = -1
    print("Injected ~10 invalid negative counts")

    # 6. Impossible timestamp relationships (~5)
    ts_idx = rng.choice(len(dirty), size=5, replace=False)
    for idx in ts_idx:
        # Set booking date AFTER appointment date (impossible)
        appt_dt = dirty.loc[idx, "appointment_datetime"]
        if pd.notna(appt_dt):
            dirty.loc[idx, "booking_created_at"] = appt_dt + timedelta(days=int(rng.integers(1, 30)))
    print("Injected 5 impossible timestamp relationships")

    # Shuffle to mix issues throughout
    dirty = dirty.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    return dirty


def main():
    """Generate and save the raw synthetic dataset."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)

    print("=" * 60)
    print("MORROW — Synthetic Dataset Generation")
    print("=" * 60)
    print()

    # Generate clean synthetic data
    df_clean = generate_synthetic_data()
    print()

    # Inject quality issues
    df_raw = inject_quality_issues(df_clean)
    print()

    # Save raw dataset
    df_raw.to_csv(RAW_DATA_PATH, index=False)
    print(f"Saved raw dataset to: {RAW_DATA_PATH}")
    print(f"Final raw record count: {len(df_raw)}")
    print(f"Columns: {list(df_raw.columns)}")
    print()

    # Summary statistics
    print("─" * 40)
    print("Dataset Summary:")
    print(f"  Total records:    {len(df_raw)}")
    print(f"  Unique appt IDs: {df_raw['appointment_id'].nunique()}")
    print(f"  No-show rate:    {df_raw['no_show'].mean():.2%}")
    print(f"  Missing values:  {df_raw.isnull().sum().sum()}")
    print(f"  Negative counts: {(df_raw[['prior_no_show_count','prior_cancellations_count']] < 0).sum().sum()}")
    print("─" * 40)


if __name__ == "__main__":
    main()

