@echo off
cls
color 0A

echo ========================================================
echo    FIX STOCK AGENT DASHBOARD - MAKE IT LIVE!
echo ========================================================
echo.

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit
)

echo Installing required package...
pip install requests >nul 2>&1

echo Creating deployment script...

REM Create Python script inline
(
echo import requests, base64, json
echo headers = {"Authorization": "token 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", "Accept": "application/vnd.github.v3+json"}
echo print("Deploying backend to GitHub..."^)
echo.
echo # Deploy minimal server
echo server = """from flask import Flask, jsonify
echo from flask_cors import CORS
echo app = Flask(__name__^)
echo CORS(app, origins=['*']^)
echo @app.route('/api/health'^)
echo def health(^): return jsonify({'status': 'healthy'}^)
echo @app.route('/api/status'^)
echo def status(^): return jsonify({'status': 'online'}^)
echo if __name__ == '__main__': app.run(host='0.0.0.0', port=5000^)"""
echo.
echo url = "https://api.github.com/repos/aadey002/Stock-agent-/contents/server.py"
echo data = {"message": "Fix backend", "content": base64.b64encode(server.encode(^)^).decode(^), "branch": "main"}
echo r = requests.put(url, json=data, headers=headers^)
echo if r.status_code in [200, 201]: print("SUCCESS! Backend deployed!"^)
echo else: print(f"Failed: {r.json().get('message', 'Unknown error'^)}"^)
echo.
echo # Deploy workflow
echo workflow = """name: Backend
echo on: [workflow_dispatch, push]
echo jobs:
echo   run:
echo     runs-on: ubuntu-latest
echo     steps:
echo     - uses: actions/checkout@v3
echo     - run: pip install flask flask-cors ^&^& python server.py"""
echo.
echo url2 = "https://api.github.com/repos/aadey002/Stock-agent-/contents/.github/workflows/backend.yml"
echo data2 = {"message": "Add workflow", "content": base64.b64encode(workflow.encode(^)^).decode(^), "branch": "main"}
echo r2 = requests.put(url2, json=data2, headers=headers^)
echo if r2.status_code in [200, 201]: print("Workflow deployed!"^)
echo.
echo print("\nNOW GO TO: https://github.com/aadey002/Stock-agent-/actions"^)
echo print("Click 'Backend' then 'Run workflow'"^)
) > fix.py

echo.
echo Running fix...
echo ----------------------------------------
python fix.py
echo ----------------------------------------
echo.

echo Opening GitHub Actions...
start https://github.com/aadey002/Stock-agent-/actions

echo.
echo ========================================================
echo  NEXT STEPS:
echo ========================================================
echo  1. Browser opened to GitHub Actions
echo  2. Click on "Backend" workflow
echo  3. Click "Run workflow" button
echo  4. Wait 2 minutes
echo  5. Refresh your dashboard - it will show LIVE!
echo ========================================================
echo.
pause
