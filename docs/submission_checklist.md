# ALGIONS Submission Checklist — MORROW

- **Candidate Identification:** `[To be completed by candidate]`
- **Internship Role:** AI & Machine Learning Intern
- **Assigning Organization:** ALGIONS AI LABS PRIVATE LIMITED
- **Exact Project Name:** MORROW — Appointment Operations & No-Show Intelligence
- **GitHub Repository URL:** `[To be completed after pushing to GitHub]`
- **Primary Branch:** `main`
- **Final Commit ID:** `[To be completed after final git commit]`
- **Demo Video Link:** `[To be completed after recording 3–5 min demo using docs/demo_script.md]`

## Core Deliverables Verification
- [x] **README:** Complete setup, architecture, metrics, and API docs (`README.md`)
- [x] **Technical Report:** 24-section report with empirical metrics & walkthrough (`docs/technical_report.md`)
- [x] **Dataset Source:** Custom synthetic generator (`ml/data/generate_synthetic_data.py`, `random_seed=42`)
- [x] **Cleaned Dataset & Audit:** `data/processed/synthetic_appointments_cleaned.csv` & `artifacts/metrics/data_quality_report.json`
- [x] **Model Artifact:** Saved Joblib pipeline (`artifacts/models/no_show_pipeline.joblib`)
- [x] **Technology Stack:** Python 3.13, Scikit-learn, Pandas, NumPy, Flask, PyMongo, MongoDB, React 18, Vite, Chart.js, Pytest
- [x] **Backend & Frontend Integration:** Verified end-to-end via Vite proxy + Flask REST API + ML inference
- [x] **Automated Tests:** 19/19 Pytest tests passing + Vite production build passing
- [x] **Documentation Package:** `architecture.md`, `data_dictionary.md`, `model_card.md`, `responsible_ai.md`, `demo_script.md`, `interview_preparation.md`

## Known Limitations & Disclosures
- **Known Limitations:** Synthetic data provenance; moderate ROC-AUC (`0.6044`) reflecting overlapping uncertainty; illustrative `$5` vs `$50` cost matrix; local fallback mode active when MongoDB daemon is not running.
- **Library & Dataset Attribution:** Scikit-learn, Pandas, NumPy, Flask, PyMongo, React, Chart.js, Lucide React; zero external patient datasets used.
- **Originality & AI Tool Disclosure:** `[Candidate to complete AI tool disclosure statement as required by ALGIONS form]`

