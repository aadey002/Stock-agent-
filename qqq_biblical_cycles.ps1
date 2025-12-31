# QQQ Biblical Cycles from Major Pivots
# ======================================

$qqqData = Import-Csv "C:\Users\adeto\Documents\Stock-agent-\data\QQQ_full.csv"

$majorPivots = @(
    @{ Date = "2000-03-24"; Price = 117.29; Type = "HIGH"; Name = "Dot-Com Peak" },
    @{ Date = "2002-10-08"; Price = 20.29; Type = "LOW"; Name = "Dot-Com Bottom" },
    @{ Date = "2007-10-31"; Price = 55.97; Type = "HIGH"; Name = "Pre-Crisis Peak" },
    @{ Date = "2009-03-09"; Price = 26.10; Type = "LOW"; Name = "Financial Crisis Bottom" },
    @{ Date = "2020-02-19"; Price = 242.97; Type = "HIGH"; Name = "Pre-COVID Peak" },
    @{ Date = "2020-03-23"; Price = 175.17; Type = "LOW"; Name = "COVID Bottom" },
    @{ Date = "2021-11-22"; Price = 409.52; Type = "HIGH"; Name = "2021 ATH" },
    @{ Date = "2022-10-13"; Price = 275.84; Type = "LOW"; Name = "2022 Bottom" },
    @{ Date = "2025-02-19"; Price = 554.39; Type = "HIGH"; Name = "2025 ATH" },
    @{ Date = "2025-04-07"; Price = 435.77; Type = "LOW"; Name = "2025 Low" }
)

$biblicalCycles = @(40, 49, 72, 90, 120, 144, 180, 216, 270, 360, 720)

Write-Host "`n=== QQQ BIBLICAL CYCLES FROM MAJOR PIVOTS ===" -ForegroundColor Cyan
Write-Host "Data: $($qqqData.Count) rows"
Write-Host ""

foreach ($pivot in $majorPivots) {
    $pivotDate = [DateTime]::Parse($pivot.Date)
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host "$($pivot.Name): $($pivot.Date) @ `$$($pivot.Price) ($($pivot.Type))" -ForegroundColor Yellow
    Write-Host ""

    foreach ($cycle in $biblicalCycles) {
        $targetDate = $pivotDate.AddDays($cycle)

        $matchingRow = $qqqData | Where-Object {
            $rowDate = [DateTime]::Parse($_.Date)
            [Math]::Abs(($rowDate - $targetDate).Days) -le 3
        } | Select-Object -First 1

        if ($matchingRow) {
            $actualDate = $matchingRow.Date
            $closePrice = [double]$matchingRow.Close
            $highPrice = [double]$matchingRow.High
            $lowPrice = [double]$matchingRow.Low

            $change = (($closePrice - $pivot.Price) / $pivot.Price * 100)
            $direction = if ($change -gt 0) { "UP" } else { "DOWN" }

            # Check for local high/low
            $idx = 0
            for ($i = 0; $i -lt $qqqData.Count; $i++) {
                if ($qqqData[$i].Date -eq $actualDate) { $idx = $i; break }
            }

            $isLocalHigh = $true
            $isLocalLow = $true

            if ($idx -gt 5 -and $idx -lt ($qqqData.Count - 5)) {
                for ($i = ($idx - 5); $i -le ($idx + 5); $i++) {
                    if ($i -ne $idx) {
                        if ([double]$qqqData[$i].High -gt $highPrice) { $isLocalHigh = $false }
                        if ([double]$qqqData[$i].Low -lt $lowPrice) { $isLocalLow = $false }
                    }
                }
            } else {
                $isLocalHigh = $false
                $isLocalLow = $false
            }

            $status = ""
            $color = "White"
            if ($isLocalHigh) { $status = " <<< LOCAL HIGH"; $color = "Green" }
            if ($isLocalLow) { $status = " <<< LOCAL LOW"; $color = "Red" }

            $cycleName = switch ($cycle) {
                40 { "Flood" }
                49 { "Jubilee" }
                72 { "Circle" }
                90 { "Quarter" }
                120 { "1/3 Yr" }
                144 { "SACRED" }
                180 { "Half" }
                216 { "666" }
                270 { "3/4 Yr" }
                360 { "Year" }
                720 { "2 Yr" }
                default { "" }
            }

            Write-Host ("  {0,4} days ({1,-7}): {2} @ `${3,7:N2} | {4}: {5,6:N1}%{6}" -f $cycle, $cycleName, $actualDate, $closePrice, $direction, [Math]::Abs($change), $status) -ForegroundColor $color
        }
    }
    Write-Host ""
}

# Count reversals
Write-Host "=== REVERSAL SUMMARY ===" -ForegroundColor Magenta
Write-Host "Cycles that marked LOCAL HIGHS or LOWS are significant turning points."
Write-Host "These are the Biblical numbers that 'work' on QQQ."
