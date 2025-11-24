#!/usr/bin/env python3
"""
Data Fetcher - Fetches SPY data from Tiingo and saves with indicators
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
TOKEN = os.environ.get('TIINGO_TOKEN', '14febdd1820f1a4aa11e1bf920cd3a38950b77a5')
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_spy_data():
    """Fetch SPY data from Tiingo API."""
    print("=" * 60)
    print("FETCHING SPY DATA FROM TIINGO")
    print("=" * 60)
    
    # Fetch 3 years of data
    start_date = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
    url = f"https://api.tiingo.com/tiingo/daily/SPY/prices?startDate={start_date}&token={TOKEN}"
    
    print(f"Fetching data from {start_date}...")
    response = requests.get(url)
    
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
    df['FastSMA'] = close.rolling(window=10).mean()
    df['SlowSMA'] = close.rolling(window=50).mean()
    
    # Bias
    df['Bias'] = 'NEUTRAL'
    df.loc[df['FastSMA'] > df['SlowSMA'], 'Bias'] = 'BULLISH'
    df.loc[df['FastSMA'] < df['SlowSMA'], 'Bias'] = 'BEARISH'
    
    # Geometric and Phi levels (simplified)
    df['GeoLevel'] = df['Close'] * 0.618
    df['PhiLevel'] = df['Close'] * 1.618
    
    # Confluence markers (simplified)
    df['PriceConfluence'] = 0
    df['TimeConfluence'] = 0
    
    # Mark confluence when price near SMA crossover
    sma_diff = abs(df['FastSMA'] - df['SlowSMA'])
    df.loc[sma_diff < df['ATR'], 'PriceConfluence'] = 1
    
    # Mark time confluence on specific days
    df['DayOfWeek'] = pd.to_datetime(df['Date']).dt.dayofweek
    df.loc[df['DayOfWeek'].isin([1, 3]), 'TimeConfluence'] = 1  # Tue, Thu
    
    # Add higher confluence for strong signals
    df.loc[(df['PriceConfluence'] == 1) & (df['Bias'] != 'NEUTRAL'), 'PriceConfluence'] = 2
    df.loc[(df['TimeConfluence'] == 1) & (df['PriceConfluence'] >= 1), 'TimeConfluence'] = 2
    
    # Drop helper column
    df = df.drop(columns=['DayOfWeek'])
    
    # Round values
    for col in ['ATR', 'FastSMA', 'SlowSMA', 'GeoLevel', 'PhiLevel']:
        df[col] = df[col].round(2)
    
    print("Indicators calculated!")
    return df

def save_data(df):
    """Save data to CSV."""
    output_path = os.path.join(DATA_DIR, "SPY_confluence.csv")
    
    # Drop NaN rows (from indicator calculations)
    df = df.dropna()
    
    df.to_csv(output_path, index=False)
    
    file_size = os.path.getsize(output_path)
    print(f"\nSaved to: {output_path}")
    print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"Total rows: {len(df)}")
    
    return output_path

def main():
    """Main execution."""
    # Fetch data
    df = fetch_spy_data()
    if df is None:
        return
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Save
    output_path = save_data(df)
    
    print("\n" + "=" * 60)
    print("DATA FETCH COMPLETE!")
    print("=" * 60)
    print(f"\nYou can now run:")
    print("  python agent_3_waves.py")
    print("  python run_all_agents.py")
    print("=" * 60)

if __name__ == "__main__":
    main()