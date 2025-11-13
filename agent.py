#!/usr/bin/env python3
"""
Confluence Agent

Daily tasks:
1) Fetch OHLCV from Tiingo for configured symbols.
2) Append to per-symbol CSV histories.
3) For each symbol, compute:
   - Square-of-Nine and Fibonacci levels from a pivot
   - Time-cycle windows
   - Confluence-based signals
   - Delta-1 trade simulation (hold/stop/target)
4) Append trade results to a portfolio log.

Environment variables:
- TIINGO_TOKEN  (required)
- SYMBOLS       (optional, comma-separated tickers, default: SPY)
"""

import os
import csv
import json
import math
import pathlib
import datetime
from typing import List, Dict, Any, Tuple

import urllib.request


# -------------------- CONFIG --------------------

DATA_DIR = pathlib.Path("data")              # price histories
REPORT_DIR = pathlib.Path("reports")         # trade logs / summaries

# Default analysis settings (you can override per symbol if you want)
DEFAULT_PIVOT_HIGH = 687.39
DEFAULT_SWING_LOW = 667.80
DEFAULT_PIVOT_DATE = "2025-10-29"           # ISO string
DEFAULT_ANGLES = [45, 90, 135, 180, 225, 270, 315, 360]
DEFAULT_FIBS = [0.382, 0.618, 1.618, 2.618]
DEFAULT_CYCLES = [30, 45, 60, 90, 120, 144, 180, 240, 360]
DEFAULT_BAND_PCT = 0.005                    # 0.5%
HOLD_DAYS = 5
STOP_PCT = 0.01                             # 1%
TARGET_PCT = 0.02                           # 2%
DEFAULT_START_DATE = "2020-01-01"


# -------------------- IO HELPERS --------------------

def load_csv(path: pathlib.Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Cast numeric columns
    for r in rows:
        r["Open"] = float(r["Open"])
        r["High"] = float(r["High"])
        r["Low"] = float(r["Low"])
        r["Close"] = float(r["Close"])
        r["Volume"] = float(r.get("Volume", 0))
    rows.sort(key=lambda x: x["Date"])
    return rows


def save_csv(path: pathlib.Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Date", "Open", "High", "Low", "Close", "Volume"],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "Date": r["Date"],
                    "Open": r["Open"],
                    "High": r["High"],
                    "Low": r["Low"],
                    "Close": r["Close"],
                    "Volume": r["Volume"],
                }
            )


def append_portfolio_log(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / "portfolio_trades.csv"
    exists = path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Symbol",
                "EntryDate",
                "Direction",
                "Entry",
                "Stop",
                "Target",
                "Exit",
                "ExitDate",
                "ExitReason",
                "PnL",
            ],
        )
        if not exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)


# -------------------- DATA FETCH (TIINGO) --------------------

