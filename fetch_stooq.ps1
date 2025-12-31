# Fetch full SPY history from Stooq
Write-Host "Downloading SPY full history from Stooq (1993-2025)..."

$url = "https://stooq.com/q/d/l/?s=spy.us&d1=19930122&d2=20251231&i=d"
Write-Host $url

try {
    Invoke-WebRequest -Uri $url -OutFile "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv" -Headers @{"User-Agent"="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    Write-Host "Download complete!"

    $content = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv"
    $rowCount = $content.Count
    Write-Host "Total rows: $rowCount"
    Write-Host ""
    Write-Host "First 5 rows:"
    $content | Select-Object -First 5
    Write-Host ""
    Write-Host "Last 5 rows:"
    $content | Select-Object -Last 5
} catch {
    Write-Host "Error: $_"
}
