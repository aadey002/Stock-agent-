# Fetch full SPY history from Yahoo Finance
$startDate = 727747200  # Jan 22, 1993
$endDate = [int](Get-Date -UFormat %s)
$url = "https://query1.finance.yahoo.com/v7/finance/download/SPY?period1=$startDate&period2=$endDate&interval=1d&events=history"

Write-Host "Downloading SPY full history from inception (1993)..."
Write-Host $url

try {
    Invoke-WebRequest -Uri $url -OutFile "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv" -Headers @{"User-Agent"="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    Write-Host "Download complete!"

    $content = Get-Content "C:\Users\adeto\Documents\Stock-agent-\data\SPY_full.csv"
    Write-Host "Total rows: $($content.Count)"
    Write-Host ""
    Write-Host "First 3 rows:"
    $content | Select-Object -First 3
    Write-Host ""
    Write-Host "Last 3 rows:"
    $content | Select-Object -Last 3
} catch {
    Write-Host "Error: $_"
}
