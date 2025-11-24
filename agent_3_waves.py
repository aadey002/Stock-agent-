#!/usr/bin/env python3
"""
3-Wave Profit Target Agent
==========================
Generates signals with 3 profit targets.
"""

import logging
import os
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = "data"
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

def calculate_targets(entry, stop, signal_type):
    """Calculate 3 profit targets."""
    risk = abs(entry - stop)
    
    if signal_type == "CALL":
        return (
            entry + (risk * 1.5),  # Target1
            entry + (risk * 2.5),  # Target2
            entry + (risk * 4.0)   # Target3
        )
    else:  # PUT
        return (
            entry - (risk * 1.5),
            entry - (risk * 2.5),
            entry - (risk * 4.0)
        )

def main():
    logger.info("=" * 60)
    logger.info("3-WAVE AGENT START")
    logger.info("=" * 60)
    
    # Load data
    data_path = os.path.join(DATA_DIR, "SPY_confluence.csv")
    if not os.path.exists(data_path):
        logger.error(f"File not found: {data_path}")
        logger.info("Run agent.py first!")
        return
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} bars")
    
    signals = []
    
    for idx, row in df.iterrows():
        price_conf = row.get('PriceConfluence', 0)
        time_conf = row.get('TimeConfluence', 0)
        
        if price_conf < 2 and time_conf < 2:
            continue
        
        close = float(row['Close'])
        atr = float(row['ATR'])
        bias = row.get('Bias', 'NEUTRAL')
        
        signal = None
        if bias == 'BULLISH':
            signal = 'CALL'
        elif bias == 'BEARISH':
            signal = 'PUT'
        
        if not signal:
            continue
        
        entry = close
        stop = close - (atr * 2.0) if signal == 'CALL' else close + (atr * 2.0)
        
        target1, target2, target3 = calculate_targets(entry, stop, signal)
        
        risk = abs(entry - stop)
        
        signals.append({
            'Date': row['Date'],
            'Symbol': 'SPY',
            'Direction': signal,
            'EntryPrice': round(entry, 2),
            'Stop': round(stop, 2),
            'Target1': round(target1, 2),
            'Target2': round(target2, 2),
            'Target3': round(target3, 2),
            'Wave1_RR': round(abs(target1 - entry) / risk, 2),
            'Wave2_RR': round(abs(target2 - entry) / risk, 2),
            'Wave3_RR': round(abs(target3 - entry) / risk, 2),
            'Status': '3_WAVE'
        })
        
        logger.info(f"{row['Date']}: {signal} @ ${entry:.2f} -> T1:${target1:.2f} T2:${target2:.2f} T3:${target3:.2f}")
    
    if signals:
        df_signals = pd.DataFrame(signals)
        output = os.path.join(REPORT_DIR, "portfolio_3_waves.csv")
        df_signals.to_csv(output, index=False)
        logger.info(f"Saved {len(signals)} signals to {output}")
        
        print("\n" + "=" * 60)
        print("MOST RECENT SIGNAL:")
        print("=" * 60)
        last = signals[-1]
        print(f"Date:      {last['Date']}")
        print(f"Direction: {last['Direction']}")
        print(f"Entry:     ${last['EntryPrice']}")
        print(f"Stop:      ${last['Stop']}")
        print(f"Target1:   ${last['Target1']} ({last['Wave1_RR']}R)")
        print(f"Target2:   ${last['Target2']} ({last['Wave2_RR']}R)")
        print(f"Target3:   ${last['Target3']} ({last['Wave3_RR']}R)")
        print("=" * 60)
    else:
        logger.warning("No signals generated")
    
    logger.info("=" * 60)
    logger.info("3-WAVE AGENT COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()