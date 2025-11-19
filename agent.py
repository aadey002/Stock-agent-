#!/usr/bin/env python3
"""
SPY Confluence Agent

Research-only agent to:
- Fetch recent SPY daily prices from Tiingo.
- Save raw prices to data/SPY.csv.
- Compute geometric + phi price levels and Gann-style time windows.
- Flag "confluence" bars where price and time overlap.
- Generate simple CALL / PUT signals based on trend + confluence.
- Backtest a fixed-horizon strategy on SPY itself (not options).
- Save enriched bar data and trade log for downstream analysis & dashboard.

NOTE: This is a research tool, NOT trading advice or an automated trading system.
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
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path("data")
REPORT_DIR = pathlib.Path("reports")
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


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


@dataclass
class Trade:
    symbol: str
    signal: str  # "CALL" or "PUT"
    entry_date: date
    entry_price: float
    exit_date: date
    exit_price: float
    pnl: float


# ---------------------------------------------------------------------------
# Tiingo fetch
# ---------------------------------------------------------------------------

def tiingo_prices(symbol: str, start_date: str, token: str) -> List[Bar]:
    url = (
        f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
        f"?startDate={start_date}&token={token}"
    )
    print(f"[INFO] Requesting {symbol} data from Tiingo starting {start_date}")
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)

    rows: List[Bar] = []
    for b in data:
        d = datetime.fromisoformat(b["date"]).date()
        rows.append(
            Bar(
                d=d,
                open=float(b["open"]),
                high=float(b["high"]),
                low=float(b["low"]),
                close=float(b["close"]),
                volume=float(b.get("volume", 0.0)),
            )
        )

    rows.sort(key=lambda x: x.d)
    print(f"[INFO] Received {len(rows)} rows for {symbol}")
    return rows


def save_raw_prices(symbol: str, bars: List[Bar]) -> None:
    path = DATA_DIR / f"{symbol}.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
        for b in bars:
            w.writerow(
                [
                    b.d.isoformat(),
                    f"{b.open:.4f}",
                    f"{b.high:.4f}",
                    f"{b.low:.4f}",
                    f"{b.close:.4f}",
                    f"{b.volume:.0f}",
                ]
            )
    print(f"[INFO] Saved {len(bars)} rows to {path}")


# ---------------------------------------------------------------------------
# Helper analytics
# ---------------------------------------------------------------------------

def sma(values: List[float], length: int) -> List[float]:
    out = [math.nan] * len(values)
    if length <= 0:
        return out
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= length:
            s -= values[i - length]
        if i >= length - 1:
            out[i] = s / length
    return out


def find_last_swing_low_high(bars: List[Bar], lookback: int = 60) -> Tuple[Tuple[float, date], Tuple[float, date]]:
    """Simple swing detector: min low and max high over recent window."""
    recent = bars[-lookback:] if len(bars) >= lookback else bars
    low_bar = min(recent, key=lambda b: b.low)
    high_bar = max(recent, key=lambda b: b.high)
    return (low_bar.low, low_bar.d), (high_bar.high, high_bar.d)


# ---------------------------------------------------------------------------
# Geometry: Square-style rotations
# ---------------------------------------------------------------------------

def square_rotation_levels(pivot_price: float, n_steps: int = 12, step_degrees: float = 45.0) -> List[float]:
    """
    Very simple Square-of-Nine inspired ladder:

    angle = sqrt(price) * 180
    rotate by +/- k * step_degrees, convert back via price = (angle/180)^2

    This is a research approximation, not a canonical implementation.
    """
    if pivot_price <= 0:
        return []
    base_angle = math.sqrt(pivot_price) * 180.0
    levels: List[float] = []
    for k in range(-n_steps, n_steps + 1):
        ang = base_angle + k * step_degrees
        if ang <= 0:
            continue
        p = (ang / 180.0) ** 2
        levels.append(p)
    return sorted(levels)


# ---------------------------------------------------------------------------
# Divine proportions: phi & sqrt ladders
# ---------------------------------------------------------------------------

PHI = (1 + 5 ** 0.5) / 2

def phi_levels_from_range(low: float, high: float) -> List[float]:
    """
    Build standard fib retracements + extensions around a swing.
    """
    if high <= low:
        return []
    r = high - low
    fib_retr = [0.236, 0.382, 0.5, 0.618, 0.786]
    fib_ext = [1.0, 1.272, 1.618, 2.0, 2.618]

    levels: List[float] = []
    for f in fib_retr:
        levels.append(low + r * f)
        levels.append(high - r * f)
    for f in fib_ext:
        levels.append(high + r * (f - 1.0))
        levels.append(low - r * (f - 1.0))
    # unique & sorted
    levels = sorted({round(x, 4) for x in levels})
    return levels


def nearest_level_distance(price: float, levels: List[float]) -> Tuple[float, float]:
    """
    Return (nearest_level, absolute_distance).
    """
    if not levels:
        return (math.nan, math.inf)
    nearest = min(levels, key=lambda x: abs(x - price))
    return nearest, abs(nearest - price)


# ---------------------------------------------------------------------------
# Gann-like time windows
# ---------------------------------------------------------------------------

def gann_time_windows(pivot_date: date,
                      counts: List[int],
                      half_width_days: int = 2) -> List[Tuple[date, date]]:
    """
    Build [start, end] windows around pivot_date + count days.
    """
    windows: List[Tuple[date, date]] = []
    for c in counts:
        center = pivot_date + timedelta(days=c)
        start = center - timedelta(days=half_width_days)
        end = center + timedelta(days=half_width_days)
        windows.append((start, end))
    return windows


def is_in_any_window(d: date, windows: List[Tuple[date, date]]) -> bool:
    return any(start <= d <= end for (start, end) in windows)


# ---------------------------------------------------------------------------
# Confluence engine
# ---------------------------------------------------------------------------

def build_confluence_dataset(symbol: str,
                             bars: List[Bar],
                             hold_days: int = 5,
                             price_tolerance_pct: float = 0.003) -> Tuple[List[dict], List[Trade]]:
    """
    Compute bar-level confluence fields and simulate a simple strategy:

    - Confluence when:
      * distance to nearest geometric level < tolerance
      * distance to nearest phi level < tolerance
      * date is inside at least one Gann window

    - Trend filter:
      * close > SMA(50) -> CALL bias
      * close < SMA(50) -> PUT bias

    - When a confluence bar appears with bias != last signal, open a new trade,
      hold for `hold_days` bars, then close.
    """
    closes = [b.close for b in bars]
    sma50 = sma(closes, 50)

    # Use last swing low/high as anchors
    (swing_low, swing_low_date), (swing_high, swing_high_date) = find_last_swing_low_high(bars, lookback=120)
    print(f"[INFO] Last swing low {swing_low:.2f} on {swing_low_date}, "
          f"high {swing_high:.2f} on {swing_high_date}")

    geom_levels = square_rotation_levels(pivot_price=swing_low, n_steps=20, step_degrees=45.0)
    phi_levels = phi_levels_from_range(swing_low, swing_high)
    time_windows = gann_time_windows(
        pivot_date=swing_low_date,
        counts=[30, 45, 60, 90, 120, 144, 180, 225, 240, 270, 288, 315, 360],
        half_width_days=2,
    )
    print(f"[INFO] Geometry levels: {len(geom_levels)}, phi levels: {len(phi_levels)}, "
          f"time windows: {len(time_windows)}")

    rows: List[dict] = []
    trades: List[Trade] = []

    last_signal = None  # "CALL"/"PUT"
    i = 0
    n = len(bars)

    while i < n:
        b = bars[i]
        price = b.close

        # distances
        g_level, g_dist = nearest_level_distance(price, geom_levels)
        f_level, f_dist = nearest_level_distance(price, phi_levels)

        # tolerance in points based on percentage of price
        tol_points = price * price_tolerance_pct

        price_confluence = (g_dist <= tol_points) and (f_dist <= tol_points)
        time_hit = is_in_any_window(b.d, time_windows)
        in_confluence = price_confluence and time_hit

        trend = None
        if not math.isnan(sma50[i]):
            if price > sma50[i]:
                trend = "UP"
            elif price < sma50[i]:
                trend = "DOWN"

        signal = "NONE"
        if in_confluence and trend == "UP":
            signal = "CALL"
        elif in_confluence and trend == "DOWN":
            signal = "PUT"

        rows.append(
            {
                "Date": b.d.isoformat(),
                "Open": b.open,
                "High": b.high,
                "Low": b.low,
                "Close": b.close,
                "Volume": b.volume,
                "SMA50": sma50[i],
                "GeomLevel": g_level,
                "GeomDist": g_dist,
                "PhiLevel": f_level,
                "PhiDist": f_dist,
                "PriceTolPts": tol_points,
                "PriceConfluence": int(price_confluence),
                "TimeWindowHit": int(time_hit),
                "ConfluenceHit": int(in_confluence),
                "Trend": trend or "",
                "Signal": signal,
            }
        )

        # Backtest logic on underlying SPY
        if signal in ("CALL", "PUT") and signal != last_signal:
            entry_idx = i
            exit_idx = min(n - 1, entry_idx + hold_days)
            entry_bar = bars[entry_idx]
            exit_bar = bars[exit_idx]

            if signal == "CALL":
                pnl = exit_bar.close - entry_bar.close
            else:
                pnl = entry_bar.close - exit_bar.close

            trades.append(
                Trade(
                    symbol=symbol,
                    signal=signal,
                    entry_date=entry_bar.d,
                    entry_price=entry_bar.close,
                    exit_date=exit_bar.d,
                    exit_price=exit_bar.close,
                    pnl=pnl,
                )
            )
            last_signal = signal
            # we still continue bar-by-bar; overlapping trades are allowed in this simple model

        i += 1

    print(f"[INFO] Generated {len(trades)} confluence trades.")
    return rows, trades


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------

def save_confluence_csv(symbol: str, rows: List[dict]) -> None:
    path = DATA_DIR / f"{symbol}_confluence.csv"
    if not rows:
        print("[WARN] No confluence rows to save.")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[INFO] Saved enriched confluence dataset to {path}")


def save_confluence_trades(trades: List[Trade]) -> None:
    path = REPORT_DIR / "portfolio_confluence.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "Symbol",
                "Signal",
                "EntryDate",
                "EntryPrice",
                "ExitDate",
                "ExitPrice",
                "PNL",
            ]
        )
        for t in trades:
            w.writerow(
                [
                    t.symbol,
                    t.signal,
                    t.entry_date.isoformat(),
                    f"{t.entry_price:.4f}",
                    t.exit_date.isoformat(),
                    f"{t.exit_price:.4f}",
                    f"{t.pnl:.4f}",
                ]
            )
    print(f"[INFO] Saved {len(trades)} trades to {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    token = os.environ.get("TIINGO_TOKEN")
    if not token:
        raise SystemExit("[ERROR] TIINGO_TOKEN environment variable is required")

    symbol_env = os.environ.get("SYMBOLS", "SPY")
    symbol = symbol_env.split(",")[0].strip().upper() or "SPY"

    # Fetch ~1 year of data for confluence analysis
    start = (date.today() - timedelta(days=365)).isoformat()
    bars = tiingo_prices(symbol, start, token)
    if not bars:
        print("[WARN] No data returned from Tiingo.")
        return

    # 1) Save raw prices
    save_raw_prices(symbol, bars)

    # 2) Build confluence dataset & trades
    rows, trades = build_confluence_dataset(symbol, bars, hold_days=5, price_tolerance_pct=0.003)

    # 3) Save outputs
    save_confluence_csv(symbol, rows)
    save_confluence_trades(trades)
    print("[INFO] Confluence agent run complete.")


if __name__ == "__main__":
    main()

    
