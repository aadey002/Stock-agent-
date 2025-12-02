# COMPLETE LOGIN REMOVAL - Stock Agent 4
$indexPath = "C:\Users\adeto\Documents\Stock-agent-\web\index.html"

Write-Host "=== Removing Login System Completely ===" -ForegroundColor Cyan

$content = Get-Content $indexPath -Raw -Encoding UTF8
$originalLength = $content.Length

# 1. Remove entire login screen div (from <!-- LOGIN SCREEN --> to the closing div before <!-- MAIN CONTENT -->)
$content = $content -replace '(?s)<!-- LOGIN SCREEN -->.*?</div>\s*</div>\s*</div>\s*(?=<!-- MAIN|<div[^>]*id="mainContent")', ''

# 2. Remove login CSS styles
$content = $content -replace '(?s)/\* LOGIN SCREEN STYLES \*/.*?\.login-footer a \{[^}]*\}\s*', ''

# 3. Remove any login JavaScript functions
$content = $content -replace '(?s)function\s+handleLogin\s*\([^)]*\)\s*\{[^}]*\}', ''
$content = $content -replace '(?s)function\s+checkLogin\s*\([^)]*\)\s*\{[^}]*\}', ''
$content = $content -replace '(?s)function\s+logout\s*\([^)]*\)\s*\{[^}]*\}', ''

# 4. Make sure mainContent is visible (remove display:none if present)
$content = $content -replace '(id="mainContent"[^>]*?)style="display:\s*none;?"', '$1'

# 5. Remove any remaining login references that might hide content
$content = $content -replace "document\.getElementById\('loginScreen'\)[^;]*;", ''
$content = $content -replace 'loginScreen[^,\s]*,?\s*', ''

# Save
[System.IO.File]::WriteAllText($indexPath, $content, [System.Text.UTF8Encoding]::new($false))

$newLength = $content.Length
Write-Host "✅ Login removed!" -ForegroundColor Green
Write-Host "   Before: $originalLength chars" -ForegroundColor Gray
Write-Host "   After:  $newLength chars" -ForegroundColor Gray
Write-Host "   Removed: $($originalLength - $newLength) chars" -ForegroundColor Gray

Write-Host ""
Write-Host "Now run:" -ForegroundColor Yellow
Write-Host "  git add web/index.html"
Write-Host '  git commit -m "Remove login system completely"'
Write-Host "  git push origin main"