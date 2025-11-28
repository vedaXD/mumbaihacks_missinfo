# Complete Installation Script for Chrome Extension
# Run this in PowerShell to set everything up

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "="*59 -ForegroundColor Cyan
Write-Host "🛡️  Misinformation Detector - Complete Setup" -ForegroundColor White
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "1️⃣  Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}

# Step 2: Activate virtual environment (if exists)
Write-Host "`n2️⃣  Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "   ✅ Virtual environment found, activating..." -ForegroundColor Green
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "   ⚠️  No virtual environment found. Creating one..." -ForegroundColor Yellow
    python -m venv .venv
    & ".venv\Scripts\Activate.ps1"
    Write-Host "   ✅ Virtual environment created and activated" -ForegroundColor Green
}

# Step 3: Install base requirements (if not already)
Write-Host "`n3️⃣  Checking base dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "   Installing base requirements (this may take a while)..." -ForegroundColor Cyan
    pip install -r requirements.txt --quiet
    Write-Host "   ✅ Base requirements installed" -ForegroundColor Green
}

# Step 4: Install API requirements
Write-Host "`n4️⃣  Installing API server dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements-api.txt") {
    pip install -r requirements-api.txt --quiet
    Write-Host "   ✅ API dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ❌ requirements-api.txt not found" -ForegroundColor Red
    exit 1
}

# Step 5: Generate extension icons
Write-Host "`n5️⃣  Generating extension icons..." -ForegroundColor Yellow
if (Test-Path "generate_icons.py") {
    python generate_icons.py
} else {
    Write-Host "   ⚠️  generate_icons.py not found, skipping..." -ForegroundColor Yellow
}

# Step 6: Check .env file
Write-Host "`n6️⃣  Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   ✅ .env file exists" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  .env file not found. Please configure API keys." -ForegroundColor Yellow
}

# Step 7: Create data directories
Write-Host "`n7️⃣  Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\reports" | Out-Null
Write-Host "   ✅ Data directories created" -ForegroundColor Green

# Summary
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`n📋 Next Steps:" -ForegroundColor White
Write-Host ""
Write-Host "1. Start the API server:" -ForegroundColor Cyan
Write-Host "   python api_server.py" -ForegroundColor White
Write-Host ""
Write-Host "2. Load Chrome extension:" -ForegroundColor Cyan
Write-Host "   - Open Chrome" -ForegroundColor White
Write-Host "   - Go to chrome://extensions/" -ForegroundColor White
Write-Host "   - Enable 'Developer mode'" -ForegroundColor White
Write-Host "   - Click 'Load unpacked'" -ForegroundColor White
Write-Host "   - Select folder: chrome_extension\" -ForegroundColor White
Write-Host ""
Write-Host "3. Test the setup:" -ForegroundColor Cyan
Write-Host "   python test_api.py" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor White
Write-Host "   - Setup Guide: CHROME_EXTENSION_SETUP.md" -ForegroundColor Gray
Write-Host "   - Extension README: chrome_extension\README.md" -ForegroundColor Gray
Write-Host ""
Write-Host "🎉 Happy fact-checking!" -ForegroundColor Green
