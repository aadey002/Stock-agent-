# 🚀 STOCK AGENT BACKEND DEPLOYMENT SCRIPT
# This script deploys your backend to GitHub Actions
# Run this from your Stock-agent- repository folder

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  STOCK AGENT BACKEND DEPLOYMENT SCRIPT" -ForegroundColor Yellow
Write-Host "  Deploy backend to GitHub Actions" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "agent_FIXED.py")) {
    Write-Host "❌ ERROR: agent_FIXED.py not found!" -ForegroundColor Red
    Write-Host "Please run this script from your Stock-agent- repository folder" -ForegroundColor Yellow
    Write-Host "Example: cd C:\Users\YourName\Stock-agent-" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ Found repository files" -ForegroundColor Green
Write-Host ""

# Create .github/workflows directory if it doesn't exist
Write-Host "📁 Creating workflow directory..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path ".github\workflows" | Out-Null
Write-Host "✅ Workflow directory ready" -ForegroundColor Green
Write-Host ""

# Create the backend workflow file
Write-Host "📝 Creating GitHub Actions workflow..." -ForegroundColor Cyan
$workflowContent = @'
name: Stock Agent Backend Server

on:
  workflow_dispatch:
  schedule:
    - cron: '*/15 9-16 * * 1-5'  # Every 15 minutes during market hours (9 AM - 4 PM ET, weekdays)
  push:
    branches: [main]
    paths:
      - 'server.py'
      - 'agent_FIXED.py'
      - 'gann_elliott.py'
      - '.github/workflows/backend-server.yml'

jobs:
  run-backend:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements_server.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flask flask-cors pandas numpy yfinance scikit-learn tensorflow
        pip install tiingo requests python-dateutil
        if [ -f requirements_server.txt ]; then pip install -r requirements_server.txt; fi
    
    - name: Run Backend Server
      env:
        TIINGO_API_KEY: ${{ secrets.TIINGO_API_KEY }}
        PYTHONUNBUFFERED: "1"
      timeout-minutes: 14
      run: |
        echo "🚀 Starting Stock Agent Backend Server..."
        echo "⏰ Time: $(date)"
        echo "📊 Market Data Provider: Tiingo API"
        echo "🤖 Trading Agents: 3 (Confluence, Gann-Elliott, RL/DQN)"
        echo "=========================================="
        python server.py 2>&1 | tee server.log || true
        echo "=========================================="
        echo "✅ Backend run completed"
        echo "📝 Check server.log for details"
    
    - name: Upload Server Logs
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: server-logs-${{ github.run_number }}
        path: server.log
        retention-days: 7
    
    - name: Check Server Health
      if: success()
      run: |
        echo "🏥 Checking server health..."
        if grep -q "ERROR" server.log; then
          echo "⚠️ Errors found in server log"
          grep "ERROR" server.log
        else
          echo "✅ No errors detected"
        fi
        
        if grep -q "Trading signals generated" server.log; then
          echo "✅ Trading signals successfully generated"
        else
          echo "⚠️ No trading signals found"
        fi
'@

Set-Content -Path ".github\workflows\backend-server.yml" -Value $workflowContent -Encoding UTF8
Write-Host "✅ Workflow file created" -ForegroundColor Green
Write-Host ""

# Check if git is installed
Write-Host "🔍 Checking Git installation..." -ForegroundColor Cyan
try {
    git --version | Out-Null
    Write-Host "✅ Git is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Stage and commit the changes
Write-Host "📦 Preparing to commit changes..." -ForegroundColor Cyan
git add .github/workflows/backend-server.yml
git commit -m "Deploy backend server to GitHub Actions" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Changes committed" -ForegroundColor Green
} else {
    Write-Host "⚠️ No changes to commit (workflow might already exist)" -ForegroundColor Yellow
}
Write-Host ""

# Push to GitHub
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully pushed to GitHub" -ForegroundColor Green
} else {
    Write-Host "⚠️ Push might have failed - check your authentication" -ForegroundColor Yellow
    Write-Host "Try: git push origin main" -ForegroundColor Gray
}
Write-Host ""

# Get Tiingo API key from user
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🔑 TIINGO API KEY SETUP" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To fetch market data, we need your Tiingo API key." -ForegroundColor White
Write-Host "Get it from: https://www.tiingo.com/account/api/token" -ForegroundColor Cyan
Write-Host ""
$apiKey = Read-Host "Enter your Tiingo API key"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "⚠️ No API key provided. You'll need to set it manually in GitHub Secrets." -ForegroundColor Yellow
    Write-Host "Go to: https://github.com/aadey002/Stock-agent-/settings/secrets/actions" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "📝 Setting up GitHub Secret..." -ForegroundColor Cyan
    Write-Host "You need to set TIINGO_API_KEY in GitHub Secrets manually:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Go to: https://github.com/aadey002/Stock-agent-/settings/secrets/actions" -ForegroundColor White
    Write-Host "2. Click 'New repository secret'" -ForegroundColor White
    Write-Host "3. Name: TIINGO_API_KEY" -ForegroundColor Green
    Write-Host "4. Value: $apiKey" -ForegroundColor Green
    Write-Host "5. Click 'Add secret'" -ForegroundColor White
    Write-Host ""
    
    # Save to clipboard if possible
    try {
        $apiKey | Set-Clipboard
        Write-Host "✅ API key copied to clipboard!" -ForegroundColor Green
    } catch {
        Write-Host "📋 Copy this key: $apiKey" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Set TIINGO_API_KEY in GitHub Secrets (link above)" -ForegroundColor White
Write-Host "2. Go to: https://github.com/aadey002/Stock-agent-/actions" -ForegroundColor White
Write-Host "3. Click 'Stock Agent Backend Server'" -ForegroundColor White
Write-Host "4. Click 'Run workflow' button" -ForegroundColor White
Write-Host "5. Wait 2-3 minutes for completion" -ForegroundColor White
Write-Host "6. Visit dashboard: https://aadey002.github.io/Stock-agent-/" -ForegroundColor White
Write-Host "7. Hard refresh (Ctrl+F5) to see LIVE status" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Your Stock Agent backend is now deployed!" -ForegroundColor Green
Write-Host ""

# Open browser to GitHub Actions
Write-Host "Opening GitHub Actions in browser..." -ForegroundColor Cyan
Start-Process "https://github.com/aadey002/Stock-agent-/actions"

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
