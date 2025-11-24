"""Paper Trader - Simulates trading with virtual money."""

import os
import json
import pandas as pd
from datetime import datetime

DATA_DIR = "data"
REPORTS_DIR = "reports"


class PaperTrader:
    """Paper trading simulator."""
    
    def __init__(self, starting_balance=10000):
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.positions = []
        self.history = []
        self.load_state()
    
    def open_position(self, signal):
        """Open a new position."""
        position = {
            'id': f"POS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'symbol': signal.get('symbol', 'SPY'),
            'direction': signal.get('final', signal.get('signal', 'CALL')),
            'entry': signal.get('entry', signal.get('close', 0)),
            'stop': signal.get('stop', 0),
            'target1': signal.get('target1', 0),
            'target2': signal.get('target2', 0),
            'target3': signal.get('target3', 0),
            'shares': signal.get('shares', 10),
            'opened': datetime.now().isoformat(),
            'status': 'OPEN',
            'waves_hit': [],
            'pnl': 0,
        }
        
        self.positions.append(position)
        self.save_state()
        
        print(f"[PAPER] Opened: {position['direction']} {position['shares']} shares @ ${position['entry']:.2f}")
        
        return position
    
    def update_positions(self, current_price):
        """Update positions with current price."""
        for pos in self.positions:
            if pos['status'] != 'OPEN':
                continue
            
            direction = pos['direction']
            entry = pos['entry']
            
            # Check stop loss
            if direction == 'CALL' and current_price <= pos['stop']:
                self._close_position(pos, current_price, 'STOPPED')
            elif direction == 'PUT' and current_price >= pos['stop']:
                self._close_position(pos, current_price, 'STOPPED')
            
            # Check targets
            elif direction == 'CALL':
                if current_price >= pos['target3'] and 3 not in pos['waves_hit']:
                    self._hit_target(pos, 3, pos['target3'])
                elif current_price >= pos['target2'] and 2 not in pos['waves_hit']:
                    self._hit_target(pos, 2, pos['target2'])
                elif current_price >= pos['target1'] and 1 not in pos['waves_hit']:
                    self._hit_target(pos, 1, pos['target1'])
            
            elif direction == 'PUT':
                if current_price <= pos['target3'] and 3 not in pos['waves_hit']:
                    self._hit_target(pos, 3, pos['target3'])
                elif current_price <= pos['target2'] and 2 not in pos['waves_hit']:
                    self._hit_target(pos, 2, pos['target2'])
                elif current_price <= pos['target1'] and 1 not in pos['waves_hit']:
                    self._hit_target(pos, 1, pos['target1'])
        
        self.save_state()
    
    def _hit_target(self, pos, wave, price):
        """Record target hit."""
        pos['waves_hit'].append(wave)
        wave_shares = pos['shares'] // 3
        
        if pos['direction'] == 'CALL':
            pnl = (price - pos['entry']) * wave_shares
        else:
            pnl = (pos['entry'] - price) * wave_shares
        
        pos['pnl'] += pnl
        self.balance += pnl
        
        print(f"[PAPER] Wave {wave} hit @ ${price:.2f} | PnL: ${pnl:.2f}")
        
        if wave == 3:
            pos['status'] = 'CLOSED'
            pos['closed'] = datetime.now().isoformat()
            self.history.append(pos)
            self.positions.remove(pos)
    
    def _close_position(self, pos, price, reason):
        """Close entire position."""
        remaining_shares = pos['shares'] - (len(pos['waves_hit']) * (pos['shares'] // 3))
        
        if pos['direction'] == 'CALL':
            pnl = (price - pos['entry']) * remaining_shares
        else:
            pnl = (pos['entry'] - price) * remaining_shares
        
        pos['pnl'] += pnl
        self.balance += pnl
        pos['status'] = reason
        pos['closed'] = datetime.now().isoformat()
        
        print(f"[PAPER] Closed ({reason}) @ ${price:.2f} | Total PnL: ${pos['pnl']:.2f}")
        
        self.history.append(pos)
        self.positions.remove(pos)
    
    def get_summary(self):
        """Get trading summary."""
        total_pnl = self.balance - self.starting_balance
        wins = len([h for h in self.history if h['pnl'] > 0])
        losses = len(self.history) - wins
        
        return {
            'starting': self.starting_balance,
            'current': round(self.balance, 2),
            'pnl': round(total_pnl, 2),
            'return_pct': round(total_pnl / self.starting_balance * 100, 2),
            'trades': len(self.history),
            'wins': wins,
            'losses': losses,
            'win_rate': round(wins / len(self.history) * 100, 1) if self.history else 0,
            'open_positions': len(self.positions),
        }
    
    def save_state(self):
        """Save state to file."""
        state = {
            'balance': self.balance,
            'positions': self.positions,
            'history': self.history,
            'updated': datetime.now().isoformat(),
        }
        with open(os.path.join(DATA_DIR, 'paper_trader.json'), 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Load state from file."""
        path = os.path.join(DATA_DIR, 'paper_trader.json')
        if os.path.exists(path):
            with open(path) as f:
                state = json.load(f)
            self.balance = state.get('balance', self.starting_balance)
            self.positions = state.get('positions', [])
            self.history = state.get('history', [])
    
    def print_summary(self):
        """Print summary."""
        s = self.get_summary()
        print("\n" + "=" * 50)
        print("  PAPER TRADER SUMMARY")
        print("=" * 50)
        print(f"  Balance:     ${s['current']:,.2f}")
        print(f"  P&L:         ${s['pnl']:,.2f} ({s['return_pct']:+.1f}%)")
        print(f"  Trades:      {s['trades']}")
        print(f"  Win Rate:    {s['win_rate']:.1f}%")
        print(f"  Open:        {s['open_positions']}")
        print("=" * 50)


if __name__ == "__main__":
    trader = PaperTrader()
    
    # Test signal
    signal = {
        'final': 'CALL',
        'entry': 650,
        'stop': 640,
        'target1': 665,
        'target2': 680,
        'target3': 700,
        'shares': 15,
    }
    
    trader.open_position(signal)
    trader.update_positions(665)  # Hit T1
    trader.update_positions(680)  # Hit T2
    trader.update_positions(700)  # Hit T3
    
    trader.print_summary()