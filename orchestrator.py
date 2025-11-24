#!/usr/bin/env python3
"""
Unified Confluence Orchestrator
================================
Super Confluence: Only trades when BOTH systems agree.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = "data"
REPORTS_DIR = "reports"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


class SystemA:
    """System A: Confluence Agent (SMA + Technical)"""
    
    def __init__(self):
        self.name = "Confluence"
    
    def generate_signal(self, data, index):
        if index < 50:
            return {'signal': 'HOLD', 'confidence': 0, 'stop': 0, 'target1': 0, 'target2': 0, 'target3': 0, 'reasons': []}
        
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
        
        price_conf = row.get('PriceConfluence', 0)
        time_conf = row.get('TimeConfluence', 0)
        total_conf = price_conf + time_conf
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        bullish_cross = prev_fast <= prev_slow and fast > slow
        bearish_cross = prev_fast >= prev_slow and fast < slow
        
        if bullish_cross or (fast > slow and bias == 'BULLISH' and total_conf >= 1):
            signal = 'CALL'
            confidence = min(0.9, 0.5 + total_conf * 0.15)
            reasons.append('Bullish SMA')
            if bullish_cross:
                reasons.append('Crossover')
        elif bearish_cross or (fast < slow and bias == 'BEARISH' and total_conf >= 1):
            signal = 'PUT'
            confidence = min(0.9, 0.5 + total_conf * 0.15)
            reasons.append('Bearish SMA')
            if bearish_cross:
                reasons.append('Crossover')
        
        if signal == 'CALL':
            stop = close - 2 * atr
            t1 = close + 1.5 * 2 * atr
            t2 = close + 2.5 * 2 * atr
            t3 = close + 4.0 * 2 * atr
        elif signal == 'PUT':
            stop = close + 2 * atr
            t1 = close - 1.5 * 2 * atr
            t2 = close - 2.5 * 2 * atr
            t3 = close - 4.0 * 2 * atr
        else:
            stop = t1 = t2 = t3 = close
        
        return {
            'signal': signal,
            'confidence': round(confidence, 2),
            'stop': round(stop, 2),
            'target1': round(t1, 2),
            'target2': round(t2, 2),
            'target3': round(t3, 2),
            'reasons': reasons,
        }


class SystemB:
    """System B: Gann-Elliott Wave System"""
    
    def __init__(self):
        self.name = "GannElliott"
    
    def generate_signal(self, data, index):
        if index < 50:
            return {'signal': 'HOLD', 'confidence': 0, 'stop': 0, 'target1': 0, 'target2': 0, 'target3': 0, 'reasons': [], 'wave': 0, 'trend': 'NEUTRAL'}
        
        row = data.iloc[index]
        lookback = data.iloc[max(0, index-50):index+1]
        
        close = row['Close']
        high_52 = lookback['High'].max()
        low_52 = lookback['Low'].min()
        price_range = high_52 - low_52
        
        if price_range == 0:
            return {'signal': 'HOLD', 'confidence': 0, 'stop': close, 'target1': close, 'target2': close, 'target3': close, 'reasons': [], 'wave': 0, 'trend': 'NEUTRAL'}
        
        range_pos = (close - low_52) / price_range
        
        # Fib levels
        fib_382 = low_52 + price_range * 0.382
        fib_500 = low_52 + price_range * 0.500
        fib_618 = low_52 + price_range * 0.618
        
        # Trend
        sma20 = lookback['Close'].tail(20).mean()
        sma50 = lookback['Close'].mean()
        trend = 'UP' if sma20 > sma50 else 'DOWN' if sma20 < sma50 else 'NEUTRAL'
        
        # Wave estimate
        wave = (index % 5) + 1
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        # Near Fib support in uptrend
        if trend == 'UP':
            dist_382 = abs(close - fib_382) / close
            dist_500 = abs(close - fib_500) / close
            dist_618 = abs(close - fib_618) / close
            
            if dist_382 < 0.02 or dist_500 < 0.02 or dist_618 < 0.02:
                if wave in [2, 4]:
                    signal = 'CALL'
                    confidence = 0.7
                    reasons.append(f'Wave {wave} at Fib support')
        
        # Near Fib resistance in downtrend  
        elif trend == 'DOWN':
            dist_382 = abs(close - fib_382) / close
            dist_500 = abs(close - fib_500) / close
            
            if dist_382 < 0.02 or dist_500 < 0.02:
                if wave in [2, 4]:
                    signal = 'PUT'
                    confidence = 0.7
                    reasons.append(f'Wave {wave} at Fib resistance')
        
        # Momentum
        if len(lookback) >= 10:
            momentum = (close - lookback.iloc[-10]['Close']) / lookback.iloc[-10]['Close']
            if abs(momentum) > 0.02 and signal == 'HOLD':
                if momentum > 0 and range_pos < 0.7:
                    signal = 'CALL'
                    confidence = 0.55
                    reasons.append('Upward momentum')
                elif momentum < 0 and range_pos > 0.3:
                    signal = 'PUT'
                    confidence = 0.55
                    reasons.append('Downward momentum')
        
        atr = row.get('ATR', close * 0.02)
        
        if signal == 'CALL':
            stop = max(low_52, close - 2 * atr)
            t1 = close + 1.5 * 2 * atr
            t2 = close + 2.5 * 2 * atr
            t3 = close + 4.0 * 2 * atr
        elif signal == 'PUT':
            stop = min(high_52, close + 2 * atr)
            t1 = close - 1.5 * 2 * atr
            t2 = close - 2.5 * 2 * atr
            t3 = close - 4.0 * 2 * atr
        else:
            stop = t1 = t2 = t3 = close
        
        return {
            'signal': signal,
            'confidence': round(confidence, 2),
            'stop': round(stop, 2),
            'target1': round(t1, 2),
            'target2': round(t2, 2),
            'target3': round(t3, 2),
            'reasons': reasons,
            'wave': wave,
            'trend': trend,
        }


class UnifiedOrchestrator:
    """Combines System A and System B. Only trades when BOTH agree."""
    
    def __init__(self):
        self.system_a = SystemA()
        self.system_b = SystemB()
        self.all_signals = []
        self.super_signals = []
        self.stats = {'total': 0, 'a_signals': 0, 'b_signals': 0, 'agree': 0, 'disagree': 0, 'both_hold': 0}
    
    def process_bar(self, data, index):
        sig_a = self.system_a.generate_signal(data, index)
        sig_b = self.system_b.generate_signal(data, index)
        
        row = data.iloc[index]
        date = row.get('Date', index)
        close = row['Close']
        
        a_action = sig_a['signal']
        b_action = sig_b['signal']
        
        self.stats['total'] += 1
        if a_action != 'HOLD':
            self.stats['a_signals'] += 1
        if b_action != 'HOLD':
            self.stats['b_signals'] += 1
        
        if a_action == b_action:
            if a_action == 'HOLD':
                agreement = 'BOTH_HOLD'
                self.stats['both_hold'] += 1
                final = 'HOLD'
                conf = 0
            else:
                agreement = 'AGREE'
                self.stats['agree'] += 1
                final = a_action
                conf = (sig_a['confidence'] + sig_b['confidence']) / 2
        else:
            agreement = 'DISAGREE'
            self.stats['disagree'] += 1
            final = 'HOLD'
            conf = 0
        
        # Get levels
        if agreement == 'AGREE':
            stop = (sig_a['stop'] + sig_b['stop']) / 2
            t1 = (sig_a['target1'] + sig_b['target1']) / 2
            t2 = (sig_a['target2'] + sig_b['target2']) / 2
            t3 = (sig_a['target3'] + sig_b['target3']) / 2
        elif a_action != 'HOLD':
            stop, t1, t2, t3 = sig_a['stop'], sig_a['target1'], sig_a['target2'], sig_a['target3']
        elif b_action != 'HOLD':
            stop, t1, t2, t3 = sig_b['stop'], sig_b['target1'], sig_b['target2'], sig_b['target3']
        else:
            stop = t1 = t2 = t3 = close
        
        result = {
            'date': str(date),
            'close': close,
            'system_a': a_action,
            'a_conf': sig_a['confidence'],
            'a_reasons': ', '.join(sig_a.get('reasons', [])),
            'system_b': b_action,
            'b_conf': sig_b['confidence'],
            'b_reasons': ', '.join(sig_b.get('reasons', [])),
            'b_wave': sig_b.get('wave', 0),
            'b_trend': sig_b.get('trend', ''),
            'agreement': agreement,
            'final': final,
            'confidence': round(conf, 2),
            'entry': round(close, 2),
            'stop': round(stop, 2),
            'target1': round(t1, 2),
            'target2': round(t2, 2),
            'target3': round(t3, 2),
        }
        
        self.all_signals.append(result)
        if agreement == 'AGREE':
            self.super_signals.append(result)
        
        return result
    
    def run(self, data):
        logger.info("=" * 60)
        logger.info("  UNIFIED CONFLUENCE ORCHESTRATOR")
        logger.info("=" * 60)
        logger.info(f"  Processing {len(data)} bars...")
        
        for i in range(len(data)):
            self.process_bar(data, i)
        
        self._save_reports()
        self._print_summary()
        
        return self.stats
    
    def _save_reports(self):
        if self.super_signals:
            df = pd.DataFrame(self.super_signals)
            path = os.path.join(REPORTS_DIR, 'super_confluence_signals.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path} ({len(df)} signals)")
        
        if self.all_signals:
            df = pd.DataFrame(self.all_signals)
            path = os.path.join(REPORTS_DIR, 'playbook_comparison.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path}")
        
        analysis = {
            'generated': datetime.now().isoformat(),
            'stats': self.stats,
            'super_signals': len(self.super_signals),
            'calls': len([s for s in self.super_signals if s['final'] == 'CALL']),
            'puts': len([s for s in self.super_signals if s['final'] == 'PUT']),
        }
        path = os.path.join(REPORTS_DIR, 'agreement_analysis.json')
        with open(path, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"  Saved: {path}")
    
    def _print_summary(self):
        print("\n" + "=" * 60)
        print("  ORCHESTRATOR SUMMARY")
        print("=" * 60)
        print(f"  Total Bars:        {self.stats['total']}")
        print(f"  System A Signals:  {self.stats['a_signals']}")
        print(f"  System B Signals:  {self.stats['b_signals']}")
        print(f"  Agreements:        {self.stats['agree']}")
        print(f"  Disagreements:     {self.stats['disagree']}")
        print(f"  Both Hold:         {self.stats['both_hold']}")
        print("")
        print(f"  SUPER CONFLUENCE SIGNALS: {len(self.super_signals)}")
        calls = len([s for s in self.super_signals if s['final'] == 'CALL'])
        puts = len([s for s in self.super_signals if s['final'] == 'PUT'])
        print(f"    CALL: {calls}")
        print(f"    PUT:  {puts}")
        print("=" * 60)
        
        if self.super_signals:
            print("\n  RECENT SIGNALS (Last 5):")
            for s in self.super_signals[-5:]:
                print(f"  {s['date']}: {s['final']} @ ${s['close']:.2f} | Conf: {s['confidence']:.0%}")
                print(f"    Stop: ${s['stop']:.2f} | T1: ${s['target1']:.2f} | T2: ${s['target2']:.2f}")


def load_data():
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
    print("\n" + "=" * 60)
    print("  Q5D UNIFIED CONFLUENCE ORCHESTRATOR")
    print("  Super Confluence Trading System")
    print("=" * 60)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    try:
        data = load_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.info("Run fetch_data.py first")
        return
    
    orchestrator = UnifiedOrchestrator()
    orchestrator.run(data)


if __name__ == "__main__":
    main()