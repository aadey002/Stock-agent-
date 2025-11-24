"""Alert System - Trading notifications."""

import os
import json
from datetime import datetime

DATA_DIR = "data"


class AlertSystem:
    """Manage trading alerts."""
    
    def __init__(self):
        self.alerts = []
        self.load_alerts()
    
    def signal_alert(self, signal, agent="Q5D"):
        """Create signal alert."""
        alert = {
            'id': f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'type': 'SIGNAL',
            'time': datetime.now().isoformat(),
            'agent': agent,
            'signal': signal.get('final', signal.get('signal', 'HOLD')),
            'entry': signal.get('entry', 0),
            'stop': signal.get('stop', 0),
            'confidence': signal.get('confidence', 0),
        }
        
        self._add(alert)
        self._print(alert)
        return alert
    
    def target_alert(self, symbol, wave, price, pnl):
        """Create target hit alert."""
        alert = {
            'id': f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'type': 'TARGET',
            'time': datetime.now().isoformat(),
            'symbol': symbol,
            'wave': wave,
            'price': price,
            'pnl': pnl,
        }
        
        self._add(alert)
        self._print(alert)
        return alert
    
    def stop_alert(self, symbol, price, pnl):
        """Create stop loss alert."""
        alert = {
            'id': f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'type': 'STOP',
            'time': datetime.now().isoformat(),
            'symbol': symbol,
            'price': price,
            'pnl': pnl,
        }
        
        self._add(alert)
        self._print(alert)
        return alert
    
    def _add(self, alert):
        """Add alert."""
        self.alerts.insert(0, alert)
        self.alerts = self.alerts[:100]
        self.save_alerts()
    
    def _print(self, alert):
        """Print alert."""
        t = alert['type']
        
        print("\n" + "=" * 50)
        if t == 'SIGNAL':
            print(f"  [ALERT] NEW SIGNAL: {alert['signal']}")
            print(f"  Entry: ${alert['entry']:.2f} | Stop: ${alert['stop']:.2f}")
            print(f"  Confidence: {alert['confidence']:.0%}")
        elif t == 'TARGET':
            print(f"  [ALERT] TARGET {alert['wave']} HIT")
            print(f"  Price: ${alert['price']:.2f} | P&L: ${alert['pnl']:.2f}")
        elif t == 'STOP':
            print(f"  [ALERT] STOP LOSS HIT")
            print(f"  Price: ${alert['price']:.2f} | Loss: ${alert['pnl']:.2f}")
        print("=" * 50)
    
    def save_alerts(self):
        """Save alerts."""
        with open(os.path.join(DATA_DIR, 'alerts.json'), 'w') as f:
            json.dump(self.alerts, f, indent=2)
    
    def load_alerts(self):
        """Load alerts."""
        path = os.path.join(DATA_DIR, 'alerts.json')
        if os.path.exists(path):
            with open(path) as f:
                self.alerts = json.load(f)


if __name__ == "__main__":
    alerts = AlertSystem()
    
    alerts.signal_alert({
        'final': 'CALL',
        'entry': 650,
        'stop': 640,
        'confidence': 0.78,
    })
    
    alerts.target_alert('SPY', 1, 665, 150)