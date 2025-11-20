#!/usr/bin/env python3
"""
SPY Confluence Agent with Playbook + Tuning

What this script does
---------------------
1. Fetches daily SPY prices from Tiingo (using TIINGO_TOKEN).
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
   - data/SPY_confluence.csv (bar-level enriched data)
   - reports/portfolio_confluence.csv (playbook trades)
6. Computes performance metrics + tuning grids:
   - data/performance_confluence.json
   - data/tuning_confluence.json

NOTE: This is a research tool, not trading advice.
"""

import csv
import json
import math
import os
import pathlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Tuple

import urllib.request

# ---------------------------------------------------------------------------
# Strategy modes & notifications (2.1)
# ---------------------------------------------------------------------------

# Which engine should the agent use when it builds playbooks?
#   "BASE"          = your original geometry/φ/time SMA agent only
#   "GANN_ELLIOTT"  = pure Gann–Elliott engine (no original geometry)
#   "UNIFIED"       = require confluence of BOTH engines
ACTIVE_STRATEGY_MODE = "UNIFIED"   # <- you can change this from the dashboard later

# Minimum confidence/quality thresholds for the Gann–Elliott engine
MIN_WAVE_CONFIDENCE = 70          # from your Wave_Confidence_Score spec
MIN_TOTAL_CONFIDENCE = 75         # final combined score to allow a trade

# Volatility / regime rules
REQUIRE_NORMAL_VOL = True         # skip trades in extreme vol regimes
INCREASE_CONF_IN_STRONG_TREND = 1.2   # multiplier for confidence in strong trends
REDUCE_SIZE_IN_HIGH_VOL = 0.5         # position size factor in high vol

# Alert / notification settings
ENABLE_ALERTS = True              # master on/off
ALERT_MIN_CONFIDENCE = 80         # only alert when confidence >= this
ALERT_INCLUDE_DIRECTION = True    # include CALL/PUT + entry/stop/targets in text

# Channels – these are placeholders that the HTML/JS or a future webhook/email
# module can use; the core agent just writes into the reports.
ALERT_CHANNELS = {
    "console": True,              # always on (GitHub Actions log)
    "webhook": False,             # set True once you wire a webhook URL
    "email": False,               # set True when SMTP or service is configured
}

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path("data")
REPORT_DIR = pathlib.Path("reports")
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Elliott Wave Engine (Detection + Confidence Model)
# ---------------------------------------------------------------------------

def zigzag(df, threshold=0.05):
    """
    Simple ZigZag pivot detector used for wave structure.
    Identifies percent-based pivots.
    """
    pivots = []
    last_pivot_price = df['close'].iloc[0]
    last_pivot_type = None  # "high" or "low"

    for i in range(1, len(df)):
        price = df['close'].iloc[i]
        change = (price - last_pivot_price) / last_pivot_price

        if last_pivot_type != "high" and change >= threshold:
            pivots.append(("low", last_pivot_price, df.index[i-1]))
            last_pivot_price = price
            last_pivot_type = "high"

        elif last_pivot_type != "low" and change <= -threshold:
            pivots.append(("high", last_pivot_price, df.index[i-1]))
            last_pivot_price = price
            last_pivot_type = "low"

    return pivots


