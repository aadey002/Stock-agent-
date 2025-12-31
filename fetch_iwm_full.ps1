# Fetch full IWM history from Stooq
# IWM (iShares Russell 2000 ETF) launched: May 22, 2000

Write-Host "=== Fetching IWM Full History ===" -ForegroundColor Cyan
Write-Host "IWM (iShares Russell 2000 ETF) launched: May 22, 2000"
Write-Host ""

# Try IWM from Stooq
$url = "https://stooq.com/q/d/l/?s=iwm.us&d1=20000522&d2=20251231&i=d"
Write-Host "Downloading IWM from Stooq..."

try {
    Invoke-WebRequest -Uri $url -OutFile "C:\Users\adeto\Documents\Stock-agent-\data\IWM_stooq.csv" -Headers @{"User-Agent"="Mozilla/5.0"}
    $content = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\IWM_stooq.csv"
    Write-Host "Stooq IWM rows: $($content.Count)"
    $content | Select-Object -First 3
    Write-Host "..."
    $content | Select-Object -Last 3
} catch {
    Write-Host "Stooq IWM failed: $_" -ForegroundColor Red
}

Write-Host ""

# Also try Russell 2000 index (RUT) which IWM tracks
$url2 = "https://stooq.com/q/d/l/?s=^rut&d1=19870101&d2=20251231&i=d"
Write-Host "Downloading Russell 2000 Index (^RUT) from Stooq..."

try {
    Invoke-WebRequest -Uri $url2 -OutFile "C:\Users\adeto\Documents\Stock-agent-\data\RUT_raw.csv" -Headers @{"User-Agent"="Mozilla/5.0"}
    $content = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\RUT_raw.csv"
    Write-Host "RUT rows: $($content.Count)"
    $content | Select-Object -First 3
    Write-Host "..."
    $content | Select-Object -Last 3
} catch {
    Write-Host "RUT failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Converting to IWM_full.csv ===" -ForegroundColor Yellow

# Check which has more data
$stooqData = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\IWM_stooq.csv" -ErrorAction SilentlyContinue
$rutData = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\RUT_raw.csv" -ErrorAction SilentlyContinue

$stooqRows = if ($stooqData) { ($stooqData | Measure-Object).Count } else { 0 }
$rutRows = if ($rutData) { ($rutData | Measure-Object).Count } else { 0 }

Write-Host "Stooq IWM: $stooqRows rows"
Write-Host "RUT Index: $rutRows rows"

# Use RUT if it has more data, scale to IWM-like prices (IWM ≈ RUT/10)
if ($rutRows -gt $stooqRows -and $rutRows -gt 1) {
    Write-Host ""
    Write-Host "Using RUT data (more history), scaling to IWM prices..."

    $output = @()
    $output += "Date,Open,High,Low,Close,Volume"

    foreach ($line in ($rutData | Select-Object -Skip 1)) {
        if ($line -match "No data" -or $line -eq "") { continue }
        $parts = $line -split ","
        if ($parts.Count -ge 6) {
            $date = $parts[0]
            # Scale RUT to IWM-like prices (divide by 10)
            $open = [math]::Round([double]$parts[1] / 10, 2)
            $high = [math]::Round([double]$parts[2] / 10, 2)
            $low = [math]::Round([double]$parts[3] / 10, 2)
            $close = [math]::Round([double]$parts[4] / 10, 2)
            $volume = $parts[5]
            $output += "$date,$open,$high,$low,$close,$volume"
        }
    }

    $output | Set-Content "C:\Users\adeto\Documents\Stock-agent-\data\IWM_full.csv" -Encoding UTF8
    Write-Host "Saved $($output.Count - 1) rows to IWM_full.csv"
} elseif ($stooqRows -gt 1) {
    Write-Host ""
    Write-Host "Using Stooq IWM data directly..."
    Copy-Item "C:\Users\adeto\Documents\Stock-agent-\data\IWM_stooq.csv" "C:\Users\adeto\Documents\Stock-agent-\data\IWM_full.csv"
    Write-Host "Copied to IWM_full.csv"
} else {
    Write-Host "No valid data found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Final IWM_full.csv ===" -ForegroundColor Green
$final = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\IWM_full.csv"
Write-Host "Total rows: $($final.Count)"
Write-Host ""
Write-Host "First 5 rows:"
$final | Select-Object -First 5
Write-Host ""
Write-Host "Last 5 rows:"
$final | Select-Object -Last 5
