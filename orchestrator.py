#!/usr/bin/env python3
"""
Q5D 4-AGENT HISTORICAL TRACKER
==============================

Tracks ALL confluence levels for historical analysis:
- 4/4 ULTRA CONFLUENCE
- 3/4 SUPER CONFLUENCE  
- 2/4 PARTIAL CONFLUENCE
- Individual agent performance

This is for RESEARCH and TRACKING only - not trade execution.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = "data"
REPORTS_DIR = "reports"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


class SystemA:
    """Agent 1: Technical Confluence"""
    
    def __init__(self):
        self.name = "Confluence"
        self.icon = "📊"
    
    def generate_signal(self, data, index):
        if index < 50:
            return self._hold()
        
        row = data.iloc[index]
        prev = data.iloc[index - 1]
        
        close = row['Close']
        fast = row.get('FastSMA', close)
        slow = row.get('SlowSMA', close)
        prev_fast = prev.get('FastSMA', close)
        prev_slow = prev.get('SlowSMA', close)
        atr = row.get('ATR', close * 0.02)
        
        bias = row.get('Bias', 'NEUTRAL')
        if isinstance(bias, (int, float)):
            bias = 'BULLISH' if bias > 0 else 'BEARISH' if bias < 0 else 'NEUTRAL'
        
        price_conf = int(row.get('PriceConfluence', 0))
        time_conf = int(row.get('TimeConfluence', 0))
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        bullish_cross = prev_fast <= prev_slow and fast > slow
        bearish_cross = prev_fast >= prev_slow and fast < slow
        
        if bullish_cross:
            signal, confidence = 'CALL', 0.75
            reasons.append('Bullish crossover')
        elif fast > slow and bias == 'BULLISH':
            signal, confidence = 'CALL', 0.60
            reasons.append('Bullish trend')
        elif bearish_cross:
            signal, confidence = 'PUT', 0.75
            reasons.append('Bearish crossover')
        elif fast < slow and bias == 'BEARISH':
            signal, confidence = 'PUT', 0.60
            reasons.append('Bearish trend')
        
        stop = close - 2*atr if signal == 'CALL' else close + 2*atr if signal == 'PUT' else close
        t1 = close + 3*atr if signal == 'CALL' else close - 3*atr if signal == 'PUT' else close
        t2 = close + 5*atr if signal == 'CALL' else close - 5*atr if signal == 'PUT' else close
        t3 = close + 8*atr if signal == 'CALL' else close - 8*atr if signal == 'PUT' else close
        
        return {
            'agent': self.name, 'signal': signal, 'confidence': confidence,
            'entry': close, 'stop': stop, 'target1': t1, 'target2': t2, 'target3': t3,
            'reasons': reasons
        }
    
    def _hold(self):
        return {'agent': self.name, 'signal': 'HOLD', 'confidence': 0,
                'entry': 0, 'stop': 0, 'target1': 0, 'target2': 0, 'target3': 0, 'reasons': []}


class SystemB:
    """Agent 2: Gann-Elliott"""
    
    def __init__(self):
        self.name = "GannElliott"
        self.icon = "🔮"
    
    def generate_signal(self, data, index):
        if index < 50:
            return self._hold()
        
        row = data.iloc[index]
        lookback = data.iloc[max(0, index-50):index+1]
        
        close = row['Close']
        high_52 = lookback['High'].max()
        low_52 = lookback['Low'].min()
        rng = high_52 - low_52
        atr = row.get('ATR', close * 0.02)
        
        if rng == 0:
            return self._hold()
        
        pos = (close - low_52) / rng
        fib_382 = low_52 + rng * 0.382
        fib_618 = low_52 + rng * 0.618
        
        sma20 = lookback['Close'].tail(20).mean()
        sma50 = lookback['Close'].mean()
        trend = 'UP' if sma20 > sma50 else 'DOWN' if sma20 < sma50 else 'NEUTRAL'
        
        wave = (index % 5) + 1
        near_fib = min(abs(close - fib_382), abs(close - fib_618)) / close < 0.02
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        if trend == 'UP' and (wave in [2, 4] or pos < 0.5):
            signal, confidence = 'CALL', 0.65
            reasons.append(f'Uptrend Wave {wave}')
        elif trend == 'DOWN' and (wave in [2, 4] or pos > 0.5):
            signal, confidence = 'PUT', 0.65
            reasons.append(f'Downtrend Wave {wave}')
        
        stop = close - 2.5*atr if signal == 'CALL' else close + 2.5*atr if signal == 'PUT' else close
        t1 = close + 3*atr if signal == 'CALL' else close - 3*atr if signal == 'PUT' else close
        t2 = close + 5*atr if signal == 'CALL' else close - 5*atr if signal == 'PUT' else close
        t3 = close + 8*atr if signal == 'CALL' else close - 8*atr if signal == 'PUT' else close
        
        return {
            'agent': self.name, 'signal': signal, 'confidence': confidence,
            'entry': close, 'stop': stop, 'target1': t1, 'target2': t2, 'target3': t3,
            'reasons': reasons, 'wave': wave, 'trend': trend
        }
    
    def _hold(self):
        return {'agent': self.name, 'signal': 'HOLD', 'confidence': 0,
                'entry': 0, 'stop': 0, 'target1': 0, 'target2': 0, 'target3': 0,
                'reasons': [], 'wave': 0, 'trend': 'NEUTRAL'}


class DQNAgent:
    """Agent 3: DQN Reinforcement Learning"""
    
    def __init__(self):
        self.name = "DQN"
        self.icon = "🧠"
    
    def generate_signal(self, data, index):
        if index < 50:
            return self._hold()
        
        row = data.iloc[index]
        lookback = data.iloc[max(0, index-20):index+1]
        
        close = row['Close']
        atr = row.get('ATR', close * 0.02)
        
        returns = lookback['Close'].pct_change().dropna()
        momentum = returns.mean() * 100
        
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        rsi = 50 if (gains + losses) == 0 else (gains / (gains + losses)) * 100
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        if momentum > 0.05 and rsi < 70:
            signal, confidence = 'CALL', 0.55 + min(0.25, momentum * 0.3)
            reasons.append(f'Bullish momentum ({momentum:.2f}%)')
        elif momentum < -0.05 and rsi > 30:
            signal, confidence = 'PUT', 0.55 + min(0.25, abs(momentum) * 0.3)
            reasons.append(f'Bearish momentum ({momentum:.2f}%)')
        elif rsi < 30:
            signal, confidence = 'CALL', 0.60
            reasons.append(f'Oversold (RSI {rsi:.0f})')
        elif rsi > 70:
            signal, confidence = 'PUT', 0.60
            reasons.append(f'Overbought (RSI {rsi:.0f})')
        
        stop = close - 2*atr if signal == 'CALL' else close + 2*atr if signal == 'PUT' else close
        t1 = close + 3*atr if signal == 'CALL' else close - 3*atr if signal == 'PUT' else close
        t2 = close + 5*atr if signal == 'CALL' else close - 5*atr if signal == 'PUT' else close
        t3 = close + 8*atr if signal == 'CALL' else close - 8*atr if signal == 'PUT' else close
        
        return {
            'agent': self.name, 'signal': signal, 'confidence': min(0.85, confidence),
            'entry': close, 'stop': stop, 'target1': t1, 'target2': t2, 'target3': t3,
            'reasons': reasons, 'rsi': rsi, 'momentum': momentum
        }
    
    def _hold(self):
        return {'agent': self.name, 'signal': 'HOLD', 'confidence': 0,
                'entry': 0, 'stop': 0, 'target1': 0, 'target2': 0, 'target3': 0,
                'reasons': [], 'rsi': 50, 'momentum': 0}


class ThreeWaveAgent:
    """Agent 4: 3-Wave Momentum System"""
    
    def __init__(self):
        self.name = "3Wave"
        self.icon = "🌊"
    
    def generate_signal(self, data, index):
        if index < 50:
            return self._hold()
        
        row = data.iloc[index]
        lookback = data.iloc[max(0, index-30):index+1]
        
        close = row['Close']
        atr = row.get('ATR', close * 0.02)
        
        mom_5 = (close - lookback.iloc[-6]['Close']) / lookback.iloc[-6]['Close'] * 100 if len(lookback) > 5 else 0
        mom_10 = (close - lookback.iloc[-11]['Close']) / lookback.iloc[-11]['Close'] * 100 if len(lookback) > 10 else 0
        mom_20 = (close - lookback.iloc[0]['Close']) / lookback.iloc[0]['Close'] * 100
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        all_pos = mom_5 > 0 and mom_10 > 0 and mom_20 > 0
        all_neg = mom_5 < 0 and mom_10 < 0 and mom_20 < 0
        
        if all_pos and mom_5 > 0.2:
            signal, confidence = 'CALL', 0.65
            reasons.append(f'Aligned bullish ({mom_5:.1f}%)')
        elif all_neg and mom_5 < -0.2:
            signal, confidence = 'PUT', 0.65
            reasons.append(f'Aligned bearish ({mom_5:.1f}%)')
        elif mom_5 > 0.5:
            signal, confidence = 'CALL', 0.55
            reasons.append(f'Strong 5d momentum ({mom_5:.1f}%)')
        elif mom_5 < -0.5:
            signal, confidence = 'PUT', 0.55
            reasons.append(f'Strong 5d momentum ({mom_5:.1f}%)')
        
        stop = close - 2*atr if signal == 'CALL' else close + 2*atr if signal == 'PUT' else close
        risk = abs(close - stop)
        t1 = close + risk*1.5 if signal == 'CALL' else close - risk*1.5 if signal == 'PUT' else close
        t2 = close + risk*2.5 if signal == 'CALL' else close - risk*2.5 if signal == 'PUT' else close
        t3 = close + risk*4.0 if signal == 'CALL' else close - risk*4.0 if signal == 'PUT' else close
        
        return {
            'agent': self.name, 'signal': signal, 'confidence': confidence,
            'entry': close, 'stop': stop, 'target1': t1, 'target2': t2, 'target3': t3,
            'reasons': reasons, 'mom_5': mom_5, 'mom_10': mom_10
        }
    
    def _hold(self):
        return {'agent': self.name, 'signal': 'HOLD', 'confidence': 0,
                'entry': 0, 'stop': 0, 'target1': 0, 'target2': 0, 'target3': 0,
                'reasons': [], 'mom_5': 0, 'mom_10': 0}


class HistoricalTracker:
    """
    Tracks ALL confluence levels for historical analysis.
    NO trade decisions - just tracking for research.
    """
    
    def __init__(self):
        self.agents = [SystemA(), SystemB(), DQNAgent(), ThreeWaveAgent()]
        
        self.all_bars = []
        self.ultra_signals = []  # 4/4 agree
        self.super_signals = []  # 3/4 agree
        self.partial_signals = []  # 2/4 agree
        
        self.stats = {
            'total_bars': 0,
            'agent_signals': {a.name: {'CALL': 0, 'PUT': 0, 'HOLD': 0} for a in self.agents},
            'confluence': {'ultra_4': 0, 'super_3': 0, 'partial_2': 0, 'weak_1': 0, 'none_0': 0},
        }
    
    def process_bar(self, data, index):
        """Process bar through all 4 agents and track results."""
        row = data.iloc[index]
        date = row.get('Date', str(index))
        close = row['Close']
        
        # Get all 4 signals
        signals = [agent.generate_signal(data, index) for agent in self.agents]
        
        # Track individual agent signals
        for sig in signals:
            self.stats['agent_signals'][sig['agent']][sig['signal']] += 1
        
        # Count votes
        calls = [s for s in signals if s['signal'] == 'CALL']
        puts = [s for s in signals if s['signal'] == 'PUT']
        
        call_count = len(calls)
        put_count = len(puts)
        
        # Determine majority
        if call_count > put_count:
            majority = 'CALL'
            majority_count = call_count
            agreeing = calls
        elif put_count > call_count:
            majority = 'PUT'
            majority_count = put_count
            agreeing = puts
        else:
            majority = 'NEUTRAL'
            majority_count = max(call_count, put_count)
            agreeing = []
        
        # Confluence level
        if majority_count == 4:
            level = 'ULTRA_4'
            self.stats['confluence']['ultra_4'] += 1
        elif majority_count == 3:
            level = 'SUPER_3'
            self.stats['confluence']['super_3'] += 1
        elif majority_count == 2:
            level = 'PARTIAL_2'
            self.stats['confluence']['partial_2'] += 1
        elif majority_count == 1:
            level = 'WEAK_1'
            self.stats['confluence']['weak_1'] += 1
        else:
            level = 'NONE_0'
            self.stats['confluence']['none_0'] += 1
        
        # Calculate levels if we have agreement
        if agreeing:
            avg_entry = np.mean([s['entry'] for s in agreeing])
            avg_stop = np.mean([s['stop'] for s in agreeing])
            avg_t1 = np.mean([s['target1'] for s in agreeing])
            avg_t2 = np.mean([s['target2'] for s in agreeing])
            avg_t3 = np.mean([s['target3'] for s in agreeing])
            avg_conf = np.mean([s['confidence'] for s in agreeing])
        else:
            avg_entry = avg_stop = avg_t1 = avg_t2 = avg_t3 = close
            avg_conf = 0
        
        # Build record
        record = {
            'date': str(date),
            'close': round(close, 2),
            
            # Individual agents
            'A1_Confluence': signals[0]['signal'],
            'A1_conf': signals[0]['confidence'],
            
            'A2_GannElliott': signals[1]['signal'],
            'A2_conf': signals[1]['confidence'],
            'A2_wave': signals[1].get('wave', 0),
            'A2_trend': signals[1].get('trend', ''),
            
            'A3_DQN': signals[2]['signal'],
            'A3_conf': signals[2]['confidence'],
            'A3_rsi': round(signals[2].get('rsi', 50), 1),
            
            'A4_3Wave': signals[3]['signal'],
            'A4_conf': signals[3]['confidence'],
            'A4_mom5': round(signals[3].get('mom_5', 0), 2),
            
            # Votes
            'call_votes': call_count,
            'put_votes': put_count,
            'hold_votes': 4 - call_count - put_count,
            
            # Confluence
            'confluence_level': level,
            'majority': majority,
            'agreement_count': majority_count,
            
            # Levels (if agreeing)
            'entry': round(avg_entry, 2),
            'stop': round(avg_stop, 2),
            'target1': round(avg_t1, 2),
            'target2': round(avg_t2, 2),
            'target3': round(avg_t3, 2),
            'avg_confidence': round(avg_conf, 2),
        }
        
        self.all_bars.append(record)
        self.stats['total_bars'] += 1
        
        # Store by confluence level
        if level == 'ULTRA_4':
            self.ultra_signals.append(record)
        elif level == 'SUPER_3':
            self.super_signals.append(record)
        elif level == 'PARTIAL_2':
            self.partial_signals.append(record)
        
        return record
    
    def run(self, data):
        """Run tracker on full dataset."""
        logger.info("=" * 70)
        logger.info("  Q5D 4-AGENT HISTORICAL TRACKER")
        logger.info("=" * 70)
        logger.info(f"  Tracking {len(data)} bars for historical analysis...")
        logger.info("")
        
        for i in range(len(data)):
            self.process_bar(data, i)
            if (i + 1) % 100 == 0:
                logger.info(f"  Processed {i + 1}/{len(data)} bars...")
        
        self._save_reports()
        self._print_summary()
        
        return self.stats
    
    def _save_reports(self):
        """Save all tracking reports."""
        
        # 1. ULTRA Confluence (4/4)
        if self.ultra_signals:
            df = pd.DataFrame(self.ultra_signals)
            path = os.path.join(REPORTS_DIR, 'ultra_confluence_4of4.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path} ({len(df)} signals)")
        
        # 2. SUPER Confluence (3/4)
        if self.super_signals:
            df = pd.DataFrame(self.super_signals)
            path = os.path.join(REPORTS_DIR, 'super_confluence_3of4.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path} ({len(df)} signals)")
        
        # 3. Combined Super Confluence (3+ out of 4)
        combined = self.ultra_signals + self.super_signals
        if combined:
            df = pd.DataFrame(combined)
            df = df.sort_values('date')
            path = os.path.join(REPORTS_DIR, 'super_confluence_signals.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path} ({len(df)} signals)")
        
        # 4. Full playbook comparison
        if self.all_bars:
            df = pd.DataFrame(self.all_bars)
            path = os.path.join(REPORTS_DIR, 'playbook_comparison.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path}")
        
        # 5. Agreement Analysis JSON
        ultra_calls = len([s for s in self.ultra_signals if s['majority'] == 'CALL'])
        ultra_puts = len([s for s in self.ultra_signals if s['majority'] == 'PUT'])
        super_calls = len([s for s in self.super_signals if s['majority'] == 'CALL'])
        super_puts = len([s for s in self.super_signals if s['majority'] == 'PUT'])
        
        analysis = {
            'generated_at': datetime.now().isoformat(),
            'total_bars': self.stats['total_bars'],
            'agents': [a.name for a in self.agents],
            
            'confluence_counts': {
                'ultra_4of4': len(self.ultra_signals),
                'super_3of4': len(self.super_signals),
                'partial_2of4': len(self.partial_signals),
                'total_3plus': len(self.ultra_signals) + len(self.super_signals),
            },
            
            'ultra_breakdown': {
                'total': len(self.ultra_signals),
                'calls': ultra_calls,
                'puts': ultra_puts,
            },
            
            'super_breakdown': {
                'total': len(self.super_signals),
                'calls': super_calls,
                'puts': super_puts,
            },
            
            'agent_activity': self.stats['agent_signals'],
            
            'confluence_distribution': self.stats['confluence'],
        }
        
        path = os.path.join(REPORTS_DIR, 'agreement_analysis.json')
        with open(path, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"  Saved: {path}")
    
    def _print_summary(self):
        """Print tracking summary."""
        ultra_calls = len([s for s in self.ultra_signals if s['majority'] == 'CALL'])
        ultra_puts = len([s for s in self.ultra_signals if s['majority'] == 'PUT'])
        super_calls = len([s for s in self.super_signals if s['majority'] == 'CALL'])
        super_puts = len([s for s in self.super_signals if s['majority'] == 'PUT'])
        
        print("\n")
        print("=" * 70)
        print("  Q5D 4-AGENT HISTORICAL TRACKER - RESULTS")
        print("=" * 70)
        print("")
        print("  AGENT ACTIVITY")
        for agent in self.agents:
            stats = self.stats['agent_signals'][agent.name]
            total = stats['CALL'] + stats['PUT']
            print(f"    {agent.icon} {agent.name}: {total} signals (CALL: {stats['CALL']}, PUT: {stats['PUT']})")
        print("")
        print("  CONFLUENCE DISTRIBUTION")
        print(f"    🔥 ULTRA (4/4):    {len(self.ultra_signals):>5} occurrences")
        print(f"    ⭐ SUPER (3/4):    {len(self.super_signals):>5} occurrences")
        print(f"    📊 PARTIAL (2/4):  {len(self.partial_signals):>5} occurrences")
        print(f"    📉 WEAK (1/4):     {self.stats['confluence']['weak_1']:>5} occurrences")
        print(f"    ❌ NONE (0/4):     {self.stats['confluence']['none_0']:>5} occurrences")
        print("")
        print("  HIGH CONVICTION SIGNALS (3+ Agreement)")
        print(f"    Total:             {len(self.ultra_signals) + len(self.super_signals)}")
        print("")
        print(f"    ULTRA (4/4):       {len(self.ultra_signals)} (CALL: {ultra_calls}, PUT: {ultra_puts})")
        print(f"    SUPER (3/4):       {len(self.super_signals)} (CALL: {super_calls}, PUT: {super_puts})")
        print("")
        print("  OUTPUT FILES")
        print("    reports/ultra_confluence_4of4.csv    [4/4 agreement]")
        print("    reports/super_confluence_3of4.csv    [3/4 agreement]")
        print("    reports/super_confluence_signals.csv [3+ agreement]")
        print("    reports/playbook_comparison.csv      [All bars, all agents]")
        print("    reports/agreement_analysis.json      [Statistics]")
        print("=" * 70)
        
        # Show recent high conviction signals
        combined = sorted(self.ultra_signals + self.super_signals, key=lambda x: x['date'])
        if combined:
            print("\n  RECENT HIGH CONVICTION SIGNALS (Last 10)")
            print("  " + "-" * 65)
            for s in combined[-10:]:
                level = "🔥 ULTRA" if s['confluence_level'] == 'ULTRA_4' else "⭐ SUPER"
                print(f"  {s['date']}: {s['majority']:4} | {level} ({s['agreement_count']}/4)")
                print(f"    Votes: CALL={s['call_votes']}, PUT={s['put_votes']}, HOLD={s['hold_votes']}")
                print(f"    Entry: ${s['entry']:.2f} | Stop: ${s['stop']:.2f} | T1: ${s['target1']:.2f}")
                print("")


def load_data():
    """Load SPY data."""
    paths = [
        os.path.join(DATA_DIR, 'SPY_confluence.csv'),
        os.path.join(DATA_DIR, 'SPY.csv'),
        'SPY.csv',
    ]
    for path in paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            logger.info(f"Loaded: {path} ({len(df)} rows)")
            return df
    raise FileNotFoundError("No SPY data found")


def main():
    print("\n")
    print("=" * 70)
    print("  Q5D 4-AGENT HISTORICAL TRACKER")
    print("  Tracking 3/4 and 4/4 Confluence for Analysis")
    print("=" * 70)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        data = load_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    tracker = HistoricalTracker()
    tracker.run(data)


if __name__ == "__main__":
    main()