def detect_elliott_waves(df):
    """
    Attempts to detect 1-5 impulsive structure and compute wave confidence.
    Produces:
        - wave labels
        - prices of wave pivots
        - confidence score (0-100)
        - current market phase ('wave_2_complete', 'wave_5_complete', etc.)
    """

    pivots = zigzag(df, threshold=0.05)
    if len(pivots) < 6:
        return None  # insufficient pivots to identify waves

    # Use latest 6 pivots as potential Wave 0-5
    candidate = pivots[-6:]
    labels = ["W0", "W1", "W2", "W3", "W4", "W5"]
    waves = {labels[i]: candidate[i][1] for i in range(6)}
    times = {labels[i]: candidate[i][2] for i in range(6)}

    # ---- HARD RULE CHECKS ----
    score = 0

    # Wave 2 cannot break below Wave 0
    if waves["W2"] > waves["W0"]:
        score += 20

    # Wave 3 must NOT be shortest among 1,3,5
    len1 = abs(waves["W1"] - waves["W0"])
    len3 = abs(waves["W3"] - waves["W2"])
    len5 = abs(waves["W5"] - waves["W4"])
    if len3 > len1 and len3 > len5:
        score += 20

    # Fibonacci checks
    retr2 = abs(waves["W1"] - waves["W2"]) / len1
    retr4 = abs(waves["W3"] - waves["W4"]) / len3

    if 0.382 <= retr2 <= 0.618:
        score += 15

    if 0.236 <= retr4 <= 0.50:
        score += 15

    # Time proportionality
    t1 = (times["W1"] - times["W0"]).days
    t3 = (times["W3"] - times["W2"]).days
    if t3 > t1:
        score += 15

    # Alternation (sharp Wave 2, sideways Wave 4)
    if (retr2 > 0.45 and retr4 < 0.35) or (retr2 < 0.45 and retr4 > 0.35):
        score += 15

    phase = None
    close = df['close'].iloc[-1]

    if close > waves["W2"] and close < waves["W3"]:
        phase = "wave_2_complete"
    elif close > waves["W4"]:
        phase = "wave_5_complete"

    return {
        "confidence": score,
        "waves": waves,
        "times": times,
        "current": phase,
        "wave_1_low": waves["W0"],
        "wave_5_high": waves["W5"]
    }
# ---------------------------------------------------------------------------
# Gann Square of 9 Engine
# ---------------------------------------------------------------------------

def gann_square_of_9(price, increments=5):
    import math
    sqrtp = math.sqrt(price)

    res = []
    sup = []

    for k in range(1, increments + 1):
        deg = k * 45
        inc = deg / 180.0
        res.append( round((sqrtp + inc)**2, 2) )
        if sqrtp > inc:
            sup.append( round((sqrtp - inc)**2, 2) )

    return {"resistance": res, "support": sup}


def nearest_gann_levels(price, gann):
    r = gann["resistance"]
    s = gann["support"]

    nearest_r = min(r, key=lambda x: abs(x - price))
    nearest_s = min(s, key=lambda x: abs(x - price))

    return nearest_s, nearest_r
# ---------------------------------------------------------------------------
# Regime Filters, Time Cycles, Position Sizing, and Gann–Elliott Strategy
# ---------------------------------------------------------------------------

NO_TRADE = None  # simple sentinel


def detect_trend_regime(df):
    """
    Returns: 'strong_uptrend', 'weak_uptrend', 'sideways',
             'weak_downtrend', 'strong_downtrend'
    """
    if len(df) < 220:
        return "unknown"

    sma50 = df['close'].rolling(50).mean()
    sma200 = df['close'].rolling(200).mean()

    sma50_last = sma50.iloc[-1]
    sma200_last = sma200.iloc[-1]
    price = df['close'].iloc[-1]

    # simple slope proxies (10 bars and 20 bars)
    sma50_prev = sma50.iloc[-10]
    sma200_prev = sma200.iloc[-20]
    slope50 = (sma50_last - sma50_prev) / 10.0
    slope200 = (sma200_last - sma200_prev) / 20.0

    if price > sma50_last > sma200_last and slope50 > 0 and slope200 > 0:
        return "strong_uptrend"
    if price > sma50_last > sma200_last:
        return "weak_uptrend"
    if abs(sma50_last - sma200_last) / max(1e-9, sma200_last) < 0.02:
        return "sideways"
    if price < sma50_last < sma200_last and slope50 < 0 and slope200 < 0:
        return "strong_downtrend"
    if price < sma50_last < sma200_last:
        return "weak_downtrend"
    return "unknown"


