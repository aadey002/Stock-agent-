#!/usr/bin/env python3
"""
Emit a plain-text alert for the latest SPY confluence playbook.

Logic:
- Read reports/portfolio_confluence.csv (latest playbook row).
- If the time window is ACTIVE or UPCOMING (based on today's date),
  print a concise alert to stdout.
- If the window is already past, print nothing (no alert).

This is research-only and does NOT place any trades.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Optional

REPORT_PATH = Path("reports/portfolio_confluence.csv")


def parse_date(value: str) -> Optional[date]:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def to_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_latest_playbook() -> Optional[dict]:
    if not REPORT_PATH.exists():
        return None

    with REPORT_PATH.open("r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return None

    # If there is more than one row, treat the last as the most recent
    rows.sort(key=lambda r: r.get("EntryDate", ""))
    return rows[-1]


def main() -> None:
    today = date.today()
    row = load_latest_playbook()
    if not row:
        return

    entry_d = parse_date(row.get("EntryDate", ""))
    exit_d = parse_date(row.get("ExitDate", ""))

    # If we can't parse dates, don't emit anything
    if not entry_d or not exit_d:
        return

    # Only alert if the window is ACTIVE or UPCOMING
    if exit_d < today:
        # Time window is already over – no fresh opportunity
        return

    if entry_d <= today <= exit_d:
        window_status = "ACTIVE"
        window_line = (
            f"Window status: ACTIVE (today {today} is between "
            f"{entry_d} and {exit_d})."
        )
    else:
        window_status = "UPCOMING"
        window_line = (
            f"Window status: UPCOMING (entry {entry_d}, exit {exit_d})."
        )

    symbol = row.get("Symbol", "SPY").strip() or "SPY"
    side = row.get("Signal", "").strip().upper()
    if side == "CALL":
        side_word = "bullish CALL"
    elif side == "PUT":
        side_word = "bearish PUT"
    else:
        side_word = side or "directional"

    entry_low = to_float(row.get("EntryLow", ""))
    entry_high = to_float(row.get("EntryHigh", ""))
    stop = to_float(row.get("Stop", ""))
    t1 = to_float(row.get("Target1", ""))
    t2 = to_float(row.get("Target2", ""))

    band_line = (
        f"Entry band: {entry_low:.2f} – {entry_high:.2f}"
        if entry_low is not None and entry_high is not None
        else "Entry band: (not available)"
    )
    stop_line = (
        f"Guard-rail stop: {stop:.2f}"
        if stop is not None
        else "Guard-rail stop: (not available)"
    )
    tgt_line = (
        f"Targets: T1 {t1:.2f}, T2 {t2:.2f}"
        if t1 is not None and t2 is not None
        else "Targets: (not available)"
    )

    print(f"{symbol} confluence opportunity – {side_word} ({window_status})")
    print(window_line)
    print(band_line)
    print(stop_line)
    print(tgt_line)
    print(f"Time stop: flatten no later than {exit_d} at the close.")
    print()
    print(
        "Checklist (research-only): "
        "1) Only engage near the entry band, 2) respect the guard-rail stop, "
        "3) scale out around T1/T2, 4) exit by the time stop if nothing else hits."
    )
    print()
    print(
        "This alert is generated from historical/confluence logic and is "
        "for backtesting and research only. It is not trading advice."
    )


if __name__ == "__main__":
    main()
