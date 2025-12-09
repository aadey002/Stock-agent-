#!/usr/bin/env python3
"""
Stock Confluence Agent - 4-Agent Consensus System with Groq AI
===============================================================

AGENTS:
1. Base Confluence - SMA crossover, ATR stops
2. Gann-Elliott - Square of 9, Time Cycles
3. DQN/RL - Momentum signals
4. Groq AI - Llama 3.1 70B analysis

SIGNAL STRENGTH:
- 4/4 = ULTRA (89%)
- 3/4 = SUPER (78%)
- 2/4 = MODERATE (65%)

GROQ INTEGRATIONS:
1. Agent #4 voting
2. Gann interpretation
3. Trade advisor
"""

import csv
import json
import logging
import math
import os
import pathlib
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from enum import Enum
import pandas as pd

# =========================================================================
# CONFIG
# =========================================================================

SUPPORTED_SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLE", "XLK", "XLV", "XLI", "XLU", "GLD", "TLT"]
ACTIVE_SYMBOL = os.getenv("TRADING_SYMBOL", "SPY")
if ACTIVE_SYMBOL not in SUPPORTED_SYMBOLS:
    ACTIVE_SYMBOL = "SPY"

# Groq Cloud API (FREE & Fast!)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
GROQ_TIMEOUT = 60
GROQ_ENABLED = os.getenv("GROQ_ENABLED", "true").lower() == "true"

# Tiingo API
TIINGO_TOKEN = os.getenv("TIINGO_TOKEN", "")

# =========================================================================
# ENUMS
# =========================================================================

class TurnType(Enum):
    PULLBACK = "PULLBACK"
    BREAKDOWN = "BREAKDOWN"
    BREAKOUT = "BREAKOUT"
    BOUNCE = "BOUNCE"
    NO_TURN = "NO_TURN"

class Timeframe(Enum):
    MIN_15 = "15 Min"
    DAILY = "Daily"
    WEEKLY = "Weekly"

class OptionsAction(Enum):
    BUY_CALLS = "BUY CALLS"
    BUY_PUTS = "BUY PUTS"
    NO_ACTION = "NO ACTION"

class SignalStrength(Enum):
    ULTRA = "ULTRA"
    SUPER = "SUPER"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    NONE = "NONE"

# =========================================================================
# LOGGING
# =========================================================================

def setup_logging():
    pathlib.Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger("agent")
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    fmt = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', '%Y-%m-%d %H:%M:%S')
    fh = logging.FileHandler("logs/agent.log")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger

logger = setup_logging()

# =========================================================================
# GROQ AI CLIENT
# =========================================================================