def detect_vol_regime(df, lookback=20):
    """
    Returns: 'low_vol', 'normal_vol', 'high_vol'
    """
    if len(df) < 260:
        return "normal_vol"

    daily_ret = df['close'].pct_change()

    realized = daily_ret.rolling(lookback).std().iloc[-1] * (252 ** 0.5)
    hist = daily_ret.rolling(252).std().iloc[-1] * (252 ** 0.5)

    if realized < hist * 0.7:
        return "low_vol"
    if realized > hist * 1.3:
        return "high_vol"
    return "normal_vol"


def identify_cycle_start_pivot(df, lookback=90):
    """
    Choose a recent significant pivot using volume and swing magnitude.
    Returns a timestamp; if not found, falls back to 90 bars ago.
    """
    if len(df) < lookback + 5:
        return df.index.max()

    window = df.iloc[-lookback:].copy()
    # simple swing magnitude vs 20-bar rolling mean
    window['roll_max'] = window['close'].rolling(20).max()
    window['roll_min'] = window['close'].rolling(20).min()
    window['swing_mag'] = (window['roll_max'] - window['roll_min']) / window['roll_min']
    window['vol_score'] = window['volume'] / window['volume'].rolling(20).mean()

    # high volume & big swing
    pivots = window[(window['swing_mag'] > 0.05) & (window['vol_score'] > 1.5)]
    if len(pivots) == 0:
        return df.index[-lookback]

    return pivots.index[-1]


GANN_CYCLES_TRADING_DAYS = [11, 22, 34, 45, 56, 67, 78, 90]


def cycle_confidence(days_from_pivot):
    """
    Higher when we are near standard Gann cycle counts.
    Returns 0.3 (weak), 0.7 (good), 1.0 (strong)
    """
    best = 0.3
    for c in GANN_CYCLES_TRADING_DAYS:
        diff = abs(days_from_pivot - c)
        if diff <= 2:
            return 1.0
        if diff <= 4:
            best = max(best, 0.7)
    return best


# --- Position sizing / R:R helpers ------------------------------------------

RISK_PER_TRADE = 1.0        # % of equity
MAX_PORTFOLIO_RISK = 6.0    # not enforced here, but kept for future use


def calculate_position_size(account_balance, entry_price, stop_price):
    risk_amount = account_balance * (RISK_PER_TRADE / 100.0)
    price_risk = abs(entry_price - stop_price)
    if price_risk <= 0:
        return 0
    size = int(risk_amount / price_risk)
    return max(size, 0)


# --- Gann–Elliott unified decision engine -----------------------------------

def gann_elliott_strategy(df, account_balance=100000.0):
    """
    Returns either NO_TRADE or a dict:
      {
        'direction': 'CALL' or 'PUT',
        'entry': float,
        'stop': float,
        'target1': float,
        'target2': float,
        'confidence': float (0-100),
        'regime': (trend, vol)
      }
    """
    if len(df) < 220:
        return NO_TRADE

    trend = detect_trend_regime(df)
    vol = detect_vol_regime(df)

    # 1. Regime filter
    if trend == "sideways":
        return NO_TRADE

    # 2. Wave structure
    waves = detect_elliott_waves(df)
    if not waves:
        return NO_TRADE

    wave_conf = waves["confidence"]
    if wave_conf < MIN_WAVE_CONFIDENCE:
        return NO_TRADE

    # 3. Gann levels near current price
    price = df['close'].iloc[-1]
    gann = gann_square_of_9(price, increments=5)
    nearest_support, nearest_resistance = nearest_gann_levels(price, gann)

    # 4. Time cycles
    pivot_date = identify_cycle_start_pivot(df)
    days_from_pivot = (df.index[-1] - pivot_date).days
    cyc = cycle_confidence(days_from_pivot)
    if cyc < 0.7:
        return NO_TRADE

    # 5. Directional logic: bullish vs bearish phase
    direction = None
    entry = price
    stop = None
    t1 = None
    t2 = None

    # wave_2_complete => looking for Wave 3 up
    if waves["current"] == "wave_2_complete" and price <= nearest_support * 1.0075:
        direction = "CALL"
        stop = waves["wave_1_low"] * 0.99
        t1 = nearest_resistance
        t2 = nearest_resistance * 1.01  # simple extension

    # wave_5_complete => looking for A/C down
    elif waves["current"] == "wave_5_complete" and price >= nearest_resistance * 0.9925:
        direction = "PUT"
        stop = waves["wave_5_high"] * 1.01
        t1 = nearest_support
        t2 = nearest_support * 0.99

    if direction is None or stop is None or t1 is None:
        return NO_TRADE

    # 6. Position size + R:R
    size = calculate_position_size(account_balance, entry, stop)
    reward = abs(t1 - entry)
    risk = abs(entry - stop)
    if risk <= 0 or reward / risk < 2.0:
        return NO_TRADE

    # 7. Final confidence score (0-100)
    at_level = (abs(price - nearest_support) / price < 0.0075) or (
        abs(price - nearest_resistance) / price < 0.0075
    )
    level_score = 100 if at_level else 0

    total_conf = (
        waves["confidence"] * 0.4 +
        cyc * 100 * 0.3 +
        level_score * 0.3
    )

    if total_conf < MIN_TOTAL_CONFIDENCE:
        return NO_TRADE

    return {
        "direction": direction,
        "entry": float(entry),
        "stop": float(stop),
        "target1": float(t1),
        "target2": float(t2),
        "size": size,
        "confidence": total_conf,
        "regime": (trend, vol),
        "gann_support": float(nearest_support),
        "gann_resistance": float(nearest_resistance),
    }
