# Generate Synthetic Dataset for MORROW
$ErrorActionPreference = "Stop"
Write-Host "Running synthetic dataset generation..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m ml.data.generate_synthetic_data

