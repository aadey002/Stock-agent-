# Gann Biblical Cycles from Major Pivots
# ==========================================

# Major pivots (manually identified significant turning points)
$majorPivots = @(
    @{ Date = "2009-03-06"; Price = 68.34; Type = "LOW"; Name = "Generational Bottom" },
    @{ Date = "2020-02-19"; Price = 338.62; Type = "HIGH"; Name = "Pre-COVID Peak" },
    @{ Date = "2020-03-23"; Price = 223.74; Type = "LOW"; Name = "COVID Bottom" },
    @{ Date = "2022-01-04"; Price = 479.35; Type = "HIGH"; Name = "2022 Peak" },
    @{ Date = "2022-10-13"; Price = 366.99; Type = "LOW"; Name = "2022 Bottom" }
)

# Biblical cycle days
$biblicalCycles = @(40, 49, 72, 90, 120, 144, 180, 216, 270, 360, 720, 1260)

# Load SPY full data
$spyData = Import-Csv "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv"
Write-Host "`n=== GANN BIBLICAL CYCLES FROM MAJOR PIVOTS ===" -ForegroundColor Cyan
Write-Host "Testing if reversals occurred at Biblical cycle dates"
Write-Host "Data: $($spyData.Count) rows from $($spyData[0].Date) to $($spyData[-1].Date)`n"

foreach ($pivot in $majorPivots) {
    $pivotDate = [DateTime]::Parse($pivot.Date)
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host "PIVOT: $($pivot.Name)" -ForegroundColor Yellow
    Write-Host "Date: $($pivot.Date) | Price: `$$($pivot.Price) | Type: $($pivot.Type)"
    Write-Host ""

    foreach ($cycle in $biblicalCycles) {
        $targetDate = $pivotDate.AddDays($cycle)
        $targetDateStr = $targetDate.ToString("yyyy-MM-dd")

        # Find closest trading day in data
        $matchingRow = $spyData | Where-Object {
            $rowDate = [DateTime]::Parse($_.Date)
            [Math]::Abs(($rowDate - $targetDate).Days) -le 3
        } | Select-Object -First 1

        if ($matchingRow) {
            $actualDate = $matchingRow.Date
            $closePrice = [double]$matchingRow.Close
            $highPrice = [double]$matchingRow.High
            $lowPrice = [double]$matchingRow.Low

            # Calculate change from pivot
            $changeFromPivot = (($closePrice - $pivot.Price) / $pivot.Price * 100)
            $direction = if ($changeFromPivot -gt 0) { "UP" } else { "DOWN" }

            # Check if this was near a local high/low (potential reversal)
            $idx = 0
            for ($i = 0; $i -lt $spyData.Count; $i++) {
                if ($spyData[$i].Date -eq $actualDate) { $idx = $i; break }
            }

            $isLocalHigh = $true
            $isLocalLow = $true

            if ($idx -gt 5 -and $idx -lt ($spyData.Count - 5)) {
                for ($i = ($idx - 5); $i -le ($idx + 5); $i++) {
                    if ($i -ne $idx) {
                        if ([double]$spyData[$i].High -gt $highPrice) { $isLocalHigh = $false }
                        if ([double]$spyData[$i].Low -lt $lowPrice) { $isLocalLow = $false }
                    }
                }
            } else {
                $isLocalHigh = $false
                $isLocalLow = $false
            }

            $reversalFlag = ""
            if ($isLocalHigh) { $reversalFlag = " <<< LOCAL HIGH" }
            if ($isLocalLow) { $reversalFlag = " <<< LOCAL LOW" }

            $cycleName = switch ($cycle) {
                40 { "Flood/Moses" }
                49 { "Jubilee 7x7" }
                72 { "Circle div 5" }
                90 { "Quarter" }
                120 { "1/3 Year" }
                144 { "SACRED 12x12" }
                180 { "Half Year" }
                216 { "6x6x6" }
                270 { "3/4 Year" }
                360 { "Prophetic Year" }
                720 { "2 Years" }
                1260 { "Daniel Days" }
                default { "" }
            }

            $color = "White"
            if ($reversalFlag -ne "") { $color = "Green" }

            Write-Host ("  {0,4} days ({1,-14}): {2} @ `${3,7:N2} | {4}: {5,6:N1}%{6}" -f $cycle, $cycleName, $actualDate, $closePrice, $direction, [Math]::Abs($changeFromPivot), $reversalFlag) -ForegroundColor $color
        }
    }
    Write-Host ""
}

# Special analysis: From March 6, 2009 (THE bottom)
Write-Host "`n=== SPECIAL: Cycles from March 6, 2009 (Generational Low) ===" -ForegroundColor Magenta
$march2009 = [DateTime]::Parse("2009-03-06")

$significantCycles = @(
    @{ Days = 144; Name = "144 Sacred" },
    @{ Days = 360; Name = "1 Year Prophetic" },
    @{ Days = 720; Name = "2 Years" },
    @{ Days = 1080; Name = "3 Years" },
    @{ Days = 1440; Name = "4 Years (4x360)" },
    @{ Days = 1800; Name = "5 Years" },
    @{ Days = 2520; Name = "7 Years (Famine)" },
    @{ Days = 3600; Name = "10 Years" },
    @{ Days = 4320; Name = "12 Years (12x360)" },
    @{ Days = 5040; Name = "14 Years (2x7yr)" },
    @{ Days = 5760; Name = "16 Years (16x360)" }
)

foreach ($cycle in $significantCycles) {
    $targetDate = $march2009.AddDays($cycle.Days)
    $targetDateStr = $targetDate.ToString("yyyy-MM-dd")

    $matchingRow = $spyData | Where-Object {
        $rowDate = [DateTime]::Parse($_.Date)
        [Math]::Abs(($rowDate - $targetDate).Days) -le 3
    } | Select-Object -First 1

    if ($matchingRow) {
        Write-Host ("  {0,5} days ({1,-18}): {2} @ `${3:N2}" -f $cycle.Days, $cycle.Name, $matchingRow.Date, [double]$matchingRow.Close)
    } else {
        Write-Host ("  {0,5} days ({1,-18}): {2} (future/no data)" -f $cycle.Days, $cycle.Name, $targetDateStr) -ForegroundColor DarkGray
    }
}

Write-Host "`n=== KEY DATES TO WATCH ===" -ForegroundColor Green

# From recent 2022 bottom (Oct 13, 2022)
$oct2022 = [DateTime]::Parse("2022-10-13")
Write-Host "`nFrom Oct 13, 2022 Bottom (`$366.99):"
@(144, 360, 720, 1080) | ForEach-Object {
    $target = $oct2022.AddDays($_)
    Write-Host "  $_ days: $($target.ToString('yyyy-MM-dd'))"
}

# From recent 2025 high (Feb 19, 2025)
$feb2025 = [DateTime]::Parse("2025-02-19")
Write-Host "`nFrom Feb 19, 2025 ATH (`$614.42):"
@(40, 49, 72, 90, 144, 180) | ForEach-Object {
    $target = $feb2025.AddDays($_)
    Write-Host "  $_ days: $($target.ToString('yyyy-MM-dd'))"
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Look for dates where Biblical cycles CLUSTER from multiple pivots"
Write-Host "These confluence zones have highest probability of significant moves"
