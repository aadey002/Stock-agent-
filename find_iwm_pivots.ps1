# Find Major Pivots in IWM Full History
Write-Host "=== MAJOR PIVOTS IN IWM (2005-2025) ===" -ForegroundColor Cyan
Write-Host ""

$data = Import-Csv "C:\Users\adeto\Documents\Stock-agent-\data\IWM_full.csv"
Write-Host "Total rows: $($data.Count)"
Write-Host "Date range: $($data[0].Date) to $($data[-1].Date)"
Write-Host ""

# Find major pivots using 50-day lookback
$lookback = 50
$pivots = @()

for ($i = $lookback; $i -lt ($data.Count - $lookback); $i++) {
    $high = [double]$data[$i].High
    $low = [double]$data[$i].Low
    $close = [double]$data[$i].Close
    $date = $data[$i].Date

    $isHigh = $true
    $isLow = $true

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

$pivots = $pivots | Sort-Object Date

Write-Host "=== MAJOR SWING HIGHS (Top 15 by Price) ===" -ForegroundColor Green
$highs = $pivots | Where-Object { $_.Type -eq "HIGH" } | Sort-Object Price -Descending | Select-Object -First 15
foreach ($p in $highs) {
    Write-Host "  $($p.Date): `$$($p.Price)"
}

Write-Host ""
Write-Host "=== MAJOR SWING LOWS (Bottom 15 by Price) ===" -ForegroundColor Red
$lows = $pivots | Where-Object { $_.Type -eq "LOW" } | Sort-Object Price | Select-Object -First 15
foreach ($p in $lows) {
    Write-Host "  $($p.Date): `$$($p.Price)"
}

Write-Host ""
Write-Host "=== KEY HISTORICAL EVENTS ===" -ForegroundColor Magenta

Write-Host ""
Write-Host "FINANCIAL CRISIS (2007-2009):"
$fcHigh = $pivots | Where-Object { $_.Date -like "2007-*" -and $_.Type -eq "HIGH" } | Sort-Object Price -Descending | Select-Object -First 1
$fcLow = $pivots | Where-Object { ($_.Date -like "2008-*" -or $_.Date -like "2009-*") -and $_.Type -eq "LOW" } | Sort-Object Price | Select-Object -First 1
if ($fcHigh) { Write-Host "  Peak: $($fcHigh.Date) @ `$$($fcHigh.Price)" -ForegroundColor Green }
if ($fcLow) { Write-Host "  Bottom: $($fcLow.Date) @ `$$($fcLow.Price)" -ForegroundColor Red }

Write-Host ""
Write-Host "COVID ERA (2020):"
$covidHigh = $pivots | Where-Object { $_.Date -like "2020-02-*" -and $_.Type -eq "HIGH" } | Select-Object -First 1
$covidLow = $pivots | Where-Object { $_.Date -like "2020-03-*" -and $_.Type -eq "LOW" } | Select-Object -First 1
if ($covidHigh) { Write-Host "  Pre-COVID Peak: $($covidHigh.Date) @ `$$($covidHigh.Price)" -ForegroundColor Green }
if ($covidLow) { Write-Host "  COVID Bottom: $($covidLow.Date) @ `$$($covidLow.Price)" -ForegroundColor Red }

Write-Host ""
Write-Host "2021-2022 BEAR MARKET:"
$bear22High = $pivots | Where-Object { ($_.Date -like "2021-11-*" -or $_.Date -like "2021-10-*" -or $_.Date -like "2021-12-*") -and $_.Type -eq "HIGH" } | Sort-Object Price -Descending | Select-Object -First 1
$bear22Low = $pivots | Where-Object { $_.Date -like "2022-*" -and $_.Type -eq "LOW" } | Sort-Object Price | Select-Object -First 1
if ($bear22High) { Write-Host "  Peak: $($bear22High.Date) @ `$$($bear22High.Price)" -ForegroundColor Green }
if ($bear22Low) { Write-Host "  Bottom: $($bear22Low.Date) @ `$$($bear22Low.Price)" -ForegroundColor Red }

Write-Host ""
Write-Host "2025:"
$ath = $pivots | Where-Object { $_.Type -eq "HIGH" } | Sort-Object Price -Descending | Select-Object -First 1
$recent25Low = $pivots | Where-Object { $_.Date -like "2025-*" -and $_.Type -eq "LOW" } | Sort-Object Date | Select-Object -First 1
if ($ath) { Write-Host "  All-Time High: $($ath.Date) @ `$$($ath.Price)" -ForegroundColor Green }
if ($recent25Low) { Write-Host "  2025 Low: $($recent25Low.Date) @ `$$($recent25Low.Price)" -ForegroundColor Red }

# Export pivots
$pivots | Export-Csv "C:\Users\adeto\Documents\Stock-agent-\data\iwm_major_pivots.csv" -NoTypeInformation
Write-Host ""
Write-Host "Pivots exported to data/iwm_major_pivots.csv" -ForegroundColor Gray
