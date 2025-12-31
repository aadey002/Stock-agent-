# Check Biblical Cycles from Feb 19, 2025 ATH
# =============================================

$spyData = Import-Csv "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv"
$feb2025 = [DateTime]::Parse("2025-02-19")
$athPrice = 614.42

Write-Host "`n=== BIBLICAL CYCLES FROM FEB 19, 2025 ATH (`$614.42) ===" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

$biblicalCycles = @(
    @{ Days = 7; Name = "Creation (7)" },
    @{ Days = 12; Name = "Tribes (12)" },
    @{ Days = 21; Name = "3x7 Daniel" },
    @{ Days = 28; Name = "4x7 Lunar" },
    @{ Days = 40; Name = "Flood/Moses" },
    @{ Days = 49; Name = "Jubilee 7x7" },
    @{ Days = 50; Name = "Pentecost" },
    @{ Days = 72; Name = "Circle/5" },
    @{ Days = 90; Name = "Quarter" },
    @{ Days = 120; Name = "1/3 Year" },
    @{ Days = 144; Name = "SACRED 12x12" },
    @{ Days = 150; Name = "Flood Duration" },
    @{ Days = 180; Name = "Half Year" },
    @{ Days = 216; Name = "6x6x6" },
    @{ Days = 270; Name = "3/4 Year" },
    @{ Days = 288; Name = "2x144" },
    @{ Days = 360; Name = "Prophetic Year" }
)

Write-Host ("{0,-6} {1,-16} {2,-12} {3,-10} {4,-8} {5,-10} {6}" -f "DAYS", "CYCLE NAME", "TARGET DATE", "ACTUAL", "PRICE", "CHANGE", "STATUS")
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

foreach ($cycle in $biblicalCycles) {
    $targetDate = $feb2025.AddDays($cycle.Days)
    $targetDateStr = $targetDate.ToString("yyyy-MM-dd")

    # Find closest trading day
    $matchingRow = $spyData | Where-Object {
        $rowDate = [DateTime]::Parse($_.Date)
        [Math]::Abs(($rowDate - $targetDate).Days) -le 2
    } | Select-Object -First 1

    if ($matchingRow) {
        $actualDate = $matchingRow.Date
        $closePrice = [double]$matchingRow.Close
        $highPrice = [double]$matchingRow.High
        $lowPrice = [double]$matchingRow.Low

        $change = (($closePrice - $athPrice) / $athPrice * 100)
        $changeStr = if ($change -ge 0) { "+$([Math]::Round($change, 1))%" } else { "$([Math]::Round($change, 1))%" }

        # Check for local high/low (5-day window)
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

        $status = "---"
        $color = "White"
        if ($isLocalHigh) { $status = "LOCAL HIGH"; $color = "Green" }
        if ($isLocalLow) { $status = "LOCAL LOW"; $color = "Red" }

        # Check if today or future
        $today = Get-Date
        if ([DateTime]::Parse($actualDate) -gt $today) {
            $status = "FUTURE"
            $color = "DarkGray"
            $closePrice = "---"
            $changeStr = "---"
        }

        Write-Host ("{0,-6} {1,-16} {2,-12} {3,-10} {4,-8} {5,-10} {6}" -f $cycle.Days, $cycle.Name, $targetDateStr, $actualDate, $(if ($closePrice -eq "---") { "---" } else { "`$$([Math]::Round($closePrice, 2))" }), $changeStr, $status) -ForegroundColor $color
    } else {
        Write-Host ("{0,-6} {1,-16} {2,-12} {3,-10} {4,-8} {5,-10} {6}" -f $cycle.Days, $cycle.Name, $targetDateStr, "NO DATA", "---", "---", "FUTURE") -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Find the April 7 low
Write-Host "`n=== NOTABLE: April 7, 2025 Low ===" -ForegroundColor Yellow
$apr7 = $spyData | Where-Object { $_.Date -like "2025-04-07*" }
if ($apr7) {
    $daysFromATH = ([DateTime]::Parse($apr7.Date) - $feb2025).Days
    Write-Host "Date: $($apr7.Date)"
    Write-Host "Price: `$$($apr7.Close)"
    Write-Host "Days from Feb 19 ATH: $daysFromATH days"
    Write-Host "Nearest Biblical: 49 days (Jubilee) - off by $($daysFromATH - 49) days"
}

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "ATH: Feb 19, 2025 @ `$614.42"
Write-Host "Major Low: Apr 7, 2025 @ ~`$506 (47 days from ATH)"
Write-Host ""
Write-Host "This low came 2 days BEFORE the 49-day Jubilee cycle!"
Write-Host "The 49-day (7x7) Jubilee cycle marked the REVERSAL ZONE."
