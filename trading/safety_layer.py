"""Safety Layer - Rule-based filters for trade validation."""

from datetime import datetime


class SafetyLayer:
    """Validate trades against safety rules."""
    
    def __init__(self):
        self.max_daily_trades = 3
        self.max_daily_loss_pct = 0.05
        self.min_confidence = 0.5
        self.min_rr_ratio = 1.5
        self.daily_trades = 0
        self.daily_pnl = 0
    
    def validate_signal(self, signal, market_conditions=None):
        """Validate a trading signal."""
        errors = []
        warnings = []
        
        # Check confidence
        conf = signal.get('confidence', 0)
        if conf < self.min_confidence:
            errors.append(f'Low confidence: {conf:.0%} < {self.min_confidence:.0%}')
        
        # Check R:R ratio
        entry = signal.get('entry', 0)
        stop = signal.get('stop', 0)
        target = signal.get('target1', 0)
        
        if entry and stop and target:
            risk = abs(entry - stop)
            reward = abs(target - entry)
            rr = reward / risk if risk > 0 else 0
            
            if rr < self.min_rr_ratio:
                errors.append(f'Low R:R: {rr:.1f} < {self.min_rr_ratio}')
        
        # Check daily limits
        if self.daily_trades >= self.max_daily_trades:
            errors.append(f'Daily trade limit reached: {self.daily_trades}')
        
        # Check market conditions
        if market_conditions:
            score = market_conditions.get('score', 100)
            if score < 30:
                errors.append(f'Poor market conditions: {score}/100')
            elif score < 50:
                warnings.append(f'Caution - market score: {score}/100')
        
        # Check time (avoid first/last 30 min)
        now = datetime.now()
        if now.hour == 9 and now.minute < 30:
            warnings.append('First 30 minutes - increased volatility')
        elif now.hour >= 15 and now.minute >= 30:
            warnings.append('Last 30 minutes - reduced liquidity')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'signal': signal.get('final', signal.get('signal', 'HOLD')),
        }
    
    def record_trade(self, pnl):
        """Record a completed trade."""
        self.daily_trades += 1
        self.daily_pnl += pnl
    
    def reset_daily(self):
        """Reset daily counters."""
        self.daily_trades = 0
        self.daily_pnl = 0
    
    def get_status(self):
        """Get current safety status."""
        return {
            'daily_trades': self.daily_trades,
            'remaining_trades': self.max_daily_trades - self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'can_trade': self.daily_trades < self.max_daily_trades,
        }


if __name__ == "__main__":
    safety = SafetyLayer()
    
    signal = {
        'signal': 'CALL',
        'confidence': 0.75,
        'entry': 650,
        'stop': 640,
        'target1': 670,
    }
    
    result = safety.validate_signal(signal)
    print(f"Valid: {result['valid']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
    
    status = safety.get_status()
    print(f"\nStatus: {status}")