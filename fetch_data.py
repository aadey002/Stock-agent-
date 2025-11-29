The `fetch_all_symbols.py` file still uses Tiingo. Let's update it to use yfinance:

```powershell
@"
#!/usr/bin/env python3
"""
Multi-Symbol Data Fetcher using yfinance (FREE - no API key needed)
"""
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA']
DATA_DIR = 'data'

def fetch_symbol(symbol, days=500):
    """Fetch historical data for a symbol using yfinance"""
    print(f"Fetching {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = ticker.history(start=start_date.strftime('%Y-%m-%d'))
        
        if df.empty:
            print(f"  WARNING: No data for {symbol}")
            return None
        
        # Rename columns to match expected format
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'Date',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        })
        
        # Keep only needed columns
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        print(f"  SUCCESS: {len(df)} bars for {symbol}")
        return df
        
    except Exception as e:
        print(f"  ERROR fetching {symbol}: {e}")
        return None

def main():
    print("=" * 50)
    print("MULTI-SYMBOL FETCHER (yfinance)")
    print("=" * 50)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for symbol in SYMBOLS:
        df = fetch_symbol(symbol)
        if df is not None:
            filepath = os.path.join(DATA_DIR, f'{symbol}.csv')
            df.to_csv(filepath, index=False)
            print(f"  Saved to {filepath}")
    
    print("=" * 50)
    print("DONE!")

if __name__ == '__main__':
    main()
"@ | Out-File -FilePath "fetch_all_symbols.py" -Encoding UTF8

git add fetch_all_symbols.py
git commit -m "Update fetch_all_symbols.py to use yfinance"
git push origin main
```

This replaces Tiingo with yfinance in the multi-symbol fetcher. Run it and let me know!
