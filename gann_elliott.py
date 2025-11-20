#!/usr/bin/env python3
"""
Gann–Elliott Confluence Strategy Engine

Implements:
- Objective Elliott-like wave detection (simplified, rule-based).
- Square-of-9 price levels for support/resistance.
- Gann cycle timing confidence.
- Trend & volatility regime filters.
- Risk-based entry/stop/target sizing.
- Final trade object compatible with the existing confluence agent.

NOTE: This is a first, mechanical implementation meant for SPY daily data.
It approximates full Elliott rules using a ZigZag backbone and indicators.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Core parameters (from your spec, converted to numeric values)
# ---------------------------------------------------------------------------

ZIGZAG_THRESHOLD = 0.05       # 5% swing to qualify as a pivot
MIN_WAVE_BARS = 8
MAX_WAVE_BARS = 89

LEVEL_TOLERANCE = 0.0075      # 0.75% tolerance to call a level "hit"
MUST_CLOSE_NEAR_LEVEL = True
MINIMUM_TIME_AT_LEVEL = 2

PRIMARY_ANGLES = [90, 180, 270, 360]
SECONDARY_ANGLES = [45, 135, 225, 315]

CARDINAL_LEVEL_WEIGHT = 2.0
ORDINAL_LEVEL_WEIGHT = 1.0

GANN_CYCLES_TRADING_DAYS = [11, 22, 34, 45, 56, 67, 78, 90]
CYCLE_TOLERANCE_DAYS = 2

RISK_PER_TRADE = 1.0  # %
MAX_PORTFOLIO_RISK = 6.0  # %

MINIMUM_WAVE_CONFIDENCE = 70.0

# Simple underlying-only phase
TRADE_UNDERLYING_SYMBOL = "SPY"

# ---------------------------------------------------------------------------
# Utility indicators: EMA, RSI, MACD, ATR
# ---------------------------------------------------------------------------

def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(length).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(length).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50.0)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
         ) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(length).mean()


# ---------------------------------------------------------------------------
# ZigZag pivot detection (simplified)
# ---------------------------------------------------------------------------

@dataclass
class Pivot:
    idx: int        # integer index in df
    price: float
    kind: str       # "H" or "L"


def compute_zigzag(
    df: pd.DataFrame,
    pct_threshold: float = ZIGZAG_THRESHOLD,
    min_bars: int = MIN_WAVE_BARS,
) -> List[Pivot]:
    """
    Simple ZigZag: marks local highs/lows when price reverses more than pct_threshold
    from the last extreme, and at least min_bars have elapsed.
    """
    closes = df["close"].values
    n = len(closes)
    if n < min_bars + 2:
        return []

    pivots: List[Pivot] = []

    # Start from the first bar, assume first pivot is a low
    last_pivot_idx = 0
    last_pivot_price = closes[0]
    last_pivot_kind = "L"  # guess
    pivots.append(Pivot(last_pivot_idx, last_pivot_price, last_pivot_kind))

    direction = 0  # 1 up, -1 down, 0 unknown

    for i in range(1, n):
        price = closes[i]
        change = (price - last_pivot_price) / last_pivot_price

        if direction >= 0:  # currently or previously up / unknown
            # looking for new high or reversal down
            if price > last_pivot_price:
                # new high
                last_pivot_idx = i
                last_pivot_price = price
                last_pivot_kind = "H"
            elif (last_pivot_price - price) / last_pivot_price >= pct_threshold and i - last_pivot_idx >= min_bars:
                # reversal down -> last pivot was a valid high
                if pivots[-1].idx != last_pivot_idx:
                    pivots[-1] = Pivot(last_pivot_idx, last_pivot_price, "H")
                direction = -1
                last_pivot_idx = i
                last_pivot_price = price
                last_pivot_kind = "L"
                pivots.append(Pivot(last_pivot_idx, last_pivot_price, last_pivot_kind))

        if direction <= 0:  # currently or previously down / unknown
            # looking for new low or reversal up
            if price < last_pivot_price:
                last_pivot_idx = i
                last_pivot_price = price
                last_pivot_kind = "L"
            elif (price - last_pivot_price) / last_pivot_price >= pct_threshold and i - last_pivot_idx >= min_bars:
                # reversal up
                if pivots[-1].idx != last_pivot_idx:
                    pivots[-1] = Pivot(last_pivot_idx, last_pivot_price, "L")
                direction = 1
                last_pivot_idx = i
                last_pivot_price = price
                last_pivot_kind = "H"
                pivots.append(Pivot(last_pivot_idx, last_pivot_price, last_pivot_kind))

    return pivots


# ---------------------------------------------------------------------------
# Simplified Elliott-like wave detection + confidence scoring
# ---------------------------------------------------------------------------

@dataclass
class WavePattern:
    direction: str              # "up" or "down"
    wave1_low: float
    wave1_high: float
    wave2_low: float
    wave3_high: float
    wave4_low: float
    wave5_high: float
    confidence: float
    label: str                  # "wave_2_complete", "wave_5_complete", etc.


def detect_elliott_waves(df: pd.DataFrame, min_confidence: float = MINIMUM_WAVE_CONFIDENCE
                         ) -> Optional[WavePattern]:
    """
    Heuristic, rule-based attempt to identify a 1–5 impulse sequence
    using the most recent ZigZag pivots and your scoring scheme.
    Returns None if confidence < min_confidence.
    """
    closes = df["close"]
    vols = df["volume"]
    rsi_series = rsi(closes, 14)
    macd_line, macd_signal, macd_hist = macd(closes)

    pivots = compute_zigzag(df)
    if len(pivots) < 6:
        return None

    # Take last 6 pivots for a candidate wave structure
    last6 = pivots[-6:]
    # For a simple uptrend impulse: L-H-L-H-L-H
    kinds = "".join(p.kind for p in last6)
    if kinds != "LHLHLH":
        # try inverse (downtrend)
        if kinds != "HLHLHL":
            return None

    # Assume uptrend for now if first is L:
    direction = "up" if kinds == "LHLHLH" else "down"
    p0, p1, p2, p3, p4, p5 = last6

    if direction == "down":
        # For now, we focus on bullish 1–5, you can extend for bearish later
        return None

    # Map pivots to waves (uptrend)
    wave1_low = p0.price
    wave1_high = p1.price
    wave2_low = p2.price
    wave3_high = p3.price
    wave4_low = p4.price
    wave5_high = p5.price

    # Lengths
    len1 = wave1_high - wave1_low
    len3 = wave3_high - wave2_low
    len5 = wave5_high - wave4_low

    # Retracements
    retr2 = (wave1_high - wave2_low) / max(len1, 1e-9)
    retr4 = (wave3_high - wave4_low) / max(len3, 1e-9)

    # Approx volumes per wave
    def wave_volume(idx_start: int, idx_end: int) -> float:
        return vols[idx_start: idx_end + 1].mean()

    v1 = wave_volume(p0.idx, p1.idx)
    v2 = wave_volume(p1.idx, p2.idx)
    v3 = wave_volume(p2.idx, p3.idx)
    v4 = wave_volume(p3.idx, p4.idx)
    v5 = wave_volume(p4.idx, p5.idx)

    # Times (bars)
    t1 = p1.idx - p0.idx
    t3 = p3.idx - p2.idx

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    score = 0.0

    # 1) Fibonacci retracement within tolerance
    fib_hits = 0
    if 0.382 <= retr2 <= 0.618:
        fib_hits += 1
    if 0.236 <= retr4 <= 0.50:
        fib_hits += 1
    if fib_hits == 2:
        score += 20.0

    # 2) Volume pattern
    vol_ok = v2 < v1 and v3 > v1 and v4 < v3
    if vol_ok:
        score += 15.0

    # 3) RSI / MACD confirmation
    # Check RSI > 50 during Wave 1 and Wave 3
    rsi1 = rsi_series[p0.idx: p1.idx + 1].mean()
    rsi3 = rsi_series[p2.idx: p3.idx + 1].mean()
    macd3 = macd_hist[p2.idx: p3.idx + 1].mean()
    if rsi1 > 50 and rsi3 > 55 and macd3 > 0:
        score += 15.0

    # 4) Hard rules: Wave 3 not shortest, no overlap
    hard_ok = True
    if not (len3 > len1 and len3 > len5):
        hard_ok = False
    if wave4_low <= wave1_high:  # overlap
        hard_ok = False
    if hard_ok:
        score += 20.0

    # 5) Time proportion: Wave 3 time > Wave 1 time
    if t3 > t1:
        score += 15.0

    # 6) Alternation: approximate by comparing retr2 vs retr4
    alt_ok = ((retr2 > 0.5 and retr4 < 0.4) or (retr2 < 0.5 and retr4 > 0.4))
    if alt_ok:
        score += 15.0

    if score < min_confidence:
        return None

    # Label current state: if last pivot was wave 2 or 5 completion
    # Heuristics: if last pivot is low close to current close -> wave 2/4,
    # else if last pivot is high -> wave 5 complete.
    current_close = df["close"].iloc[-1]
    if abs(current_close - wave2_low) / wave2_low < 0.01:
        label = "wave_2_complete"
    elif abs(current_close - wave4_low) / wave4_low < 0.01:
        label = "wave_4_complete"
    elif abs(current_close - wave5_high) / wave5_high < 0.01:
        label = "wave_5_complete"
    else:
        label = "wave_pattern_detected"

    return WavePattern(
        direction=direction,
        wave1_low=wave1_low,
        wave1_high=wave1_high,
        wave2_low=wave2_low,
        wave3_high=wave3_high,
        wave4_low=wave4_low,
        wave5_high=wave5_high,
        confidence=score,
        label=label,
    )


# ---------------------------------------------------------------------------
# Gann Square of 9 price geometry
# ---------------------------------------------------------------------------

def gann_square_of_9(price: float, increments: int = 8) -> Dict[str, List[float]]:
    """
    Returns resistance/support levels from Square of 9-like rotation.
    """
    sqrt_price = math.sqrt(price)

    levels = {
        "resistance": [],
        "support": [],
    }

    for i in range(1, increments + 1):
        angle_degrees = i * 45.0
        degree_increment = angle_degrees / 180.0

        r_value = (sqrt_price + degree_increment) ** 2
        levels["resistance"].append(round(r_value, 2))

        if sqrt_price > degree_increment:
            s_value = (sqrt_price - degree_increment) ** 2
            levels["support"].append(round(s_value, 2))

    return levels


def nearest_gann_levels(price: float, levels: Dict[str, List[float]]) -> Tuple[float, float]:
    """
    Returns nearest support and resistance to current price.
    """
    supports = levels.get("support", []) or [price]
    resistances = levels.get("resistance", []) or [price]

    nearest_support = min(supports, key=lambda x: abs(x - price))
    nearest_resistance = min(resistances, key=lambda x: abs(x - price))

    return nearest_support, nearest_resistance


def is_at_gann_level(price: float, level: float, tolerance: float = LEVEL_TOLERANCE) -> bool:
    return abs(price - level) / level <= tolerance


# ---------------------------------------------------------------------------
# Gann time cycles
# ---------------------------------------------------------------------------

def identify_cycle_start_pivot(df: pd.DataFrame, lookback: int = 90) -> Optional[pd.Timestamp]:
    """
    Objective pivot identification within last `lookback` bars:
    - Approximate swing magnitude by (high-low)/close.
    - Weight by volume spike.
    - Return timestamp of most "significant" pivot.
    """
    window = df.iloc[-lookback:].copy()
    swing_mag = (window["high"] - window["low"]) / window["close"]
    vol_spike = window["volume"] / window["volume"].rolling(20).mean()
    score = swing_mag * vol_spike
    score = score.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    idx = score.idxmax()
    return idx


def cycle_confidence(distance_from_pivot: int) -> float:
    """
    Returns a 0–1 timing confidence as a function of distance from
    nearest Gann cycle day.
    """
    best = 0.3
    for cycle_days in GANN_CYCLES_TRADING_DAYS:
        diff = abs(distance_from_pivot - cycle_days)
        if diff <= 2:
            return 1.0
        elif diff <= 4:
            best = max(best, 0.7)
    return best


# ---------------------------------------------------------------------------
# Regime detection (trend + volatility)
# ---------------------------------------------------------------------------

def detect_trend_regime(df: pd.DataFrame) -> str:
    """
    Returns: 'strong_uptrend', 'weak_uptrend', 'sideways', 'weak_downtrend', 'strong_downtrend'
    """
    closes = df["close"]
    sma50 = closes.rolling(50).mean()
    sma200 = closes.rolling(200).mean()
    if len(sma200.dropna()) == 0:
        return "sideways"

    sma_50 = sma50.iloc[-1]
    sma_200 = sma200.iloc[-1]
    current_price = closes.iloc[-1]

    sma_50_prev = sma50.iloc[-10] if len(sma50.dropna()) > 10 else sma50.iloc[-1]
    sma_200_prev = sma200.iloc[-20] if len(sma200.dropna()) > 20 else sma200.iloc[-1]

    sma_50_slope = (sma_50 - sma_50_prev) / 10
    sma_200_slope = (sma_200 - sma_200_prev) / 20

    if current_price > sma_50 > sma_200 and sma_50_slope > 0 and sma_200_slope > 0:
        return "strong_uptrend"
    elif current_price > sma_50 > sma_200:
        return "weak_uptrend"
    elif current_price < sma_50 < sma_200 and sma_50_slope < 0 and sma_200_slope < 0:
        return "strong_downtrend"
    elif current_price < sma_50 < sma_200:
        return "weak_downtrend"
    else:
        # If MAs are close together, treat as sideways
        if abs(sma_50 - sma_200) / sma_200 < 0.02:
            return "sideways"
        return "sideways"


def detect_vol_regime(df: pd.DataFrame, lookback: int = 20) -> str:
    """
    Realized vol regime based on 20-day vs ~1-year vol.
    """
    returns = df["close"].pct_change()
    rv = returns.rolling(lookback).std() * (252 ** 0.5)
    long_rv = returns.rolling(252).std() * (252 ** 0.5)

    if rv.iloc[-1] == 0 or long_rv.iloc[-1] == 0 or np.isnan(rv.iloc[-1]) or np.isnan(long_rv.iloc[-1]):
        return "normal_vol"

    if rv.iloc[-1] < long_rv.iloc[-1] * 0.7:
        return "low_vol"
    elif rv.iloc[-1] > long_rv.iloc[-1] * 1.3:
        return "high_vol"
    else:
        return "normal_vol"


# ---------------------------------------------------------------------------
# Risk & position sizing
# ---------------------------------------------------------------------------

def calculate_position_size(account_balance: float, entry_price: float, stop_price: float) -> int:
    risk_amount = account_balance * (RISK_PER_TRADE / 100.0)
    price_risk = abs(entry_price - stop_price)
    if price_risk <= 0:
        return 0
    size = risk_amount / price_risk
    return max(int(size), 0)


# ---------------------------------------------------------------------------
# Main strategy function
# ---------------------------------------------------------------------------

def gann_elliott_strategy(
    df: pd.DataFrame,
    account_balance: float = 100_000.0,
) -> Optional[Dict]:
    """
    Full systematic Gann–Elliott strategy on underlying (SPY).
    Returns a trade dict or None (no trade).
    """
    if len(df) < 260:
        return None

    df = df.copy()
    df = df.sort_index()
    df["rsi"] = rsi(df["close"], 14)
    df["atr"] = atr(df, 14)

    trend = detect_trend_regime(df)
    vol_regime = detect_vol_regime(df)

    # Avoid trades in sideways regime
    if trend == "sideways":
        return None

    # Elliott-like wave detection
    pattern = detect_elliott_waves(df, min_confidence=MINIMUM_WAVE_CONFIDENCE)
    if pattern is None:
        return None

    # Gann levels from last close
    current_price = float(df["close"].iloc[-1])
    levels = gann_square_of_9(current_price, increments=5)
    nearest_support, nearest_resistance = nearest_gann_levels(current_price, levels)

    # Time cycle
    pivot_ts = identify_cycle_start_pivot(df, lookback=90)
    if pivot_ts is None:
        return None

    # Use trading days distance
    try:
        pivot_loc = df.index.get_loc(pivot_ts)
    except KeyError:
        pivot_loc = max(0, len(df) - 90)

    distance_from_pivot = len(df) - 1 - pivot_loc
    t_conf = cycle_confidence(distance_from_pivot)
    if t_conf < 0.7:
        return None

    atr14 = float(df["atr"].iloc[-1])
    if atr14 <= 0:
        atr14 = current_price * 0.01  # fallback

    # Entry logic (bullish only in this version)
    direction = None
    entry = None
    stop = None
    target = None
    entry_label = None

    # Wave 2 pullback near support: bullish call/long
    if pattern.label == "wave_2_complete" and is_at_gann_level(current_price, nearest_support):
        direction = "LONG"
        entry = current_price
        stop = min(pattern.wave1_low, nearest_support - 2 * atr14)
        target = nearest_resistance
        entry_label = "wave2_support"

    # Wave 5 completion near resistance: bearish (placeholder, not trading yet)
    elif pattern.label == "wave_5_complete" and is_at_gann_level(current_price, nearest_resistance):
        # For now, underlying implementation is long-only; you can extend to shorts later.
        direction = None

    if direction is None:
        return None

    # Position size
    size = calculate_position_size(account_balance, entry, stop)
    if size <= 0:
        return None

    # Reward/risk
    reward = abs(target - entry)
    risk = abs(entry - stop)
    if risk <= 0 or reward / risk < 2.0:
        return None

    # Final confluence confidence (0–100)
    # 40% from wave confidence, 30% from timing, 30% from price-level hit.
    price_conf = 1.0 if is_at_gann_level(current_price, nearest_support) or is_at_gann_level(current_price, nearest_resistance) else 0.0
    total_conf = (
        pattern.confidence * 0.4
        + (t_conf * 100.0) * 0.3
        + (price_conf * 100.0) * 0.3
    )

    if total_conf < 75.0:
        return None

    trade = {
        "Symbol": TRADE_UNDERLYING_SYMBOL,
        "Direction": direction,
        "EntryPrice": entry,
        "StopPrice": stop,
        "TargetPrice": target,
        "Size": size,
        "WaveConfidence": pattern.confidence,
        "TimeConfidence": t_conf * 100.0,
        "PriceConfluence": price_conf * 100.0,
        "TotalConfidence": total_conf,
        "TrendRegime": trend,
        "VolRegime": vol_regime,
        "GannSupport": nearest_support,
        "GannResistance": nearest_resistance,
        "EntryLabel": entry_label,
        "DistanceFromPivot": distance_from_pivot,
        "CyclePivotDate": df.index[pivot_loc].date() if isinstance(df.index[pivot_loc], (pd.Timestamp,)) else df.index[pivot_loc],
    }

    return trade
gann_elliott.py
