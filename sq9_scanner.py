#!/usr/bin/env python3
"""
SQ9 Scanner - Automated Square of 9 Level Detection
Scans multiple ETFs and stocks for SQ9 entry signals

Usage:
    python sq9_scanner.py                    # Scan all watchlist symbols
    python sq9_scanner.py --symbol SPY       # Scan specific symbol
    python sq9_scanner.py --ready            # Show only ready setups
    python sq9_scanner.py --watching         # Show watching + ready setups
"""

import math
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

# Try to import yfinance for live data
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("Warning: yfinance not installed. Using cached/sample data.")
    print("Install with: pip install yfinance")

# ===========================================
# CONFIGURATION
# ===========================================

# Pivot data from confirmed major lows (Apr 7, 2025)
PIVOT_DATA = {
    # Index ETFs
    'SPY': {'price': 481.80, 'date': '2025-04-07', 'type': 'LOW'},
    'QQQ': {'price': 402.39, 'date': '2025-04-07', 'type': 'LOW'},
    'IWM': {'price': 171.73, 'date': '2025-04-07', 'type': 'LOW'},
    'DIA': {'price': 364.42, 'date': '2025-04-07', 'type': 'LOW'},
    # Sector ETFs
    'XLF': {'price': 42.35, 'date': '2025-04-07', 'type': 'LOW'},
    'XLE': {'price': 78.12, 'date': '2025-04-07', 'type': 'LOW'},
    'XLK': {'price': 186.50, 'date': '2025-04-07', 'type': 'LOW'},
    'XLV': {'price': 131.25, 'date': '2025-04-07', 'type': 'LOW'},
    'XLI': {'price': 112.80, 'date': '2025-04-07', 'type': 'LOW'},
    'XLB': {'price': 79.45, 'date': '2025-04-07', 'type': 'LOW'},
    'XLU': {'price': 68.90, 'date': '2025-04-07', 'type': 'LOW'},
    'XLP': {'price': 75.20, 'date': '2025-04-07', 'type': 'LOW'},
    'XLY': {'price': 175.30, 'date': '2025-04-07', 'type': 'LOW'},
}

# Check thresholds (in percentage)
THRESHOLDS = {
    'signal_active': 3.0,      # Within 3% to show signal
    'zone_reset': 4.0,         # Beyond 4% resets zone
    'touched': 1.5,            # Within 1.5% = touched
    'candle': 1.0,             # Within 1.0% = candle pattern likely
    'volume': 2.0,             # Within 2.0% = volume check
    'rsi': 1.5,                # Within 1.5% = RSI check
}

# ===========================================
# SQ9 CALCULATION FUNCTIONS
# ===========================================

def calc_sq9_levels(pivot_price: float, current_price: float, range_pct: float = 10.0) -> List[Dict]:
    """
    Calculate SQ9 levels from a pivot price.
    Returns levels within range_pct of current price.
    """
    sqrt_pivot = math.sqrt(pivot_price)
    levels = []

    # Calculate rotations (each 0.5 = 180 degrees on the wheel)
    for r in [x * 0.5 for x in range(8, 29)]:  # 4.0 to 14.0 in 0.5 steps
        price = (sqrt_pivot + r * 0.5) ** 2
        dist_pct = ((price - current_price) / current_price) * 100

        if -range_pct <= dist_pct <= range_pct:
            levels.append({
                'rotation': r,
                'price': price,
                'distance': dist_pct,
                'type': 'resist' if price > current_price else 'support'
            })

    return sorted(levels, key=lambda x: -x['price'])


def find_nearest_level(levels: List[Dict], current_price: float) -> Optional[Dict]:
    """Find the nearest SQ9 level to current price."""
    if not levels:
        return None

    nearest = None
    min_dist = float('inf')

    for level in levels:
        dist = abs(level['price'] - current_price)
        if dist < min_dist:
            min_dist = dist
            nearest = level

    return nearest


def get_trade_direction(nearest: Dict, current_price: float) -> str:
    """Determine trade direction based on nearest level."""
    if not nearest:
        return 'NEUTRAL'

    dist_pct = abs(nearest['distance'])
    if dist_pct > THRESHOLDS['signal_active']:
        return 'NEUTRAL'

    return 'PUT' if nearest['type'] == 'resist' else 'CALL'


