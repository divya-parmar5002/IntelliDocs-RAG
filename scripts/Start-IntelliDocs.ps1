# Starts the host-side AI runtime before the Dockerized IntelliDocs services.
# Run manually with: powershell -ExecutionPolicy Bypass -File .\scripts\Start-IntelliDocs.ps1

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$ollamaExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"

if (-not (Test-Path -LiteralPath $ollamaExe)) {
    throw "Ollama was not found at $ollamaExe. Install Ollama, pull the required models, then retry."
}

if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
    # Docker reaches the Windows host through host.docker.internal, so bind the
    # Ollama API to all local interfaces instead of only 127.0.0.1.
    $env:OLLAMA_HOST = "0.0.0.0:11434"
    Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
}

$deadline = (Get-Date).AddSeconds(30)
do {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null
        break
    }
    catch {
        Start-Sleep -Seconds 2
    }
} while ((Get-Date) -lt $deadline)

if ((Get-Date) -ge $deadline) {
    throw "Ollama did not become ready on port 11434 within 30 seconds."
}

Set-Location -LiteralPath $projectRoot
docker compose up -d

Write-Host "IntelliDocs is ready: http://localhost:3000"
