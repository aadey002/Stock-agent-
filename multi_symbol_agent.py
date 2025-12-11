#!/usr/bin/env python3
"""
Multi-Symbol Confluence Agent
Generates trading signals for all 12 ETFs in the portfolio.
"""

import csv
import math
from datetime import date, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import os

# All ETFs to analyze
SYMBOLS = ["SPY", "QQQ", "IWM", "XLE", "XLF", "XLK", "XLV", "XLI", "XLB", "XLU", "XLP", "XLY"]

# Agent parameters
ATR_LENGTH = 14
FAST_SMA_LEN = 10
SLOW_SMA_LEN = 30
HOLD_DAYS = 5
ENTRY_BAND_ATR = 0.5
STOP_ATR = 1.5
PRICE_TOL_PCT = 0.0075


@dataclass
class Bar:
    d: date
    o: float
    h: float
    l: float
    c: float
    v: float = 0.0
    atr: float = float('nan')
    fast_sma: float = float('nan')
    slow_sma: float = float('nan')
    bias: str = ""
    geo_level: float = float('nan')
    phi_level: float = float('nan')
    price_confluence: bool = False
    time_confluence: bool = False

    @property
    def close(self):
        return self.c

    @property
    def high(self):
        return self.h

    @property
    def low(self):
        return self.l


def log(msg: str):
    print(f"[MultiSymbolAgent] {msg}")


def compute_atr(bars: List[Bar], length: int = 14):
    """Compute ATR for all bars."""
    for i, b in enumerate(bars):
        if i < length:
            b.atr = float('nan')
            continue
        tr_sum = 0.0
        for j in range(i - length + 1, i + 1):
            prev = bars[j - 1] if j > 0 else bars[j]
            tr = max(
                bars[j].h - bars[j].l,
                abs(bars[j].h - prev.c),
                abs(bars[j].l - prev.c)
            )
            tr_sum += tr
        b.atr = tr_sum / length


def compute_sma(bars: List[Bar], length: int) -> List[float]:
    """Compute SMA."""
    result = []
    for i in range(len(bars)):
        if i < length - 1:
            result.append(float('nan'))
        else:
            avg = sum(b.c for b in bars[i - length + 1:i + 1]) / length
            result.append(avg)
    return result


def compute_bias(bars: List[Bar]):
    """Determine CALL/PUT bias based on SMA crossover."""
    for b in bars:
        if math.isnan(b.fast_sma) or math.isnan(b.slow_sma):
            b.bias = ""
        elif b.fast_sma > b.slow_sma:
            b.bias = "CALL"
        else:
            b.bias = "PUT"


def compute_geo_phi_levels(bars: List[Bar]):
    """Compute geometric and phi levels."""
    PHI = 1.618033988749895
    for b in bars:
        sqrt_price = math.sqrt(b.c)
        b.geo_level = (sqrt_price + 2) ** 2
        b.phi_level = b.c * PHI


def tag_confluence(bars: List[Bar], price_tol: float = 0.0075):
    """Tag bars with price and time confluence."""
    for i, b in enumerate(bars):
        # Price confluence: close near geo or phi level
        if not math.isnan(b.geo_level):
            geo_dist = abs(b.c - b.geo_level) / b.c
            phi_dist = abs(b.c - b.phi_level) / b.c
            b.price_confluence = geo_dist < price_tol or phi_dist < price_tol

        # Time confluence: simplified - every 30 bars or at key dates
        b.time_confluence = (i % 30 == 0) or (i > 0 and i % 7 == 0)


def load_bars(symbol: str) -> List[Bar]:
    """Load bars from CSV for a symbol."""
    bars = []
    paths_to_try = [
        f"data/{symbol}.csv",
        f"{symbol}.csv",
        f"reports/{symbol}.csv"
    ]

    filepath = None
    for p in paths_to_try:
        if os.path.exists(p):
            filepath = p
            break

    if not filepath:
        log(f"No data file found for {symbol}")
        return []

    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    bar = Bar(
                        d=date.fromisoformat(row['Date']),
                        o=float(row['Open']),
                        h=float(row['High']),
                        l=float(row['Low']),
                        c=float(row['Close']),
                        v=float(row.get('Volume', 0))
                    )
                    bars.append(bar)
                except (ValueError, KeyError) as e:
                    continue
    except Exception as e:
        log(f"Error loading {symbol}: {e}")

    return bars


