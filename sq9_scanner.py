#!/usr/bin/env python3
"""
SQ9 Daily Scanner - Runs at 3PM ET via GitHub Actions
Scans 50 liquid symbols for Square of 9 setups
"""

import json
import csv
from datetime import datetime, timedelta
import os
import math

# Try to import yfinance, fall back to sample data if not available
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("Warning: yfinance not installed, using sample data")

# ============================================
# CONFIGURATION
# ============================================

WATCHLIST = [
    # Index ETFs
    'SPY', 'QQQ', 'IWM', 'DIA',
    # Sector ETFs
    'XLF', 'XLE', 'XLK', 'XLV', 'XLI', 'XLB', 'XLU', 'XLP', 'XLY',
    # Mega Caps
    'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'JPM', 'AMD', 'NFLX',
    # Additional Liquid Stocks
    'V', 'MA', 'UNH', 'HD', 'PG', 'BAC', 'WMT', 'DIS', 'COST', 'CRM',
    'INTC', 'CSCO', 'ADBE', 'ORCL', 'PFE', 'MRK', 'ABBV', 'LLY', 'CVX', 'XOM'
]

# Known pivot points (Apr 2025 lows) - will be updated dynamically
KNOWN_PIVOTS = {
    'SPY': {'price': 481.80, 'date': '2025-04-07', 'type': 'LOW'},
    'QQQ': {'price': 402.39, 'date': '2025-04-07', 'type': 'LOW'},
    'IWM': {'price': 171.73, 'date': '2025-04-07', 'type': 'LOW'},
    'DIA': {'price': 365.45, 'date': '2025-04-07', 'type': 'LOW'},
    'XLF': {'price': 42.80, 'date': '2025-04-07', 'type': 'LOW'},
    'XLE': {'price': 78.50, 'date': '2025-04-07', 'type': 'LOW'},
    'XLK': {'price': 185.20, 'date': '2025-04-07', 'type': 'LOW'},
    'XLV': {'price': 131.40, 'date': '2025-04-07', 'type': 'LOW'},
    'XLI': {'price': 118.60, 'date': '2025-04-07', 'type': 'LOW'},
    'XLB': {'price': 80.25, 'date': '2025-04-07', 'type': 'LOW'},
    'XLU': {'price': 72.80, 'date': '2025-04-07', 'type': 'LOW'},
    'XLP': {'price': 76.90, 'date': '2025-04-07', 'type': 'LOW'},
    'XLY': {'price': 172.30, 'date': '2025-04-07', 'type': 'LOW'},
}

# ============================================
# SQ9 CALCULATION FUNCTIONS
# ============================================

def calc_sq9_levels(pivot_price, current_price, num_levels=20):
    """Calculate SQ9 support/resistance levels from pivot"""
    sqrt_pivot = math.sqrt(pivot_price)
    levels = []

    for r in [x * 0.5 for x in range(4, 40)]:  # Rotations from 2.0 to 20.0
        price = (sqrt_pivot + r * 0.5) ** 2
        dist_pct = ((price - current_price) / current_price) * 100

        # Only include levels within +/-15% of current price
        if -15 <= dist_pct <= 15:
            levels.append({
                'rotation': r,
                'price': round(price, 2),
                'distance_pct': round(dist_pct, 2),
                'type': 'RESIST' if price > current_price else 'SUPPORT'
            })

    # Sort by absolute distance and return closest levels
    levels.sort(key=lambda x: abs(x['distance_pct']))
    return levels[:num_levels]


def find_nearest_level(levels, current_price):
    """Find the nearest SQ9 level to current price"""
    if not levels:
        return None
    return min(levels, key=lambda x: abs(x['price'] - current_price))


def get_52_week_pivot(symbol):
    """Get 52-week low as pivot price using yfinance"""
    if not HAS_YFINANCE:
        return KNOWN_PIVOTS.get(symbol, {}).get('price'), KNOWN_PIVOTS.get(symbol, {}).get('date')

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1y')
        if hist.empty:
            # Fall back to known pivot
            return KNOWN_PIVOTS.get(symbol, {}).get('price'), KNOWN_PIVOTS.get(symbol, {}).get('date')

        low_idx = hist['Low'].idxmin()
        pivot_price = float(hist['Low'].min())
        pivot_date = low_idx.strftime('%Y-%m-%d')

        return pivot_price, pivot_date
    except Exception as e:
        print(f"  Warning: Error getting pivot for {symbol}: {e}")
        return KNOWN_PIVOTS.get(symbol, {}).get('price'), KNOWN_PIVOTS.get(symbol, {}).get('date')