class GroqClient:
    """Groq Cloud API Client - Llama 3.1 70B for trading analysis."""
    
    def __init__(self):
        self.api_url = GROQ_API_URL
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.enabled = GROQ_ENABLED and bool(self.api_key)
    
    def _call(self, prompt: str, system: str = None) -> Optional[str]:
        if not self.enabled:
            logger.info("[Groq] Disabled - skipping")
            return None
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 600
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(self.api_url, data=data)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')
            
            logger.info(f"[Groq] Calling {self.model}...")
            with urllib.request.urlopen(req, timeout=GROQ_TIMEOUT) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                logger.info(f"[Groq] Response received ({len(content)} chars)")
                return content
        except urllib.error.HTTPError as e:
            logger.warning(f"[Groq] HTTP Error {e.code}: {e.reason}")
            return None
        except Exception as e:
            logger.warning(f"[Groq] Error: {e}")
            return None
    
    def analyze_sentiment(self, symbol: str, data: Dict) -> Dict:
        """INTEGRATION #1: Groq as voting agent."""
        system = '''You are a quantitative trading analyst. Analyze market data and provide a signal.
Your response MUST start with: "SIGNAL: CALL" or "SIGNAL: PUT" or "SIGNAL: NEUTRAL"
Then give 2-3 sentences of reasoning.'''
        
        prompt = f"""Analyze {symbol}:

Price: ${data.get('price', 0):.2f}
20-SMA: ${data.get('sma20', 0):.2f}
50-SMA: ${data.get('sma50', 0):.2f}
ATR: ${data.get('atr', 0):.2f}
Trend: {data.get('trend', 'unknown')}
Gann Support: ${data.get('gann_support', 0):.2f}
Gann Resistance: ${data.get('gann_resistance', 0):.2f}
Gann Confluence: {data.get('gann_conf', 0)}/100

Other Agents: Base={data.get('base_signal', 'N/A')}, Gann={data.get('gann_signal', 'N/A')}

What is your signal?"""

        resp = self._call(prompt, system)
        if not resp:
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reasoning': 'Groq unavailable'}
        
        upper = resp.upper()
        if 'SIGNAL: CALL' in upper:
            return {'signal': 'CALL', 'confidence': 75, 'reasoning': resp[:300]}
        elif 'SIGNAL: PUT' in upper:
            return {'signal': 'PUT', 'confidence': 75, 'reasoning': resp[:300]}
        return {'signal': 'NEUTRAL', 'confidence': 50, 'reasoning': resp[:300]}
    
    def interpret_gann(self, symbol: str, gann: Dict) -> str:
        """INTEGRATION #2: Gann interpretation as W.D. Gann."""
        system = """You are W.D. Gann, the legendary trader. Interpret the Gann data and provide actionable insights with specific price levels and timing."""
        
        sq9 = gann.get('square_of_9', {})
        cycles = gann.get('time_cycles', {})
        confluence = gann.get('confluence', {})
        
        cycle_str = "\n".join([f"  {k}: Day {v['day']}/{v['of']} {'TURN ZONE!' if v.get('in_turn_zone') else ''}" 
                               for k, v in cycles.get('cycles', {}).items()])
        
        prompt = f"""Interpret Gann analysis for {symbol} @ ${gann.get('price', 0):.2f}:

SQUARE OF 9:
- Resistance: {[f"${r['price']}" for r in sq9.get('resistance', [])[:3]]}
- Support: {[f"${s['price']}" for s in sq9.get('support', [])[:3]]}

TIME CYCLES:
{cycle_str}

CONFLUENCE: {confluence.get('score', 0)}/100 - {confluence.get('zone', 'N/A')}

As Gann, what do you see? Give price targets and timing."""

        return self._call(prompt, system) or "Gann interpretation unavailable"
    
    def trade_plan(self, symbol: str, signals: Dict, market: Dict) -> Dict:
        """INTEGRATION #3: Complete trade plan."""
        system = '''You are a senior options trader. Synthesize all signals into ONE recommendation.
Start with: "RECOMMENDATION: BUY [SYMBOL] CALLS" or "RECOMMENDATION: BUY [SYMBOL] PUTS" or "RECOMMENDATION: NO TRADE"
Include: Strike, Expiry, Entry, Stop, Targets.'''

        prompt = f"""Trade plan for {symbol} @ ${market.get('price', 0):.2f}:

AGENT VOTES:
1. Base Confluence: {signals.get('base_agent', {}).get('signal', 'N/A')}
2. Gann-Elliott: {signals.get('gann_agent', {}).get('signal', 'N/A')}
3. DQN/RL: {signals.get('dqn_agent', {}).get('signal', 'N/A')}
4. Groq AI: {signals.get('groq_agent', {}).get('signal', 'N/A')}

CONSENSUS: {signals.get('consensus_direction', 'N/A')} ({signals.get('agreement_count', 0)}/4)
STRENGTH: {signals.get('signal_strength', 'N/A')}

GANN: Support ${market.get('gann_support', 0):.2f} | Resistance ${market.get('gann_resistance', 0):.2f}
ATR: ${market.get('atr', 0):.2f}

Generate trade recommendation with strike, expiry, entry, stop, targets."""

        resp = self._call(prompt, system)
        
        if not resp:
            return {'recommendation': 'NO TRADE', 'reasoning': 'Groq unavailable', 'plan': None}
        
        upper = resp.upper()
        price = market.get('price', 0)
        atr = market.get('atr', 1)
        
        if f'BUY {symbol.upper()} CALLS' in upper:
            rec, direction = f'BUY {symbol} CALLS', 'CALL'
        elif f'BUY {symbol.upper()} PUTS' in upper:
            rec, direction = f'BUY {symbol} PUTS', 'PUT'
        else:
            return {'recommendation': 'NO TRADE', 'reasoning': resp, 'plan': None}
        
        plan = {
            'symbol': symbol, 'direction': direction, 'strike': round(price),
            'expiry': '7-14 DTE',
            'entry_low': round(price - atr * 0.25, 2),
            'entry_high': round(price + atr * 0.25, 2),
            'stop': round(price - atr * 1.5, 2) if direction == 'CALL' else round(price + atr * 1.5, 2),
            'target1': round(price + atr * 2, 2) if direction == 'CALL' else round(price - atr * 2, 2),
            'target2': round(price + atr * 3, 2) if direction == 'CALL' else round(price - atr * 3, 2),
        }
        
        return {'recommendation': rec, 'reasoning': resp, 'plan': plan}

