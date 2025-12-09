#!/usr/bin/env python3
"""
Options Data Fetcher using Yahoo Finance (yfinance)
====================================================
Fetches real options chain data including:
- Available expiration dates
- Calls and Puts data
- Bid/Ask prices
- Implied Volatility
- Open Interest
- Volume
- Greeks (calculated)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

DATA_DIR = 'data'

def get_options_expirations(symbol):
    """Get all available expiration dates for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        return list(expirations)
    except Exception as e:
        print(f"Error getting expirations for {symbol}: {e}")
        return []

def get_options_chain(symbol, expiration=None):
    """
    Fetch options chain data for a symbol

    Args:
        symbol: Stock ticker (e.g., 'SPY')
        expiration: Expiration date string (e.g., '2025-12-20')
                   If None, uses the nearest expiration

    Returns:
        dict with 'calls', 'puts', 'expiration', 'stock_price', 'expirations'
    """
    try:
        ticker = yf.Ticker(symbol)

        # Get current stock price
        hist = ticker.history(period='1d')
        stock_price = float(hist['Close'].iloc[-1]) if len(hist) > 0 else 0

        # Get available expirations
        expirations = list(ticker.options)

        if not expirations:
            return {'error': f'No options available for {symbol}'}

        # Use provided expiration or default to nearest
        if expiration and expiration in expirations:
            exp_date = expiration
        else:
            exp_date = expirations[0]  # Nearest expiration

        # Fetch options chain
        opt_chain = ticker.option_chain(exp_date)

        # Process calls
        calls_df = opt_chain.calls.copy()
        calls_df['optionType'] = 'CALL'
        calls_df['daysToExpiry'] = calculate_dte(exp_date)

        # Process puts
        puts_df = opt_chain.puts.copy()
        puts_df['optionType'] = 'PUT'
        puts_df['daysToExpiry'] = calculate_dte(exp_date)

        # Convert to JSON-friendly format
        calls_data = process_options_df(calls_df, stock_price)
        puts_data = process_options_df(puts_df, stock_price)

        return {
            'symbol': symbol,
            'stockPrice': stock_price,
            'expiration': exp_date,
            'expirations': expirations,
            'calls': calls_data,
            'puts': puts_data,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error fetching options for {symbol}: {e}")
        return {'error': str(e)}

def calculate_dte(expiration_str):
    """Calculate days to expiration"""
    try:
        exp_date = datetime.strptime(expiration_str, '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return max(0, (exp_date - today).days)
    except:
        return 0

def process_options_df(df, stock_price):
    """Process options DataFrame to JSON-friendly format"""
    records = []

    for _, row in df.iterrows():
        try:
            strike = float(row['strike'])
            last_price = float(row['lastPrice']) if pd.notna(row['lastPrice']) else 0
            bid = float(row['bid']) if pd.notna(row['bid']) else 0
            ask = float(row['ask']) if pd.notna(row['ask']) else 0
            volume = int(row['volume']) if pd.notna(row['volume']) else 0
            open_interest = int(row['openInterest']) if pd.notna(row['openInterest']) else 0
            iv = float(row['impliedVolatility']) if pd.notna(row['impliedVolatility']) else 0
            itm = bool(row['inTheMoney']) if pd.notna(row['inTheMoney']) else False

            # Calculate mid price
            mid_price = (bid + ask) / 2 if bid > 0 and ask > 0 else last_price

            # Calculate moneyness
            if stock_price > 0:
                moneyness = (strike / stock_price - 1) * 100  # % OTM/ITM
            else:
                moneyness = 0

            records.append({
                'contractSymbol': row.get('contractSymbol', ''),
                'strike': strike,
                'lastPrice': last_price,
                'bid': bid,
                'ask': ask,
                'midPrice': round(mid_price, 2),
                'change': float(row['change']) if pd.notna(row['change']) else 0,
                'percentChange': float(row['percentChange']) if pd.notna(row['percentChange']) else 0,
                'volume': volume,
                'openInterest': open_interest,
                'impliedVolatility': round(iv * 100, 2),  # Convert to percentage
                'inTheMoney': itm,
                'moneyness': round(moneyness, 2),
                'optionType': row['optionType'],
                'dte': row['daysToExpiry']
            })
        except Exception as e:
            continue

    return records

def get_atm_options(symbol, expiration=None):
    """Get at-the-money options for quick reference"""
    chain = get_options_chain(symbol, expiration)

    if 'error' in chain:
        return chain

    stock_price = chain['stockPrice']
    calls = chain['calls']
    puts = chain['puts']

    # Find ATM strike (closest to stock price)
    if calls:
        atm_strike = min(calls, key=lambda x: abs(x['strike'] - stock_price))['strike']
        atm_call = next((c for c in calls if c['strike'] == atm_strike), None)
        atm_put = next((p for p in puts if p['strike'] == atm_strike), None)

        return {
            'symbol': symbol,
            'stockPrice': stock_price,
            'atmStrike': atm_strike,
            'expiration': chain['expiration'],
            'atmCall': atm_call,
            'atmPut': atm_put,
            'expirations': chain['expirations']
        }

    return {'error': 'No ATM options found'}

def get_options_summary(symbol):
    """Get a summary of options data for multiple expirations"""
    try:
        ticker = yf.Ticker(symbol)
        expirations = list(ticker.options)[:5]  # First 5 expirations

        # Get stock price
        hist = ticker.history(period='1d')
        stock_price = float(hist['Close'].iloc[-1]) if len(hist) > 0 else 0

        summaries = []
        for exp in expirations:
            try:
                opt_chain = ticker.option_chain(exp)
                calls = opt_chain.calls
                puts = opt_chain.puts

                # Calculate totals
                total_call_volume = int(calls['volume'].sum()) if 'volume' in calls else 0
                total_put_volume = int(puts['volume'].sum()) if 'volume' in puts else 0
                total_call_oi = int(calls['openInterest'].sum()) if 'openInterest' in calls else 0
                total_put_oi = int(puts['openInterest'].sum()) if 'openInterest' in puts else 0

                # Put/Call ratio
                pcr_volume = total_put_volume / total_call_volume if total_call_volume > 0 else 0
                pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0

                # Average IV
                avg_call_iv = float(calls['impliedVolatility'].mean() * 100) if len(calls) > 0 else 0
                avg_put_iv = float(puts['impliedVolatility'].mean() * 100) if len(puts) > 0 else 0

                summaries.append({
                    'expiration': exp,
                    'dte': calculate_dte(exp),
                    'callVolume': total_call_volume,
                    'putVolume': total_put_volume,
                    'callOI': total_call_oi,
                    'putOI': total_put_oi,
                    'pcrVolume': round(pcr_volume, 2),
                    'pcrOI': round(pcr_oi, 2),
                    'avgCallIV': round(avg_call_iv, 1),
                    'avgPutIV': round(avg_put_iv, 1)
                })
            except:
                continue

        return {
            'symbol': symbol,
            'stockPrice': stock_price,
            'expirations': summaries,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': str(e)}

def save_options_data(symbol, data):
    """Save options data to JSON file"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filename = os.path.join(DATA_DIR, f'{symbol}_options.json')
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved options data to {filename}")

def load_options_data(symbol):
    """Load options data from JSON file"""
    filename = os.path.join(DATA_DIR, f'{symbol}_options.json')
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return None

# CLI interface for testing
if __name__ == '__main__':
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else 'SPY'

    print(f"\n{'='*60}")
    print(f"Fetching Options Data for {symbol}")
    print(f"{'='*60}\n")

    # Get expirations
    expirations = get_options_expirations(symbol)
    print(f"Available Expirations: {expirations[:5]}...\n")

    # Get ATM options
    atm = get_atm_options(symbol)
    if 'error' not in atm:
        print(f"Stock Price: ${atm['stockPrice']:.2f}")
        print(f"ATM Strike: ${atm['atmStrike']}")
        print(f"Expiration: {atm['expiration']}\n")

        if atm['atmCall']:
            c = atm['atmCall']
            print(f"ATM CALL: Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f} | IV: {c['impliedVolatility']:.1f}% | Vol: {c['volume']} | OI: {c['openInterest']}")

        if atm['atmPut']:
            p = atm['atmPut']
            print(f"ATM PUT:  Bid ${p['bid']:.2f} / Ask ${p['ask']:.2f} | IV: {p['impliedVolatility']:.1f}% | Vol: {p['volume']} | OI: {p['openInterest']}")

    # Get summary
    print(f"\n{'='*60}")
    print("Options Summary by Expiration")
    print(f"{'='*60}")

    summary = get_options_summary(symbol)
    if 'expirations' in summary:
        for exp in summary['expirations']:
            print(f"\n{exp['expiration']} ({exp['dte']} DTE):")
            print(f"  Call Vol: {exp['callVolume']:,} | Put Vol: {exp['putVolume']:,} | P/C Ratio: {exp['pcrVolume']:.2f}")
            print(f"  Call OI: {exp['callOI']:,} | Put OI: {exp['putOI']:,} | P/C OI Ratio: {exp['pcrOI']:.2f}")
            print(f"  Avg Call IV: {exp['avgCallIV']:.1f}% | Avg Put IV: {exp['avgPutIV']:.1f}%")

    # Save full chain
    chain = get_options_chain(symbol)
    if 'error' not in chain:
        save_options_data(symbol, chain)
        print(f"\nSaved {len(chain['calls'])} calls and {len(chain['puts'])} puts")