def generate_trades_for_symbol(symbol: str) -> List[Dict]:
    """Generate confluence trades for a single symbol."""
    bars = load_bars(symbol)
    if not bars:
        return []

    # Compute indicators
    compute_atr(bars, ATR_LENGTH)
    fast = compute_sma(bars, FAST_SMA_LEN)
    slow = compute_sma(bars, SLOW_SMA_LEN)
    for b, f, s in zip(bars, fast, slow):
        b.fast_sma = f
        b.slow_sma = s
    compute_bias(bars)
    compute_geo_phi_levels(bars)
    tag_confluence(bars, PRICE_TOL_PCT)

    trades = []

    for i, b in enumerate(bars):
        if (
            b.bias in ("CALL", "PUT")
            and b.price_confluence
            and b.time_confluence
            and not math.isnan(b.atr)
        ):
            entry_mid = b.close
            entry_low = entry_mid - ENTRY_BAND_ATR * b.atr
            entry_high = entry_mid + ENTRY_BAND_ATR * b.atr

            if b.bias == "CALL":
                stop = b.low - STOP_ATR * b.atr
                risk = entry_mid - stop
                direction = 1
            else:
                stop = b.high + STOP_ATR * b.atr
                risk = stop - entry_mid
                direction = -1

            if risk <= 0:
                continue

            target1 = entry_mid + direction * 2 * risk
            target2 = entry_mid + direction * 3 * risk

            exit_idx = min(i + HOLD_DAYS, len(bars) - 1)
            exit_bar = bars[exit_idx]
            exit_price = exit_bar.close
            pnl = (exit_price - entry_mid) * direction

            # Determine status
            today = date.today()
            if exit_bar.d >= today:
                status = "ACTIVE"
            elif pnl > 0:
                status = "WIN"
            else:
                status = "LOSS"

            trade = {
                "Symbol": symbol,
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
                "ExpiryDate": (b.d + timedelta(days=HOLD_DAYS)).isoformat(),
                "Status": status,
            }
            trades.append(trade)

    return trades


def generate_current_signals() -> List[Dict]:
    """Generate current trading signals for all symbols."""
    signals = []

    for symbol in SYMBOLS:
        bars = load_bars(symbol)
        if not bars or len(bars) < SLOW_SMA_LEN + 1:
            continue

        # Compute indicators
        compute_atr(bars, ATR_LENGTH)
        fast = compute_sma(bars, FAST_SMA_LEN)
        slow = compute_sma(bars, SLOW_SMA_LEN)
        for b, f, s in zip(bars, fast, slow):
            b.fast_sma = f
            b.slow_sma = s
        compute_bias(bars)
        compute_geo_phi_levels(bars)
        tag_confluence(bars, PRICE_TOL_PCT)

        # Get latest bar
        latest = bars[-1]

        if math.isnan(latest.atr) or not latest.bias:
            continue

        entry = latest.close
        atr = latest.atr

        if latest.bias == "CALL":
            stop = latest.low - STOP_ATR * atr
            risk = entry - stop
            direction = 1
        else:
            stop = latest.high + STOP_ATR * atr
            risk = stop - entry
            direction = -1

        if risk <= 0:
            continue

        target1 = entry + direction * 2 * risk
        target2 = entry + direction * 3 * risk

        # Calculate confidence based on confluence factors
        confidence = 50  # Base
        if latest.price_confluence:
            confidence += 15
        if latest.time_confluence:
            confidence += 10
        if latest.fast_sma > latest.slow_sma and latest.bias == "CALL":
            confidence += 10
        elif latest.fast_sma < latest.slow_sma and latest.bias == "PUT":
            confidence += 10

        # Calculate strike price (round to nearest $1 for ETFs, $5 for larger)
        if entry > 100:
            strike = round(entry / 5) * 5
        else:
            strike = round(entry)

        signal = {
            "Symbol": symbol,
            "Signal": latest.bias,
            "Confidence": min(confidence, 95),
            "Entry": round(entry, 2),
            "EntryLow": round(entry - ENTRY_BAND_ATR * atr, 2),
            "EntryHigh": round(entry + ENTRY_BAND_ATR * atr, 2),
            "Stop": round(stop, 2),
            "Target1": round(target1, 2),
            "Target2": round(target2, 2),
            "Strike": f"${strike} {latest.bias}",
            "ATR": round(atr, 2),
            "Date": latest.d.isoformat(),
            "PriceConfluence": latest.price_confluence,
            "TimeConfluence": latest.time_confluence,
        }
        signals.append(signal)

    return signals


