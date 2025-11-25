#!/usr/bin/env python3
"""
Agent 3: Hybrid Multi-Agent Voting System
==========================================

Combines signals from multiple agents using 2-out-of-3 voting.
Implements Kelly Criterion for position sizing.

Usage:
    python agent_hybrid.py
"""

import csv
import json
import logging
import os
from datetime import datetime
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REPORT_DIR = "reports"
DATA_DIR = "data"
MIN_VOTES_REQUIRED = 2  # 2 out of 3 agents must agree

# Kelly Criterion parameters
MAX_KELLY_FRACTION = 0.25
MIN_KELLY_FRACTION = 0.01
KELLY_DIVISOR = 4

def normalize_direction(direction):
    """Normalize direction to CALL or PUT."""
    direction = str(direction).upper().strip()
    if direction in ('CALL', 'LONG', 'BUY'):
        return 'CALL'
    elif direction in ('PUT', 'SHORT', 'SELL'):
        return 'PUT'
    else:
        return 'HOLD'

def load_agent_signals(date_str):
    """Load signals from all agents for a specific date."""
    signals = {
        'confluence': None,
        'gann_elliott': None,
        'dqn': None
    }
    
    # Load base confluence
    conf_path = os.path.join(REPORT_DIR, "portfolio_confluence.csv")
    if os.path.exists(conf_path):
        try:
            df = pd.read_csv(conf_path)
            df_filtered = df[df['EntryDate'] == date_str]
            if not df_filtered.empty:
                row = df_filtered.iloc[-1]
                signals['confluence'] = {
                    'direction': normalize_direction(row['Signal']),
                    'entry': float(row['EntryPrice']),
                    'stop': float(row['Stop']),
                    'target': float(row['Target1'])
                }
        except Exception as e:
            logger.warning(f"Error loading confluence: {e}")
    
    # Load Gann-Elliott
    gann_path = os.path.join(REPORT_DIR, "portfolio_gann_elliott.csv")
    if os.path.exists(gann_path):
        try:
            df = pd.read_csv(gann_path)
            df_filtered = df[df['EntryDate'] == date_str]
            if not df_filtered.empty:
                row = df_filtered.iloc[-1]
                signals['gann_elliott'] = {
                    'direction': normalize_direction(row['Signal']),
                    'entry': float(row['EntryPrice']),
                    'stop': float(row['Stop']),
                    'target': float(row['Target1'])
                }
        except Exception as e:
            logger.warning(f"Error loading Gann-Elliott: {e}")
    
    # Load DQN
    dqn_path = os.path.join(REPORT_DIR, "portfolio_dqn.csv")
    if os.path.exists(dqn_path):
        try:
            df = pd.read_csv(dqn_path)
            df_filtered = df[df['Date'] == date_str]
            if not df_filtered.empty:
                row = df_filtered.iloc[-1]
                signals['dqn'] = {
                    'direction': normalize_direction(row['Signal']),
                    'entry': float(row['EntryPrice']),
                    'stop': float(row['EntryPrice']) * 0.98,
                    'target': float(row['EntryPrice']) * 1.04
                }
        except Exception as e:
            logger.warning(f"Error loading DQN: {e}")
    
    return signals

def vote_on_signals(signals):
    """Apply 2-out-of-3 voting."""
    votes = {'CALL': [], 'PUT': [], 'HOLD': []}
    
    for agent, signal in signals.items():
        if signal:
            direction = signal['direction']
            if direction in votes:
                votes[direction].append((agent, signal))
    
    # Find direction with most votes
    max_votes = max(len(v) for v in votes.values())
    
    if max_votes < MIN_VOTES_REQUIRED:
        return None
    
    # Get winning direction
    for direction, voting_signals in votes.items():
        if len(voting_signals) == max_votes and direction != 'HOLD':
            # Calculate average entry, stop, target
            avg_entry = np.mean([s['entry'] for _, s in voting_signals])
            avg_stop = np.mean([s['stop'] for _, s in voting_signals])
            avg_target = np.mean([s['target'] for _, s in voting_signals])
            
            return {
                'direction': direction,
                'votes': len(voting_signals),
                'agents': [agent for agent, _ in voting_signals],
                'entry': avg_entry,
                'stop': avg_stop,
                'target': avg_target,
                'confidence': len(voting_signals) / 3.0
            }
    
    return None

def calculate_kelly_fraction(win_rate=0.55, avg_win=0.02, avg_loss=0.01):
    """Calculate Kelly Criterion position size."""
    if win_rate <= 0 or avg_loss <= 0:
        return MIN_KELLY_FRACTION
    
    b = avg_win / avg_loss
    p = win_rate
    q = 1 - p
    
    kelly = (p * b - q) / b
    kelly_conservative = kelly / KELLY_DIVISOR
    
    return max(MIN_KELLY_FRACTION, min(MAX_KELLY_FRACTION, kelly_conservative))

def generate_hybrid_signals():
    """Generate hybrid consensus signals."""
    logger.info("Generating hybrid consensus signals...")
    
    # Load confluence dates
    conf_path = os.path.join(REPORT_DIR, "portfolio_confluence.csv")
    if not os.path.exists(conf_path):
        logger.error("No confluence signals found")
        return
    
    df_conf = pd.read_csv(conf_path)
    dates = df_conf['EntryDate'].unique()
    
    hybrid_signals = []
    
    for date_str in dates:
        signals = load_agent_signals(date_str)
        consensus = vote_on_signals(signals)
        
        if consensus:
            kelly = calculate_kelly_fraction()
            position_size = 100000 * kelly  # Assuming $100k account
            
            hybrid_signals.append({
                'Date': date_str,
                'Symbol': 'SPY',
                'Direction': consensus['direction'],
                'Votes': consensus['votes'],
                'Agents': '+'.join(consensus['agents']),
                'Confidence': round(consensus['confidence'], 3),
                'EntryPrice': round(consensus['entry'], 2),
                'Stop': round(consensus['stop'], 2),
                'Target': round(consensus['target'], 2),
                'KellyFraction': round(kelly, 4),
                'PositionSize': round(position_size, 2),
                'Status': 'HYBRID_CONSENSUS'
            })
            
            logger.info(f"{date_str}: {consensus['direction']} with {consensus['votes']} votes")
    
    # Save hybrid signals
    if hybrid_signals:
        hybrid_df = pd.DataFrame(hybrid_signals)
        output_path = os.path.join(REPORT_DIR, "portfolio_hybrid.csv")
        hybrid_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(hybrid_signals)} hybrid signals to {output_path}")
    else:
        logger.warning("No hybrid consensus signals generated")

def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("HYBRID MULTI-AGENT SYSTEM START")
    logger.info("=" * 60)
    
    generate_hybrid_signals()
    
    logger.info("=" * 60)
    logger.info("HYBRID SYSTEM COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()