def calculate_checks(dist_pct: float, direction: str, current_price: float, level_price: float) -> Dict:
    """Calculate the 5 entry checks based on distance."""
    checks = {
        'touched': dist_pct <= THRESHOLDS['touched'],
        'candle': dist_pct <= THRESHOLDS['candle'],
        'volume': dist_pct <= THRESHOLDS['volume'],
        'rsi': dist_pct <= THRESHOLDS['rsi'],
        'closed': False
    }

    # Check if price closed beyond level
    if direction == 'PUT':
        checks['closed'] = current_price < level_price and checks['candle']
    else:
        checks['closed'] = current_price > level_price and checks['candle']

    return checks


def get_status(check_count: int) -> str:
    """Get status based on check count."""
    if check_count == 5:
        return 'READY'
    elif check_count >= 3:
        return 'WATCHING'
    elif check_count >= 1:
        return 'PARTIAL'
    return 'NONE'


# ===========================================
# DATA FETCHING
# ===========================================

def get_current_price(symbol: str) -> Optional[float]:
    """Fetch current price for a symbol."""
    if not HAS_YFINANCE:
        # Return sample data if yfinance not available
        sample_prices = {
            'SPY': 595.50, 'QQQ': 520.30, 'IWM': 225.80, 'DIA': 435.20,
            'XLF': 48.50, 'XLE': 85.30, 'XLK': 225.40, 'XLV': 145.60,
            'XLI': 128.90, 'XLB': 88.40, 'XLU': 75.20, 'XLP': 82.30,
            'XLY': 195.80
        }
        return sample_prices.get(symbol)

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

    return None


# ===========================================
# SCANNER
# ===========================================

def scan_symbol(symbol: str) -> Optional[Dict]:
    """Scan a single symbol for SQ9 setup."""
    pivot = PIVOT_DATA.get(symbol)
    if not pivot:
        return None

    current_price = get_current_price(symbol)
    if not current_price:
        return None

    # Calculate SQ9 levels
    levels = calc_sq9_levels(pivot['price'], current_price)
    nearest = find_nearest_level(levels, current_price)

    if not nearest:
        return None

    dist_pct = abs(nearest['distance'])

    # Skip if too far from any level
    if dist_pct > THRESHOLDS['zone_reset']:
        return None

    direction = get_trade_direction(nearest, current_price)
    if direction == 'NEUTRAL':
        return None

    # Calculate checks
    checks = calculate_checks(dist_pct, direction, current_price, nearest['price'])
    check_count = sum(checks.values())
    status = get_status(check_count)

    if status == 'NONE':
        return None

    # Calculate target and stop
    sqrt_base = math.sqrt(pivot['price'])
    if direction == 'CALL':
        target_rot = nearest['rotation'] + 0.5
        stop_rot = nearest['rotation'] - 0.5
    else:
        target_rot = nearest['rotation'] - 0.5
        stop_rot = nearest['rotation'] + 0.5

    target_price = (sqrt_base + target_rot * 0.5) ** 2
    stop_price = (sqrt_base + stop_rot * 0.5) ** 2

    # Fix for PUT direction
    if direction == 'PUT':
        if target_price > current_price:
            target_rot = nearest['rotation'] - 1.0
            target_price = (sqrt_base + target_rot * 0.5) ** 2
        if stop_price < current_price:
            stop_rot = nearest['rotation'] + 1.0
            stop_price = (sqrt_base + stop_rot * 0.5) ** 2

    # Calculate risk/reward
    risk = abs(stop_price - current_price)
    reward = abs(target_price - current_price)
    rr_ratio = reward / risk if risk > 0 else 0

    # Missing checks
    missing = [k.upper() for k, v in checks.items() if not v]

    return {
        'symbol': symbol,
        'price': current_price,
        'pivot': pivot['price'],
        'sq9_level': nearest['price'],
        'distance': nearest['distance'],
        'direction': direction,
        'checks': checks,
        'check_count': check_count,
        'status': status,
        'target': target_price,
        'stop': stop_price,
        'rr_ratio': rr_ratio,
        'missing': missing,
        'rotation': nearest['rotation']
    }


def run_scan(symbols: List[str] = None, filter_status: str = None) -> List[Dict]:
    """Run scan on multiple symbols."""
    if symbols is None:
        symbols = list(PIVOT_DATA.keys())

    results = []

    print(f"\n{'='*60}")
    print(f"  SQ9 SCANNER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Scanning {len(symbols)} symbols...\n")

    for symbol in symbols:
        result = scan_symbol(symbol)
        if result:
            # Apply filter if specified
            if filter_status:
                if filter_status == 'ready' and result['status'] != 'READY':
                    continue
                if filter_status == 'watching' and result['status'] not in ['READY', 'WATCHING']:
                    continue
            results.append(result)

    # Sort by check count (highest first), then by distance (closest first)
    results.sort(key=lambda x: (-x['check_count'], abs(x['distance'])))

    return results