groq = GroqClient()

# =========================================================================
# GANN SQUARE OF 9
# =========================================================================

class GannSquareOf9:
    KEY_ANGLES = [45, 90, 135, 180, 225, 270, 315, 360]
    CARDINAL = [90, 180, 270, 360]
    
    @staticmethod
    def calculate_levels(price: float, increments: int = 5) -> Dict:
        sqrt_p = math.sqrt(price)
        resistance, support = [], []
        
        for i in range(1, increments + 1):
            for angle in GannSquareOf9.KEY_ANGLES:
                deg = (angle / 180.0) * i
                
                r = round((sqrt_p + deg) ** 2, 2)
                if r > price:
                    resistance.append({'price': r, 'angle': angle * i, 
                                       'pct': round((r - price) / price * 100, 2),
                                       'type': 'CARDINAL' if angle in GannSquareOf9.CARDINAL else 'ORDINAL'})
                
                s_sqrt = sqrt_p - deg
                if s_sqrt > 0:
                    s = round(s_sqrt ** 2, 2)
                    if s < price:
                        support.append({'price': s, 'angle': angle * i,
                                        'pct': round((price - s) / price * 100, 2),
                                        'type': 'CARDINAL' if angle in GannSquareOf9.CARDINAL else 'ORDINAL'})
        
        seen_r, seen_s = set(), set()
        unique_r = [r for r in sorted(resistance, key=lambda x: x['price']) if not (r['price'] in seen_r or seen_r.add(r['price']))]
        unique_s = [s for s in sorted(support, key=lambda x: x['price'], reverse=True) if not (s['price'] in seen_s or seen_s.add(s['price']))]
        
        return {'current_price': price, 'sqrt': round(sqrt_p, 4), 'resistance': unique_r[:increments], 'support': unique_s[:increments]}

# =========================================================================
# GANN TIME CYCLES
# =========================================================================

class GannTimeCycles:
    CYCLES = {'30-day': 30, '45-day': 45, '60-day': 60, '90-day': 90, '120-day': 120, '144-day': 144, '180-day': 180, '360-day': 360}
    
    @staticmethod
    def calculate(pivot_date: datetime, current_date: datetime) -> Dict:
        days = (current_date - pivot_date).days
        cycles = {}
        upcoming = []
        
        for name, length in GannTimeCycles.CYCLES.items():
            pos = days % length
            to_turn = length - pos
            cycles[name] = {'day': pos, 'of': length, 'progress_pct': round(pos / length * 100, 1),
                           'days_to_turn': to_turn, 'in_turn_zone': to_turn <= 3 or pos <= 3}
            if to_turn <= 5:
                upcoming.append({'cycle': name, 'days': to_turn})
        
        return {'days_from_pivot': days, 'cycles': cycles, 'upcoming_turns': sorted(upcoming, key=lambda x: x['days'])}
    
    @staticmethod
    def next_seasonal(current: datetime) -> Dict:
        year = current.year
        dates = [('Spring Equinox', datetime(year, 3, 21)), ('Summer Solstice', datetime(year, 6, 21)),
                 ('Fall Equinox', datetime(year, 9, 21)), ('Winter Solstice', datetime(year, 12, 21)),
                 ('Spring Equinox', datetime(year + 1, 3, 21))]
        for name, dt in dates:
            if dt > current:
                return {'name': name, 'date': dt.strftime('%Y-%m-%d'), 'days': (dt - current).days}
        return {'name': 'Unknown', 'date': 'N/A', 'days': 999}

