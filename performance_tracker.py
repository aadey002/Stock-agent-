"""Performance Tracker - Track trading metrics."""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data"
REPORTS_DIR = "reports"


class PerformanceTracker:
    """Track and analyze trading performance."""
    
    def __init__(self):
        self.trades = []
        self.load_data()
    
    def load_data(self):
        """Load trade data."""
        path = os.path.join(DATA_DIR, 'paper_trader.json')
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.trades = data.get('history', [])
    
    def calculate_metrics(self, starting=10000):
        """Calculate performance metrics."""
        if not self.trades:
            return self._empty()
        
        pnls = [t.get('pnl', 0) for t in self.trades]
        total = sum(pnls)
        
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        return {
            'total_trades': len(self.trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(len(wins) / len(self.trades) * 100, 1),
            'total_pnl': round(total, 2),
            'avg_pnl': round(total / len(self.trades), 2),
            'avg_win': round(sum(wins) / len(wins), 2) if wins else 0,
            'avg_loss': round(sum(losses) / len(losses), 2) if losses else 0,
            'largest_win': round(max(pnls), 2),
            'largest_loss': round(min(pnls), 2),
            'profit_factor': round(sum(wins) / abs(sum(losses)), 2) if losses else float('inf'),
            'return_pct': round(total / starting * 100, 2),
        }
    
    def _empty(self):
        """Return empty metrics."""
        return {k: 0 for k in ['total_trades', 'wins', 'losses', 'win_rate', 'total_pnl']}
    
    def print_report(self):
        """Print performance report."""
        m = self.calculate_metrics()
        
        print("\n" + "=" * 60)
        print("  PERFORMANCE REPORT")
        print("=" * 60)
        print(f"  Total Trades:   {m['total_trades']}")
        print(f"  Win Rate:       {m['win_rate']:.1f}%")
        print(f"  Total P&L:      ${m['total_pnl']:,.2f}")
        print(f"  Avg P&L:        ${m['avg_pnl']:,.2f}")
        print(f"  Avg Win:        ${m['avg_win']:,.2f}")
        print(f"  Avg Loss:       ${m['avg_loss']:,.2f}")
        print(f"  Profit Factor:  {m['profit_factor']:.2f}")
        print(f"  Return:         {m['return_pct']:+.1f}%")
        print("=" * 60)


if __name__ == "__main__":
    tracker = PerformanceTracker()
    tracker.print_report()