# Start MORROW React Frontend Dev Server
$ErrorActionPreference = "Stop"

# Ensure Node.js is available in the current terminal session PATH
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    $nodeDir = "C:\Program Files\nodejs"
    if (Test-Path (Join-Path $nodeDir "npm.cmd")) {
        $env:PATH = "$nodeDir;$env:PATH"
    } else {
        Write-Error "Node.js / npm not found. Please install Node.js LTS or add it to PATH."
        exit 1
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"

Write-Host "Starting MORROW React Frontend..." -ForegroundColor Cyan
Push-Location $frontendDir
try {
    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Host "Installing frontend packages..." -ForegroundColor Yellow
        npm install
    }
    npm run dev
} finally {
    Pop-Location
}
