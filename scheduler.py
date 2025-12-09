#!/usr/bin/env python3
"""
Stock Agent Scheduler
=====================
Automated scheduler for data updates, signal generation, and options fetching.
Runs continuously and performs tasks at specified intervals.

Usage:
    python scheduler.py                    # Run with default 5-minute interval
    python scheduler.py --interval 1       # Run every 1 minute
    python scheduler.py --interval 15      # Run every 15 minutes
    python scheduler.py --no-market-hours  # Run even outside market hours
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
import threading
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scheduler.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Import local modules
try:
    from fetch_data import fetch_symbol_data, SYMBOLS
    logger.info("fetch_data module loaded")
except ImportError:
    logger.warning("fetch_data module not found - will use yfinance directly")
    SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY', 'XLI', 'XLB', 'XLP', 'XLU', 'XLRE']

try:
    from options_data import get_options_chain, get_options_summary, save_options_data
    logger.info("options_data module loaded")
except ImportError:
    logger.warning("options_data module not found")
    get_options_chain = None

try:
    import yfinance as yf
    logger.info("yfinance module loaded")
except ImportError:
    logger.error("yfinance not installed! Run: pip install yfinance")
    yf = None

# Scheduler configuration
class SchedulerConfig:
    def __init__(self):
        self.interval_minutes = 5
        self.market_hours_only = True
        self.fetch_prices = True
        self.fetch_options = True
        self.generate_signals = True
        self.running = False
        self.last_run = {}

config = SchedulerConfig()

def is_market_hours():
    """Check if current time is within extended market hours (8 AM - 6 PM ET)"""
    from datetime import datetime
    import pytz

    try:
        et = pytz.timezone('America/New_York')
        now = datetime.now(et)
    except:
        # Fallback if pytz not installed
        now = datetime.now()
        # Rough ET adjustment (not DST aware)
        now = now - timedelta(hours=5)

    # Weekend check
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False

    # Extended hours: 8 AM to 6 PM ET
    hour = now.hour
    return 8 <= hour < 18

def fetch_price_data():
    """Fetch latest price data for all symbols"""
    logger.info("📊 Fetching price data...")

    if yf is None:
        logger.error("yfinance not available")
        return

    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)

    for symbol in SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)

            # Fetch 3 years of daily data
            df = ticker.history(period='3y', interval='1d')

            if len(df) > 0:
                # Save to CSV
                filepath = os.path.join(data_dir, f'{symbol}_data.csv')
                df.to_csv(filepath)
                logger.info(f"  ✅ {symbol}: {len(df)} bars saved")
            else:
                logger.warning(f"  ⚠️ {symbol}: No data returned")

        except Exception as e:
            logger.error(f"  ❌ {symbol}: {str(e)}")

    config.last_run['prices'] = datetime.now().isoformat()
    logger.info("📊 Price data fetch complete")

def fetch_options_data():
    """Fetch options chain data for all symbols"""
    logger.info("📡 Fetching options data...")

    if get_options_chain is None:
        logger.warning("options_data module not available")
        return

    for symbol in SYMBOLS[:5]:  # Limit to first 5 symbols to avoid rate limits
        try:
            chain = get_options_chain(symbol)

            if 'error' not in chain:
                save_options_data(symbol, chain)
                calls_count = len(chain.get('calls', []))
                puts_count = len(chain.get('puts', []))
                logger.info(f"  ✅ {symbol}: {calls_count} calls, {puts_count} puts")
            else:
                logger.warning(f"  ⚠️ {symbol}: {chain.get('error')}")

        except Exception as e:
            logger.error(f"  ❌ {symbol}: {str(e)}")

        # Small delay to avoid rate limiting
        time.sleep(1)

    config.last_run['options'] = datetime.now().isoformat()
    logger.info("📡 Options data fetch complete")

def generate_signals():
    """Generate trading signals (placeholder - actual signals generated in JS)"""
    logger.info("🎯 Signal generation triggered")

    # This would trigger signal generation
    # For now, just log that it happened
    # Actual signals are generated client-side from the CSV data

    config.last_run['signals'] = datetime.now().isoformat()
    logger.info("🎯 Signal generation complete")

def run_scheduled_tasks():
    """Run all scheduled tasks"""
    logger.info(f"\n{'='*60}")
    logger.info(f"⏰ Running scheduled tasks at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*60}")

    # Check market hours
    if config.market_hours_only and not is_market_hours():
        logger.info("🌙 Outside market hours - skipping refresh")
        logger.info("   (Use --no-market-hours to run anyway)")
        return

    start_time = time.time()

    # Run tasks
    if config.fetch_prices:
        fetch_price_data()

    if config.fetch_options:
        fetch_options_data()

    if config.generate_signals:
        generate_signals()

    elapsed = time.time() - start_time
    logger.info(f"\n✅ All tasks completed in {elapsed:.1f} seconds")

    # Save status
    status = {
        'last_run': datetime.now().isoformat(),
        'elapsed_seconds': elapsed,
        'market_hours': is_market_hours(),
        'tasks': config.last_run
    }

    with open('scheduler_status.json', 'w') as f:
        json.dump(status, f, indent=2)

def scheduler_loop():
    """Main scheduler loop"""
    logger.info(f"\n{'='*60}")
    logger.info("🚀 Stock Agent Scheduler Started")
    logger.info(f"{'='*60}")
    logger.info(f"   Interval: {config.interval_minutes} minutes")
    logger.info(f"   Market hours only: {config.market_hours_only}")
    logger.info(f"   Symbols: {len(SYMBOLS)}")
    logger.info(f"{'='*60}\n")

    config.running = True

    # Run immediately on start
    run_scheduled_tasks()

    # Then run at intervals
    while config.running:
        try:
            # Sleep for the interval
            sleep_seconds = config.interval_minutes * 60
            logger.info(f"\n⏳ Next run in {config.interval_minutes} minutes...")

            # Sleep in small chunks so we can respond to stop signals
            for _ in range(sleep_seconds):
                if not config.running:
                    break
                time.sleep(1)

            if config.running:
                run_scheduled_tasks()

        except KeyboardInterrupt:
            logger.info("\n🛑 Scheduler stopped by user")
            config.running = False
            break
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            time.sleep(60)  # Wait a minute before retrying

def main():
    parser = argparse.ArgumentParser(description='Stock Agent Scheduler')
    parser.add_argument('--interval', type=int, default=5,
                        help='Refresh interval in minutes (default: 5)')
    parser.add_argument('--no-market-hours', action='store_true',
                        help='Run even outside market hours')
    parser.add_argument('--no-prices', action='store_true',
                        help='Skip price data fetching')
    parser.add_argument('--no-options', action='store_true',
                        help='Skip options data fetching')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit (no loop)')

    args = parser.parse_args()

    # Apply configuration
    config.interval_minutes = args.interval
    config.market_hours_only = not args.no_market_hours
    config.fetch_prices = not args.no_prices
    config.fetch_options = not args.no_options

    if args.once:
        # Run once and exit
        run_scheduled_tasks()
    else:
        # Run continuously
        scheduler_loop()

if __name__ == '__main__':
    main()