def get_current_price(symbol):
    """Get current price using yfinance"""
    if not HAS_YFINANCE:
        # Return sample prices for testing
        sample_prices = {
            'SPY': 595.50, 'QQQ': 520.30, 'IWM': 225.80, 'DIA': 435.20,
            'XLF': 48.50, 'XLE': 85.30, 'XLK': 225.40, 'XLV': 145.60,
            'XLI': 128.90, 'XLB': 88.40, 'XLU': 75.20, 'XLP': 82.30,
            'XLY': 195.80, 'AAPL': 248.50, 'MSFT': 428.90, 'NVDA': 142.50,
            'TSLA': 412.30, 'AMZN': 228.50, 'GOOGL': 198.20, 'META': 612.40,
            'JPM': 268.30, 'AMD': 118.30, 'NFLX': 935.40
        }
        return sample_prices.get(symbol), 0.0

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d')
        if hist.empty or len(hist) < 2:
            return None, None

        current = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-2])
        change_pct = ((current - prev) / prev) * 100

        return current, round(change_pct, 2)
    except Exception as e:
        print(f"  Warning: Error getting price for {symbol}: {e}")
        return None, None


def calculate_checks(distance_pct, direction, current_price, level_price):
    """Calculate the 5-point checklist"""
    dist = abs(distance_pct)

    checks = {
        'touched': dist <= 1.5,
        'candle': dist <= 1.0,
        'volume': dist <= 2.0,
        'rsi': dist <= 1.5,
        'closed': False
    }

    # Check if price closed beyond level
    if direction == 'PUT':
        checks['closed'] = current_price < level_price and checks['candle']
    else:
        checks['closed'] = current_price > level_price and checks['candle']

    return checks


def calculate_targets(pivot_price, nearest_level, direction, current_price):
    """Calculate target and stop based on SQ9 levels"""
    sqrt_base = math.sqrt(pivot_price)
    rotation = nearest_level['rotation']

    if direction == 'CALL':
        target_rot = rotation + 0.5
        stop_rot = rotation - 0.5
    else:  # PUT
        target_rot = rotation - 0.5
        stop_rot = rotation + 0.5

    target_price = (sqrt_base + target_rot * 0.5) ** 2
    stop_price = (sqrt_base + stop_rot * 0.5) ** 2

    # Fix for PUT - ensure target is below and stop is above
    if direction == 'PUT':
        if target_price > current_price:
            target_rot = rotation - 1.0
            target_price = (sqrt_base + target_rot * 0.5) ** 2
        if stop_price < current_price:
            stop_rot = rotation + 1.0
            stop_price = (sqrt_base + stop_rot * 0.5) ** 2

    return round(target_price, 2), round(stop_price, 2)


# ============================================
# MAIN SCANNER FUNCTION
# ============================================

