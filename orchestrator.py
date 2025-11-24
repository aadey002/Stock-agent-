#!/usr/bin/env python3
"""
Q5D Unified Confluence Orchestrator
====================================

KEY FEATURES:
1. Independent Validation - Two different methodologies
2. Complete Transparency - See both outputs, understand why
3. Risk Management - Conservative sizing, wider stops, 2:1 R:R
4. Automated Daily Analysis - GitHub Actions integration

OUTPUTS:
- reports/portfolio_confluence.csv       [System A trades]
- reports/super_confluence_signals.csv   [Final approved trades]
- reports/playbook_comparison.csv        [Side-by-side comparison]
- reports/super_confluence_tracking.csv  [Full tracking data]
- reports/agreement_analysis.json        [Agreement statistics]
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


class RiskManager:
    """
    Risk Management Module
    - Conservative position sizing
    - Wider stops (safer of both)
    - Minimum 2:1 R:R ratio enforced
    """
    
    def __init__(self, min_rr_ratio=2.0, max_risk_pct=0.02):
        self.min_rr_ratio = min_rr_ratio
        self.max_risk_pct = max_risk_pct
    
    def validate_trade(self, entry, stop, target1):
        """Validate trade meets minimum R:R requirement."""
        risk = abs(entry - stop)
        reward = abs(target1 - entry)
        
        if risk == 0:
            return False, 0, "Zero risk - invalid"
        
        rr_ratio = reward / risk
        
        if rr_ratio < self.min_rr_ratio:
            return False, rr_ratio, f"R:R {rr_ratio:.1f} < {self.min_rr_ratio} minimum"
        
        return True, rr_ratio, f"R:R {rr_ratio:.1f} meets minimum"
    
    def get_conservative_levels(self, sig_a, sig_b, direction):
        """
        Get conservative levels using safer of both systems.
        - Stop: Use wider (more protective) stop
        - Targets: Use closer (more achievable) targets
        """
        entry = (sig_a['entry'] + sig_b['entry']) / 2
        
        if direction == 'CALL':
            # Wider stop = lower price for CALL
            stop = min(sig_a['stop'], sig_b['stop'])
            # Closer targets = lower price for CALL
            t1 = min(sig_a['target1'], sig_b['target1'])
            t2 = min(sig_a['target2'], sig_b['target2'])
            t3 = min(sig_a['target3'], sig_b['target3'])
        else:  # PUT
            # Wider stop = higher price for PUT
            stop = max(sig_a['stop'], sig_b['stop'])
            # Closer targets = higher price for PUT
            t1 = max(sig_a['target1'], sig_b['target1'])
            t2 = max(sig_a['target2'], sig_b['target2'])
            t3 = max(sig_a['target3'], sig_b['target3'])
        
        return entry, stop, t1, t2, t3
    
    def calculate_position_size(self, account_balance, entry, stop):
        """Calculate position size based on risk."""
        risk_per_share = abs(entry - stop)
        if risk_per_share == 0:
            return 0
        
        risk_amount = account_balance * self.max_risk_pct
        shares = int(risk_amount / risk_per_share)
        
        # Cap at 10% of account
        max_shares = int(account_balance * 0.10 / entry)
        return min(shares, max_shares)


class SystemA:
    """
    System A: Technical Confluence
    
    Methodology:
    - SMA Crossovers (Fast/Slow)
    - Price Confluence Levels
    - Time Confluence Windows
    - Trend Bias
    
    NO SHARED INDICATORS with System B
    """
    
    def __init__(self):
        self.name = "Confluence"
        self.methodology = "SMA + Technical Confluence"
    
    def generate_signal(self, data, index):
        if index < 50:
            return self._hold_signal()
        
        row = data.iloc[index]
        prev = data.iloc[index - 1]
        
        close = row['Close']
        fast = row.get('FastSMA', close)
        slow = row.get('SlowSMA', close)
        prev_fast = prev.get('FastSMA', close)
        prev_slow = prev.get('SlowSMA', close)
        atr = row.get('ATR', close * 0.02)
        
        # Bias
        bias = row.get('Bias', 'NEUTRAL')
        if isinstance(bias, (int, float)):
            bias = 'BULLISH' if bias > 0 else 'BEARISH' if bias < 0 else 'NEUTRAL'
        
        # Confluence scores
        price_conf = int(row.get('PriceConfluence', 0))
        time_conf = int(row.get('TimeConfluence', 0))
        total_conf = price_conf + time_conf
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        # Crossover detection
        bullish_cross = prev_fast <= prev_slow and fast > slow
        bearish_cross = prev_fast >= prev_slow and fast < slow
        
        # CALL conditions
        if bullish_cross:
            signal = 'CALL'
            confidence = 0.7
            reasons.append('Bullish SMA crossover')
        elif fast > slow and bias == 'BULLISH' and total_conf >= 2:
            signal = 'CALL'
            confidence = 0.6 + (total_conf * 0.05)
            reasons.append('Bullish trend alignment')
        
        # PUT conditions
        elif bearish_cross:
            signal = 'PUT'
            confidence = 0.7
            reasons.append('Bearish SMA crossover')
        elif fast < slow and bias == 'BEARISH' and total_conf >= 2:
            signal = 'PUT'
            confidence = 0.6 + (total_conf * 0.05)
            reasons.append('Bearish trend alignment')
        
        # Add confluence reasons
        if price_conf > 0:
            reasons.append(f'Price confluence: {price_conf}')
        if time_conf > 0:
            reasons.append(f'Time confluence: {time_conf}')
        if bias != 'NEUTRAL':
            reasons.append(f'{bias} bias')
        
        # Calculate levels
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
            'confidence': min(0.95, round(confidence, 2)),
            'entry': round(close, 2),
            'stop': round(stop, 2),
            'target1': round(t1, 2),
            'target2': round(t2, 2),
            'target3': round(t3, 2),
            'reasons': reasons,
            'indicators': {
                'fast_sma': round(fast, 2),
                'slow_sma': round(slow, 2),
                'bias': bias,
                'price_conf': price_conf,
                'time_conf': time_conf,
            }
        }
    
    def _hold_signal(self):
        return {
            'signal': 'HOLD',
            'confidence': 0,
            'entry': 0, 'stop': 0,
            'target1': 0, 'target2': 0, 'target3': 0,
            'reasons': ['Insufficient data'],
            'indicators': {}
        }


class SystemB:
    """
    System B: Gann-Elliott Wave Analysis
    
    Methodology:
    - Elliott Wave Position
    - Fibonacci Retracements
    - Gann Square of 9 Levels
    - Geometric Price Relationships
    
    NO SHARED INDICATORS with System A
    """
    
    def __init__(self):
        self.name = "GannElliott"
        self.methodology = "Wave Structure + Fibonacci + Gann"
    
    def generate_signal(self, data, index):
        if index < 50:
            return self._hold_signal()
        
        row = data.iloc[index]
        lookback = data.iloc[max(0, index-50):index+1]
        
        close = row['Close']
        high_52 = lookback['High'].max()
        low_52 = lookback['Low'].min()
        price_range = high_52 - low_52
        
        if price_range == 0:
            return self._hold_signal()
        
        # Position in range (0-1)
        range_pos = (close - low_52) / price_range
        
        # Fibonacci levels
        fib_382 = low_52 + price_range * 0.382
        fib_500 = low_52 + price_range * 0.500
        fib_618 = low_52 + price_range * 0.618
        
        # Trend from geometric mean
        geo_level = row.get('GeoLevel', np.sqrt(high_52 * low_52))
        phi_level = row.get('PhiLevel', low_52 * 1.618)
        
        # Wave detection
        wave_info = self._detect_wave(lookback)
        trend = wave_info['trend']
        wave = wave_info['wave']
        
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        # Distance to Fib levels
        dist_382 = abs(close - fib_382) / close
        dist_500 = abs(close - fib_500) / close
        dist_618 = abs(close - fib_618) / close
        near_fib = min(dist_382, dist_500, dist_618) < 0.02
        
        # CALL: Wave 2/4 correction in uptrend at Fib support
        if trend == 'UP' and wave in [2, 4] and near_fib:
            signal = 'CALL'
            confidence = 0.75
            reasons.append(f'Wave {wave} correction at Fib support')
            reasons.append('Uptrend continuation setup')
        
        # CALL: Above geometric level in uptrend
        elif trend == 'UP' and close > geo_level and range_pos < 0.7:
            signal = 'CALL'
            confidence = 0.60
            reasons.append('Above Gann geometric level')
            reasons.append('Room to run (range < 70%)')
        
        # PUT: Wave 2/4 correction in downtrend at Fib resistance
        elif trend == 'DOWN' and wave in [2, 4] and near_fib:
            signal = 'PUT'
            confidence = 0.75
            reasons.append(f'Wave {wave} correction at Fib resistance')
            reasons.append('Downtrend continuation setup')
        
        # PUT: Below geometric level in downtrend
        elif trend == 'DOWN' and close < geo_level and range_pos > 0.3:
            signal = 'PUT'
            confidence = 0.60
            reasons.append('Below Gann geometric level')
            reasons.append('Room to fall (range > 30%)')
        
        # Add wave info to reasons
        if wave > 0:
            reasons.append(f'Elliott Wave {wave} ({wave_info["phase"]})')
        reasons.append(f'Trend: {trend}')
        
        # Calculate levels using Gann
        atr = row.get('ATR', close * 0.02)
        
        if signal == 'CALL':
            stop = max(low_52, close - 2.5 * atr)
            t1 = close + 1.5 * 2 * atr
            t2 = min(fib_618, close + 2.5 * 2 * atr)
            t3 = min(phi_level, close + 4.0 * 2 * atr)
        elif signal == 'PUT':
            stop = min(high_52, close + 2.5 * atr)
            t1 = close - 1.5 * 2 * atr
            t2 = max(fib_382, close - 2.5 * 2 * atr)
            t3 = max(geo_level * 0.9, close - 4.0 * 2 * atr)
        else:
            stop = t1 = t2 = t3 = close
        
        return {
            'signal': signal,
            'confidence': min(0.95, round(confidence, 2)),
            'entry': round(close, 2),
            'stop': round(stop, 2),
            'target1': round(t1, 2),
            'target2': round(t2, 2),
            'target3': round(t3, 2),
            'reasons': reasons,
            'indicators': {
                'wave': wave,
                'trend': trend,
                'range_position': round(range_pos, 3),
                'fib_382': round(fib_382, 2),
                'fib_618': round(fib_618, 2),
                'geo_level': round(geo_level, 2),
            }
        }
    
    def _detect_wave(self, data):
        """Detect Elliott Wave position."""
        if len(data) < 20:
            return {'wave': 0, 'trend': 'NEUTRAL', 'phase': 'unknown'}
        
        closes = data['Close'].values
        sma20 = np.mean(closes[-20:])
        sma50 = np.mean(closes)
        
        if sma20 > sma50 * 1.01:
            trend = 'UP'
        elif sma20 < sma50 * 0.99:
            trend = 'DOWN'
        else:
            trend = 'NEUTRAL'
        
        # Count swing points for wave estimate
        highs = data['High'].values
        lows = data['Low'].values
        
        swing_count = 0
        for i in range(5, len(data) - 5):
            if highs[i] == max(highs[max(0,i-5):i+6]):
                swing_count += 1
            if lows[i] == min(lows[max(0,i-5):i+6]):
                swing_count += 1
        
        wave = (swing_count % 5) + 1
        phase = 'impulse' if wave in [1, 3, 5] else 'corrective'
        
        return {'wave': wave, 'trend': trend, 'phase': phase}
    
    def _hold_signal(self):
        return {
            'signal': 'HOLD',
            'confidence': 0,
            'entry': 0, 'stop': 0,
            'target1': 0, 'target2': 0, 'target3': 0,
            'reasons': ['Insufficient data'],
            'indicators': {}
        }


class UnifiedOrchestrator:
    """
    Unified Confluence Orchestrator
    
    Combines System A and System B with:
    - Independent validation (no shared indicators)
    - Complete transparency (full logging)
    - Conservative risk management
    - Automated analysis output
    """
    
    def __init__(self):
        self.system_a = SystemA()
        self.system_b = SystemB()
        self.risk_mgr = RiskManager(min_rr_ratio=2.0)
        
        self.all_signals = []
        self.super_signals = []
        self.portfolio_a = []
        
        self.stats = {
            'total_bars': 0,
            'system_a_signals': 0,
            'system_b_signals': 0,
            'agreements': 0,
            'disagreements': 0,
            'both_hold': 0,
            'rejected_rr': 0,
        }
    
    def process_bar(self, data, index):
        """Process single bar through both systems."""
        sig_a = self.system_a.generate_signal(data, index)
        sig_b = self.system_b.generate_signal(data, index)
        
        row = data.iloc[index]
        date = row.get('Date', str(index))
        close = row['Close']
        
        a_action = sig_a['signal']
        b_action = sig_b['signal']
        
        self.stats['total_bars'] += 1
        
        if a_action != 'HOLD':
            self.stats['system_a_signals'] += 1
            # Add to portfolio A
            self.portfolio_a.append({
                'Symbol': 'SPY',
                'Signal': a_action,
                'EntryDate': date,
                'ExitDate': '',
                'EntryPrice': sig_a['entry'],
                'ExitPrice': 0,
                'PNL': 0,
                'EntryLow': row['Low'],
                'EntryHigh': row['High'],
                'Stop': sig_a['stop'],
                'Target1': sig_a['target1'],
                'Target2': sig_a['target2'],
                'ExpiryDate': '',
                'Status': 'OPEN'
            })
        
        if b_action != 'HOLD':
            self.stats['system_b_signals'] += 1
        
        # Check agreement
        if a_action == b_action:
            if a_action == 'HOLD':
                agreement = 'BOTH_HOLD'
                self.stats['both_hold'] += 1
                final_signal = 'HOLD'
                final_conf = 0
                approved = False
                rejection_reason = 'Both systems hold'
            else:
                agreement = 'AGREE'
                self.stats['agreements'] += 1
                
                # Get conservative levels
                entry, stop, t1, t2, t3 = self.risk_mgr.get_conservative_levels(
                    sig_a, sig_b, a_action
                )
                
                # Validate R:R ratio
                valid, rr, rr_msg = self.risk_mgr.validate_trade(entry, stop, t1)
                
                if valid:
                    final_signal = a_action
                    final_conf = (sig_a['confidence'] + sig_b['confidence']) / 2
                    approved = True
                    rejection_reason = ''
                else:
                    final_signal = 'HOLD'
                    final_conf = 0
                    approved = False
                    rejection_reason = rr_msg
                    self.stats['rejected_rr'] += 1
        else:
            agreement = 'DISAGREE'
            self.stats['disagreements'] += 1
            final_signal = 'HOLD'
            final_conf = 0
            approved = False
            rejection_reason = f'Disagreement: A={a_action}, B={b_action}'
            entry = close
            stop = t1 = t2 = t3 = close
        
        # Build result
        if agreement == 'AGREE' and approved:
            entry, stop, t1, t2, t3 = self.risk_mgr.get_conservative_levels(
                sig_a, sig_b, final_signal
            )
        else:
            entry = close
            stop = sig_a['stop'] if a_action != 'HOLD' else sig_b['stop'] if b_action != 'HOLD' else close
            t1 = sig_a['target1'] if a_action != 'HOLD' else sig_b['target1'] if b_action != 'HOLD' else close
            t2 = sig_a['target2'] if a_action != 'HOLD' else sig_b['target2'] if b_action != 'HOLD' else close
            t3 = sig_a['target3'] if a_action != 'HOLD' else sig_b['target3'] if b_action != 'HOLD' else close
        
        result = {
            'date': str(date),
            'close': close,
            
            # System A
            'system_a': a_action,
            'a_confidence': sig_a['confidence'],
            'a_reasons': ' | '.join(sig_a['reasons']),
            'a_stop': sig_a['stop'],
            'a_target1': sig_a['target1'],
            
            # System B
            'system_b': b_action,
            'b_confidence': sig_b['confidence'],
            'b_reasons': ' | '.join(sig_b['reasons']),
            'b_wave': sig_b['indicators'].get('wave', 0),
            'b_trend': sig_b['indicators'].get('trend', ''),
            
            # Agreement
            'agreement': agreement,
            'approved': approved,
            'rejection_reason': rejection_reason,
            
            # Final
            'final': final_signal,
            'confidence': round(final_conf, 2),
            'entry': round(entry, 2),
            'stop': round(stop, 2),
            'target1': round(t1, 2),
            'target2': round(t2, 2),
            'target3': round(t3, 2),
        }
        
        self.all_signals.append(result)
        
        if approved and final_signal != 'HOLD':
            self.super_signals.append(result)
        
        return result
    
    def run(self, data):
        """Run orchestrator on full dataset."""
        logger.info("=" * 70)
        logger.info("  Q5D UNIFIED CONFLUENCE ORCHESTRATOR")
        logger.info("=" * 70)
        logger.info(f"  Processing {len(data)} bars...")
        logger.info("")
        
        for i in range(len(data)):
            self.process_bar(data, i)
            if (i + 1) % 100 == 0:
                logger.info(f"  Processed {i + 1}/{len(data)} bars...")
        
        self._save_all_reports()
        self._print_summary()
        
        return self.stats
    
    def _save_all_reports(self):
        """Save all output reports."""
        
        # 1. Portfolio Confluence (System A trades)
        if self.portfolio_a:
            df = pd.DataFrame(self.portfolio_a)
            path = os.path.join(REPORTS_DIR, 'portfolio_confluence.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path} ({len(df)} trades)")
        
        # 2. Super Confluence Signals (approved trades)
        if self.super_signals:
            df = pd.DataFrame(self.super_signals)
            path = os.path.join(REPORTS_DIR, 'super_confluence_signals.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path} ({len(df)} signals)")
        
        # 3. Playbook Comparison (side-by-side)
        if self.all_signals:
            df = pd.DataFrame(self.all_signals)
            path = os.path.join(REPORTS_DIR, 'playbook_comparison.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path}")
        
        # 4. Full Tracking Data
        if self.all_signals:
            df = pd.DataFrame(self.all_signals)
            path = os.path.join(REPORTS_DIR, 'super_confluence_tracking.csv')
            df.to_csv(path, index=False)
            logger.info(f"  Saved: {path}")
        
        # 5. Agreement Analysis (JSON)
        calls = len([s for s in self.super_signals if s['final'] == 'CALL'])
        puts = len([s for s in self.super_signals if s['final'] == 'PUT'])
        
        active_signals = self.stats['system_a_signals'] + self.stats['system_b_signals']
        agreement_rate = (self.stats['agreements'] / max(1, self.stats['agreements'] + self.stats['disagreements'])) * 100
        
        analysis = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.stats,
            'agreement_rate': round(agreement_rate, 1),
            'super_confluence': {
                'total': len(self.super_signals),
                'calls': calls,
                'puts': puts,
                'avg_confidence': round(
                    np.mean([s['confidence'] for s in self.super_signals]) if self.super_signals else 0, 2
                ),
            },
            'risk_management': {
                'min_rr_ratio': self.risk_mgr.min_rr_ratio,
                'rejected_for_rr': self.stats['rejected_rr'],
                'max_risk_pct': self.risk_mgr.max_risk_pct,
            },
            'methodologies': {
                'system_a': self.system_a.methodology,
                'system_b': self.system_b.methodology,
            }
        }
        
        path = os.path.join(REPORTS_DIR, 'agreement_analysis.json')
        with open(path, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"  Saved: {path}")
    
    def _print_summary(self):
        """Print summary to console."""
        calls = len([s for s in self.super_signals if s['final'] == 'CALL'])
        puts = len([s for s in self.super_signals if s['final'] == 'PUT'])
        
        print("\n")
        print("=" * 70)
        print("  Q5D ORCHESTRATOR - SUMMARY")
        print("=" * 70)
        print("")
        print("  PROCESSING STATS")
        print(f"    Total Bars:           {self.stats['total_bars']}")
        print(f"    System A Signals:     {self.stats['system_a_signals']}")
        print(f"    System B Signals:     {self.stats['system_b_signals']}")
        print("")
        print("  AGREEMENT ANALYSIS")
        print(f"    Agreements:           {self.stats['agreements']}")
        print(f"    Disagreements:        {self.stats['disagreements']}")
        print(f"    Both Hold:            {self.stats['both_hold']}")
        print(f"    Rejected (R:R < 2):   {self.stats['rejected_rr']}")
        print("")
        print("  SUPER CONFLUENCE (APPROVED TRADES)")
        print(f"    Total Approved:       {len(self.super_signals)}")
        print(f"    CALL Signals:         {calls}")
        print(f"    PUT Signals:          {puts}")
        if self.super_signals:
            avg_conf = np.mean([s['confidence'] for s in self.super_signals])
            print(f"    Avg Confidence:       {avg_conf:.0%}")
        print("")
        print("  OUTPUT FILES")
        print("    reports/portfolio_confluence.csv")
        print("    reports/super_confluence_signals.csv")
        print("    reports/playbook_comparison.csv")
        print("    reports/super_confluence_tracking.csv")
        print("    reports/agreement_analysis.json")
        print("=" * 70)
        
        # Show recent approved signals
        if self.super_signals:
            print("\n  RECENT APPROVED SIGNALS (Last 5)")
            print("  " + "-" * 60)
            for s in self.super_signals[-5:]:
                print(f"  {s['date']}: {s['final']} @ ${s['close']:.2f}")
                print(f"    Confidence: {s['confidence']:.0%}")
                print(f"    Stop: ${s['stop']:.2f} | T1: ${s['target1']:.2f} | T2: ${s['target2']:.2f}")
                print(f"    System A: {s['a_reasons']}")
                print(f"    System B: {s['b_reasons']}")
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
    
    raise FileNotFoundError("No SPY data found. Run fetch_data.py first.")


def main():
    """Main entry point."""
    print("\n")
    print("=" * 70)
    print("  Q5D UNIFIED CONFLUENCE ORCHESTRATOR")
    print("  Independent Validation + Risk Management + Automation")
    print("=" * 70)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("")
    
    try:
        data = load_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    orchestrator = UnifiedOrchestrator()
    orchestrator.run(data)


if __name__ == "__main__":
    main()