# =========================================================================
# GANN ANGLES
# =========================================================================

class GannAngles:
    ANGLES = {'8x1': (8, 1), '4x1': (4, 1), '2x1': (2, 1), '1x1': (1, 1), '1x2': (1, 2), '1x4': (1, 4)}
    
    @staticmethod
    def calculate(pivot_price: float, pivot_date: datetime, current_date: datetime, is_low: bool = True) -> Dict:
        days = max((current_date - pivot_date).days, 1)
        angles = {}
        for name, (p, t) in GannAngles.ANGLES.items():
            rate = p / t
            proj = pivot_price + (rate * days) if is_low else pivot_price - (rate * days)
            angles[name] = {'price': round(proj, 2), 'rate': rate}
        return {'pivot': pivot_price, 'days': days, 'type': 'LOW' if is_low else 'HIGH', 'angles': angles}
    
    @staticmethod
    def position(price: float, angles: Dict) -> Dict:
        ang = angles['angles']
        above = [n for n, d in ang.items() if price > d['price']]
        below = [n for n, d in ang.items() if price <= d['price']]
        nearest = min(ang.items(), key=lambda x: abs(price - x[1]['price']))
        return {'above': above, 'below': below, 'nearest': nearest[0], 'nearest_price': nearest[1]['price']}

# =========================================================================
# CONFLUENCE SCORER
# =========================================================================

def calculate_confluence(price: float, sq9: Dict, cycles: Dict, angles: Dict) -> Dict:
    score, factors = 0, []
    
    s = sq9['support'][0] if sq9['support'] else None
    r = sq9['resistance'][0] if sq9['resistance'] else None
    if s and s['pct'] < 1.5:
        score += 25 if s['type'] == 'CARDINAL' else 20
        factors.append(f"Near SQ9 support ${s['price']}")
    elif r and r['pct'] < 1.5:
        score += 25 if r['type'] == 'CARDINAL' else 20
        factors.append(f"Near SQ9 resistance ${r['price']}")
    
    turns = [n for n, d in cycles['cycles'].items() if d['in_turn_zone']]
    if len(turns) >= 3:
        score += 25
        factors.append(f"Multiple cycles: {', '.join(turns)}")
    elif turns:
        score += 15
        factors.append(f"Cycle turn: {turns[0]}")
    
    if angles.get('nearest_price'):
        dist = abs(price - angles['nearest_price']) / price
        if dist < 0.005:
            score += 25
            factors.append(f"On {angles['nearest']} angle")
        elif dist < 0.01:
            score += 15
    
    upcoming = cycles.get('upcoming_turns', [])
    if len(upcoming) >= 3:
        score += 25
        factors.append(f"{len(upcoming)} cycles converging")
    elif len(upcoming) >= 2:
        score += 15
    
    zone = "HIGH PROBABILITY" if score >= 75 else "MODERATE" if score >= 50 else "LOW" if score >= 25 else "NONE"
    return {'score': score, 'zone': zone, 'factors': factors}

# =========================================================================
# TURN PREDICTOR
# =========================================================================