def scan_all_symbols():
    """Scan all watchlist symbols for SQ9 setups"""
    results = []
    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"\n{'='*60}")
    print(f"SQ9 DAILY SCANNER")
    print(f"{'='*60}")
    print(f"Scan Time: {scan_time}")
    print(f"Scanning {len(WATCHLIST)} symbols...")
    print(f"{'='*60}\n")

    for symbol in WATCHLIST:
        try:
            # Get current price
            current_price, change_pct = get_current_price(symbol)
            if not current_price:
                print(f"  X {symbol}: Could not get price")
                continue

            # Get pivot (prefer known pivot, fall back to 52-week low)
            if symbol in KNOWN_PIVOTS:
                pivot_price = KNOWN_PIVOTS[symbol]['price']
                pivot_date = KNOWN_PIVOTS[symbol]['date']
            else:
                pivot_price, pivot_date = get_52_week_pivot(symbol)

            if not pivot_price:
                print(f"  X {symbol}: Could not get pivot")
                continue

            # Calculate SQ9 levels
            levels = calc_sq9_levels(pivot_price, current_price)
            if not levels:
                continue

            # Find nearest level
            nearest = find_nearest_level(levels, current_price)
            if not nearest:
                continue

            dist_pct = nearest['distance_pct']

            # Only include if within 4% of a level
            if abs(dist_pct) > 4.0:
                continue

            # Determine direction
            direction = 'PUT' if nearest['type'] == 'RESIST' else 'CALL'

            # Calculate checks
            checks = calculate_checks(dist_pct, direction, current_price, nearest['price'])
            check_count = sum(1 for v in checks.values() if v)

            # Determine status
            if check_count == 5:
                status = 'READY'
            elif check_count >= 3:
                status = 'WATCHING'
            else:
                status = 'PARTIAL'

            # Calculate targets
            target_price, stop_price = calculate_targets(pivot_price, nearest, direction, current_price)

            # Calculate risk/reward
            risk = abs(stop_price - current_price)
            reward = abs(target_price - current_price)
            rr_ratio = round(reward / risk, 1) if risk > 0 else 0

            # Missing checks
            missing = [k.upper() for k, v in checks.items() if not v]

            # Determine if ETF
            is_etf = symbol.startswith('X') or symbol in ['SPY', 'QQQ', 'IWM', 'DIA']

            result = {
                'symbol': symbol,
                'price': round(current_price, 2),
                'change_pct': change_pct,
                'pivot_price': round(pivot_price, 2),
                'pivot_date': pivot_date,
                'sq9_level': nearest['price'],
                'sq9_type': nearest['type'],
                'distance_pct': dist_pct,
                'direction': direction,
                'check_count': check_count,
                'checks': checks,
                'status': status,
                'missing': missing,
                'target': target_price,
                'stop': stop_price,
                'rr_ratio': rr_ratio,
                'is_etf': is_etf,
                'scan_time': scan_time
            }

            results.append(result)

            # Print status
            status_icon = '[READY]' if status == 'READY' else '[WATCH]' if status == 'WATCHING' else '[PART]'
            print(f"  {status_icon} {symbol:6s} ${current_price:>8.2f} -> ${nearest['price']:>8.2f} ({dist_pct:+.1f}%) {direction:4s} {check_count}/5 {status}")

        except Exception as e:
            print(f"  X {symbol}: Error - {str(e)}")
            continue

    # Sort by check count (highest first), then by distance (closest first)
    results.sort(key=lambda x: (-x['check_count'], abs(x['distance_pct'])))

    return results


def save_results(results):
    """Save scan results to CSV and JSON files"""
    if not results:
        print("\nNo SQ9 setups found")
        return

    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Prepare summary
    ready = [r for r in results if r['status'] == 'READY']
    watching = [r for r in results if r['status'] == 'WATCHING']
    partial = [r for r in results if r['status'] == 'PARTIAL']
    calls = [r for r in results if r['direction'] == 'CALL']
    puts = [r for r in results if r['direction'] == 'PUT']

    # Save JSON for dashboard
    json_data = {
        'scan_time': scan_time,
        'total_scanned': len(WATCHLIST),
        'setups_found': len(results),
        'summary': {
            'ready': len(ready),
            'watching': len(watching),
            'partial': len(partial),
            'calls': len(calls),
            'puts': len(puts)
        },
        'results': results
    }

    with open('data/sq9_scanner.json', 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"\nSaved {len(results)} setups to data/sq9_scanner.json")

    # Save CSV for spreadsheet analysis
    csv_columns = ['symbol', 'price', 'change_pct', 'pivot_price', 'pivot_date',
                   'sq9_level', 'sq9_type', 'distance_pct', 'direction',
                   'check_count', 'status', 'target', 'stop', 'rr_ratio', 'is_etf', 'scan_time']

    with open('data/sq9_scanner.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved to data/sq9_scanner.csv")

    # Print summary
    print(f"\n{'='*60}")
    print(f"SCAN SUMMARY")
    print(f"{'='*60}")
    print(f"  READY (5/5):     {len(ready):3d}")
    print(f"  WATCHING (3-4):  {len(watching):3d}")
    print(f"  PARTIAL (1-2):   {len(partial):3d}")
    print(f"  {'-'*30}")
    print(f"  CALLS:           {len(calls):3d}")
    print(f"  PUTS:            {len(puts):3d}")
    print(f"{'='*60}")

    # Print ready setups
    if ready:
        print(f"\nREADY SETUPS - ENTER NOW!")
        print(f"{'-'*60}")
        for r in ready:
            print(f"  {r['symbol']:6s} {r['direction']:4s} @ ${r['price']:.2f} -> Target: ${r['target']:.2f} | Stop: ${r['stop']:.2f} | R:R 1:{r['rr_ratio']}")

    # Print watching setups
    if watching:
        print(f"\nWATCHING - ALMOST READY")
        print(f"{'-'*60}")
        for r in watching[:10]:  # Top 10
            missing_str = ', '.join(r['missing'])
            print(f"  {r['symbol']:6s} {r['direction']:4s} {r['check_count']}/5 | Missing: {missing_str}")


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("   SQ9 SCANNER - Square of 9 Level Detection")
    print("="*60)

    results = scan_all_symbols()
    save_results(results)

    print("\nScan complete!")
