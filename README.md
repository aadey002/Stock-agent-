# Confluence Agent

Daily Gann + Fibonacci + Time-cycle agent using Tiingo data.

- Fetches OHLCV from Tiingo for configured symbols
- Maintains `data/<SYMBOL>.csv`
- Logs trades and P&L in `reports/portfolio_trades.csv`
- Runs automatically via GitHub Actions
