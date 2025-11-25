#!/usr/bin/env python3
"""Bar Aggregator - 5-Minute Bar Generation"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bar_aggregator")

class BarAggregator:
    """Aggregates prices into 5-minute bars."""
    
    def __init__(self):
        """Initialize bar aggregator."""
        self.current_bar = None
        self.bars = []
        logger.info("BarAggregator initialized")
    
    def add_price(self, price: float, timestamp: str) -> None:
        """Add a price to current bar."""
        if self.current_bar is None:
            self.current_bar = {
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'timestamp': timestamp,
                'tick_count': 1
            }
        else:
            self.current_bar['high'] = max(self.current_bar['high'], price)
            self.current_bar['low'] = min(self.current_bar['low'], price)
            self.current_bar['close'] = price
            self.current_bar['tick_count'] += 1
    
    def finalize_bar(self) -> Dict:
        """Finalize current bar and start new one."""
        if self.current_bar is None:
            return None
        
        bar = self.current_bar.copy()
        self.bars.append(bar)
        self.current_bar = None
        
        logger.info(f"? Bar: O:{bar['open']:.2f} H:{bar['high']:.2f} L:{bar['low']:.2f} C:{bar['close']:.2f}")
        return bar
    
    def get_bars(self) -> List[Dict]:
        """Get all bars."""
        return self.bars
    
    def get_latest_bar(self) -> Dict:
        """Get latest completed bar."""
        return self.bars[-1] if self.bars else None

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("BAR AGGREGATOR - TEST")
    logger.info("=" * 60)
    
    agg = BarAggregator()
    
    prices = [450.00, 451.50, 451.20, 450.50, 452.00, 450.00, 450.50, 451.75, 450.50]
    
    for i, price in enumerate(prices):
        agg.add_price(price, f"2025-11-23 14:30:{i:02d}")
        if (i + 1) % 3 == 0:
            agg.finalize_bar()
    
    logger.info(f"Generated {len(agg.get_bars())} bars")
    logger.info("=" * 60)
