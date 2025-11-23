#!/usr/bin/env python3
"""Indicator Calculator - Technical Analysis"""

import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("indicator_calculator")

class IndicatorCalculator:
    """Calculates technical indicators."""
    
    def __init__(self):
        """Initialize calculator."""
        self.bars = []
        logger.info("IndicatorCalculator initialized")
    
    def add_bar(self, bar: Dict) -> None:
        """Add a bar."""
        self.bars.append(bar)
    
    def calculate_atr(self, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(self.bars) < period:
            return 0.0
        
        tr_values = []
        for i in range(len(self.bars) - period, len(self.bars)):
            bar = self.bars[i]
            tr = bar['high'] - bar['low']
            tr_values.append(tr)
        
        return sum(tr_values) / len(tr_values)
    
    def calculate_sma(self, period: int = 20) -> float:
        """Calculate Simple Moving Average."""
        if len(self.bars) < period:
            return 0.0
        
        closes = [bar['close'] for bar in self.bars[-period:]]
        return sum(closes) / len(closes)
    
    def get_indicators(self) -> Dict:
        """Get all indicators."""
        return {
            'atr_14': self.calculate_atr(14),
            'sma_20': self.calculate_sma(20),
            'sma_50': self.calculate_sma(50),
            'bars_count': len(self.bars)
        }

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("INDICATOR CALCULATOR - TEST")
    logger.info("=" * 60)
    
    calc = IndicatorCalculator()
    
    for i in range(100):
        bar = {
            'open': 450.00 + (i * 0.01),
            'high': 452.00 + (i * 0.01),
            'low': 450.00 + (i * 0.01),
            'close': 451.00 + (i * 0.01)
        }
        calc.add_bar(bar)
    
    indicators = calc.get_indicators()
    logger.info(f"Indicators: {indicators}")
    logger.info("=" * 60)
