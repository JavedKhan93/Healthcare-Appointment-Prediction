# Start MORROW Flask Backend API
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Starting MORROW Flask Backend Server..." -ForegroundColor Cyan
Push-Location $repoRoot
try {
    & (Join-Path $repoRoot ".venv\Scripts\python.exe") -m backend.run
} finally {
    Pop-Location
}
