#!/usr/bin/env python3
"""
Q5D Unified Multi-Agent Trading System
======================================
Stock Agent 4 - Complete Multi-Symbol Analysis

This script:
1. Fetches daily OHLCV from Yahoo Finance for all configured symbols
2. Runs 4 trading agents on each symbol:
   - Base Confluence Agent (SMA crossover + geometric levels)
   - Gann-Elliott Agent (Square of 9 + Wave patterns)
   - DQN Agent (Momentum + RSI signals)
   - 3-Wave Agent (Fibonacci retracements)
3. Generates consensus voting (ULTRA 4/4, SUPER 3/4, PARTIAL 2/4)
4. Outputs all required CSV files for dashboard

Output Files:
- data/{SYMBOL}.csv               - OHLCV with indicators
- reports/portfolio_confluence.csv - Base playbook trades
- reports/playbook_comparison.csv  - All 4 agents comparison
- reports/ultra_confluence_4of4.csv - 4/4 consensus signals
- reports/super_confluence_signals.csv - 3/4+ signals
- reports/sector_rotation.csv      - Sector performance
- reports/market_conditions.json   - Guard rail data

Author: Dr. Tee / Q5D Options Platform
Version: 4.0
"""

import csv
import json
import logging
import math
import os
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

# Try yfinance, fallback to sample data
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("[WARN] yfinance not installed. Using sample data.")

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("[WARN] pandas/numpy not installed.")

# =========================================================================
# CONFIGURATION
# =========================================================================

# Symbols to process
SYMBOLS = [
    "SPY",   # S&P 500
    "QQQ",   # NASDAQ 100
    "IWM",   # Russell 2000
    "XLE",   # Energy
    "XLF",   # Financials
    "XLK",   # Technology
    "XLV",   # Healthcare
    "XLI",   # Industrials
    "XLB",   # Materials
    "XLU",   # Utilities
    "XLP",   # Consumer Staples
    "XLY",   # Consumer Discretionary
]

SYMBOL_NAMES = {
    "SPY": "S&P 500",
    "QQQ": "NASDAQ 100",
    "IWM": "Russell 2000",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLK": "Technology",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary",
}

CYCLICAL_SECTORS = ["XLK", "XLF", "XLY", "XLI", "XLB"]
DEFENSIVE_SECTORS = ["XLV", "XLP", "XLU"]

# Paths
DATA_DIR = pathlib.Path("data")
REPORT_DIR = pathlib.Path("reports")
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Trading parameters
START_DATE = "2022-01-01"
ATR_LENGTH = 14
FAST_SMA_LEN = 10
SLOW_SMA_LEN = 20
RSI_LENGTH = 14
PRICE_TOL_PCT = 0.008
ENTRY_BAND_ATR = 0.5
STOP_ATR = 1.5
HOLD_DAYS = 5

# Gann cycles (trading days)
GANN_CYCLES = [11, 22, 34, 45, 56, 67, 78, 90]

# =========================================================================
# LOGGING SETUP
# =========================================================================

def setup_logging():
    """Setup logging configuration."""
    log_dir = pathlib.Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_dir / "unified_agent.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("unified_agent")

logger = setup_logging()

# =========================================================================
# DATA STRUCTURES
# =========================================================================

@dataclass
class Bar:
    """Daily OHLCV bar with indicators."""
    date: str
    open_: float
    high: float
    low: float
    close: float
    volume: float
    atr: Optional[float] = None
    fast_sma: Optional[float] = None
    slow_sma: Optional[float] = None
    rsi: Optional[float] = None
    bias: Optional[str] = None
    geo_level: Optional[float] = None
    phi_level: Optional[float] = None
    price_confluence: int = 0
    time_confluence: int = 0
    gann_support: Optional[float] = None
    gann_resistance: Optional[float] = None
    wave_position: Optional[str] = None

@dataclass
class AgentSignal:
    """Signal from a single agent."""
    agent_name: str
    signal: str  # CALL, PUT, HOLD
    confidence: float
    entry: float
    stop: float
    target1: float
    target2: float
    reasons: List[str] = field(default_factory=list)

@dataclass
class ConsensusResult:
    """Result of multi-agent consensus voting."""
    date: str
    symbol: str
    signals: List[AgentSignal]
    call_votes: int
    put_votes: int
    hold_votes: int
    consensus: str  # CALL, PUT, HOLD
    confluence_level: str  # ULTRA, SUPER, PARTIAL, NONE
    confidence: float
    entry: float
    stop: float
    target1: float
    target2: float
    target3: float
    approved: bool

