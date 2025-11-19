#!/usr/bin/env python3
"""
Minimal Tiingo test agent.

Purpose:
- Fetch recent SPY daily prices from Tiingo using TIINGO_TOKEN.
- Create data/SPY.csv
- Create reports/portfolio_trades.csv (dummy summary)
- Print clear log messages so we can see what happened in Actions.
"""

import os
import csv
import json
import pathlib
import datetime
import urllib.request


DATA_DIR = pathlib.Path("data")
REPORT_DIR = pathlib.Path("reports")
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def tiingo_prices(symbol: str, start_date: str, token: str):
    url = (
        f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
        f"?startDate={start_date}&token={token}"
    )
    print(f"[INFO] Requesting {symbol} data from Tiingo starting {start_date}")
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
    rows = []
    for b in data:
        d = b["date"][:10]
        rows.append(
            {
                "Date": d,
                "Open": float(b["open"]),
                "High": float(b["high"]),
                "Low": float(b["low"]),
                "Close": float(b["close"]),
                "Volume": float(b.get("volume", 0)),
            }
        )
    rows.sort(key=lambda x: x["Date"])
    print(f"[INFO] Received {len(rows)} rows for {symbol}")
    return rows


def save_prices(symbol: str, rows):
    path = DATA_DIR / f"{symbol}.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["Date", "Open", "High", "Low", "Close", "Volume"]
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[INFO] Saved {len(rows)} rows to {path}")


def write_dummy_trades(symbol: str, rows):
    """
    For now just write a simple summary so we confirm reports/ works.
    """
    path = REPORT_DIR / "portfolio_trades.csv"
    last = rows[-1] if rows else None
    with path.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Symbol",
                "LastDate",
                "LastClose",
                "TotalRows",
            ],
        )
        w.writeheader()
        if last:
            w.writerow(
                {
                    "Symbol": symbol,
                    "LastDate": last["Date"],
                    "LastClose": last["Close"],
                    "TotalRows": len(rows),
                }
            )
    print(f"[INFO] Wrote dummy trades summary to {path}")


def main():
    token = os.environ.get("TIINGO_TOKEN")
    if not token:
        raise SystemExit("[ERROR] TIINGO_TOKEN environment variable is required")

    symbol = os.environ.get("SYMBOLS", "SPY").split(",")[0].strip() or "SPY"

    # pull the last 90 days as a simple test
    start = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    rows = tiingo_prices(symbol, start, token)
    if not rows:
        print("[WARN] No data returned from Tiingo.")
        return

    save_prices(symbol, rows)
    write_dummy_trades(symbol, rows)
    print("[INFO] Done.")


if __name__ == "__main__":
    main()

     
    
           
