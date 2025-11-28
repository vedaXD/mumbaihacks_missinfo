Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Vishwas Netra Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

if (Test-Path ".env") {
    Write-Host " .env file found" -ForegroundColor Green
}

Write-Host "Creating directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path "data" -Force | Out-Null
New-Item -ItemType Directory -Path "logs" -Force | Out-Null
Write-Host " Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "Checking packages..." -ForegroundColor Cyan
pip list | Select-String "google-adk|google-generativeai|torch|transformers"
Write-Host ""
Write-Host " Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. python api_server.py" -ForegroundColor White
Write-Host "  2. python telegram_bot.py" -ForegroundColor White