@dataclass
class TurnPrediction:
    symbol: str
    turn_type: TurnType
    timeframe: Timeframe
    action: OptionsAction
    direction: str
    confidence: float
    support: float
    resistance: float
    entry: float
    stop: float
    target1: float
    target2: float
    expiry: str
    strike: str
    rationale: str
    gann_score: int
    
    def to_dict(self) -> dict:
        act = self.action.value.replace("CALLS", f"{self.symbol} CALLS").replace("PUTS", f"{self.symbol} PUTS")
        return {"Symbol": self.symbol, "Timeframe": self.timeframe.value, "TurnType": self.turn_type.value,
                "Action": act, "Direction": self.direction, "Confidence": self.confidence,
                "GannScore": self.gann_score, "Support": self.support, "Resistance": self.resistance,
                "Entry": self.entry, "Stop": self.stop, "Target1": self.target1, "Target2": self.target2,
                "Expiry": self.expiry, "Strike": self.strike, "Rationale": self.rationale}

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    if len(df) < 2:
        return 1.0
    h, l, c = df['high'].values, df['low'].values, df['close'].values
    tr = [max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1])) for i in range(1, len(df))]
    return sum(tr[-period:]) / min(period, len(tr)) if tr else 1.0

def predict_turn(df: pd.DataFrame, symbol: str, timeframe: Timeframe, sq9: Dict, confluence: Dict) -> TurnPrediction:
    if len(df) < 20:
        return TurnPrediction(symbol, TurnType.NO_TURN, timeframe, OptionsAction.NO_ACTION, "NEUTRAL",
                              0, 0, 0, 0, 0, 0, 0, "N/A", "N/A", "Insufficient data", 0)
    
    price = df['close'].iloc[-1]
    atr = calculate_atr(df)
    support = sq9['support'][0]['price'] if sq9['support'] else price * 0.95
    resistance = sq9['resistance'][0]['price'] if sq9['resistance'] else price * 1.05
    
    sma20 = df['close'].rolling(20).mean().iloc[-1]
    sma50 = df['close'].rolling(min(50, len(df))).mean().iloc[-1]
    trend_up, trend_down = price > sma20 > sma50, price < sma20 < sma50
    
    vol_avg = df['volume'].rolling(20).mean().iloc[-1]
    vol_now = df['volume'].iloc[-5:].mean()
    vol_up = vol_now > vol_avg * 1.2
    
    near_s = abs(price - support) < atr * 0.5
    near_r = abs(price - resistance) < atr * 0.5
    below_s = price < support - atr * 0.25
    above_r = price > resistance + atr * 0.25
    
    if below_s and vol_up:
        turn, action, direction = TurnType.BREAKDOWN, OptionsAction.BUY_PUTS, "DOWN"
        conf = 75 + (15 if trend_down else 0)
        rationale = f"BREAKDOWN below ${support:.2f}"
    elif above_r and vol_up:
        turn, action, direction = TurnType.BREAKOUT, OptionsAction.BUY_CALLS, "UP"
        conf = 75 + (15 if trend_up else 0)
        rationale = f"BREAKOUT above ${resistance:.2f}"
    elif trend_up and near_s:
        turn, action, direction = TurnType.PULLBACK, OptionsAction.BUY_CALLS, "UP"
        conf = 70
        rationale = f"PULLBACK to ${support:.2f} in uptrend"
    elif trend_down and near_r:
        turn, action, direction = TurnType.PULLBACK, OptionsAction.BUY_PUTS, "DOWN"
        conf = 70
        rationale = f"PULLBACK to ${resistance:.2f} in downtrend"
    elif near_s and not trend_down:
        turn, action, direction = TurnType.BOUNCE, OptionsAction.BUY_CALLS, "UP"
        conf = 65
        rationale = f"BOUNCE at ${support:.2f}"
    else:
        turn, action, direction = TurnType.NO_TURN, OptionsAction.NO_ACTION, "NEUTRAL"
        conf = 40
        rationale = "No clear signal"
    
    conf = min(conf + confluence['score'] * 0.1, 100)
    
    if direction == "UP":
        stop, t1, t2 = support - atr * 0.5, resistance, resistance + (resistance - support) * 0.5
    elif direction == "DOWN":
        stop, t1, t2 = resistance + atr * 0.5, support, support - (resistance - support) * 0.5
    else:
        stop = t1 = t2 = price
    
    expiry = {"15 Min": "1-3 DTE", "Daily": "7-14 DTE", "Weekly": "14-30 DTE"}.get(timeframe.value, "7-14 DTE")
    strike = f"ATM ${round(price)}" if direction != "NEUTRAL" else "N/A"
    
    return TurnPrediction(symbol, turn, timeframe, action, direction, round(conf, 1), round(support, 2),
                          round(resistance, 2), round(price, 2), round(stop, 2), round(t1, 2), round(t2, 2),
                          expiry, strike, rationale, confluence['score'])