def tiingo_prices(symbol: str, start_date: str, token: str) -> List[Dict[str, Any]]:
    url = (
        f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
        f"?startDate={start_date}&token={token}"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
    out: List[Dict[str, Any]] = []
    for b in data:
        d = b["date"][:10]
        out.append(
            {
                "Date": d,
                "Open": float(b["open"]),
                "High": float(b["high"]),
                "Low": float(b["low"]),
                "Close": float(b["close"]),
                "Volume": float(b.get("volume", 0)),
            }
        )
    return out


def merge_bars(old: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_date = {r["Date"]: r for r in old}
    for r in new:
        by_date[r["Date"]] = r
    rows = list(by_date.values())
    rows.sort(key=lambda x: x["Date"])
    return rows


def next_start_date(history: List[Dict[str, Any]]) -> str:
    if not history:
        return DEFAULT_START_DATE
    last = history[-1]["Date"]
    dt = datetime.date.fromisoformat(last) + datetime.timedelta(days=1)
    return dt.isoformat()


# -------------------- CONFLUENCE ENGINE --------------------

def square_of_nine_levels(seed_price: float, angles: List[float]) -> List[Tuple[float, float]]:
    root = math.sqrt(seed_price)
    out = []
    for a in angles:
        lvl = (root + a / 180.0) ** 2
        out.append((a, round(lvl, 4)))
    return out


def fib_levels(swing_high: float, swing_low: float, ratios: List[float]) -> List[Tuple[str, float, float]]:
    rng = swing_high - swing_low
    out = []
    for r in ratios:
        retr = swing_high - rng * r
        ext = swing_high + rng * r
        out.append(("Retracement", r, round(retr, 4)))
        out.append(("Extension", r, round(ext, 4)))
    return out


def time_cycles_from_pivot(pivot_date: str, days_list: List[int], window: int = 3) -> List[Dict[str, Any]]:
    p = datetime.date.fromisoformat(pivot_date)
    rows = []
    for d in days_list:
        proj = p + datetime.timedelta(days=d)
        start = proj - datetime.timedelta(days=window)
        end = proj + datetime.timedelta(days=window)
        expected = "Call" if d % 90 == 0 else "Put"
        rows.append(
            {
                "pivot": p.isoformat(),
                "days": d,
                "projected": proj.isoformat(),
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
                "expected": expected,
            }
        )
    return rows


def in_band(price: float, level: float, pct_band: float) -> bool:
    return abs(price - level) <= level * pct_band


def build_confluence_levels(
    so9: List[Tuple[float, float]],
    fibs: List[Tuple[str, float, float]],
    pct_band: float,
) -> List[float]:
    so = [x[1] for x in so9]
    fb = [x[2] for x in fibs]
    confl: List[float] = []
    for s in so:
        for f in fb:
            if abs(s - f) <= max(pct_band, 0.003) * f:
                mid = round((s + f) / 2.0, 4)
                if mid not in confl:
                    confl.append(mid)
    confl.sort()
    return confl


def within_cycle_window(date_str: str, cycle: Dict[str, Any]) -> bool:
    d = datetime.date.fromisoformat(date_str)
    s = datetime.date.fromisoformat(cycle["window_start"])
    e = datetime.date.fromisoformat(cycle["window_end"])
    return s <= d <= e


# -------------------- SIGNALS + BACKTEST --------------------

def generate_signals(
    history: List[Dict[str, Any]],
    confluence_levels: List[float],
    cycles: List[Dict[str, Any]],
    pct_band: float,
) -> List[Dict[str, Any]]:
    """
    For each bar: if price is near a confluence level and date inside any cycle window,
    create a signal with direction from that cycle.
    """
    signals: List[Dict[str, Any]] = []
    for bar in history:
        d = bar["Date"]
        close = bar["Close"]

        # price confluence
        confl_hit = None
        for lvl in confluence_levels:
            if in_band(close, lvl, pct_band):
                confl_hit = lvl
                break

        # time cycle confluence
        in_cycle = False
        direction = None
        for c in cycles:
            if within_cycle_window(d, c):
                in_cycle = True
                direction = c["expected"]
                break

        if confl_hit and in_cycle:
            signals.append(
                {
                    "Date": d,
                    "Close": close,
                    "ConfluenceLevel": confl_hit,
                    "Direction": direction,
                }
            )
    return signals


def simulate_trades(
    symbol: str,
    history: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
    hold_days: int,
    sl_pct: float,
    tp_pct: float,
) -> List[Dict[str, Any]]:
    """
    Delta-1 proxy backtest. Entry at close on signal day.
    """
    trades: List[Dict[str, Any]] = []
    date_to_idx = {bar["Date"]: i for i, bar in enumerate(history)}

    for sig in signals:
        d = sig["Date"]
        direction = sig["Direction"]
        idx = date_to_idx.get(d)
        if idx is None:
            continue

        entry_bar = history[idx]
        entry = entry_bar["Close"]
        stop = entry * (1 - sl_pct) if direction == "Call" else entry * (1 + sl_pct)
        target = entry * (1 + tp_pct) if direction == "Call" else entry * (1 - tp_pct)

        exit_price = entry
        exit_date = d
        reason = "time"

        horizon = history[idx + 1 : idx + 1 + hold_days]
        for bar in horizon:
            high = bar["High"]
            low = bar["Low"]
            date = bar["Date"]

            if direction == "Call":
                if low <= stop:
                    exit_price = stop
                    exit_date = date
                    reason = "stop"
                    break
                if high >= target:
                    exit_price = target
                    exit_date = date
                    reason = "tp"
                    break
            else:
                if high >= stop:
                    exit_price = stop
                    exit_date = date
                    reason = "stop"
                    break
                if low <= target:
                    exit_price = target
                    exit_date = date
                    reason = "tp"
                    break

            exit_price = bar["Close"]
            exit_date = date

        pnl = (exit_price - entry) if direction == "Call" else (entry - exit_price)
        trades.append(
            {
                "Symbol": symbol,
                "EntryDate": d,
                "Direction": direction,
                "Entry": round(entry, 4),
                "Stop": round(stop, 4),
                "Target": round(target, 4),
                "Exit": round(exit_price, 4),
                "ExitDate": exit_date,
                "ExitReason": reason,
                "PnL": round(pnl, 4),
            }
        )

    return trades


# -------------------- AGENT ORCHESTRATION --------------------

def run_for_symbol(
    symbol: str,
    token: str,
    pivot_high: float = DEFAULT_PIVOT_HIGH,
    swing_low: float = DEFAULT_SWING_LOW,
    pivot_date: str = DEFAULT_PIVOT_DATE,
    angles: List[float] = None,
    fibs: List[float] = None,
    cycles_days: List[int] = None,
    band_pct: float = DEFAULT_BAND_PCT,
) -> List[Dict[str, Any]]:
    """
    Full pipeline for a single symbol:
      - Fetch and update history.
      - Compute levels, cycles, signals.
      - Simulate trades.
      - Return trades for logging.
    """
    if angles is None:
        angles = DEFAULT_ANGLES
    if fibs is None:
        fibs = DEFAULT_FIBS
    if cycles_days is None:
        cycles_days = DEFAULT_CYCLES

    symbol = symbol.upper()
    price_path = DATA_DIR / f"{symbol}.csv"

    # 1) Load existing history
    history = load_csv(price_path)
    start_date = next_start_date(history)

    # 2) Fetch new bars
    new_bars = tiingo_prices(symbol, start_date, token)
    if new_bars:
        history = merge_bars(history, new_bars)
        save_csv(price_path, history)
        print(f"[{symbol}] +{len(new_bars)} new bars, total {len(history)}")
    else:
        print(f"[{symbol}] no new bars (history size {len(history)})")

    if len(history) < 30:
        print(f"[{symbol}] not enough data for analysis")
        return []

    # 3) Confluence setup
    so9 = square_of_nine_levels(pivot_high, angles)
    fib = fib_levels(pivot_high, swing_low, fibs)
    cycles = time_cycles_from_pivot(pivot_date, cycles_days, window=3)
    confl = build_confluence_levels(so9, fib, band_pct)

    # 4) Signals
    signals = generate_signals(history, confl, cycles, band_pct)
    print(f"[{symbol}] signals generated: {len(signals)}")

    # 5) Trades
    trades = simulate_trades(symbol, history, signals, HOLD_DAYS, STOP_PCT, TARGET_PCT)
    print(f"[{symbol}] trades simulated: {len(trades)}")

    return trades


def main() -> None:
    token = os.environ.get("TIINGO_TOKEN")
    if not token:
        raise SystemExit("TIINGO_TOKEN environment variable is required")

    symbols_env = os.environ.get("SYMBOLS", "SPY")
    symbols = [s.strip() for s in symbols_env.split(",") if s.strip()]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    all_trades: List[Dict[str, Any]] = []
    for sym in symbols:
        try:
            trades = run_for_symbol(sym, token)
            all_trades.extend(trades)
        except Exception as e:
            print(f"[{sym}] ERROR: {e}")

    append_portfolio_log(all_trades)

    # summary
    if all_trades:
        total = len(all_trades)
        wins = sum(1 for t in all_trades if t["PnL"] > 0)
        losses = total - wins
        pnl = sum(t["PnL"] for t in all_trades)
        win_rate = wins / total * 100
        print(f"Portfolio: {total} trades, {wins} wins, {losses} losses, "
              f"win rate {win_rate:.1f}%, PnL {pnl:.2f}")
    else:
        print("No trades generated for this run.")


if __name__ == "__main__":
    main()