# ---------------------------------------------------------------------------
# Config (core parameters)
# ---------------------------------------------------------------------------

# indicator lengths
ATR_LENGTH = 14
FAST_SMA_LEN = 10
SLOW_SMA_LEN = 20

# playbook parameters (these are the "live" settings)
ENTRY_BAND_ATR = 0.5   # entry zone = close ± 0.5 * ATR
STOP_ATR = 1.5         # guard rail = bar extreme ± 1.5 * ATR
HOLD_DAYS = 5          # time stop (bars)
PRICE_TOL_PCT = 0.008  # 0.8% tolerance for price confluence

# universe
SYMBOLS = ["SPY"]

# Tiingo config
TIINGO_TOKEN_ENV = "TIINGO_TOKEN"
TIINGO_BASE = "https://api.tiingo.com/tiingo/daily/{symbol}/prices"

# data start
START_DATE = date(2022, 11, 20)

# ---------------------------------------------------------------------------
# Tuning grids (Light / Medium / Deep)
# ---------------------------------------------------------------------------

LIGHT_GRID = [
    {"ENTRY_BAND_ATR": 0.5, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.4, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.6, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.5, "STOP_ATR": 1.2, "HOLD_DAYS": 4, "PRICE_TOL_PCT": 0.008},
]

MEDIUM_GRID = [
    {"ENTRY_BAND_ATR": 0.4, "STOP_ATR": 1.2, "HOLD_DAYS": 4, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.4, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.4, "STOP_ATR": 2.0, "HOLD_DAYS": 7, "PRICE_TOL_PCT": 0.010},
    {"ENTRY_BAND_ATR": 0.5, "STOP_ATR": 1.2, "HOLD_DAYS": 4, "PRICE_TOL_PCT": 0.008},
    {"ENTRY_BAND_ATR": 0.5, "STOP_ATR": 1.5, "HOLD_DAYS": 7, "PRICE_TOL_PCT": 0.010},
    {"ENTRY_BAND_ATR": 0.6, "STOP_ATR": 1.5, "HOLD_DAYS": 5, "PRICE_TOL_PCT": 0.008},
]

