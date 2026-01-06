#!/usr/bin/env python3
"""
Multi-Symbol Data Fetcher using yfinance (FREE - no API key needed)
Fetches 3 years of data for all symbols
"""
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Main ETFs + All Sector ETFs + Individual Stocks (must match web/index.html SYMBOLS array)
SYMBOLS = [
    'SPY', 'QQQ', 'IWM', 'DIA',  # Main ETFs
    'XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLU', 'XLB', 'XLC', 'XLRE', 'XLY',  # Sector ETFs
    'MSFT', 'AAPL', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA',  # Tech Giants
    'JPM', 'MA', 'LLY', 'WMT', 'ORCL', 'CVX', 'CSCO'  # Other Major Stocks
]
DATA_DIR = 'data'
LOOKBACK_DAYS = 1095  # 3 years

def fetch_symbol(symbol):
    """Fetch historical data for a symbol using yfinance"""
    print(f"Fetching {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        
        df = ticker.history(start=start_date.strftime('%Y-%m-%d'))
        
        if df.empty:
            print(f"  WARNING: No data for {symbol}")
            return None
        
        # Reset index and format
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

def fetch_vix():
    """Fetch VIX data with special handling (no volume, add bias indicator)"""
    print("Fetching VIX (^VIX)...")
    try:
        ticker = yf.Ticker('^VIX')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)

        df = ticker.history(start=start_date.strftime('%Y-%m-%d'))

        if df.empty:
            print("  WARNING: No data for VIX")
            return None

        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

        # VIX has no meaningful volume, set to 0
        df['Volume'] = 0

        # Add VIX-specific indicators
        df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
        df['FastSMA'] = df['Close'].rolling(5).mean()
        df['SlowSMA'] = df['Close'].rolling(20).mean()

        # VIX Bias: HIGH (fear) > 20, LOW (complacency) < 15, NORMAL 15-20
        df['Bias'] = df['Close'].apply(lambda x: 'HIGH' if x > 20 else ('LOW' if x < 15 else 'NORMAL'))

        # Keep needed columns
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'ATR', 'FastSMA', 'SlowSMA', 'Bias']]

        print(f"  SUCCESS: {len(df)} bars for VIX")
        return df

    except Exception as e:
        print(f"  ERROR fetching VIX: {e}")
        return None

def main():
    print("=" * 50)
    print("MULTI-SYMBOL FETCHER (yfinance - NO API KEY)")
    print(f"Fetching {LOOKBACK_DAYS} days (3 years) of data")
    print("=" * 50)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for symbol in SYMBOLS:
        df = fetch_symbol(symbol)
        if df is not None:
            filepath = os.path.join(DATA_DIR, f'{symbol}.csv')
            df.to_csv(filepath, index=False)
            print(f"  Saved to {filepath}")
    
    # Fetch VIX separately with special handling
    vix_df = fetch_vix()
    if vix_df is not None:
        filepath = os.path.join(DATA_DIR, 'VIX.csv')
        vix_df.to_csv(filepath, index=False)
        print(f"  Saved to {filepath}")

    print("=" * 50)
    print("DONE!")

if __name__ == '__main__':
    main()
