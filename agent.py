#!/usr/bin/env python3
"""
SPY Confluence Agent with Playbook Outputs

Research-only agent to:
- Fetch recent SPY daily prices from Tiingo.
- Save raw prices to data/SPY.csv.
- Compute geometric + phi price levels and Gann-style time windows.
- Flag "confluence" bars where price and time overlap.
- Generate CALL / PUT bias from trend + confluence.
- For each new signal, create a structured playbook:
    * entry zone (ATR-based)
    * guard-rail stop
    * 2R / 3R targets
    * time stop (N bars)
    * status based on how price evolved

Outputs:
- data/SPY.csv                 (raw history)
- data/SPY_confluence.csv      (bar-level confluence fields + ATR)
- reports/portfolio_confluence.csv (playbook-style trade log)

NOTE: This is a research tool, not trading advice or an automated trading system.
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
# Config (you can tune these numbers later)
# ---------------------------------------------------------------------------

ATR_LENGTH = 14
ENTRY_BAND_ATR = 0.5   # entry zone = close ± 0.5 * ATR
STOP_ATR = 1.5         # guard rail = bar extreme ± 1.5 * ATR
HOLD_DAYS = 5          # time stop (bars)
PRICE_TOL_PCT = 0.008  # 0.8% tolerance for price confluence (looser)

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
    entry_low: float
    entry_high: float
    stop: float
    target1: float
    target2: float
    expiry_date: date
    status: str


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


def atr(bars: List[Bar], length: int = ATR_LENGTH) -> List[float]:
    """Average True Range."""
    trs: List[float] = []
    prev_close = None
    for b in bars:
        if prev_close is None:
            tr = b.high - b.low
        else:
            tr = max(
                b.high - b.low,
                abs(b.high - prev_close),
                abs(b.low - prev_close),
            )
        trs.append(tr)
        prev_close = b.close
    return sma(trs, length)


def find_last_swing_low_high(
    bars: List[Bar], lookback: int = 250
) -> Tuple[Tuple[float, date], Tuple[float, date]]:
    """Simple swing detector: min low and max high over recent window."""
    recent = bars[-lookback:] if len(bars) >= lookback else bars
    low_bar = min(recent, key=lambda b: b.low)
    high_bar = max(recent, key=lambda b: b.high)
    return (low_bar.low, low_bar.d), (high_bar.high, high_bar.d)


# ---------------------------------------------------------------------------
# Geometry: Square-style rotations
# ---------------------------------------------------------------------------

def square_rotation_levels(
    pivot_price: float, n_steps: int = 12, step_degrees: float = 45.0
) -> List[float]:
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
    """Build standard fib retracements + extensions around a swing."""
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
    levels = sorted({round(x, 4) for x in levels})
    return levels


def nearest_level_distance(price: float, levels: List[float]) -> Tuple[float, float]:
    """Return (nearest_level, absolute_distance)."""
    if not levels:
        return (math.nan, math.inf)
    nearest = min(levels, key=lambda x: abs(x - price))
    return nearest, abs(nearest - price)


# ---------------------------------------------------------------------------
# Gann-like time windows
# ---------------------------------------------------------------------------

def gann_time_windows(
    pivot_date: date, counts: List[int], half_width_days: int = 2
) -> List[Tuple[date, date]]:
    """Build [start, end] windows around pivot_date + count days."""
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
# Playbook simulation
# ---------------------------------------------------------------------------

def simulate_trade_from_signal(
    symbol: str,
    bars: List[Bar],
    idx: int,
    signal: str,
    atr_value: float,
    hold_days: int = HOLD_DAYS,
) -> Trade:
    """
    Create a playbook for a signal at index `idx` and simulate its evolution.

    Rules:
    - Entry zone: close ± ENTRY_BAND_ATR * ATR
    - Stop: bar low/high ± STOP_ATR * ATR (direction dependent)
    - Targets: 2R and 3R where R is distance from entry_mid to stop
    - Time stop: max of `hold_days` bars after signal
    - Status tracks whether price:
        * never touched zone (EXPIRED_UNTRIGGERED)
        * entered zone but hit stop / TP1 / TP2
        * or exited on time (EXITED_TIME)
    """
    b0 = bars[idx]
    entry_mid = b0.close
    band = ENTRY_BAND_ATR * atr_value
    entry_low = entry_mid - band
    entry_high = entry_mid + band

    if signal == "CALL":
        stop = b0.low - STOP_ATR * atr_value
        risk = entry_mid - stop
        target1 = entry_mid + 2 * risk
        target2 = entry_mid + 3 * risk
    else:  # PUT
        stop = b0.high + STOP_ATR * atr_value
        risk = stop - entry_mid
        target1 = entry_mid - 2 * risk
        target2 = entry_mid - 3 * risk

    n = len(bars)
    expiry_index = min(n - 1, idx + hold_days)
    expiry_date = bars[expiry_index].d

    has_entered = False
    status = "WAITING"
    exit_price = entry_mid
    exit_date = expiry_date

    for j in range(idx + 1, expiry_index + 1):
        bj = bars[j]

        # entry trigger: any touch of the entry band
        if not has_entered:
            if bj.low <= entry_high and bj.high >= entry_low:
                has_entered = True
                status = "ACTIVE"

        if has_entered:
            if signal == "CALL":
                # guard rail first
                if bj.low <= stop:
                    status = "EXITED_STOP"
                    exit_price = stop
                    exit_date = bj.d
                    break
                # then higher targets
                if bj.high >= target2:
                    status = "EXITED_TP2"
                    exit_price = target2
                    exit_date = bj.d
                    break
                if bj.high >= target1:
                    status = "EXITED_TP1"
                    exit_price = target1
                    exit_date = bj.d
                    break
            else:  # PUT
                if bj.high >= stop:
                    status = "EXITED_STOP"
                    exit_price = stop
                    exit_date = bj.d
                    break
                if bj.low <= target2:
                    status = "EXITED_TP2"
                    exit_price = target2
                    exit_date = bj.d
                    break
                if bj.low <= target1:
                    status = "EXITED_TP1"
                    exit_price = target1
                    exit_date = bj.d
                    break

    if has_entered and status in ("ACTIVE", "WAITING"):
        status = "EXITED_TIME"
        exit_price = bars[expiry_index].close
        exit_date = bars[expiry_index].d
    elif not has_entered:
        status = "EXPIRED_UNTRIGGERED"
        exit_price = bars[expiry_index].close
        exit_date = bars[expiry_index].d

    if has_entered:
        pnl = exit_price - entry_mid if signal == "CALL" else entry_mid - exit_price
    else:
        pnl = 0.0

    return Trade(
        symbol=symbol,
        signal=signal,
        entry_date=b0.d,
        entry_price=entry_mid,
        exit_date=exit_date,
        exit_price=exit_price,
        pnl=pnl,
        entry_low=entry_low,
        entry_high=entry_high,
        stop=stop,
        target1=target1,
        target2=target2,
        expiry_date=expiry_date,
        status=status,
    )


# ---------------------------------------------------------------------------
# Confluence engine
# ---------------------------------------------------------------------------

def build_confluence_dataset(
    symbol: str,
    bars: List[Bar],
    hold_days: int = HOLD_DAYS,
    price_tolerance_pct: float = PRICE_TOL_PCT,
) -> Tuple[List[dict], List[Trade]]:
    """
    Compute bar-level confluence fields and create playbook-style trades.

    Confluence when:
    - distance to nearest geometric level < tolerance
    - distance to nearest phi level < tolerance
    - date is inside at least one Gann window

    Trend filter:
    - close > SMA(50) -> CALL bias
    - close < SMA(50) -> PUT bias
    """
    closes = [b.close for b in bars]
    sma50 = sma(closes, 50)
    atr14 = atr(bars, ATR_LENGTH)

    # Use last swing low/high as anchors (now over ~1 trading year)
    (swing_low, swing_low_date), (swing_high, swing_high_date) = \
        find_last_swing_low_high(bars, lookback=250)
    print(
        f"[INFO] Last swing low {swing_low:.2f} on {swing_low_date}, "
        f"high {swing_high:.2f} on {swing_high_date}"
    )

    geom_levels = square_rotation_levels(
        pivot_price=swing_low, n_steps=20, step_degrees=45.0
    )
    phi_levels = phi_levels_from_range(swing_low, swing_high)
    time_windows = gann_time_windows(
        pivot_date=swing_low_date,
        counts=[30, 45, 60, 90, 120, 144, 180, 225, 240, 270, 288, 315, 360],
        half_width_days=4,  # wider timing windows (±4 days)
    )
    print(
        f"[INFO] Geometry levels: {len(geom_levels)}, "
        f"phi levels: {len(phi_levels)}, time windows: {len(time_windows)}"
    )

    rows: List[dict] = []
    trades: List[Trade] = []
    last_signal = None  # "CALL"/"PUT"
    n = len(bars)

    for i in range(n):
        b = bars[i]
        price = b.close

        g_level, g_dist = nearest_level_distance(price, geom_levels)
        f_level, f_dist = nearest_level_distance(price, phi_levels)
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
                "ATR14": atr14[i],
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

        # Playbook trade creation
        if (
            signal in ("CALL", "PUT")
            and signal != last_signal
            and not math.isnan(atr14[i])
        ):
            trade = simulate_trade_from_signal(
                symbol=symbol,
                bars=bars,
                idx=i,
                signal=signal,
                atr_value=atr14[i],
                hold_days=hold_days,
            )
            trades.append(trade)
            last_signal = signal

    print(f"[INFO] Generated {len(trades)} confluence trades with playbooks.")
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
                "EntryLow",
                "EntryHigh",
                "Stop",
                "Target1",
                "Target2",
                "ExpiryDate",
                "Status",
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
                    f"{t.entry_low:.4f}",
                    f"{t.entry_high:.4f}",
                    f"{t.stop:.4f}",
                    f"{t.target1:.4f}",
                    f"{t.target2:.4f}",
                    t.expiry_date.isoformat(),
                    t.status,
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

    # Fetch ~3 years of data for confluence analysis
    start = (date.today() - timedelta(days=3 * 365)).isoformat()
    bars = tiingo_prices(symbol, start, token)
    if not bars:
        print("[WARN] No data returned from Tiingo.")
        return

    # 1) Save raw prices
    save_raw_prices(symbol, bars)

    # 2) Build confluence dataset & playbook trades
    rows, trades = build_confluence_dataset(
        symbol, bars, hold_days=HOLD_DAYS, price_tolerance_pct=PRICE_TOL_PCT
    )

    # 3) Save outputs
    save_confluence_csv(symbol, rows)
    save_confluence_trades(trades)
    print("[INFO] Confluence agent run complete.")


if __name__ == "__main__":
    main()