def run_all_and_save():
    """Run agent for all symbols and save to CSV."""
    all_trades = []

    log("Starting multi-symbol confluence analysis...")

    for symbol in SYMBOLS:
        trades = generate_trades_for_symbol(symbol)
        all_trades.extend(trades)
        log(f"{symbol}: {len(trades)} trades")

    # Save to portfolio_confluence.csv
    if all_trades:
        output_path = "reports/portfolio_confluence.csv"
        os.makedirs("reports", exist_ok=True)

        fieldnames = [
            "Symbol", "Signal", "EntryDate", "ExitDate", "EntryPrice",
            "ExitPrice", "PNL", "EntryLow", "EntryHigh", "Stop",
            "Target1", "Target2", "ExpiryDate", "Status"
        ]

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_trades)

        log(f"Saved {len(all_trades)} trades to {output_path}")

    # Generate and save current signals
    signals = generate_current_signals()
    if signals:
        signals_path = "reports/current_signals.csv"

        fieldnames = [
            "Symbol", "Signal", "Confidence", "Entry", "EntryLow", "EntryHigh",
            "Stop", "Target1", "Target2", "Strike", "ATR", "Date",
            "PriceConfluence", "TimeConfluence"
        ]

        with open(signals_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(signals)

        log(f"Saved {len(signals)} current signals to {signals_path}")

    return all_trades, signals


def print_signal_summary(signals: List[Dict]):
    """Print a formatted summary of current signals."""
    print("\n" + "=" * 80)
    print("CURRENT SIGNALS FOR ALL ETFs")
    print("=" * 80)

    call_signals = [s for s in signals if s["Signal"] == "CALL"]
    put_signals = [s for s in signals if s["Signal"] == "PUT"]

    print(f"\nCALL Signals ({len(call_signals)}):")
    print("-" * 40)
    for s in call_signals:
        print(f"  {s['Symbol']:4} | Entry: ${s['Entry']:.2f} | Stop: ${s['Stop']:.2f} | "
              f"T1: ${s['Target1']:.2f} | Conf: {s['Confidence']}%")

    print(f"\nPUT Signals ({len(put_signals)}):")
    print("-" * 40)
    for s in put_signals:
        print(f"  {s['Symbol']:4} | Entry: ${s['Entry']:.2f} | Stop: ${s['Stop']:.2f} | "
              f"T1: ${s['Target1']:.2f} | Conf: {s['Confidence']}%")

    print("\n" + "=" * 80)
    print(f"Total: {len(signals)} signals | CALL: {len(call_signals)} | PUT: {len(put_signals)}")
    print("=" * 80)


if __name__ == "__main__":
    trades, signals = run_all_and_save()

    print("\n" + "=" * 80)
    print("CURRENT SIGNALS FOR ALL ETFs")
    print("=" * 80)

    for s in signals:
        emoji = "\U0001F7E2" if s["Signal"] == "CALL" else "\U0001F534"
        print(f"{emoji} {s['Symbol']:4} | {s['Signal']:4} | Conf: {s['Confidence']}% | "
              f"Entry: ${s['Entry']:.2f} | Stop: ${s['Stop']:.2f} | T1: ${s['Target1']:.2f}")

    print("\n" + "=" * 80)
    print(f"Total trades generated: {len(trades)}")
    print(f"Active signals: {len(signals)}")

    # Calculate win rate from historical trades
    wins = len([t for t in trades if t["Status"] == "WIN"])
    losses = len([t for t in trades if t["Status"] == "LOSS"])
    if wins + losses > 0:
        win_rate = wins / (wins + losses) * 100
        print(f"Historical win rate: {win_rate:.1f}% ({wins}W/{losses}L)")
    print("=" * 80)
