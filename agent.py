#!/usr/bin/env python3
"""
SPY Data Fetcher using yfinance (FREE - no API key needed)
With intraday support for live market data
"""

import os
import csv
from datetime import datetime, timedelta

# Try to import yfinance
try:
    import yfinance as yf
    print("yfinance imported successfully")
except ImportError:
    print("yfinance not installed. Installing...")
    os.system("pip install yfinance")
    import yfinance as yf

SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA']

def fetch_symbol_data(symbol, days=1095):
    """Fetch historical data using yfinance with intraday support"""
    print(f"Fetching {symbol} data...")

    try:
        import pandas as pd
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch daily historical data
        df = ticker.history(start=start_date.strftime('%Y-%m-%d'),
                           end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'))

        if df.empty:
            print(f"   No data for {symbol}")
            return None

        print(f"   Got {len(df)} daily bars for {symbol}")

        # Fetch intraday data for today (during market hours)
        try:
            today_df = ticker.history(period='1d', interval='5m')
            if not today_df.empty and len(today_df) > 0:
                # Get OHLCV from intraday data
                latest = today_df.iloc[-1]
                today_open = today_df.iloc[0]['Open']
                today_high = today_df['High'].max()
                today_low = today_df['Low'].min()
                today_close = latest['Close']
                today_volume = int(today_df['Volume'].sum())

                today_date = today_df.index[-1].date()
                last_daily_date = df.index[-1].date()

                # Add today's data if not already present
                if last_daily_date < today_date:
                    today_row = pd.DataFrame({
                        'Open': [today_open],
                        'High': [today_high],
                        'Low': [today_low],
                        'Close': [today_close],
                        'Volume': [today_volume],
                        'Dividends': [0.0],
                        'Stock Splits': [0.0]
                    }, index=[pd.Timestamp(today_date)])
                    df = pd.concat([df, today_row])
                    print(f"   Added today's live data: ${today_close:.2f} (as of {today_df.index[-1].strftime('%H:%M')})")
        except Exception as e:
            print(f"   Intraday fetch note: {e}")

        return df
    except Exception as e:
        print(f"   Error fetching {symbol}: {e}")
        return None

def calculate_indicators(df):
    """Calculate technical indicators"""
    
    # ATR (14-period)
    df['TR'] = df[['High', 'Low', 'Close']].apply(
        lambda x: max(x['High'] - x['Low'], 
                     abs(x['High'] - x['Close']), 
                     abs(x['Low'] - x['Close'])), axis=1)
    df['ATR'] = df['TR'].rolling(window=14).mean()
    
    # SMAs
    df['FastSMA'] = df['Close'].rolling(window=9).mean()
    df['SlowSMA'] = df['Close'].rolling(window=21).mean()
    
    # Bias
    df['Bias'] = df.apply(lambda x: 'BULLISH' if x['FastSMA'] > x['SlowSMA'] 
                          else ('BEARISH' if x['FastSMA'] < x['SlowSMA'] else 'NEUTRAL'), axis=1)
    
    # GeoLevel and PhiLevel
    df['GeoLevel'] = ((df['Close'] ** 0.5) + 0.125) ** 2
    df['PhiLevel'] = df['Close'] * 1.618
    
    # PriceConfluence (simplified)
    df['PriceConfluence'] = 0
    df.loc[(df['Bias'] == 'BULLISH') & (df['Close'] > df['FastSMA']), 'PriceConfluence'] += 1
    df.loc[(df['Bias'] == 'BEARISH') & (df['Close'] < df['FastSMA']), 'PriceConfluence'] += 1
    df.loc[df['Close'] > df['Close'].shift(1), 'PriceConfluence'] += 1
    df.loc[df['Volume'] > df['Volume'].shift(1), 'PriceConfluence'] += 1
    
    # TimeConfluence
    df['TimeConfluence'] = df.index.dayofweek.map(lambda x: 2 if x in [1,2,3] else 1)
    
    return df

def save_to_csv(symbol, df, folder='data'):
    """Save data to CSV"""
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f'{symbol}.csv')
    
    # Prepare output
    output_df = df[['Open', 'High', 'Low', 'Close', 'Volume', 
                    'ATR', 'FastSMA', 'SlowSMA', 'Bias',
                    'GeoLevel', 'PhiLevel', 'PriceConfluence', 'TimeConfluence']].copy()
    
    output_df = output_df.round({'Open': 2, 'High': 2, 'Low': 2, 'Close': 2,
                                  'ATR': 4, 'FastSMA': 2, 'SlowSMA': 2,
                                  'GeoLevel': 2, 'PhiLevel': 2})
    
    output_df.index.name = 'Date'
    output_df.to_csv(filepath)
    
    print(f"   Saved {len(output_df)} bars to {filepath}")
    return filepath

def main():
    print("=" * 50)
    print("YFINANCE DATA FETCHER (FREE) - WITH INTRADAY")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    for symbol in SYMBOLS:
        print(f"\n{'='*30}")
        df = fetch_symbol_data(symbol)
        
        if df is not None and not df.empty:
            df = calculate_indicators(df)
            save_to_csv(symbol, df)
    
    print("\nCOMPLETE!")
    
    # Show latest data
    if os.path.exists('data/SPY.csv'):
        print("\nLatest SPY data:")
        with open('data/SPY.csv', 'r') as f:
            lines = f.readlines()
            for line in lines[-3:]:
                print(f"   {line.strip()}")

if __name__ == '__main__':
    main()
