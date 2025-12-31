# Fetch full QQQ history from Stooq
# QQQ launched March 10, 1999

Write-Host "=== Fetching QQQ Full History ===" -ForegroundColor Cyan
Write-Host "QQQ (Invesco QQQ Trust) launched: March 10, 1999"
Write-Host ""

# Try QQQ from Stooq
$url = "https://stooq.com/q/d/l/?s=qqq.us&d1=19990310&d2=20251231&i=d"
Write-Host "Downloading from Stooq..."
Write-Host $url

try {
    Invoke-WebRequest -Uri $url -OutFile "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_stooq.csv" -Headers @{"User-Agent"="Mozilla/5.0"}
    $content = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_stooq.csv"
    Write-Host "Stooq QQQ rows: $($content.Count)"
    $content | Select-Object -First 3
    Write-Host "..."
    $content | Select-Object -Last 3
} catch {
    Write-Host "Stooq QQQ failed: $_" -ForegroundColor Red
}

Write-Host ""

# Also try NASDAQ 100 index (NDX) which QQQ tracks - might have longer history
$url2 = "https://stooq.com/q/d/l/?s=^ndx&d1=19850101&d2=20251231&i=d"
Write-Host "Downloading NASDAQ-100 Index (^NDX) from Stooq..."

try {
    Invoke-WebRequest -Uri $url2 -OutFile "C:\Users\adeto\Documents\Stock-agent-\data\NDX_raw.csv" -Headers @{"User-Agent"="Mozilla/5.0"}
    $content = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\NDX_raw.csv"
    Write-Host "NDX rows: $($content.Count)"
    $content | Select-Object -First 3
    Write-Host "..."
    $content | Select-Object -Last 3
} catch {
    Write-Host "NDX failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Converting to QQQ_full.csv ===" -ForegroundColor Yellow

# Use the better data source
$stooqData = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_stooq.csv"
$ndxData = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\NDX_raw.csv"

# Check which has more/better data
$stooqRows = ($stooqData | Measure-Object).Count
$ndxRows = ($ndxData | Measure-Object).Count

Write-Host "Stooq QQQ: $stooqRows rows"
Write-Host "NDX Index: $ndxRows rows"

# If NDX has more data, scale it to QQQ-like prices (QQQ ≈ NDX/40)
if ($ndxRows -gt $stooqRows) {
    Write-Host ""
    Write-Host "Using NDX data (more history), scaling to QQQ prices..."

    $output = @()
    $output += "Date,Open,High,Low,Close,Volume"

    foreach ($line in ($ndxData | Select-Object -Skip 1)) {
        if ($line -match "No data" -or $line -eq "") { continue }
        $parts = $line -split ","
        if ($parts.Count -ge 6) {
            $date = $parts[0]
            # Scale NDX to QQQ-like prices (divide by 40)
            $open = [math]::Round([double]$parts[1] / 40, 2)
            $high = [math]::Round([double]$parts[2] / 40, 2)
            $low = [math]::Round([double]$parts[3] / 40, 2)
            $close = [math]::Round([double]$parts[4] / 40, 2)
            $volume = $parts[5]
            $output += "$date,$open,$high,$low,$close,$volume"
        }
    }

    $output | Set-Content "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_full.csv" -Encoding UTF8
    Write-Host "Saved $($output.Count - 1) rows to QQQ_full.csv"
} else {
    Write-Host ""
    Write-Host "Using Stooq QQQ data directly..."
    Copy-Item "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_stooq.csv" "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_full.csv"
    Write-Host "Copied to QQQ_full.csv"
}

Write-Host ""
Write-Host "=== Final QQQ_full.csv ===" -ForegroundColor Green
$final = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_full.csv"
Write-Host "Total rows: $($final.Count)"
Write-Host ""
Write-Host "First 5 rows:"
$final | Select-Object -First 5
Write-Host ""
Write-Host "Last 5 rows:"
$final | Select-Object -Last 5
