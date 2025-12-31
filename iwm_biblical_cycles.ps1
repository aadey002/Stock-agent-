# IWM Biblical Cycles from Major Pivots
# ======================================

$iwmData = Import-Csv "C:\Users\adeto\Documents\Stock-agent-\data\IWM_full.csv"

$majorPivots = @(
    @{ Date = "2007-07-09"; Price = 72.86; Type = "HIGH"; Name = "Pre-Crisis Peak" },
    @{ Date = "2009-03-09"; Price = 29.22; Type = "LOW"; Name = "Financial Crisis Bottom" },
    @{ Date = "2020-02-12"; Price = 166.89; Type = "HIGH"; Name = "Pre-COVID Peak" },
    @{ Date = "2020-03-19"; Price = 100.47; Type = "LOW"; Name = "COVID Bottom" },
    @{ Date = "2021-11-08"; Price = 239.48; Type = "HIGH"; Name = "2021 ATH" },
    @{ Date = "2022-06-16"; Price = 163.06; Type = "LOW"; Name = "2022 Bottom" },
    @{ Date = "2024-11-25"; Price = 242.40; Type = "HIGH"; Name = "2024 ATH" },
    @{ Date = "2025-04-07"; Price = 179.55; Type = "LOW"; Name = "2025 Low" }
)

$biblicalCycles = @(40, 49, 72, 90, 120, 144, 180, 216, 270, 360, 720)

Write-Host "`n=== IWM BIBLICAL CYCLES FROM MAJOR PIVOTS ===" -ForegroundColor Cyan
Write-Host "Data: $($iwmData.Count) rows"
Write-Host ""

foreach ($pivot in $majorPivots) {
    $pivotDate = [DateTime]::Parse($pivot.Date)
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host "$($pivot.Name): $($pivot.Date) @ `$$($pivot.Price) ($($pivot.Type))" -ForegroundColor Yellow
    Write-Host ""

    foreach ($cycle in $biblicalCycles) {
        $targetDate = $pivotDate.AddDays($cycle)

        $matchingRow = $iwmData | Where-Object {
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
            for ($i = 0; $i -lt $iwmData.Count; $i++) {
                if ($iwmData[$i].Date -eq $actualDate) { $idx = $i; break }
            }

            $isLocalHigh = $true
            $isLocalLow = $true

            if ($idx -gt 5 -and $idx -lt ($iwmData.Count - 5)) {
                for ($i = ($idx - 5); $i -le ($idx + 5); $i++) {
                    if ($i -ne $idx) {
                        if ([double]$iwmData[$i].High -gt $highPrice) { $isLocalHigh = $false }
                        if ([double]$iwmData[$i].Low -lt $lowPrice) { $isLocalLow = $false }
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
Write-Host "These are the Biblical numbers that 'work' on IWM."

# Check Feb 2025 cycles specifically
Write-Host ""
Write-Host "=== FEBRUARY 2025 ANALYSIS ===" -ForegroundColor Cyan
Write-Host "IWM ATH: Nov 25, 2024 @ `$242.40"
Write-Host "IWM 2025 Low: Apr 7, 2025 @ `$179.55"
$athDate = [DateTime]::Parse("2024-11-25")
$lowDate = [DateTime]::Parse("2025-04-07")
$daysBetween = ($lowDate - $athDate).Days
Write-Host "Days from ATH to Low: $daysBetween days"
Write-Host ""
Write-Host "Nearest Biblical cycles:"
Write-Host "  120 days (1/3 Year) - off by $($daysBetween - 120) days"
Write-Host "  144 days (SACRED 12x12) - off by $(144 - $daysBetween) days"
