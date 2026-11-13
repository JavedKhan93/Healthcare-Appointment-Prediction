# Run Complete ML Pipeline: EDA -> Compare -> Train -> Threshold -> Evaluate
$ErrorActionPreference = "Stop"
Write-Host "1/5 Running Exploratory Data Analysis..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m ml.eda.analyze_dataset

Write-Host "2/5 Comparing Candidate Models..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m ml.training.compare_models

Write-Host "3/5 Training & Calibrating Selected Model..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m ml.training.train

Write-Host "4/5 Running Threshold & Cost Analysis..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m ml.training.threshold_analysis

Write-Host "5/5 Evaluating on Held-Out Chronological Test Set..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m ml.training.evaluate

Write-Host "All ML pipeline stages completed successfully." -ForegroundColor Green

