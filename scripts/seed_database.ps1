# Seed MongoDB with Cleaned Appointments and Artifacts (Idempotent)
$ErrorActionPreference = "Stop"
Write-Host "Initializing and seeding MongoDB..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -c "from backend.database import init_db; init_db()"

