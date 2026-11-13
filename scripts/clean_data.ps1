# Clean Raw Dataset and Generate Quality Report
$ErrorActionPreference = "Stop"
Write-Host "Running data cleaning pipeline..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m ml.data.clean_dataset