DEEP_GRID = [
    {"ENTRY_BAND_ATR": eb, "STOP_ATR": st, "HOLD_DAYS": hd, "PRICE_TOL_PCT": pt}
    for eb in (0.4, 0.5, 0.6)
    for st in (1.2, 1.5, 2.0)
    for hd in (4, 5, 7)
    for pt in (0.008, 0.010)
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Bar:
    d: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    atr: float = math.nan
    fast_sma: float = math.nan
    slow_sma: float = math.nan
    bias: str = ""           # CALL / PUT / ""
    geo_level: float = math.nan
    phi_level: float = math.nan
    time_confluence: bool = False
    price_confluence: bool = False


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    print(f"[INFO] {msg}")


def get_tiingo_token() -> str:
    tok = os.environ.get(TIINGO_TOKEN_ENV)
    if not tok:
        raise RuntimeError(
            f"Environment variable {TIINGO_TOKEN_ENV} is not set; "
            "make sure your GitHub secret is configured."
        )
    return tok


def fetch_tiingo_daily(symbol: str, start: date) -> List[Bar]:
    """Fetch daily bars from Tiingo and return as Bar list."""
    token = get_tiingo_token()
    url = (
        TIINGO_BASE.format(symbol=symbol)
        + f"?startDate={start.isoformat()}&format=csv&token={token}"
    )
    log(f"Requesting {symbol} data from Tiingo starting {start.isoformat()}")
    try:
        with urllib.request.urlopen(url) as resp:
            data = resp.read().decode("utf-8").splitlines()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Tiingo HTTP error: {e}") from e

    reader = csv.DictReader(data)
    bars: List[Bar] = []
    for row in reader:
        d = datetime.fromisoformat(row["date"].split("T")[0]).date()
        bars.append(
            Bar(
                d=d,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
        )
    log(f"Received {len(bars)} rows for {symbol}")
    return bars


def write_spy_csv(symbol: str, bars: List[Bar]) -> None:
    path = DATA_DIR / f"{symbol}.csv"
    with path.open("w", newline="") as f:
        fieldnames = [
            "Date", "Open", "High", "Low", "Close", "Volume",
            "ATR", "FastSMA", "SlowSMA", "Bias",
            "GeoLevel", "PhiLevel", "PriceConfluence", "TimeConfluence",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for b in bars:
            writer.writerow(
                {
                    "Date": b.d.isoformat(),
                    "Open": b.open,
                    "High": b.high,
                    "Low": b.low,
                    "Close": b.close,
                    "Volume": b.volume,
                    "ATR": b.atr,
                    "FastSMA": b.fast_sma,
                    "SlowSMA": b.slow_sma,
                    "Bias": b.bias,
                    "GeoLevel": b.geo_level,
                    "PhiLevel": b.phi_level,
                    "PriceConfluence": int(b.price_confluence),
                    "TimeConfluence": int(b.time_confluence),
                }
            )
    log(f"Saved {len(bars)} rows to {path}")


def write_spy_confluence_csv(symbol: str, bars: List[Bar]) -> None:
    path = DATA_DIR / f"{symbol}_confluence.csv"
    with path.open("w", newline="") as f:
        fieldnames = [
            "Date", "Close", "ATR", "FastSMA", "SlowSMA", "Bias",
            "GeoLevel", "PhiLevel", "PriceConfluence", "TimeConfluence",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for b in bars:
            writer.writerow(
                {
                    "Date": b.d.isoformat(),
                    "Close": b.close,
                    "ATR": b.atr,
                    "FastSMA": b.fast_sma,
                    "SlowSMA": b.slow_sma,
                    "Bias": b.bias,
                    "GeoLevel": b.geo_level,
                    "PhiLevel": b.phi_level,
                    "PriceConfluence": int(b.price_confluence),
                    "TimeConfluence": int(b.time_confluence),
                }
            )
    log(f"Saved enriched confluence dataset to {path}")


# ---------------------------------------------------------------------------
# Indicators & confluence logic
# ---------------------------------------------------------------------------

def compute_atr(bars: List[Bar], length: int) -> None:
    prev_close = None
    trs: List[float] = []
    for i, b in enumerate(bars):
        if prev_close is None:
            tr = b.high - b.low
        else:
            tr = max(
                b.high - b.low,
                abs(b.high - prev_close),
                abs(b.low - prev_close),
            )
        trs.append(tr)
        if len(trs) >= length:
            b.atr = sum(trs[-length:]) / length
        prev_close = b.close


def compute_sma(bars: List[Bar], length: int) -> List[float]:
    vals: List[float] = []
    closes = [b.close for b in bars]
    for i in range(len(bars)):
        if i + 1 < length:
            vals.append(math.nan)
        else:
            window = closes[i + 1 - length : i + 1]
            vals.append(sum(window) / length)
    return vals


def compute_bias(bars: List[Bar]) -> None:
    for b in bars:
        if math.isnan(b.fast_sma) or math.isnan(b.slow_sma):
            b.bias = ""
        elif b.fast_sma > b.slow_sma:
            b.bias = "CALL"
        elif b.fast_sma < b.slow_sma:
            b.bias = "PUT"
        else:
            b.bias = ""


def last_swing_low_high(bars: List[Bar], lookback: int = 250) -> Tuple[float, float, int]:
    if not bars:
        return math.nan, math.nan, -1
    window = bars[-lookback:]
    lows = [b.low for b in window]
    highs = [b.high for b in window]
    swing_low = min(lows)
    swing_high = max(highs)
    # index of swing_low relative to full series
    idx = lows.index(swing_low)
    swing_idx = len(bars) - len(window) + idx
    return swing_low, swing_high, swing_idx


def build_geometry_levels(swing_low: float, swing_high: float, n_levels: int = 41) -> List[float]:
    step = (swing_high - swing_low) / (n_levels - 1)
    return [swing_low + i * step for i in range(n_levels)]


def build_phi_levels(swing_low: float, swing_high: float) -> List[float]:
    phi = (1 + 5 ** 0.5) / 2
    span = swing_high - swing_low
    levels = [
        swing_low + span * (1 / phi),
        swing_low + span * (1 / phi ** 2),
        swing_low + span * (1 - 1 / phi),
        swing_low + span * (1 - 1 / phi ** 2),
    ]
    # add mirrored levels around midpoint
    mid = (swing_low + swing_high) / 2
    mirrored = [mid + (mid - lvl) for lvl in levels]
    return sorted(set(levels + mirrored))


def build_time_windows(bars: List[Bar], swing_idx: int) -> List[int]:
    """Return bar indices that are time windows based on Fibonacci day counts from swing."""
    fibs = [13, 21, 34, 55, 89, 144]
    idxs = []
    for f in fibs:
        i = swing_idx + f
        if 0 <= i < len(bars):
            idxs.append(i)
    return idxs


def tag_confluence(bars: List[Bar], price_tol_pct: float) -> None:
    """Set geo_level, phi_level, price_confluence, time_confluence on each bar."""
    swing_low, swing_high, swing_idx = last_swing_low_high(bars)
    if math.isnan(swing_low) or math.isnan(swing_high):
        return

    geo_levels = build_geometry_levels(swing_low, swing_high, n_levels=41)
    phi_levels = build_phi_levels(swing_low, swing_high)
    time_windows_idx = build_time_windows(bars, swing_idx)

    log(
        f"Last swing low {swing_low:.2f} on {bars[swing_idx].d}, "
        f"high {swing_high:.2f} on {max(b.high for b in bars):.2f}"
    )
    log(
        f"Geometry levels: {len(geo_levels)}, "
        f"phi levels: {len(phi_levels)}, "
        f"time windows: {len(time_windows_idx)}"
    )

    for i, b in enumerate(bars):
        # nearest geometry level
        geo = min(geo_levels, key=lambda x: abs(x - b.close))
        phi = min(phi_levels, key=lambda x: abs(x - b.close))
        b.geo_level = geo
        b.phi_level = phi

        price_tol = price_tol_pct * b.close
        b.price_confluence = (
            abs(b.close - geo) <= price_tol or abs(b.close - phi) <= price_tol
        )
        b.time_confluence = i in time_windows_idx


# ---------------------------------------------------------------------------
# Playbook construction
# ---------------------------------------------------------------------------

def build_confluence_trades(
    bars: List[Bar],
    entry_band_atr: float,
    stop_atr: float,
    hold_days: int,
    price_tol_pct: float,
) -> List[dict]:
    """
    Build playbook trades based on:
      - bias from SMA
      - price + time confluence
    Returns a list of trade dicts.
    """
    if not bars:
        return []

    # ensure indicators & tags are populated
    compute_atr(bars, ATR_LENGTH)
    fast = compute_sma(bars, FAST_SMA_LEN)
    slow = compute_sma(bars, SLOW_SMA_LEN)
    for b, f, s in zip(bars, fast, slow):
        b.fast_sma = f
        b.slow_sma = s
    compute_bias(bars)
    tag_confluence(bars, price_tol_pct)

    trades: List[dict] = []

    for i, b in enumerate(bars):
        if (
            b.bias in ("CALL", "PUT")
            and b.price_confluence
            and b.time_confluence
            and not math.isnan(b.atr)
        ):
            # build playbook for this bar
            entry_mid = b.close
            entry_low = entry_mid - entry_band_atr * b.atr
            entry_high = entry_mid + entry_band_atr * b.atr

            if b.bias == "CALL":
                stop = b.low - stop_atr * b.atr
                risk = entry_mid - stop
                direction = 1
            else:
                stop = b.high + stop_atr * b.atr
                risk = stop - entry_mid
                direction = -1

            if risk <= 0:
                continue

            target1 = entry_mid + direction * 2 * risk
            target2 = entry_mid + direction * 3 * risk

            # time exit
            exit_idx = min(i + hold_days, len(bars) - 1)
            exit_bar = bars[exit_idx]
            exit_price = exit_bar.close
            pnl = (exit_price - entry_mid) * direction

            trade = {
                "Symbol": "SPY",
                "Signal": b.bias,
                "EntryDate": b.d.isoformat(),
                "ExitDate": exit_bar.d.isoformat(),
                "EntryPrice": round(entry_mid, 4),
                "ExitPrice": round(exit_price, 4),
                "PNL": round(pnl, 4),
                "EntryLow": round(entry_low, 4),
                "EntryHigh": round(entry_high, 4),
                "Stop": round(stop, 4),
                "Target1": round(target1, 4),
                "Target2": round(target2, 4),
                "ExpiryDate": (b.d + timedelta(days=hold_days)).isoformat(),
                "Status": "EXITED_TIME",
            }
            trades.append(trade)

    log(f"Generated {len(trades)} confluence trades with playbooks.")
    return trades


def write_portfolio_confluence(trades: List[dict]) -> None:
    path = REPORT_DIR / "portfolio_confluence.csv"
    fieldnames = [
        "Symbol",
        "Signal",
        "EntryDate",
        "ExitDate",
        "EntryPrice",
        "ExitPrice",
        "PNL",
        "EntryLow",
        "EntryHigh",
        "Stop",
        "Target1",
        "Target2",
        "ExpiryDate",
        "Status",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in trades:
            writer.writerow(t)
    log(f"Saved {len(trades)} trades to {path}")


# ---------------------------------------------------------------------------
# Performance & tuning helpers
# ---------------------------------------------------------------------------

def trade_r_multiple(trade: dict) -> float | None:
    entry_low = trade.get("EntryLow")
    entry_high = trade.get("EntryHigh")
    stop = trade.get("Stop")
    pnl = trade.get("PNL")

    if None in (entry_low, entry_high, stop, pnl):
        return None

    entry_mid = (entry_low + entry_high) / 2.0
    risk = abs(entry_mid - stop)
    if risk <= 0:
        return None
    return pnl / risk


def evaluate_confluence_performance(trades: List[dict], bars: List[Bar]) -> dict:
    if not trades:
        summary = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_pnl": 0.0,
            "median_pnl": 0.0,
            "max_drawdown": 0.0,
            "avg_r": 0.0,
            "best_r": 0.0,
            "worst_r": 0.0,
            "avg_hold_days": 0.0,
        }
    else:
        pnls = [t["PNL"] for t in trades]
        total_trades = len(trades)
        wins = sum(1 for t in trades if t["PNL"] > 0)
        losses = sum(1 for t in trades if t["PNL"] < 0)

        win_rate = wins / total_trades * 100.0
        avg_pnl = sum(pnls) / total_trades
        med_pnl = median(pnls)

        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            equity += t["PNL"]
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        r_vals = [trade_r_multiple(t) for t in trades]
        r_vals = [r for r in r_vals if r is not None]
        if r_vals:
            avg_r = sum(r_vals) / len(r_vals)
            best_r = max(r_vals)
            worst_r = min(r_vals)
        else:
            avg_r = best_r = worst_r = 0.0

        hold_days = []
        for t in trades:
            ed = datetime.fromisoformat(t["EntryDate"]).date()
            xd = datetime.fromisoformat(t["ExitDate"]).date()
            hold_days.append((xd - ed).days)
        avg_hold = sum(hold_days) / len(hold_days) if hold_days else 0.0

        summary = {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_pnl": avg_pnl,
            "median_pnl": med_pnl,
            "max_drawdown": max_dd,
            "avg_r": avg_r,
            "best_r": best_r,
            "worst_r": worst_r,
            "avg_hold_days": avg_hold,
        }

    # benchmark: SPY buy & hold
    if bars:
        start_close = bars[0].close
        end_close = bars[-1].close
        buy_hold_ret = (end_close - start_close) / start_close * 100.0
        start_date = bars[0].d
        end_date = bars[-1].d
    else:
        buy_hold_ret = 0.0
        start_date = end_date = None

    benchmark = {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "spy_buy_hold_return": buy_hold_ret,
        "confluence_pnl": sum(t["PNL"] for t in trades) if trades else 0.0,
        "sma_pnl": None,
    }

    return {"summary": summary, "benchmark": benchmark}


def run_tuning_grid(bars: List[Bar], grid: List[dict]) -> List[dict]:
    results: List[dict] = []
    for params in grid:
        trades = build_confluence_trades(
            bars,
            entry_band_atr=params["ENTRY_BAND_ATR"],
            stop_atr=params["STOP_ATR"],
            hold_days=params["HOLD_DAYS"],
            price_tol_pct=params["PRICE_TOL_PCT"],
        )
        perf = evaluate_confluence_performance(trades, bars)["summary"]
        results.append(
            {
                "ENTRY_BAND_ATR": params["ENTRY_BAND_ATR"],
                "STOP_ATR": params["STOP_ATR"],
                "HOLD_DAYS": params["HOLD_DAYS"],
                "PRICE_TOL_PCT": params["PRICE_TOL_PCT"],
                "total_trades": perf["total_trades"],
                "win_rate": perf["win_rate"],
                "avg_r": perf["avg_r"],
            }
        )
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    all_trades: List[dict] = []
    all_bars: List[Bar] = []

    for symbol in SYMBOLS:
        bars = fetch_tiingo_daily(symbol, START_DATE)
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

        trades = build_confluence_trades(
            bars,
            entry_band_atr=ENTRY_BAND_ATR,
            stop_atr=STOP_ATR,
            hold_days=HOLD_DAYS,
            price_tol_pct=PRICE_TOL_PCT,
        )
        write_portfolio_confluence(trades)

        all_trades.extend(trades)
        all_bars = bars  # single symbol, so this is fine

    # performance + tuning for SPY
    perf = evaluate_confluence_performance(all_trades, all_bars)
    (DATA_DIR / "performance_confluence.json").write_text(
        json.dumps(perf, indent=2)
    )

    tuning_results = {
        "light": run_tuning_grid(all_bars, LIGHT_GRID),
        "medium": run_tuning_grid(all_bars, MEDIUM_GRID),
        "deep": run_tuning_grid(all_bars, DEEP_GRID),
    }
    (DATA_DIR / "tuning_confluence.json").write_text(
        json.dumps(tuning_results, indent=2)
    )

    log("Confluence agent run complete.")


if __name__ == "__main__":
    main()
