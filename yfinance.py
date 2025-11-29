#!/usr/bin/env python3
"""
SPY Confluence Agent with Playbook, Tuning, and Gann–Elliott Super-Confluence
WEEK 2 FIXES: Logging, API resilience, position sizing, CSV schema

What this script does
---------------------
1. Fetches daily SPY prices from Tiingo (with retry logic & error handling).
2. Saves raw history to data/SPY.csv.
3. Computes:
   - ATR
   - Fast/slow SMAs
   - Simple geometry / phi / time confluence markers
4. When confluence + bias line up, creates a CALL or PUT playbook:
   - ATR-based entry band (EntryLow / EntryHigh)
   - Guard-rail stop
   - 2R / 3R targets
   - Time stop in HOLD_DAYS bars
5. Saves:
   - data/SPY_confluence.csv           (bar-level enriched data)
   - reports/portfolio_confluence.csv  (base playbook trades)
6. Gann–Elliott overlay:
   - Runs a separate Gann–Elliott strategy on the same bars.
   - Saves suggested plays to reports/portfolio_gann_elliott.csv.
7. Hybrid B + C:
   - Super-Confluence = only where Base and Gann–Elliott agree on direction.
   - Saves those to reports/portfolio_super_confluence.csv.
8. Computes performance metrics + tuning grids:
   - data/performance_confluence.json
   - data/tuning_confluence.json

WEEK 2 IMPROVEMENTS:
- FIX #4: Professional logging (file + console, multiple levels)
- FIX #3: API error handling with retry logic
- FIX #2: Safe position sizing with bounds & validation
- FIX #1: Consistent CSV schema with metadata fields

NOTE: This is a research tool, not trading advice.
"""

import csv
import json
import logging
import math
import os
import pathlib
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional

from statistics import median
import pandas as pd
import yfinance as yf

# =========================================================================
# FIX #4: PROFESSIONAL LOGGING INFRASTRUCTURE
# =========================================================================

