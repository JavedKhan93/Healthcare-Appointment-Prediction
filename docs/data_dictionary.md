# Data Dictionary — MORROW Synthetic Appointment Dataset

> **Provenance Notice:** This dataset is 100% synthetic, generated locally by `ml/data/generate_synthetic_data.py` with `random_seed = 42`. It does **not** represent measured clinical patient attendance behavior or actual hospital records.

---

## 1. Column Specifications

| # | Column Name | Data Type | Available at Prediction Time? | Description | Example Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `appointment_id` | String | Identifier Only | Unique sequential appointment record identifier. | `APT-000142` |
| 2 | `booking_created_at` | Datetime (`datetime64[ns]`) | Split Only (Not Model Input) | Timestamp when booking was created; used strictly for chronological 70/15/15 splitting. | `2023-05-14 09:20:00` |
| 3 | `appointment_datetime` | Datetime (`datetime64[ns]`) | Reference Only | Scheduled appointment date and time. | `2023-05-28 10:30:00` |
| 4 | `booking_lead_days` | Float / Int (`0–365`) | **Yes (Model Feature)** | Days elapsed between booking creation and scheduled visit. | `14` |
| 5 | `appointment_weekday` | Int (`0–6`) | **Yes (Model Feature)** | Day of week of scheduled appointment (`0=Monday` to `6=Sunday`). | `4` |
| 6 | `appointment_hour` | Int (`6–21`) | **Yes (Model Feature)** | Hour of day of scheduled clinic appointment. | `10` |
| 7 | `booking_hour` | Int (`0–23`) | **Yes (Model Feature)** | Hour of day when reservation was created. | `9` |
| 8 | `booking_channel` | String (`online`, `phone`, `in_person`) | **Yes (Model Feature)** | Booking origin channel standardized to lowercase enum. | `online` |
| 9 | `prior_appointments_count` | Float / Int (`>= 0`) | **Yes (Model Feature)** | Count of earlier completed appointments for the simulated entity before this booking. | `3` |
| 10 | `prior_no_show_count` | Float / Int (`>= 0`) | **Yes (Model Feature)** | Count of historical missed appointments prior to this booking. | `1` |
| 11 | `prior_cancellations_count` | Float / Int (`>= 0`) | **Yes (Model Feature)** | Count of prior cancelled appointments prior to this booking. | `0` |
| 12 | `prior_no_show_rate` | Float (`0.0–1.0`) | **Yes (Model Feature)** | Ratio of `prior_no_show_count / prior_appointments_count` (`0.0` if first visit). | `0.3333` |
| 13 | `days_since_last_appointment` | Float / Int (`>= 0`) | **Yes (Model Feature)** | Calendar days elapsed since the prior scheduled visit (`0` if first visit). | `45` |
| 14 | `no_show` | Binary (`0` or `1`) | **Target Variable (Prohibited Input)** | `0 = Attended`, `1 = No-Show`. Excluded from inference inputs. | `0` |

---

## 2. Synthetic Generation Assumptions & Leakage Controls

1. **Sequential Entity Simulation:** During generation, 2,500 simulated patient trajectories are walked forward chronologically across 2023–2024 (`9,955` clean appointments). Each appointment's historical counts derive strictly from earlier appointments.
2. **Key Stripping:** The temporary `patient_key` is discarded prior to exporting `data/raw/synthetic_appointments_raw.csv`. It is never stored in MongoDB or passed to ML models.
3. **Probabilistic Target (`no_show`):** Outcomes are sampled from Bernoulli trials governed by patient base risk (`Beta(2, 5)`), lead time, weekday, clinic hour, booking channel, prior history, and zero-mean Gaussian noise (`Normal(0, 0.08)`), clipped to `[0.05, 0.65]`. No single feature deterministically dictates the label.
4. **Controlled Quality Issues:** `50` duplicate rows, `28` numerical NaNs, `20` categorical NaNs, `15` inconsistent channel strings (`ONLINE`, `telephone`, `in-person`), `10` negative counts (`-1`), and `5` impossible timestamps (`booking_created_at > appointment_datetime`) were injected into the raw CSV to exercise the automated cleaning pipeline.

