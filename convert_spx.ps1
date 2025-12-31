# Download S&P 500 Index and convert to SPY-like format for backtesting
Write-Host "Downloading S&P 500 Index full history (1993-2025)..."

$url = "https://stooq.com/q/d/l/?s=^spx&d1=19930101&d2=20251231&i=d"
$tempFile = "C:\Users\adeto\Documents\Stock-agent-\data\SPX_raw.csv"
$outputFile = "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv"

Invoke-WebRequest -Uri $url -OutFile $tempFile -Headers @{"User-Agent"="Mozilla/5.0"}

# Read and convert - SPY is roughly 1/10 of S&P 500 index
# But for pattern analysis, we can scale it
$lines = Get-Content $tempFile
$output = @()
$output += "Date,Open,High,Low,Close,Volume"

foreach ($line in ($lines | Select-Object -Skip 1)) {
    if ($line -match "No data" -or $line -eq "") { continue }
    $parts = $line -split ","
    if ($parts.Count -ge 6) {
        $date = $parts[0]
        # Scale prices to SPY-like range (divide by 10)
        $open = [math]::Round([double]$parts[1] / 10, 2)
        $high = [math]::Round([double]$parts[2] / 10, 2)
        $low = [math]::Round([double]$parts[3] / 10, 2)
        $close = [math]::Round([double]$parts[4] / 10, 2)
        $volume = $parts[5]
        $output += "$date,$open,$high,$low,$close,$volume"
    }
}

$output | Set-Content $outputFile -Encoding UTF8

Write-Host "Converted $($output.Count - 1) rows"
Write-Host ""
Write-Host "First 5 rows:"
$output | Select-Object -First 6
Write-Host ""
Write-Host "Last 5 rows:"
$output | Select-Object -Last 5
Write-Host ""
Write-Host "File saved to: $outputFile"