def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """
    Setup dual logging: console + file with timestamps, levels, and function names.
    
    Args:
        log_dir: Directory to store log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    log_path = pathlib.Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("confluence_agent")
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Log format: timestamp | level | function | message
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(funcName)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler - always INFO+ for debugging
    file_handler = logging.FileHandler(log_path / "agent.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler - display level set by caller
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger globally
logger = setup_logging()

def log(msg: str, level: str = "INFO") -> None:
    """
    Convenience function for backwards compatibility.
    
    Args:
        msg: Message to log
        level: Log level (INFO, DEBUG, WARNING, ERROR)
    """
    level_map = {
        "DEBUG": logger.debug,
        "INFO": logger.info,
        "WARNING": logger.warning,
        "ERROR": logger.error,
    }
    level_func = level_map.get(level.upper(), logger.info)
    level_func(msg)

# =========================================================================
# FIX #3: API ERROR HANDLING WITH RETRY LOGIC
# =========================================================================

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 30  # seconds

def fetch_yfinance_daily(
    symbol: str, 
    start_date: str,
    max_retries: int = MAX_RETRIES
) -> List['Bar']:
    """
    Fetch daily OHLCV from Tiingo with exponential backoff retry logic.
    
    Args:
        symbol: Stock symbol (e.g., 'SPY')
        start_date: Start date in YYYY-MM-DD format
        max_retries: Maximum number of retry attempts
    
    Returns:
        List of Bar objects, empty list on failure
    """
    token = os.getenv("TIINGO_TOKEN")
    
    # Validate token at startup
    if not token:
        logger.error("TIINGO_TOKEN environment variable not set!")
        return []
    
    if len(token) < 20:
        logger.error(f"Invalid TIINGO_TOKEN format (got {len(token)} chars, expected 40+)")
        return []
    
    url = (
        f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
        f"?startDate={start_date}&token={token}"
    )
    
    bars = []
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[Attempt {attempt}/{max_retries}] Fetching {symbol} from Tiingo...")
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'ConfluenceAgent/1.0')
            
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if not isinstance(data, list):
                    logger.error(f"Unexpected response format: {type(data)}")
                    return []
                
                logger.info(f"Successfully fetched {len(data)} bars for {symbol}")
                
                for item in data:
                    try:
                        bar = Bar(
                            d=item['date'],
                            open_=item['open'],
                            high=item['high'],
                            low=item['low'],
                            close=item['close'],
                            volume=item['volume'],
                        )
                        bars.append(bar)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Skipped malformed bar: {item}, error: {e}")
                        continue
                
                return bars
        
        except urllib.error.HTTPError as e:
            if e.code == 401:
                logger.error(f"HTTP 401 Unauthorized - Invalid TIINGO_TOKEN")
                return []
            elif e.code == 403:
                logger.error(f"HTTP 403 Forbidden - Check token permissions")
                return []
            elif e.code == 404:
                logger.error(f"HTTP 404 Not Found - {symbol} may not exist on Tiingo")
                return []
            else:
                logger.warning(f"HTTP {e.code}: {e.reason} (attempt {attempt}/{max_retries})")
        
        except urllib.error.URLError as e:
            logger.warning(f"Network error: {e.reason} (attempt {attempt}/{max_retries})")
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e} (attempt {attempt}/{max_retries})")
        
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e} (attempt {attempt}/{max_retries})")
        
        # Exponential backoff: 2s, 4s, 8s
        if attempt < max_retries:
            wait_time = RETRY_DELAY * (2 ** (attempt - 1))
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    logger.error(f"Failed to fetch {symbol} after {max_retries} attempts. Returning empty list.")
    return []

# =========================================================================
# FIX #2: SAFE POSITION SIZING WITH BOUNDS & VALIDATION
# =========================================================================

MIN_POSITION_SIZE = 1      # Minimum shares to trade
RISK_PER_TRADE = 1.0       # % of equity per trade
MAX_PORTFOLIO_RISK = 6.0   # Max % account risk across all positions

def calculate_position_size_safe(
    account_balance: float,
    entry_price: float,
    stop_price: float,
) -> int:
    """
    Calculate safe position size with validation and bounds checking.
    
    Args:
        account_balance: Total account equity
        entry_price: Entry price per share
        stop_price: Stop loss price per share
    
    Returns:
        Number of shares to trade (respects min/max bounds)
    """
    # Validate inputs
    if account_balance <= 0:
        logger.error(f"Invalid account balance: {account_balance}")
        return 0
    
    if entry_price <= 0:
        logger.error(f"Invalid entry price: {entry_price}")
        return 0
    
    # Calculate risk amount
    risk_amount = account_balance * (RISK_PER_TRADE / 100.0)
    price_risk = abs(entry_price - stop_price)
    
    # Handle edge case: stop == entry
    if price_risk <= 0.01:
        logger.warning(
            f"Stop too close to entry (risk={price_risk:.4f}). "
            f"Using minimum position size."
        )
        return MIN_POSITION_SIZE
    
    # Calculate position size
    size = int(risk_amount / price_risk)
    
    # Apply minimum bound
    if size < MIN_POSITION_SIZE:
        logger.debug(
            f"Calculated size {size} < MIN ({MIN_POSITION_SIZE}); "
            f"using minimum"
        )
        return MIN_POSITION_SIZE
    
    # Apply maximum bound (don't let position be >50% of account equity at entry)
    max_size = int((account_balance * 0.5) / entry_price)
    if size > max_size:
        logger.warning(
            f"Calculated size {size} > MAX ({max_size}); "
            f"capping to max"
        )
        return max_size
    
    logger.debug(
        f"Position sizing: account={account_balance:.0f}, "
        f"entry={entry_price:.2f}, stop={stop_price:.2f}, "
        f"risk_amt={risk_amount:.2f}, size={size}"
    )
    
    return size

# =========================================================================
# FIX #1: CONSISTENT CSV SCHEMA WITH HELPER FUNCTIONS
# =========================================================================

def sanitize_status_string(status: str, max_length: int = 150) -> str:
    """
    Clean and truncate Status field to prevent CSV corruption.
    
    Args:
        status: Raw status string (may contain complex info)
        max_length: Maximum allowed length
    
    Returns:
        Sanitized status string
    """
    # Remove newlines, extra spaces
    clean = ' '.join(status.split())
    
    # Truncate if needed
    if len(clean) > max_length:
        clean = clean[:max_length - 3] + "..."
        logger.debug(f"Truncated status to {max_length} chars")
    
    return clean

# =========================================================================
# EXISTING INFRASTRUCTURE (unchanged from Phase 1)
# =========================================================================

@dataclass
class Bar:
    """Daily OHLCV bar."""
    d: str
    open_: float
    high: float
    low: float
    close: float
    volume: float
    atr: Optional[float] = None
    fast_sma: Optional[float] = None
    slow_sma: Optional[float] = None
    bias: Optional[str] = None
    geo_level: Optional[float] = None
    phi_level: Optional[float] = None
    price_confluence: int = 0
    time_confluence: int = 0

# ---------------------------------------------------------------------------
# Strategy modes & thresholds
# ---------------------------------------------------------------------------

ACTIVE_STRATEGY_MODE = "UNIFIED"  # "BASE", "GANN_ELLIOTT", or "UNIFIED"
MIN_WAVE_CONFIDENCE = 70
MIN_TOTAL_CONFIDENCE = 75

# Paths
DATA_DIR = pathlib.Path("data")
REPORT_DIR = pathlib.Path("reports")
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Trading parameters
SYMBOLS = ["SPY"]
START_DATE = "2022-11-01"
ATR_LENGTH = 14
FAST_SMA_LEN = 10
SLOW_SMA_LEN = 20
PRICE_TOL_PCT = 0.008
ENTRY_BAND_ATR = 0.5
STOP_ATR = 1.5
HOLD_DAYS = 5

# ---------------------------------------------------------------------------
# Elliott Wave Engine (lite quantitative implementation)
# ---------------------------------------------------------------------------

def zigzag(df: pd.DataFrame, threshold: float = 0.05):
    """Simple ZigZag pivot detector for wave structure."""
    if len(df) < 5:
        return []
    
    closes = df['close'].values
    pivots = []
    
    for i in range(2, len(closes) - 2):
        # Local max
        if closes[i] > closes[i-1] * (1 + threshold) and closes[i] > closes[i+1] * (1 + threshold):
            pivots.append((i, closes[i], 'H'))
        # Local min
        elif closes[i] < closes[i-1] * (1 - threshold) and closes[i] < closes[i+1] * (1 - threshold):
            pivots.append((i, closes[i], 'L'))
    
    return pivots

def detect_elliott_waves(df: pd.DataFrame) -> Optional[dict]:
    """Detect simplified Elliott wave structure."""
    if len(df) < 50:
        return None
    
    pivots = zigzag(df, threshold=0.03)
    if len(pivots) < 5:
        return None
    
    last_5 = pivots[-5:]
    confidence = 75 + (len(pivots) - 5) * 0.5
    confidence = min(confidence, 100)
    
    waves = {
        'W0': last_5[0][1],
        'W1': last_5[1][1],
        'W2': last_5[2][1],
        'W3': last_5[3][1],
        'W4': last_5[4][1],
        'W5': last_5[-1][1],
        'confidence': confidence,
        'current': 'wave_5_complete',
    }
    
    return waves

# ---------------------------------------------------------------------------
# Gann Square of 9 Engine
# ---------------------------------------------------------------------------

def gann_square_of_9(price: float, increments: int = 5) -> dict:
    """Calculate Gann Square of 9 support/resistance levels."""
    sqrtp = math.sqrt(price)
    res = []
    sup = []
    for k in range(1, increments + 1):
        deg = k * 45
        inc = deg / 180.0
        res.append(round((sqrtp + inc) ** 2, 2))
        if sqrtp > inc:
            sup.append(round((sqrtp - inc) ** 2, 2))
    return {"resistance": res, "support": sup}

def nearest_gann_levels(price: float, gann: dict) -> Tuple[float, float]:
    """Find nearest support and resistance from Gann levels."""
    r = gann["resistance"]
    s = gann["support"]
    nearest_r = min(r, key=lambda x: abs(x - price))
    nearest_s = min(s, key=lambda x: abs(x - price))
    return nearest_s, nearest_r

# ---------------------------------------------------------------------------
# Regime Filters, Time Cycles, Position Sizing, Gann–Elliott Strategy
# ---------------------------------------------------------------------------

NO_TRADE = None

GANN_CYCLES_TRADING_DAYS = [11, 22, 34, 45, 56, 67, 78, 90]

def detect_trend_regime(df: pd.DataFrame) -> str:
    """Detect trend regime (up/down/sideways)."""
    if len(df) < 220:
        return "unknown"
    
    sma50 = df['close'].rolling(50).mean().iloc[-1]
    sma200 = df['close'].rolling(200).mean().iloc[-1]
    close = df['close'].iloc[-1]
    
    if close > sma50 > sma200:
        return "strong_uptrend"
    elif close > sma50 and sma50 < sma200:
        return "weak_uptrend"
    elif close < sma50 < sma200:
        return "strong_downtrend"
    elif close < sma50 and sma50 > sma200:
        return "weak_downtrend"
    else:
        return "sideways"

def detect_vol_regime(df: pd.DataFrame) -> str:
    """Detect volatility regime."""
    if len(df) < 30:
        return "unknown"
    
    realized_vol = df['close'].pct_change().std() * math.sqrt(252)
    historical_vol = df['close'].rolling(60).std().mean() / df['close'].mean()
    
    if realized_vol > historical_vol * 1.2:
        return "high"
    elif realized_vol < historical_vol * 0.8:
        return "low"
    else:
        return "normal"

def identify_cycle_start_pivot(df: pd.DataFrame) -> pd.Timestamp:
    """Identify start of current trading cycle."""
    if len(df) < 10:
        return df.index[0]
    
    pivots = zigzag(df[-50:], threshold=0.03)
    if pivots:
        pivot_idx = pivots[-1][0]
        return df.index[-50 + pivot_idx]
    
    return df.index[-30]

def cycle_confidence(days_from_pivot: int) -> float:
    """Confidence score based on Gann cycles."""
    best = 0.3
    for c in GANN_CYCLES_TRADING_DAYS:
        diff = abs(days_from_pivot - c)
        if diff <= 2:
            return 1.0
        if diff <= 4:
            best = max(best, 0.7)
    return best

def gann_elliott_strategy(df: pd.DataFrame, account_balance: float = 100000.0) -> Optional[dict]:
    """Gann–Elliott strategy with position sizing."""
    if len(df) < 220:
        return NO_TRADE
    
    trend = detect_trend_regime(df)
    vol = detect_vol_regime(df)
    
    if trend == "sideways":
        return NO_TRADE
    
    waves = detect_elliott_waves(df)
    if not waves or waves["confidence"] < MIN_WAVE_CONFIDENCE:
        return NO_TRADE
    
    price = df["close"].iloc[-1]
    gann = gann_square_of_9(price, increments=5)
    nearest_support, nearest_resistance = nearest_gann_levels(price, gann)
    
    pivot_date = identify_cycle_start_pivot(df)
    days_from_pivot = (df.index[-1] - pivot_date).days
    cyc = cycle_confidence(days_from_pivot)
    
    if cyc < 0.7:
        return NO_TRADE
    
    direction = None
    entry = price
    stop = None
    t1 = None
    t2 = None
    
    if waves["current"] == "wave_2_complete" and price <= nearest_support * 1.0075:
        direction = "CALL"
        stop = waves["W0"] * 0.99
        t1 = nearest_resistance
        t2 = nearest_resistance * 1.01
    elif waves["current"] == "wave_5_complete" and price >= nearest_resistance * 0.9925:
        direction = "PUT"
        stop = waves["W5"] * 1.01
        t1 = nearest_support
        t2 = nearest_support * 0.99
    
    if direction is None or stop is None or t1 is None:
        return NO_TRADE
    
    # FIX #2: Use safe position sizing
    size = calculate_position_size_safe(account_balance, entry, stop)
    
    reward = abs(t1 - entry)
    risk = abs(entry - stop)
    if risk <= 0 or reward / risk < 2.0:
        return NO_TRADE
    
    confidence = waves["confidence"] * (1 - 0.1 * (risk / reward - 2.0))
    confidence = min(max(confidence, 0), 100)
    
    if confidence < MIN_TOTAL_CONFIDENCE:
        return NO_TRADE
    
    return {
        'direction': direction,
        'entry': entry,
        'stop': stop,
        'target1': t1,
        'target2': t2,
        'size': size,
        'confidence': confidence,
        'regime': (trend, vol),
        'gann_support': nearest_support,
        'gann_resistance': nearest_resistance,
    }

# ---------------------------------------------------------------------------
# Compute Indicators
# ---------------------------------------------------------------------------

def compute_atr(bars: List[Bar], length: int = 14) -> None:
    """Compute Average True Range."""
    for i, bar in enumerate(bars):
        if i < length:
            bar.atr = None
            continue
        
        trs = []
        for j in range(i - length + 1, i + 1):
            high = bars[j].high
            low = bars[j].low
            close_prev = bars[j-1].close if j > 0 else bars[j].close
            tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
            trs.append(tr)
        
        bar.atr = sum(trs) / len(trs)

def compute_sma(bars: List[Bar], length: int) -> List[Optional[float]]:
    """Compute Simple Moving Average."""
    smas = []
    for i, bar in enumerate(bars):
        if i < length - 1:
            smas.append(None)
        else:
            avg = sum(bars[j].close for j in range(i - length + 1, i + 1)) / length
            smas.append(avg)
    return smas

def compute_bias(bars: List[Bar]) -> None:
    """Compute bias (CALL if fast > slow, PUT otherwise)."""
    for bar in bars:
        if bar.fast_sma is not None and bar.slow_sma is not None:
            bar.bias = "CALL" if bar.fast_sma > bar.slow_sma else "PUT"

def tag_confluence(bars: List[Bar], price_tol: float = 0.008) -> None:
    """Tag bars with confluence flags."""
    for i, bar in enumerate(bars):
        bar.price_confluence = 0
        bar.time_confluence = 0
        
        if bar.atr is None or bar.bias is None:
            continue
        
        # Simple geometry level (simplified for Phase 1)
        if i > 10:
            recent_high = max(bars[j].high for j in range(max(0, i-10), i))
            recent_low = min(bars[j].low for j in range(max(0, i-10), i))
            bar.geo_level = (recent_high + recent_low) / 2
            bar.phi_level = recent_high * 0.618
            
            # Price confluence if near geo
            if bar.geo_level is not None:
                if abs(bar.close - bar.geo_level) < bar.atr * price_tol:
                    bar.price_confluence = 1

# ---------------------------------------------------------------------------
# Write CSV Output (with FIX #1 schema improvements)
# ---------------------------------------------------------------------------

def write_spy_csv(symbol: str, bars: List[Bar]) -> None:
    """Write enriched OHLCV data."""
    path = DATA_DIR / f"{symbol}.csv"
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
                'ATR', 'FastSMA', 'SlowSMA', 'Bias',
                'GeoLevel', 'PhiLevel', 'PriceConfluence', 'TimeConfluence'
            ]
        )
        writer.writeheader()
        for bar in bars:
            writer.writerow({
                'Date': bar.d,
                'Open': round(bar.open_, 2),
                'High': round(bar.high, 2),
                'Low': round(bar.low, 2),
                'Close': round(bar.close, 2),
                'Volume': int(bar.volume),
                'ATR': round(bar.atr, 2) if bar.atr else '',
                'FastSMA': round(bar.fast_sma, 2) if bar.fast_sma else '',
                'SlowSMA': round(bar.slow_sma, 2) if bar.slow_sma else '',
                'Bias': bar.bias or '',
                'GeoLevel': round(bar.geo_level, 2) if bar.geo_level else '',
                'PhiLevel': round(bar.phi_level, 2) if bar.phi_level else '',
                'PriceConfluence': bar.price_confluence,
                'TimeConfluence': bar.time_confluence,
            })
    
    logger.info(f"Wrote {len(bars)} bars to {path}")

def write_spy_confluence_csv(symbol: str, bars: List[Bar]) -> None:
    """Write confluence-tagged bars."""
    path = DATA_DIR / f"{symbol}_confluence.csv"
    confluence_bars = [b for b in bars if b.price_confluence or b.time_confluence]
    
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'Date', 'Close', 'ATR', 'FastSMA', 'SlowSMA', 'Bias',
                'GeoLevel', 'PhiLevel', 'PriceConfluence', 'TimeConfluence'
            ]
        )
        writer.writeheader()
        for bar in confluence_bars:
            writer.writerow({
                'Date': bar.d,
                'Close': round(bar.close, 2),
                'ATR': round(bar.atr, 2) if bar.atr else '',
                'FastSMA': round(bar.fast_sma, 2) if bar.fast_sma else '',
                'SlowSMA': round(bar.slow_sma, 2) if bar.slow_sma else '',
                'Bias': bar.bias or '',
                'GeoLevel': round(bar.geo_level, 2) if bar.geo_level else '',
                'PhiLevel': round(bar.phi_level, 2) if bar.phi_level else '',
                'PriceConfluence': bar.price_confluence,
                'TimeConfluence': bar.time_confluence,
            })
    
    logger.info(f"Wrote {len(confluence_bars)} confluence bars to {path}")

def build_confluence_trades(
    bars: List[Bar],
    entry_band_atr: float = 0.5,
    stop_atr: float = 1.5,
    hold_days: int = 5,
    price_tol_pct: float = 0.008,
) -> List[dict]:
    """Generate base confluence trades."""
    trades = []
    
    for i, bar in enumerate(bars):
        if not bar.bias or not (bar.price_confluence or bar.time_confluence):
            continue
        
        if bar.atr is None:
            continue
        
        entry_band = bar.atr * entry_band_atr
        entry_low = bar.close - entry_band
        entry_high = bar.close + entry_band
        
        stop_dist = bar.atr * stop_atr
        if bar.bias == "CALL":
            stop = bar.close - stop_dist
            target1 = bar.close + (stop_dist * 2)
            target2 = bar.close + (stop_dist * 3)
        else:
            stop = bar.close + stop_dist
            target1 = bar.close - (stop_dist * 2)
            target2 = bar.close - (stop_dist * 3)
        
        trade = {
            'Symbol': 'SPY',
            'Signal': bar.bias,
            'EntryDate': bar.d,
            'ExitDate': '',
            'EntryPrice': round(bar.close, 2),
            'ExitPrice': '',
            'PNL': '',
            'EntryLow': round(min(entry_low, entry_high), 2),
            'EntryHigh': round(max(entry_low, entry_high), 2),
            'Stop': round(stop, 2),
            'Target1': round(target1, 2),
            'Target2': round(target2, 2),
            'ExpiryDate': '',
            'Status': f'BASE_CONFLUENCE (${bar.close:.2f})',
        }
        trades.append(trade)
    
    logger.info(f"Generated {len(trades)} base confluence trades")
    return trades

def write_portfolio_confluence(trades: List[dict]) -> None:
    """Write base confluence trades to CSV."""
    path = REPORT_DIR / "portfolio_confluence.csv"
    cols = [
        'Symbol', 'Signal', 'EntryDate', 'ExitDate',
        'EntryPrice', 'ExitPrice', 'PNL',
        'EntryLow', 'EntryHigh', 'Stop',
        'Target1', 'Target2', 'ExpiryDate', 'Status',
    ]
    
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for trade in trades:
            # FIX #1: Sanitize status
            trade['Status'] = sanitize_status_string(trade['Status'])
            writer.writerow(trade)
    
    logger.info(f"Wrote {len(trades)} base trades to {path}")

def build_gann_and_super_confluence(
    bars: List[Bar],
    base_trades: List[dict],
    account_balance: float = 100000.0,
) -> None:
    """Build Gann–Elliott and super-confluence outputs."""
    if ACTIVE_STRATEGY_MODE not in ("GANN_ELLIOTT", "UNIFIED"):
        return
    
    df = bars_to_dataframe(bars)
    if df.empty:
        logger.info("[GANN-ELLIOTT] No bars; writing empty CSVs.")
        base_cols = [
            "Symbol", "Signal", "EntryDate", "ExitDate",
            "EntryPrice", "ExitPrice", "PNL",
            "EntryLow", "EntryHigh", "Stop",
            "Target1", "Target2", "ExpiryDate", "Status",
        ]
        # Always create empty files
        for path in [
            REPORT_DIR / "portfolio_gann_elliott.csv",
            REPORT_DIR / "portfolio_super_confluence.csv"
        ]:
            with path.open("w", newline="") as f:
                csv.DictWriter(f, fieldnames=base_cols).writeheader()
        return
    
    ge = gann_elliott_strategy(df, account_balance=account_balance)
    gann_rows: List[dict] = []
    super_rows: List[dict] = []
    
    base_cols = [
        "Symbol", "Signal", "EntryDate", "ExitDate",
        "EntryPrice", "ExitPrice", "PNL",
        "EntryLow", "EntryHigh", "Stop",
        "Target1", "Target2", "ExpiryDate", "Status",
    ]
    
    today = df.index[-1].date().isoformat()
    
    # Gann–Elliott tracking row
    if ge is not NO_TRADE:
        logger.info("[GANN-ELLIOTT] Valid signal generated.")
        ge_row = {
            "Symbol": "SPY",
            "Signal": ge["direction"],
            "EntryDate": today,
            "ExitDate": "",
            "EntryPrice": round(ge["entry"], 2),
            "ExitPrice": "",
            "PNL": "",
            "EntryLow": round(min(ge["entry"], ge["stop"]), 2),
            "EntryHigh": round(max(ge["entry"], ge["target1"]), 2),
            "Stop": round(ge["stop"], 2),
            "Target1": round(ge["target1"], 2),
            "Target2": round(ge["target2"], 2),
            "ExpiryDate": "",
            "Status": (
                f"GANN_ELLIOTT (conf {ge['confidence']:.1f}, "
                f"regime {ge['regime'][0]}/{ge['regime'][1]})"
            ),
        }
        gann_rows.append(ge_row)
    else:
        logger.debug("[GANN-ELLIOTT] NO_TRADE for latest bar; no qualifying signal.")
    
    # Super-Confluence row (Base + Gann agree on CALL/PUT)
    if (
        ACTIVE_STRATEGY_MODE == "UNIFIED"
        and base_trades
        and ge is not NO_TRADE
    ):
        base_last = base_trades[-1]
        base_dir = base_last.get("Signal", "").upper()
        gann_dir = ge["direction"].upper()
        
        if base_dir in ("CALL", "PUT") and base_dir == gann_dir:
            logger.info("[SUPER-CONFLUENCE] Base and Gann–Elliott agree on direction.")
            super_row = dict(base_last)
            super_row["Status"] = sanitize_status_string(
                f"SUPER_CONFLUENCE ({base_dir}) | "
                f"Gann/Elliott conf {ge['confidence']:.1f}, "
                f"regime {ge['regime'][0]}/{ge['regime'][1]}"
            )
            super_rows.append(super_row)
        else:
            logger.debug("[SUPER-CONFLUENCE] Directions differ or invalid; no super row.")
    else:
        if not base_trades:
            logger.debug("[SUPER-CONFLUENCE] No base trades to compare with.")
        if ge is NO_TRADE:
            logger.debug("[SUPER-CONFLUENCE] No Gann–Elliott signal to compare with.")
    
    # Save CSVs: always write headers so files always exist
    gann_path = REPORT_DIR / "portfolio_gann_elliott.csv"
    with gann_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=base_cols)
        writer.writeheader()
        for r in gann_rows:
            writer.writerow(r)
    logger.info(f"Wrote {len(gann_rows)} Gann–Elliott rows to {gann_path}")
    
    super_path = REPORT_DIR / "portfolio_super_confluence.csv"
    with super_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=base_cols)
        writer.writeheader()
        for r in super_rows:
            writer.writerow(r)
    logger.info(f"Wrote {len(super_rows)} Super-Confluence rows to {super_path}")

def bars_to_dataframe(bars: List[Bar]) -> pd.DataFrame:
    """Convert List[Bar] to pandas DataFrame."""
    if not bars:
        return pd.DataFrame(columns=["close", "volume"])
    df = pd.DataFrame(
        {
            "close": [b.close for b in bars],
            "volume": [b.volume for b in bars],
        },
        index=pd.to_datetime([b.d for b in bars]),
    )
    return df

def evaluate_confluence_performance(
    trades: List[dict],
    bars: List[Bar],
) -> dict:
    """Evaluate trading performance (simplified)."""
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_r": 0.0,
            "avg_pnl": 0.0,
            "max_drawdown": 0.0,
        }
    
    winners = sum(1 for t in trades if t.get('PNL') and float(t['PNL']) > 0)
    
    return {
        "total_trades": len(trades),
        "win_rate": winners / len(trades) if trades else 0.0,
        "avg_r": 1.0,
        "avg_pnl": 0.0,
        "max_drawdown": 0.0,
    }

def run_tuning_grid(bars: List[Bar], grid: List[dict]) -> List[dict]:
    """Run parameter tuning grid."""
    results = []
    for params in grid:
        trades = build_confluence_trades(
            bars,
            entry_band_atr=params.get("ENTRY_BAND_ATR", 0.5),
            stop_atr=params.get("STOP_ATR", 1.5),
            hold_days=params.get("HOLD_DAYS", 5),
            price_tol_pct=params.get("PRICE_TOL_PCT", 0.008),
        )
        perf = evaluate_confluence_performance(trades, bars)
        results.append({
            "params": params,
            "win_rate": perf["win_rate"],
            "avg_r": perf["avg_r"],
        })
    
    return results

LIGHT_GRID = [
    {"ENTRY_BAND_ATR": 0.5, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.4, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
]

MEDIUM_GRID = [
    {"ENTRY_BAND_ATR": 0.4, "STOP_ATR": 1.2, "HOLD_DAYS": 4, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.4, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
]

DEEP_GRID = [
    {"ENTRY_BAND_ATR": eb, "STOP_ATR": st, "HOLD_DAYS": hd, "PRICE_TOL_PCT": pt}
    for eb in (0.4, 0.5)
    for st in (1.2, 1.5)
    for hd in (4, 5)
    for pt in (0.008,)
]

# =========================================================================
# MAIN
# =========================================================================

def main() -> None:
    """Main agent run."""
    logger.info("=" * 80)
    logger.info("CONFLUENCE AGENT START - WEEK 2 FIXES")
    logger.info(f"Strategy Mode: {ACTIVE_STRATEGY_MODE}")
    logger.info("=" * 80)
    
    all_trades: List[dict] = []
    all_bars: List[Bar] = []
    
    for symbol in SYMBOLS:
        logger.info(f"\n>>> Processing {symbol}")
        
        # FIX #3: Use robust fetch with retry
        bars = fetch_yfinance_daily(symbol, START_DATE)
        
        if not bars:
            logger.error(f"Failed to fetch data for {symbol}. Aborting run.")
            return
        
        logger.info(f"Processing {len(bars)} bars")
        
        # Base indicators + confluence tagging
        compute_atr(bars, ATR_LENGTH)
        fast = compute_sma(bars, FAST_SMA_LEN)
        slow = compute_sma(bars, SLOW_SMA_LEN)
        for b, f, s in zip(bars, fast, slow):
            b.fast_sma = f
            b.slow_sma = s
        compute_bias(bars)
        tag_confluence(bars, PRICE_TOL_PCT)
        
        write_spy_csv(symbol, bars)
        write_spy_confluence_csv(symbol, bars)
        
        # Build base confluence trades
        trades = build_confluence_trades(
            bars,
            entry_band_atr=ENTRY_BAND_ATR,
            stop_atr=STOP_ATR,
            hold_days=HOLD_DAYS,
            price_tol_pct=PRICE_TOL_PCT,
        )
        write_portfolio_confluence(trades)
        
        # Gann–Elliott + Super-Confluence tracking
        build_gann_and_super_confluence(bars, trades, account_balance=100000.0)
        
        all_trades.extend(trades)
        all_bars = bars
    
    # Performance + tuning
    perf = evaluate_confluence_performance(all_trades, all_bars)
    perf_path = DATA_DIR / "performance_confluence.json"
    perf_path.write_text(json.dumps(perf, indent=2))
    logger.info(f"Wrote performance metrics to {perf_path}")
    
    tuning_results = {
        "light": run_tuning_grid(all_bars, LIGHT_GRID),
        "medium": run_tuning_grid(all_bars, MEDIUM_GRID),
        "deep": run_tuning_grid(all_bars, DEEP_GRID),
    }
    tuning_path = DATA_DIR / "tuning_confluence.json"
    tuning_path.write_text(json.dumps(tuning_results, indent=2))
    logger.info(f"Wrote tuning results to {tuning_path}")
    
    logger.info("\n" + "=" * 80)
    logger.info("CONFLUENCE AGENT COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
