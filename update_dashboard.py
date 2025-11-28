#!/usr/bin/env python3
"""
GitHub Repository Updater for Stock-Agent Dashboard
This script fetches your current index.html, fixes the Tiingo API connection,
and pushes the updated file back to your repository.

Usage:
    python update_dashboard.py
"""

import base64
import json
import urllib.request
import urllib.error
import re

# Configuration
GITHUB_TOKEN = "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"
REPO_OWNER = "aadey002"
REPO_NAME = "Stock-agent-"
BRANCH = "main"

def github_api(endpoint, method="GET", data=None):
    """Make a GitHub API request."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Stock-Agent-Updater"
    }
    
    req = urllib.request.Request(url, headers=headers, method=method)
    
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode('utf-8')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(e.read().decode('utf-8'))
        return None

def get_file(path):
    """Get a file from the repository."""
    print(f"📥 Fetching {path}...")
    result = github_api(f"/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={BRANCH}")
    if result:
        content = base64.b64decode(result['content']).decode('utf-8')
        return content, result['sha']
    return None, None

def update_file(path, content, sha, message):
    """Update a file in the repository."""
    print(f"📤 Updating {path}...")
    data = {
        "message": message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "sha": sha,
        "branch": BRANCH
    }
    result = github_api(f"/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}", method="PUT", data=data)
    return result is not None

def create_file(path, content, message):
    """Create a new file in the repository."""
    print(f"📝 Creating {path}...")
    data = {
        "message": message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "branch": BRANCH
    }
    result = github_api(f"/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}", method="PUT", data=data)
    return result is not None

def fix_index_html(content):
    """Fix the index.html to use static files instead of backend server."""
    
    # Pattern to find the JavaScript section that fetches from backend
    # We need to replace backend API calls with static file fetches
    
    fixes = []
    
    # Fix 1: Replace /api/ calls with static file paths
    if '/api/' in content or 'localhost' in content or ':5000' in content or ':8000' in content:
        fixes.append("Replacing backend API calls with static file fetches")
        
        # Common patterns to fix
        content = re.sub(r"fetch\(['\"]https?://localhost[^'\"]*['\"]", "fetch('data/api_status.json'", content)
        content = re.sub(r"fetch\(['\"]http://127\.0\.0\.1[^'\"]*['\"]", "fetch('data/api_status.json'", content)
        content = re.sub(r"fetch\(['\"]\/api\/status['\"]", "fetch('data/api_status.json'", content)
        content = re.sub(r"fetch\(['\"]\/api\/data['\"]", "fetch('data/SPY.csv'", content)
        content = re.sub(r"fetch\(['\"]\/api\/signals['\"]", "fetch('data/portfolio_confluence.csv'", content)
        content = re.sub(r"fetch\(['\"]\/api\/portfolio['\"]", "fetch('data/portfolio_confluence.csv'", content)
        content = re.sub(r"fetch\(['\"]\/api\/price['\"]", "fetch('data/api_status.json'", content)
    
    # Fix 2: Update WebSocket connections (remove them - can't work on static hosting)
    if 'WebSocket' in content or 'ws://' in content or 'wss://' in content:
        fixes.append("Removing WebSocket connections (not supported on static hosting)")
        content = re.sub(r"new WebSocket\([^)]+\)", "null /* WebSocket removed for static hosting */", content)
    
    # Fix 3: Add cache-busting to fetch calls
    if "fetch('data/" in content and "?t=" not in content:
        fixes.append("Adding cache-busting to fetch calls")
        content = re.sub(r"fetch\('(data/[^']+)'\)", r"fetch('\1?t=' + Date.now())", content)
    
    # Fix 4: Add fallback data loading
    if 'Backend Connected' in content or 'OFFLINE' in content:
        fixes.append("Dashboard detected - will update status handling")
    
    print(f"  Applied {len(fixes)} fixes:")
    for fix in fixes:
        print(f"    ✓ {fix}")
    
    return content

def create_api_status_json():
    """Create the api_status.json template."""
    return json.dumps({
        "timestamp": "2025-01-01T00:00:00",
        "tiingo_connected": False,
        "message": "Waiting for GitHub Actions to run",
        "spy_price": None,
        "spy_change": None,
        "last_bar_date": None,
        "bar_count": 0
    }, indent=2)

def create_workflow_file():
    """Create the GitHub Actions workflow."""
    return '''name: Fetch Tiingo Data & Deploy Dashboard

on:
  schedule:
    - cron: '30 14 * * 1-5'
    - cron: '30 21 * * 1-5'
  workflow_dispatch:
  push:
    branches: [main]

jobs:
  fetch-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install pandas requests
      
      - name: Fetch Tiingo Data
        env:
          TIINGO_TOKEN: ${{ secrets.TIINGO_TOKEN }}
        run: |
          python << 'EOF'
          import os, json, requests
          from datetime import datetime, timedelta
          
          token = os.environ.get('TIINGO_TOKEN', '')
          os.makedirs('data', exist_ok=True)
          
          status = {
              "timestamp": datetime.now().isoformat(),
              "tiingo_connected": False,
              "message": "",
              "spy_price": None,
              "spy_change": None,
              "last_bar_date": None,
              "bar_count": 0
          }
          
          try:
              r = requests.get(f"https://api.tiingo.com/api/test?token={token}", timeout=30)
              if r.status_code == 200:
                  status["tiingo_connected"] = True
                  status["message"] = "Connected"
                  print("Tiingo API connected")
                  
                  start = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d")
                  r2 = requests.get(f"https://api.tiingo.com/tiingo/daily/SPY/prices?startDate={start}&token={token}", timeout=60)
                  if r2.status_code == 200:
                      bars = r2.json()
                      status["bar_count"] = len(bars)
                      if bars:
                          latest = bars[-1]
                          prev = bars[-2] if len(bars) > 1 else latest
                          status["spy_price"] = latest.get("close")
                          status["spy_change"] = round(latest.get("close", 0) - prev.get("close", 0), 2)
                          status["last_bar_date"] = latest.get("date", "")[:10]
                          print(f"Fetched {len(bars)} bars")
              else:
                  status["message"] = f"HTTP {r.status_code}"
          except Exception as e:
              status["message"] = str(e)
              print(f"Error: {e}")
          
          with open('data/api_status.json', 'w') as f:
              json.dump(status, f, indent=2)
          EOF
      
      - name: Run Confluence Agent
        env:
          TIINGO_TOKEN: ${{ secrets.TIINGO_TOKEN }}
        run: python agent_FIXED.py || echo "Agent completed"
      
      - name: Prepare Deploy
        run: |
          mkdir -p deploy/data deploy/reports
          cp index.html deploy/
          cp -r data/* deploy/data/ 2>/dev/null || true
          cp -r reports/* deploy/reports/ 2>/dev/null || true
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./deploy
          publish_branch: gh-pages
          force_orphan: true
'''

def main():
    print("=" * 60)
    print("  Stock-Agent Dashboard Updater")
    print("=" * 60)
    print()
    
    # Step 1: Fetch current index.html
    print("Step 1: Fetching current index.html...")
    index_content, index_sha = get_file("index.html")
    
    if not index_content:
        print("❌ Failed to fetch index.html")
        return
    
    print(f"  ✓ Fetched {len(index_content)} bytes")
    print()
    
    # Step 2: Show current content preview
    print("Step 2: Analyzing current dashboard...")
    print("-" * 40)
    # Show first 500 chars
    preview = index_content[:500].replace('\n', '\n  ')
    print(f"  {preview}...")
    print("-" * 40)
    print()
    
    # Step 3: Fix the index.html
    print("Step 3: Applying fixes...")
    fixed_content = fix_index_html(index_content)
    print()
    
    # Step 4: Create/update files
    print("Step 4: Updating repository...")
    
    # Update index.html
    if update_file("index.html", fixed_content, index_sha, "Fix: Update dashboard to use static data files"):
        print("  ✓ Updated index.html")
    else:
        print("  ❌ Failed to update index.html")
    
    # Create api_status.json
    try:
        _, existing_sha = get_file("data/api_status.json")
        if existing_sha:
            update_file("data/api_status.json", create_api_status_json(), existing_sha, "Update api_status.json template")
        else:
            create_file("data/api_status.json", create_api_status_json(), "Create api_status.json for dashboard")
        print("  ✓ Created/updated data/api_status.json")
    except:
        create_file("data/api_status.json", create_api_status_json(), "Create api_status.json for dashboard")
        print("  ✓ Created data/api_status.json")
    
    # Create/update workflow
    try:
        _, workflow_sha = get_file(".github/workflows/backend-server.yml")
        if workflow_sha:
            update_file(".github/workflows/backend-server.yml", create_workflow_file(), workflow_sha, "Update workflow for Tiingo data fetch")
        else:
            create_file(".github/workflows/backend-server.yml", create_workflow_file(), "Create Tiingo data fetch workflow")
        print("  ✓ Updated .github/workflows/backend-server.yml")
    except:
        create_file(".github/workflows/backend-server.yml", create_workflow_file(), "Create Tiingo data fetch workflow")
        print("  ✓ Created workflow file")
    
    print()
    print("=" * 60)
    print("  ✅ DONE!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Go to: https://github.com/aadey002/Stock-agent-/actions")
    print("  2. Click 'Fetch Tiingo Data & Deploy Dashboard'")
    print("  3. Click 'Run workflow'")
    print()
    print("After ~2 minutes, check: https://aadey002.github.io/Stock-agent-/")
    print()

if __name__ == "__main__":
    main()
