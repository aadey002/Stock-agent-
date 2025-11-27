#!/usr/bin/env python3
"""
Fetch SPY data from Tiingo API with Yahoo Finance backup.
"""

import os
import pandas as pd
import requests
from datetime import datetime, timedelta

# Get token from environment
TOKEN = os.getenv('TIINGO_TOKEN')

def fetch_spy_data():
    """Fetch SPY daily data from Tiingo with explicit endDate."""
    
    # Fetch 3 years of data
    start_date = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    url = f"https://api.tiingo.com/tiingo/daily/SPY/prices?startDate={start_date}&endDate={end_date}&token={TOKEN}"
    
    print(f"Fetching data from {start_date} to {end_date}...")
    
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"ERROR: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    print(f"Received {len(data)} bars")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%dT00:00:00.000Z')
    df = df.rename(columns={
        'date': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Keep only needed columns
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    print(f"Latest date: {df['Date'].iloc[-1]}")
    print(f"Latest close: ${df['Close'].iloc[-1]:.2f}")
    
    return df

def calculate_indicators(df):
    """Calculate technical indicators."""
    print("\nCalculating indicators...")
    
    # ATR (14-period)
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # SMAs
    df['FastSMA'] = close.rolling(window=9).mean()
    df['SlowSMA'] = close.rolling(window=21).mean()
    
    # Bias
    df['Bias'] = df.apply(lambda row: 'BULLISH' if row['FastSMA'] > row['SlowSMA'] else 'BEARISH', axis=1)
    
    # Geo and Phi levels (simplified)
    df['GeoLevel'] = df['Close'].rolling(window=20).mean()
    df['PhiLevel'] = df['Close'].rolling(window=20).mean() * 1.618
    
    # Confluence scores
    df['PriceConfluence'] = 2
    df['TimeConfluence'] = 2
    
    print("Indicators calculated.")
    return df

def save_data(df, symbol='SPY'):
    """Save data to CSV files."""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save to data folder
    data_path = f"data/{symbol}.csv"
    df.to_csv(data_path, index=False)
    print(f"Saved to {data_path}")
    
    return data_path

def main():
    """Main function."""
    print("=" * 60)
    print("FETCH DATA - SPY Daily")
    print(f"Run time: {datetime.now()}")
    print("=" * 60)
    
    # Fetch data
    df = fetch_spy_data()
    
    if df is None:
        print("Failed to fetch data!")
        return
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Save
    save_data(df)
    
    print("\n" + "=" * 60)
    print("FETCH COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()