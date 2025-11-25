"""Gann Square of 9 Calculator."""

import numpy as np


class GannSquare9:
    """Calculate Gann Square of 9 levels."""
    
    def __init__(self):
        self.key_angles = [45, 90, 120, 135, 180, 225, 270, 315, 360]
    
    def calculate_levels(self, base_price, levels=5):
        """Calculate Square of 9 price levels."""
        sqrt_price = np.sqrt(base_price)
        
        resistance = []
        support = []
        
        for i in range(1, levels + 1):
            for angle in [90, 180, 270, 360]:
                rotation = i * (angle / 360)
                
                up = sqrt_price + rotation
                resistance.append(round(up ** 2, 2))
                
                down = sqrt_price - rotation
                if down > 0:
                    support.append(round(down ** 2, 2))
        
        return {
            'base': base_price,
            'resistance': sorted(list(set([r for r in resistance if r > base_price]))),
            'support': sorted(list(set([s for s in support if s < base_price])), reverse=True),
        }
    
    def find_nearest(self, current, base, count=3):
        """Find nearest support/resistance levels."""
        levels = self.calculate_levels(base, levels=10)
        
        res_above = [(r, r - current) for r in levels['resistance'] if r > current]
        res_above.sort(key=lambda x: x[1])
        
        sup_below = [(s, current - s) for s in levels['support'] if s < current]
        sup_below.sort(key=lambda x: x[1])
        
        return {
            'resistance': res_above[:count],
            'support': sup_below[:count],
        }
    
    def get_targets(self, entry, stop, direction='long'):
        """Calculate price targets using Gann."""
        risk = abs(entry - stop)
        
        if direction == 'long':
            return {
                'target_1R': entry + risk,
                'target_1.5R': entry + risk * 1.5,
                'target_2R': entry + risk * 2,
                'target_2.618R': entry + risk * 2.618,
                'target_3R': entry + risk * 3,
                'target_4R': entry + risk * 4,
            }
        else:
            return {
                'target_1R': entry - risk,
                'target_1.5R': entry - risk * 1.5,
                'target_2R': entry - risk * 2,
                'target_2.618R': entry - risk * 2.618,
                'target_3R': entry - risk * 3,
                'target_4R': entry - risk * 4,
            }


if __name__ == "__main__":
    gann = GannSquare9()
    levels = gann.calculate_levels(650)
    print(f"Base: $650")
    print(f"Resistance: {levels['resistance'][:5]}")
    print(f"Support: {levels['support'][:5]}")