# =========================================================================
# DATA FETCHING
# =========================================================================

def fetch_yahoo_data(symbol: str, start_date: str) -> List[Bar]:
    """Fetch daily OHLCV from Yahoo Finance."""
    if not HAS_YFINANCE:
        logger.warning(f"yfinance not available, using sample data for {symbol}")
        return generate_sample_data(symbol)
    
    try:
        logger.info(f"Fetching {symbol} from Yahoo Finance...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, interval="1d")
        
        if df.empty:
            logger.warning(f"No data returned for {symbol}")
            return generate_sample_data(symbol)
        
        bars = []
        for idx, row in df.iterrows():
            bar = Bar(
                date=idx.strftime('%Y-%m-%d'),
                open_=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=float(row['Volume']),
            )
            bars.append(bar)
        
        logger.info(f"Fetched {len(bars)} bars for {symbol}")
        return bars
        
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return generate_sample_data(symbol)

def generate_sample_data(symbol: str) -> List[Bar]:
    """Generate sample data when API unavailable."""
    logger.info(f"Generating sample data for {symbol}")
    bars = []
    base_price = {"SPY": 600, "QQQ": 500, "IWM": 230, "XLE": 90}.get(symbol, 100)
    
    start = datetime(2022, 1, 3)
    for i in range(700):
        date = start + timedelta(days=i)
        if date.weekday() >= 5:  # Skip weekends
            continue
        
        noise = (hash(f"{symbol}{i}") % 100 - 50) / 100
        price = base_price * (1 + 0.0015 * i + 0.02 * noise)
        
        bar = Bar(
            date=date.strftime('%Y-%m-%d'),
            open_=price * 0.999,
            high=price * 1.01,
            low=price * 0.99,
            close=price,
            volume=50000000 + hash(f"{symbol}{i}") % 10000000,
        )
        bars.append(bar)
    
    return bars

# =========================================================================
# INDICATOR CALCULATIONS
# =========================================================================

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
    for i in range(len(bars)):
        if i < length - 1:
            smas.append(None)
        else:
            avg = sum(bars[j].close for j in range(i - length + 1, i + 1)) / length
            smas.append(avg)
    return smas

def compute_rsi(bars: List[Bar], length: int = 14) -> None:
    """Compute Relative Strength Index."""
    for i, bar in enumerate(bars):
        if i < length:
            bar.rsi = 50  # Default
            continue
        
        gains = []
        losses = []
        for j in range(i - length + 1, i + 1):
            change = bars[j].close - bars[j-1].close if j > 0 else 0
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / length
        avg_loss = sum(losses) / length
        
        if avg_loss == 0:
            bar.rsi = 100
        else:
            rs = avg_gain / avg_loss
            bar.rsi = 100 - (100 / (1 + rs))

def compute_bias(bars: List[Bar]) -> None:
    """Compute bias (CALL if fast > slow, PUT otherwise)."""
    for bar in bars:
        if bar.fast_sma is not None and bar.slow_sma is not None:
            bar.bias = "CALL" if bar.fast_sma > bar.slow_sma else "PUT"

def compute_gann_levels(bars: List[Bar]) -> None:
    """Compute Gann Square of 9 support/resistance levels."""
    for bar in bars:
        price = bar.close
        sqrt_price = math.sqrt(price)
        
        # Calculate nearest support/resistance from Square of 9
        res_levels = []
        sup_levels = []
        for k in range(1, 6):
            deg = k * 45
            inc = deg / 180.0
            res_levels.append((sqrt_price + inc) ** 2)
            if sqrt_price > inc:
                sup_levels.append((sqrt_price - inc) ** 2)
        
        bar.gann_support = min(sup_levels, key=lambda x: abs(x - price)) if sup_levels else price * 0.95
        bar.gann_resistance = min(res_levels, key=lambda x: abs(x - price)) if res_levels else price * 1.05

def compute_geometric_levels(bars: List[Bar]) -> None:
    """Compute geometric/Fibonacci levels."""
    for i, bar in enumerate(bars):
        if i > 20:
            recent_high = max(bars[j].high for j in range(max(0, i-20), i))
            recent_low = min(bars[j].low for j in range(max(0, i-20), i))
            bar.geo_level = (recent_high + recent_low) / 2
            bar.phi_level = recent_low + (recent_high - recent_low) * 0.618
        else:
            bar.geo_level = bar.close
            bar.phi_level = bar.close * 0.618

def compute_wave_position(bars: List[Bar]) -> None:
    """Detect Elliott Wave position (simplified)."""
    for i, bar in enumerate(bars):
        if i < 50:
            bar.wave_position = "Unknown"
            continue
        
        # Simple wave detection based on recent highs/lows
        recent_bars = bars[max(0, i-50):i+1]
        highs = [b.high for b in recent_bars]
        lows = [b.low for b in recent_bars]
        
        max_idx = highs.index(max(highs))
        min_idx = lows.index(min(lows))
        
        if max_idx > min_idx:
            if max_idx > len(recent_bars) * 0.8:
                bar.wave_position = "Wave 5 UP"
            elif max_idx > len(recent_bars) * 0.5:
                bar.wave_position = "Wave 3 UP"
            else:
                bar.wave_position = "Wave 1 UP"
        else:
            if min_idx > len(recent_bars) * 0.8:
                bar.wave_position = "Wave 5 DOWN"
            elif min_idx > len(recent_bars) * 0.5:
                bar.wave_position = "Wave 3 DOWN"
            else:
                bar.wave_position = "Wave 2 DOWN"

def tag_confluence(bars: List[Bar], price_tol: float = 0.008) -> None:
    """Tag bars with price and time confluence."""
    for i, bar in enumerate(bars):
        bar.price_confluence = 0
        bar.time_confluence = 0
        
        if bar.atr is None:
            continue
        
        # Price confluence: near geometric or phi level
        if bar.geo_level:
            if abs(bar.close - bar.geo_level) < bar.atr * 0.5:
                bar.price_confluence = 1
        
        # Time confluence: near Gann cycle
        days_from_start = i
        for cycle in GANN_CYCLES:
            if abs(days_from_start % cycle) <= 2 or abs(days_from_start % cycle - cycle) <= 2:
                bar.time_confluence = 1
                break

def process_indicators(bars: List[Bar]) -> None:
    """Compute all indicators on bars."""
    compute_atr(bars, ATR_LENGTH)
    
    fast = compute_sma(bars, FAST_SMA_LEN)
    slow = compute_sma(bars, SLOW_SMA_LEN)
    for b, f, s in zip(bars, fast, slow):
        b.fast_sma = f
        b.slow_sma = s
    
    compute_rsi(bars, RSI_LENGTH)
    compute_bias(bars)
    compute_gann_levels(bars)
    compute_geometric_levels(bars)
    compute_wave_position(bars)
    tag_confluence(bars)

# =========================================================================
# TRADING AGENTS
# =========================================================================

def base_confluence_agent(bar: Bar) -> AgentSignal:
    """Base Confluence Agent - SMA crossover with geometric levels."""
    signal = "HOLD"
    confidence = 0
    reasons = []
    
    if bar.bias == "CALL" and bar.price_confluence:
        signal = "CALL"
        confidence = 65
        reasons.append("SMA bullish crossover")
        reasons.append("Near geometric level")
    elif bar.bias == "PUT" and bar.price_confluence:
        signal = "PUT"
        confidence = 65
        reasons.append("SMA bearish crossover")
        reasons.append("Near geometric level")
    
    # Calculate entry/stop/targets
    atr = bar.atr or 5
    entry = bar.close
    
    if signal == "CALL":
        stop = entry - atr * 1.5
        target1 = entry + atr * 2
        target2 = entry + atr * 3
    elif signal == "PUT":
        stop = entry + atr * 1.5
        target1 = entry - atr * 2
        target2 = entry - atr * 3
    else:
        stop = entry
        target1 = entry
        target2 = entry
    
    return AgentSignal(
        agent_name="Base Confluence",
        signal=signal,
        confidence=confidence,
        entry=round(entry, 2),
        stop=round(stop, 2),
        target1=round(target1, 2),
        target2=round(target2, 2),
        reasons=reasons
    )

def gann_elliott_agent(bar: Bar) -> AgentSignal:
    """Gann-Elliott Agent - Square of 9 + Wave patterns."""
    signal = "HOLD"
    confidence = 0
    reasons = []
    
    # Check wave position and Gann levels
    if bar.wave_position and "UP" in bar.wave_position:
        if bar.close <= bar.gann_support * 1.01:
            signal = "CALL"
            confidence = 72
            reasons.append(f"{bar.wave_position}")
            reasons.append("Near Gann support")
    elif bar.wave_position and "DOWN" in bar.wave_position:
        if bar.close >= bar.gann_resistance * 0.99:
            signal = "PUT"
            confidence = 72
            reasons.append(f"{bar.wave_position}")
            reasons.append("Near Gann resistance")
    
    # Add time confluence bonus
    if bar.time_confluence:
        confidence += 5
        reasons.append("Gann time cycle")
    
    atr = bar.atr or 5
    entry = bar.close
    
    if signal == "CALL":
        stop = bar.gann_support * 0.99 if bar.gann_support else entry - atr * 1.5
        target1 = bar.gann_resistance if bar.gann_resistance else entry + atr * 2
        target2 = target1 * 1.01
    elif signal == "PUT":
        stop = bar.gann_resistance * 1.01 if bar.gann_resistance else entry + atr * 1.5
        target1 = bar.gann_support if bar.gann_support else entry - atr * 2
        target2 = target1 * 0.99
    else:
        stop = entry
        target1 = entry
        target2 = entry
    
    return AgentSignal(
        agent_name="Gann-Elliott",
        signal=signal,
        confidence=confidence,
        entry=round(entry, 2),
        stop=round(stop, 2),
        target1=round(target1, 2),
        target2=round(target2, 2),
        reasons=reasons
    )

def dqn_momentum_agent(bar: Bar) -> AgentSignal:
    """DQN/Momentum Agent - RSI + momentum signals."""
    signal = "HOLD"
    confidence = 0
    reasons = []
    
    rsi = bar.rsi or 50
    
    # Oversold = CALL opportunity
    if rsi < 30:
        signal = "CALL"
        confidence = 71
        reasons.append(f"RSI oversold ({rsi:.0f})")
    # Overbought = PUT opportunity
    elif rsi > 70:
        signal = "PUT"
        confidence = 71
        reasons.append(f"RSI overbought ({rsi:.0f})")
    # Momentum confirmation
    elif bar.bias == "CALL" and rsi > 50 and rsi < 70:
        signal = "CALL"
        confidence = 60
        reasons.append(f"Bullish momentum (RSI {rsi:.0f})")
    elif bar.bias == "PUT" and rsi < 50 and rsi > 30:
        signal = "PUT"
        confidence = 60
        reasons.append(f"Bearish momentum (RSI {rsi:.0f})")
    
    atr = bar.atr or 5
    entry = bar.close
    
    if signal == "CALL":
        stop = entry - atr * 1.0
        target1 = entry + atr * 1.5
        target2 = entry + atr * 2.5
    elif signal == "PUT":
        stop = entry + atr * 1.0
        target1 = entry - atr * 1.5
        target2 = entry - atr * 2.5
    else:
        stop = entry
        target1 = entry
        target2 = entry
    
    return AgentSignal(
        agent_name="DQN Momentum",
        signal=signal,
        confidence=confidence,
        entry=round(entry, 2),
        stop=round(stop, 2),
        target1=round(target1, 2),
        target2=round(target2, 2),
        reasons=reasons
    )

def three_wave_agent(bar: Bar) -> AgentSignal:
    """3-Wave/Fibonacci Agent - Retracement patterns."""
    signal = "HOLD"
    confidence = 0
    reasons = []
    
    # Check if near phi level (0.618 retracement)
    if bar.phi_level and bar.geo_level:
        price = bar.close
        
        # Near 0.618 retracement from recent range
        if abs(price - bar.phi_level) < (bar.atr or 5) * 0.5:
            if bar.bias == "CALL":
                signal = "CALL"
                confidence = 68
                reasons.append("0.618 Fibonacci support")
                reasons.append("Bullish trend continuation")
            elif bar.bias == "PUT":
                signal = "PUT"
                confidence = 68
                reasons.append("0.618 Fibonacci resistance")
                reasons.append("Bearish trend continuation")
    
    atr = bar.atr or 5
    entry = bar.close
    
    if signal == "CALL":
        stop = entry - atr * 1.2
        target1 = entry + atr * 2
        target2 = entry + atr * 3.5
    elif signal == "PUT":
        stop = entry + atr * 1.2
        target1 = entry - atr * 2
        target2 = entry - atr * 3.5
    else:
        stop = entry
        target1 = entry
        target2 = entry
    
    return AgentSignal(
        agent_name="3-Wave Fibonacci",
        signal=signal,
        confidence=confidence,
        entry=round(entry, 2),
        stop=round(stop, 2),
        target1=round(target1, 2),
        target2=round(target2, 2),
        reasons=reasons
    )

# =========================================================================
# CONSENSUS ENGINE
# =========================================================================

def calculate_consensus(date: str, symbol: str, bar: Bar) -> ConsensusResult:
    """Run all 4 agents and calculate consensus."""
    # Get signals from all agents
    signals = [
        base_confluence_agent(bar),
        gann_elliott_agent(bar),
        dqn_momentum_agent(bar),
        three_wave_agent(bar),
    ]
    
    # Count votes
    call_votes = sum(1 for s in signals if s.signal == "CALL")
    put_votes = sum(1 for s in signals if s.signal == "PUT")
    hold_votes = sum(1 for s in signals if s.signal == "HOLD")
    
    # Determine consensus
    max_votes = max(call_votes, put_votes, hold_votes)
    
    if max_votes >= 4:
        confluence_level = "ULTRA"
    elif max_votes >= 3:
        confluence_level = "SUPER"
    elif max_votes >= 2:
        confluence_level = "PARTIAL"
    else:
        confluence_level = "NONE"
    
    if call_votes > put_votes and call_votes > hold_votes:
        consensus = "CALL"
    elif put_votes > call_votes and put_votes > hold_votes:
        consensus = "PUT"
    else:
        consensus = "HOLD"
    
    # Calculate average confidence
    active_signals = [s for s in signals if s.signal != "HOLD"]
    avg_confidence = sum(s.confidence for s in active_signals) / len(active_signals) if active_signals else 0
    
    # Calculate average entry/stop/targets
    if active_signals:
        entry = sum(s.entry for s in active_signals) / len(active_signals)
        stop = sum(s.stop for s in active_signals) / len(active_signals)
        target1 = sum(s.target1 for s in active_signals) / len(active_signals)
        target2 = sum(s.target2 for s in active_signals) / len(active_signals)
        target3 = target2 * 1.1 if consensus == "CALL" else target2 * 0.9
    else:
        entry = bar.close
        stop = bar.close
        target1 = bar.close
        target2 = bar.close
        target3 = bar.close
    
    # Approval requires 3+ votes
    approved = max_votes >= 3 and consensus != "HOLD"
    
    return ConsensusResult(
        date=date,
        symbol=symbol,
        signals=signals,
        call_votes=call_votes,
        put_votes=put_votes,
        hold_votes=hold_votes,
        consensus=consensus,
        confluence_level=confluence_level,
        confidence=round(avg_confidence, 1),
        entry=round(entry, 2),
        stop=round(stop, 2),
        target1=round(target1, 2),
        target2=round(target2, 2),
        target3=round(target3, 2),
        approved=approved,
    )

# =========================================================================
# CSV OUTPUT
# =========================================================================

def write_symbol_csv(symbol: str, bars: List[Bar]) -> None:
    """Write symbol OHLCV data with indicators."""
    path = DATA_DIR / f"{symbol}.csv"
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
            'ATR', 'FastSMA', 'SlowSMA', 'RSI', 'Bias',
            'GeoLevel', 'PhiLevel', 'PriceConfluence', 'TimeConfluence'
        ])
        writer.writeheader()
        
        for bar in bars:
            writer.writerow({
                'Date': bar.date,
                'Open': round(bar.open_, 2),
                'High': round(bar.high, 2),
                'Low': round(bar.low, 2),
                'Close': round(bar.close, 2),
                'Volume': int(bar.volume),
                'ATR': round(bar.atr, 2) if bar.atr else '',
                'FastSMA': round(bar.fast_sma, 2) if bar.fast_sma else '',
                'SlowSMA': round(bar.slow_sma, 2) if bar.slow_sma else '',
                'RSI': round(bar.rsi, 1) if bar.rsi else '',
                'Bias': bar.bias or '',
                'GeoLevel': round(bar.geo_level, 2) if bar.geo_level else '',
                'PhiLevel': round(bar.phi_level, 2) if bar.phi_level else '',
                'PriceConfluence': bar.price_confluence,
                'TimeConfluence': bar.time_confluence,
            })
    
    logger.info(f"Wrote {len(bars)} bars to {path}")

