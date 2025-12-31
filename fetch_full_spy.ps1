# Try multiple sources for full SPY history

Write-Host "Attempting to download full SPY history..."
Write-Host ""

# Try Stooq with different ticker formats
$urls = @(
    @{name="Stooq SPY.US"; url="https://stooq.com/q/d/l/?s=spy.us&d1=19930101&d2=20251231&i=d"},
    @{name="Stooq SPY"; url="https://stooq.com/q/d/l/?s=spy&d1=19930101&d2=20251231&i=d"},
    @{name="Stooq ^SPX"; url="https://stooq.com/q/d/l/?s=^spx&d1=19930101&d2=20251231&i=d"}
)

foreach ($source in $urls) {
    Write-Host "Trying $($source.name)..."
    try {
        $tempFile = "C:\Users\adeto\Documents\Stock-agent-\data\temp_$($source.name -replace '[^a-zA-Z0-9]','').csv"
        Invoke-WebRequest -Uri $source.url -OutFile $tempFile -Headers @{"User-Agent"="Mozilla/5.0"} -TimeoutSec 30
        $content = Get-Content $tempFile
        $firstDataRow = $content | Select-Object -Skip 1 -First 1
        $lastDataRow = $content | Select-Object -Last 1
        Write-Host "  Rows: $($content.Count)"
        Write-Host "  First: $firstDataRow"
        Write-Host "  Last: $lastDataRow"
        Write-Host ""
    } catch {
        Write-Host "  Error: $($_.Exception.Message)"
    }
}

# Check current data
Write-Host "Current SPY.csv has:"
$current = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\SPY.csv"
Write-Host "  Rows: $($current.Count)"
$current | Select-Object -Skip 1 -First 1
$current | Select-Object -Last 1