# ===========================================
# OUTPUT FORMATTING
# ===========================================

def print_results(results: List[Dict]):
    """Print scan results in formatted table."""
    if not results:
        print("\nNo active SQ9 setups found.")
        return

    # Group by status
    ready = [r for r in results if r['status'] == 'READY']
    watching = [r for r in results if r['status'] == 'WATCHING']
    partial = [r for r in results if r['status'] == 'PARTIAL']

    # Summary
    print(f"\n{'='*60}")
    print(f"  SCAN SUMMARY")
    print(f"{'='*60}")
    print(f"  READY (5/5):    {len(ready)}")
    print(f"  WATCHING (3-4): {len(watching)}")
    print(f"  PARTIAL (1-2):  {len(partial)}")
    print(f"  TOTAL:          {len(results)}")

    # Ready setups
    if ready:
        print(f"\n{'='*60}")
        print(f"  READY SETUPS - ENTER NOW!")
        print(f"{'='*60}")
        print(f"{'SYMBOL':<8} {'PRICE':>10} {'SQ9':>10} {'DIST':>8} {'DIR':>6} {'TARGET':>10} {'STOP':>10} {'R/R':>6}")
        print(f"{'-'*76}")
        for r in ready:
            dist_str = f"{r['distance']:+.1f}%"
            print(f"{r['symbol']:<8} ${r['price']:>9.2f} ${r['sq9_level']:>9.2f} {dist_str:>8} {r['direction']:>6} ${r['target']:>9.2f} ${r['stop']:>9.2f} {r['rr_ratio']:>5.1f}x")

    # Watching setups
    if watching:
        print(f"\n{'='*60}")
        print(f"  WATCHING SETUPS - Almost Ready")
        print(f"{'='*60}")
        print(f"{'SYMBOL':<8} {'PRICE':>10} {'SQ9':>10} {'DIST':>8} {'DIR':>6} {'CHECKS':>8} {'MISSING':<20}")
        print(f"{'-'*76}")
        for r in watching:
            dist_str = f"{r['distance']:+.1f}%"
            missing_str = ', '.join(r['missing'][:3])
            print(f"{r['symbol']:<8} ${r['price']:>9.2f} ${r['sq9_level']:>9.2f} {dist_str:>8} {r['direction']:>6} {r['check_count']:>5}/5   {missing_str:<20}")

    # Partial setups (compact)
    if partial:
        print(f"\n{'='*60}")
        print(f"  APPROACHING - On Radar ({len(partial)} symbols)")
        print(f"{'='*60}")
        for r in partial:
            print(f"  {r['symbol']}: ${r['price']:.2f} -> ${r['sq9_level']:.2f} ({abs(r['distance']):.1f}% away) [{r['direction']}] {r['check_count']}/5")


def export_json(results: List[Dict], filename: str = 'sq9_scan_results.json'):
    """Export results to JSON file."""
    output = {
        'scan_time': datetime.now().isoformat(),
        'total_symbols': len(PIVOT_DATA),
        'active_setups': len(results),
        'results': results
    }

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults exported to {filename}")


# ===========================================
# MAIN
# ===========================================

def main():
    parser = argparse.ArgumentParser(description='SQ9 Scanner - Automated Square of 9 Level Detection')
    parser.add_argument('--symbol', '-s', type=str, help='Scan specific symbol')
    parser.add_argument('--ready', action='store_true', help='Show only READY setups')
    parser.add_argument('--watching', action='store_true', help='Show READY and WATCHING setups')
    parser.add_argument('--export', '-e', action='store_true', help='Export results to JSON')
    parser.add_argument('--list', '-l', action='store_true', help='List all tracked symbols')

    args = parser.parse_args()

    # List symbols
    if args.list:
        print("\nTracked Symbols:")
        print("-" * 40)
        for sym, data in PIVOT_DATA.items():
            print(f"  {sym}: ${data['price']:.2f} ({data['date']} {data['type']})")
        return

    # Determine filter
    filter_status = None
    if args.ready:
        filter_status = 'ready'
    elif args.watching:
        filter_status = 'watching'

    # Run scan
    if args.symbol:
        symbols = [args.symbol.upper()]
    else:
        symbols = None

    results = run_scan(symbols, filter_status)
    print_results(results)

    # Export if requested
    if args.export:
        export_json(results)

    print(f"\n{'='*60}")
    print(f"  Scan complete. {len(results)} active setups found.")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
