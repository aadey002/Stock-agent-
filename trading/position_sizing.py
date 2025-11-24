"""Position Sizing Module - Kelly Criterion and Risk Management."""

import numpy as np


class PositionSizer:
    """Calculate optimal position sizes."""
    
    def __init__(self, account_balance=10000, max_risk_pct=0.02):
        self.account_balance = account_balance
        self.max_risk_pct = max_risk_pct
    
    def fixed_risk(self, entry, stop):
        """Calculate shares based on fixed risk per trade."""
        risk_per_share = abs(entry - stop)
        if risk_per_share == 0:
            return 0
        
        risk_amount = self.account_balance * self.max_risk_pct
        shares = int(risk_amount / risk_per_share)
        
        # Max 50% of account in one trade
        max_shares = int(self.account_balance * 0.5 / entry)
        
        return min(shares, max_shares)
    
    def kelly_criterion(self, win_rate, avg_win, avg_loss):
        """Calculate Kelly Criterion position size."""
        if avg_loss == 0:
            return 0
        
        win_loss_ratio = abs(avg_win / avg_loss)
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Half-Kelly for safety
        half_kelly = kelly / 2
        
        # Cap at 25% of account
        return max(0, min(0.25, half_kelly))
    
    def volatility_adjusted(self, entry, atr, target_risk_pct=0.02):
        """Adjust position size based on volatility."""
        if atr == 0:
            return 0
        
        # Stop at 2 ATR
        stop_distance = 2 * atr
        risk_amount = self.account_balance * target_risk_pct
        
        shares = int(risk_amount / stop_distance)
        max_shares = int(self.account_balance * 0.5 / entry)
        
        return min(shares, max_shares)
    
    def calculate_3_waves(self, total_shares):
        """Split position into 3 waves."""
        w1 = int(total_shares * 0.33)
        w2 = int(total_shares * 0.33)
        w3 = total_shares - w1 - w2
        
        return {'wave1': w1, 'wave2': w2, 'wave3': w3}
    
    def get_position(self, entry, stop, atr=None, win_rate=0.6, avg_rr=2.0):
        """Get complete position sizing recommendation."""
        # Basic fixed risk
        fixed = self.fixed_risk(entry, stop)
        
        # Volatility adjusted
        vol_adj = self.volatility_adjusted(entry, atr or abs(entry - stop) / 2) if atr else fixed
        
        # Kelly
        kelly_pct = self.kelly_criterion(win_rate, avg_rr, 1.0)
        kelly_shares = int(self.account_balance * kelly_pct / entry)
        
        # Use most conservative
        recommended = min(fixed, vol_adj, kelly_shares) if kelly_shares > 0 else min(fixed, vol_adj)
        
        waves = self.calculate_3_waves(recommended)
        
        return {
            'shares': recommended,
            'waves': waves,
            'risk_amount': abs(entry - stop) * recommended,
            'risk_pct': abs(entry - stop) * recommended / self.account_balance * 100,
            'position_value': entry * recommended,
        }


if __name__ == "__main__":
    sizer = PositionSizer(account_balance=10000)
    
    pos = sizer.get_position(entry=650, stop=630, atr=10)
    print(f"Recommended shares: {pos['shares']}")
    print(f"Waves: {pos['waves']}")
    print(f"Risk: ${pos['risk_amount']:.2f} ({pos['risk_pct']:.1f}%)")
    print(f"Position value: ${pos['position_value']:.2f}")