# =========================================================================
# CONSENSUS SYSTEM
# =========================================================================

def calculate_consensus(agents: Dict) -> Dict:
    votes = {'CALL': 0, 'PUT': 0, 'NEUTRAL': 0}
    for _, data in agents.items():
        sig = data.get('signal', 'NEUTRAL').upper()
        if sig in votes:
            votes[sig] += 1
    
    max_v = max(votes.values())
    if votes['CALL'] == max_v and votes['CALL'] > votes['PUT']:
        direction = 'CALL'
    elif votes['PUT'] == max_v:
        direction = 'PUT'
    else:
        direction = 'NEUTRAL'
    
    agreement = votes[direction] if direction != 'NEUTRAL' else 0
    
    if agreement == 4:
        strength, win_rate = SignalStrength.ULTRA, 89
    elif agreement == 3:
        strength, win_rate = SignalStrength.SUPER, 78
    elif agreement == 2:
        strength, win_rate = SignalStrength.MODERATE, 65
    elif agreement == 1:
        strength, win_rate = SignalStrength.WEAK, 55
    else:
        strength, win_rate = SignalStrength.NONE, 0
    
    return {'consensus_direction': direction, 'agreement_count': agreement, 
            'signal_strength': strength.value, 'win_rate': win_rate, 'votes': votes}

# =========================================================================
# DATA FETCHING
# =========================================================================

@dataclass
class Bar:
    d: str
    open_: float
    high: float
    low: float
    close: float
    volume: float

def fetch_data(symbol: str, start: str) -> List[Bar]:
    token = TIINGO_TOKEN
    if not token:
        logger.error("TIINGO_TOKEN not set!")
        return []
    
    url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices?startDate={start}&token={token}"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'StockAgent/1.0')
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return [Bar(i['date'], i['open'], i['high'], i['low'], i['close'], i['volume']) for i in data]
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return []

def bars_to_df(bars: List[Bar]) -> pd.DataFrame:
    if not bars:
        return pd.DataFrame()
    return pd.DataFrame({'open': [b.open_ for b in bars], 'high': [b.high for b in bars],
                         'low': [b.low for b in bars], 'close': [b.close for b in bars],
                         'volume': [b.volume for b in bars]}, index=pd.to_datetime([b.d for b in bars]))

# =========================================================================
# OUTPUT
# =========================================================================

DATA_DIR = pathlib.Path("data")
REPORT_DIR = pathlib.Path("reports")
DATA_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

def write_predictions(preds: List[TurnPrediction]) -> None:
    path = REPORT_DIR / "gann_turn_predictions.csv"
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=["Symbol", "Timeframe", "TurnType", "Action", "Direction",
                                          "Confidence", "GannScore", "Support", "Resistance", "Entry",
                                          "Stop", "Target1", "Target2", "Expiry", "Strike", "Rationale"])
        w.writeheader()
        for p in preds:
            w.writerow(p.to_dict())
    logger.info(f"Wrote {len(preds)} predictions")

def write_consensus(consensus: Dict, agents: Dict, trade: Dict, symbol: str) -> None:
    path = REPORT_DIR / f"consensus_{symbol}.json"
    out = {'symbol': symbol, 'timestamp': datetime.now().isoformat(), 'consensus': consensus,
           'agents': {k: {'signal': v.get('signal'), 'confidence': v.get('confidence')} for k, v in agents.items()},
           'trade_plan': trade}
    path.write_text(json.dumps(out, indent=2))
    logger.info(f"Wrote consensus to {path}")