def write_playbook_comparison(all_results: List[ConsensusResult]) -> None:
    """Write playbook comparison CSV (all 4 agents for each bar)."""
    path = REPORT_DIR / "playbook_comparison.csv"
    
    rows = []
    for result in all_results:
        row = {
            'Date': result.date,
            'Symbol': result.symbol,
            'Signal': result.consensus,
            'Confluence': result.confluence_level,
            'Entry': result.entry,
            'Stop': result.stop,
            'Target': result.target1,
            'Confidence': f"{result.confidence:.0f}%",
            
            # Agent 1: Base Confluence
            'Agent1_Signal': result.signals[0].signal,
            'Agent1_Conf': result.signals[0].confidence,
            
            # Agent 2: Gann-Elliott
            'Agent2_Signal': result.signals[1].signal,
            'Agent2_Conf': result.signals[1].confidence,
            
            # Agent 3: DQN Momentum
            'Agent3_Signal': result.signals[2].signal,
            'Agent3_Conf': result.signals[2].confidence,
            
            # Agent 4: 3-Wave Fibonacci
            'Agent4_Signal': result.signals[3].signal,
            'Agent4_Conf': result.signals[3].confidence,
            
            'CallVotes': result.call_votes,
            'PutVotes': result.put_votes,
            'HoldVotes': result.hold_votes,
            'Approved': result.approved,
        }
        rows.append(row)
    
    with open(path, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    
    logger.info(f"Wrote {len(rows)} rows to {path}")

def write_ultra_confluence(all_results: List[ConsensusResult]) -> None:
    """Write ultra confluence (4/4 consensus) signals."""
    path = REPORT_DIR / "ultra_confluence_4of4.csv"
    
    ultra = [r for r in all_results if r.confluence_level == "ULTRA"]
    
    rows = []
    for result in ultra:
        row = {
            'Date': result.date,
            'Symbol': result.symbol,
            'Signal': result.consensus,
            'Votes': f"{max(result.call_votes, result.put_votes)}C/{4 - max(result.call_votes, result.put_votes)}P/0H",
            'WaveTrend': result.signals[1].reasons[0] if result.signals[1].reasons else '',
            'Confidence': f"{result.confidence:.0f}%",
            'Entry': result.entry,
            'Stop': result.stop,
            'Target1': result.target1,
            'Target2': result.target2,
        }
        rows.append(row)
    
    with open(path, 'w', newline='') as f:
        fieldnames = ['Date', 'Symbol', 'Signal', 'Votes', 'WaveTrend', 'Confidence', 
                      'Entry', 'Stop', 'Target1', 'Target2']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    call_count = sum(1 for r in ultra if r.consensus == "CALL")
    put_count = sum(1 for r in ultra if r.consensus == "PUT")
    logger.info(f"Wrote {len(rows)} ultra signals ({call_count} CALL, {put_count} PUT) to {path}")

def write_super_confluence(all_results: List[ConsensusResult]) -> None:
    """Write super confluence (3/4+) signals."""
    path = REPORT_DIR / "super_confluence_signals.csv"
    
    super_signals = [r for r in all_results if r.confluence_level in ("ULTRA", "SUPER")]
    
    rows = []
    for result in super_signals:
        row = {
            'Date': result.date,
            'Symbol': result.symbol,
            'Signal': result.consensus,
            'Confluence': result.confluence_level,
            'Confidence': result.confidence,
            'Entry': result.entry,
            'Stop': result.stop,
            'Target1': result.target1,
            'Target2': result.target2,
            'Target3': result.target3,
        }
        rows.append(row)
    
    with open(path, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    
    logger.info(f"Wrote {len(rows)} super confluence signals to {path}")

def write_portfolio_confluence(all_results: List[ConsensusResult]) -> None:
    """Write base portfolio confluence trades."""
    path = REPORT_DIR / "portfolio_confluence.csv"
    
    # Only write approved signals
    approved = [r for r in all_results if r.approved][-20:]  # Last 20
    
    rows = []
    for result in approved:
        row = {
            'Symbol': result.symbol,
            'Signal': result.consensus,
            'EntryDate': result.date,
            'ExitDate': '',
            'EntryPrice': result.entry,
            'ExitPrice': '',
            'PNL': '',
            'EntryLow': round(min(result.entry, result.stop), 2),
            'EntryHigh': round(max(result.entry, result.target1), 2),
            'Stop': result.stop,
            'Target1': result.target1,
            'Target2': result.target2,
            'ExpiryDate': '',
            'Status': f"{result.confluence_level} ({result.confidence:.0f}%)",
        }
        rows.append(row)
    
    with open(path, 'w', newline='') as f:
        fieldnames = ['Symbol', 'Signal', 'EntryDate', 'ExitDate', 'EntryPrice', 
                      'ExitPrice', 'PNL', 'EntryLow', 'EntryHigh', 'Stop', 
                      'Target1', 'Target2', 'ExpiryDate', 'Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Wrote {len(rows)} portfolio trades to {path}")

def write_sector_rotation(symbol_data: Dict[str, List[Bar]]) -> None:
    """Write sector rotation analysis."""
    path = REPORT_DIR / "sector_rotation.csv"
    
    rows = []
    for symbol, bars in symbol_data.items():
        if len(bars) < 22:
            continue
        
        current = bars[-1]
        prev_5 = bars[-6] if len(bars) >= 6 else bars[0]
        prev_20 = bars[-21] if len(bars) >= 21 else bars[0]
        
        perf_1w = ((current.close - prev_5.close) / prev_5.close) * 100
        perf_1m = ((current.close - prev_20.close) / prev_20.close) * 100
        
        is_cyclical = symbol in CYCLICAL_SECTORS
        
        row = {
            'Symbol': symbol,
            'Name': SYMBOL_NAMES.get(symbol, symbol),
            'Price': round(current.close, 2),
            'Change1W': round(perf_1w, 2),
            'Change1M': round(perf_1m, 2),
            'RSI': round(current.rsi, 1) if current.rsi else '',
            'Bias': current.bias or '',
            'Type': 'Cyclical' if is_cyclical else 'Defensive',
            'Signal': 'OVERWEIGHT' if perf_1w > 1 else ('UNDERWEIGHT' if perf_1w < -1 else 'NEUTRAL'),
        }
        rows.append(row)
    
    # Sort by 1-week performance
    rows.sort(key=lambda x: x['Change1W'], reverse=True)
    
    with open(path, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    
    logger.info(f"Wrote {len(rows)} sector rotation entries to {path}")

def write_market_conditions(symbol_data: Dict[str, List[Bar]]) -> None:
    """Write market conditions JSON for Guard Rail."""
    path = REPORT_DIR / "market_conditions.json"
    
    spy_bars = symbol_data.get("SPY", [])
    
    if not spy_bars:
        conditions = {
            "generated_at": datetime.now().isoformat(),
            "safe_to_trade": False,
            "message": "No SPY data available"
        }
    else:
        current = spy_bars[-1]
        
        # VIX proxy: use ATR-based volatility
        atr_pct = (current.atr / current.close * 100) if current.atr else 1.5
        vix_estimate = atr_pct * 10  # Rough estimate
        
        # SPY trend
        sma_20 = current.slow_sma or current.close
        trend_distance = ((current.close - sma_20) / sma_20) * 100
        
        if trend_distance > 0:
            spy_trend = "Above 20MA"
            spy_trend_pct = round(trend_distance, 1)
        else:
            spy_trend = "Below 20MA"
            spy_trend_pct = round(trend_distance, 1)
        
        # Sector rotation (cyclical vs defensive)
        cyclical_perfs = []
        defensive_perfs = []
        
        for symbol, bars in symbol_data.items():
            if len(bars) >= 6:
                perf = ((bars[-1].close - bars[-6].close) / bars[-6].close) * 100
                if symbol in CYCLICAL_SECTORS:
                    cyclical_perfs.append(perf)
                elif symbol in DEFENSIVE_SECTORS:
                    defensive_perfs.append(perf)
        
        cyclical_avg = sum(cyclical_perfs) / len(cyclical_perfs) if cyclical_perfs else 0
        defensive_avg = sum(defensive_perfs) / len(defensive_perfs) if defensive_perfs else 0
        
        if cyclical_avg > defensive_avg + 0.5:
            rotation = "Risk-On"
            rotation_desc = "Tech Leading"
        elif defensive_avg > cyclical_avg + 0.5:
            rotation = "Risk-Off"
            rotation_desc = "Defensive Leading"
        else:
            rotation = "Neutral"
            rotation_desc = "Mixed"
        
        # Safe to trade logic
        conditions_met = 0
        if vix_estimate < 20:
            conditions_met += 1
        if trend_distance > 0:
            conditions_met += 1
        if rotation in ("Risk-On", "Neutral"):
            conditions_met += 1
        
        safe_to_trade = conditions_met >= 2
        
        conditions = {
            "generated_at": datetime.now().isoformat(),
            "last_date": current.date,
            "spy_price": round(current.close, 2),
            
            "vix_level": round(vix_estimate, 1),
            "vix_status": "Low Volatility" if vix_estimate < 20 else ("High Volatility" if vix_estimate > 30 else "Normal"),
            
            "spy_trend": spy_trend,
            "spy_trend_pct": spy_trend_pct,
            
            "sector_rotation": rotation,
            "sector_rotation_desc": rotation_desc,
            "cyclical_avg": round(cyclical_avg, 2),
            "defensive_avg": round(defensive_avg, 2),
            
            "conditions_met": conditions_met,
            "trade_conditions": "Favorable" if conditions_met == 3 else ("Mixed" if conditions_met == 2 else "Unfavorable"),
            
            "safe_to_trade": safe_to_trade,
            "message": "Market conditions support trading." if safe_to_trade else "Exercise caution.",
        }
    
    with open(path, 'w') as f:
        json.dump(conditions, f, indent=2)
    
    logger.info(f"Wrote market conditions to {path}")

# =========================================================================
# MAIN EXECUTION
# =========================================================================

def main():
    """Main execution function."""
    logger.info("=" * 70)
    logger.info("  Q5D UNIFIED MULTI-AGENT TRADING SYSTEM")
    logger.info("  Stock Agent 4 - Complete Analysis")
    logger.info("=" * 70)
    logger.info(f"  Symbols: {', '.join(SYMBOLS)}")
    logger.info(f"  Start Date: {START_DATE}")
    logger.info(f"  Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    symbol_data: Dict[str, List[Bar]] = {}
    all_results: List[ConsensusResult] = []
    
    # Process each symbol
    for symbol in SYMBOLS:
        logger.info(f"\n>>> Processing {symbol} ({SYMBOL_NAMES.get(symbol, symbol)})")
        
        # Fetch data
        bars = fetch_yahoo_data(symbol, START_DATE)
        
        if not bars:
            logger.warning(f"No data for {symbol}, skipping")
            continue
        
        # Compute indicators
        process_indicators(bars)
        
        # Save symbol data
        symbol_data[symbol] = bars
        write_symbol_csv(symbol, bars)
        
        # Run consensus on last 100 bars
        for bar in bars[-100:]:
            result = calculate_consensus(bar.date, symbol, bar)
            all_results.append(result)
    
    # Sort results by date
    all_results.sort(key=lambda x: x.date, reverse=True)
    
    # Write output files
    logger.info("\n" + "=" * 70)
    logger.info("  GENERATING OUTPUT FILES")
    logger.info("=" * 70)
    
    write_playbook_comparison(all_results)
    write_ultra_confluence(all_results)
    write_super_confluence(all_results)
    write_portfolio_confluence(all_results)
    write_sector_rotation(symbol_data)
    write_market_conditions(symbol_data)
    
    # Print summary
    ultra_count = sum(1 for r in all_results if r.confluence_level == "ULTRA")
    super_count = sum(1 for r in all_results if r.confluence_level == "SUPER")
    partial_count = sum(1 for r in all_results if r.confluence_level == "PARTIAL")
    
    logger.info("\n" + "=" * 70)
    logger.info("  ANALYSIS COMPLETE")
    logger.info("=" * 70)
    logger.info(f"  Total Signals Analyzed: {len(all_results)}")
    logger.info(f"  ULTRA (4/4): {ultra_count}")
    logger.info(f"  SUPER (3/4): {super_count}")
    logger.info(f"  PARTIAL (2/4): {partial_count}")
    logger.info("")
    logger.info("  Output Files Generated:")
    logger.info("    - data/{SYMBOL}.csv (for each symbol)")
    logger.info("    - reports/playbook_comparison.csv")
    logger.info("    - reports/ultra_confluence_4of4.csv")
    logger.info("    - reports/super_confluence_signals.csv")
    logger.info("    - reports/portfolio_confluence.csv")
    logger.info("    - reports/sector_rotation.csv")
    logger.info("    - reports/market_conditions.json")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
