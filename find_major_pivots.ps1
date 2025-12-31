# Find Major Pivots in SPY Full History
Write-Host "=== MAJOR PIVOTS IN SPY (1993-2025) ===" -ForegroundColor Cyan
Write-Host ""

$data = Import-Csv "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv"
Write-Host "Total rows: $($data.Count)"
Write-Host "Date range: $($data[0].Date) to $($data[-1].Date)"
Write-Host ""

# Find major pivots using 50-day lookback (significant turns only)
$lookback = 50
$pivots = @()

for ($i = $lookback; $i -lt ($data.Count - $lookback); $i++) {
    $high = [double]$data[$i].High
    $low = [double]$data[$i].Low
    $close = [double]$data[$i].Close
    $date = $data[$i].Date

    $isHigh = $true
    $isLow = $true

    # Check if highest/lowest in lookback period
    for ($j = ($i - $lookback); $j -le ($i + $lookback); $j++) {
        if ($j -eq $i) { continue }
        if ([double]$data[$j].High -gt $high) { $isHigh = $false }
        if ([double]$data[$j].Low -lt $low) { $isLow = $false }
    }

    if ($isHigh) {
        $pivots += [PSCustomObject]@{
            Date = $date
            Type = "HIGH"
            Price = [math]::Round($close, 2)
            Index = $i
        }
    }
    if ($isLow) {
        $pivots += [PSCustomObject]@{
            Date = $date
            Type = "LOW"
            Price = [math]::Round($close, 2)
            Index = $i
        }
    }
}

Write-Host "Found $($pivots.Count) major pivots (50-day significance)" -ForegroundColor Yellow
Write-Host ""

# Sort by date
$pivots = $pivots | Sort-Object Date

Write-Host "=== MAJOR SWING HIGHS ===" -ForegroundColor Green
$highs = $pivots | Where-Object { $_.Type -eq "HIGH" } | Sort-Object Price -Descending
foreach ($p in $highs) {
    $year = $p.Date.Substring(0,4)
    Write-Host "  $($p.Date): `$$($p.Price) (Year: $year)"
}

Write-Host ""
Write-Host "=== MAJOR SWING LOWS ===" -ForegroundColor Red
$lows = $pivots | Where-Object { $_.Type -eq "LOW" } | Sort-Object Price
foreach ($p in $lows) {
    $year = $p.Date.Substring(0,4)
    Write-Host "  $($p.Date): `$$($p.Price) (Year: $year)"
}

Write-Host ""
Write-Host "=== CHRONOLOGICAL PIVOT LIST ===" -ForegroundColor Cyan
foreach ($p in $pivots) {
    $symbol = if ($p.Type -eq "HIGH") { "▲" } else { "▼" }
    $color = if ($p.Type -eq "HIGH") { "Green" } else { "Red" }
    Write-Host "  $($p.Date) $symbol $($p.Type): `$$($p.Price)" -ForegroundColor $color
}

Write-Host ""
Write-Host "=== KEY MARKET EVENTS ===" -ForegroundColor Magenta

# Identify specific historical pivots
$allTimeHigh = $highs | Select-Object -First 1
$allTimeLow = $lows | Select-Object -First 1

Write-Host "All-Time High: $($allTimeHigh.Date) @ `$$($allTimeHigh.Price)"
Write-Host "All-Time Low: $($allTimeLow.Date) @ `$$($allTimeLow.Price)"

# Export to CSV for reference
$pivots | Export-Csv "C:\Users\adeto\Documents\Stock-agent-\data\major_pivots.csv" -NoTypeInformation
Write-Host ""
Write-Host "Pivots exported to data/major_pivots.csv" -ForegroundColor Gray