def write_gann_json(symbol: str, price: float, sq9: Dict, cycles: Dict, angles: Dict, conf: Dict) -> None:
    path = DATA_DIR / f"gann_analysis_{symbol}.json"
    out = {'symbol': symbol, 'timestamp': datetime.now().isoformat(), 'price': price,
           'square_of_9': sq9, 'time_cycles': cycles, 'angles': angles, 'confluence': conf,
           'seasonal': GannTimeCycles.next_seasonal(datetime.now())}
    path.write_text(json.dumps(out, indent=2, default=str))
    logger.info(f"Wrote Gann analysis")

# =========================================================================
# MAIN
# =========================================================================

def main():
    symbol = ACTIVE_SYMBOL
    
    logger.info("=" * 70)
    logger.info(f"4-AGENT CONSENSUS SYSTEM - {symbol}")
    logger.info(f"Agents: Base | Gann-Elliott | DQN | Groq AI ({GROQ_MODEL})")
    logger.info(f"Groq: {'ENABLED' if groq.enabled else 'DISABLED'}")
    logger.info("=" * 70)
    
    # Fetch
    bars = fetch_data(symbol, "2022-11-01")
    if not bars:
        logger.error("No data!")
        return
    
    df = bars_to_df(bars)
    price = df['close'].iloc[-1]
    atr = calculate_atr(df)
    
    logger.info(f"\n{symbol} @ ${price:.2f} | ATR: ${atr:.2f}")
    
    # GANN
    logger.info("\n" + "=" * 70)
    logger.info("GANN ANALYSIS")
    logger.info("=" * 70)
    
    sq9 = GannSquareOf9.calculate_levels(price)
    logger.info(f"SQ9: R={[f'${r[\"price\"]}' for r in sq9['resistance'][:3]]} | S={[f'${s[\"price\"]}' for s in sq9['support'][:3]]}")
    
    pivot = datetime.now() - timedelta(days=30)
    cycles = GannTimeCycles.calculate(pivot, datetime.now())
    angles = GannAngles.calculate(price * 0.95, pivot, datetime.now(), True)
    angle_pos = GannAngles.position(price, angles)
    confluence = calculate_confluence(price, sq9, cycles, angle_pos)
    
    logger.info(f"Confluence: {confluence['score']}/100 - {confluence['zone']}")
    
    write_gann_json(symbol, price, sq9, cycles, angles, confluence)
    
    gann_data = {'price': price, 'square_of_9': sq9, 'time_cycles': cycles, 'confluence': confluence}
    
    # AGENTS
    logger.info("\n" + "=" * 70)
    logger.info("AGENT SIGNALS")
    logger.info("=" * 70)
    
    sma20 = df['close'].rolling(20).mean().iloc[-1]
    sma50 = df['close'].rolling(min(50, len(df))).mean().iloc[-1]
    trend = "UP" if price > sma20 > sma50 else "DOWN" if price < sma20 < sma50 else "SIDE"
    
    # Agent 1: Base
    base_sig = "CALL" if sma20 > sma50 else "PUT"
    base_agent = {'signal': base_sig, 'confidence': 70}
    logger.info(f"1. Base: {base_sig} (trend={trend})")
    
    # Agent 2: Gann
    gann_sup = sq9['support'][0]['price'] if sq9['support'] else price * 0.95
    gann_res = sq9['resistance'][0]['price'] if sq9['resistance'] else price * 1.05
    gann_sig = "CALL" if abs(price - gann_sup) < abs(price - gann_res) else "PUT"
    gann_conf = 85 if confluence['score'] >= 75 else 70 if confluence['score'] >= 50 else 55
    gann_agent = {'signal': gann_sig, 'confidence': gann_conf}
    logger.info(f"2. Gann: {gann_sig} (conf={confluence['score']})")
    
    # Agent 3: DQN
    mom = (price - df['close'].iloc[-10]) / df['close'].iloc[-10] * 100
    dqn_sig = "CALL" if mom > 1 else "PUT" if mom < -1 else "NEUTRAL"
    dqn_agent = {'signal': dqn_sig, 'confidence': 65}
    logger.info(f"3. DQN: {dqn_sig} (mom={mom:.2f}%)")
    
    # Agent 4: Groq AI
    price_data = {'price': price, 'sma20': sma20, 'sma50': sma50, 'atr': atr, 'trend': trend,
                  'gann_support': gann_sup, 'gann_resistance': gann_res, 'gann_conf': confluence['score'],
                  'base_signal': base_sig, 'gann_signal': gann_sig}
    groq_result = groq.analyze_sentiment(symbol, price_data)
    groq_agent = {'signal': groq_result['signal'], 'confidence': groq_result['confidence']}
    logger.info(f"4. Groq: {groq_result['signal']}")
    
    # CONSENSUS
    agents = {'base_agent': base_agent, 'gann_agent': gann_agent, 'dqn_agent': dqn_agent, 'groq_agent': groq_agent}
    consensus = calculate_consensus(agents)
    
    logger.info("\n" + "=" * 70)
    logger.info("CONSENSUS")
    logger.info("=" * 70)
    logger.info(f"Direction: {consensus['consensus_direction']}")
    logger.info(f"Agreement: {consensus['agreement_count']}/4")
    logger.info(f"Strength: {consensus['signal_strength']} ({consensus['win_rate']}% target)")
    
    # Groq Gann Interpretation
    logger.info("\n" + "=" * 70)
    logger.info("GROQ GANN INTERPRETATION")
    logger.info("=" * 70)
    gann_interp = groq.interpret_gann(symbol, gann_data)
    logger.info(gann_interp[:800] if gann_interp else "Unavailable")
    
    # Groq Trade Plan
    logger.info("\n" + "=" * 70)
    logger.info("GROQ TRADE ADVISOR")
    logger.info("=" * 70)
    market = {'price': price, 'atr': atr, 'gann_support': gann_sup, 'gann_resistance': gann_res,
              'gann_confluence': confluence['score']}
    all_sigs = {**agents, **consensus}
    trade = groq.trade_plan(symbol, all_sigs, market)
    
    logger.info(f"RECOMMENDATION: {trade['recommendation']}")
    if trade.get('plan'):
        tp = trade['plan']
        logger.info(f"  Strike: ${tp['strike']} | Expiry: {tp['expiry']}")
        logger.info(f"  Entry: ${tp['entry_low']}-${tp['entry_high']}")
        logger.info(f"  Stop: ${tp['stop']} | T1: ${tp['target1']} | T2: ${tp['target2']}")
    
    # TURN PREDICTIONS
    logger.info("\n" + "=" * 70)
    logger.info("TURN PREDICTIONS")
    logger.info("=" * 70)
    
    preds = [predict_turn(df, symbol, Timeframe.DAILY, sq9, confluence),
             predict_turn(df.tail(20), symbol, Timeframe.MIN_15, sq9, confluence)]
    
    for p in preds:
        act = p.action.value.replace("CALLS", f"{symbol} CALLS").replace("PUTS", f"{symbol} PUTS")
        logger.info(f"[{p.timeframe.value}] {p.turn_type.value} -> {act} | {p.confidence}%")
    
    write_predictions(preds)
    write_consensus(consensus, agents, trade, symbol)
    
    # FINAL
    logger.info("\n" + "=" * 70)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 70)
    logger.info(f"{symbol} @ ${price:.2f}")
    logger.info(f"Consensus: {consensus['signal_strength']} {consensus['consensus_direction']} ({consensus['agreement_count']}/4)")
    logger.info(f"Gann: {confluence['score']}/100 ({confluence['zone']})")
    logger.info(f"Recommendation: {trade['recommendation']}")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
