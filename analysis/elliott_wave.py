"""Elliott Wave Analysis."""

import numpy as np
import pandas as pd


class ElliottWaveAnalyzer:
    """Detect Elliott Wave patterns."""
    
    def __init__(self, swing_lookback=5):
        self.swing_lookback = swing_lookback
    
    def find_swings(self, data):
        """Find swing highs and lows."""
        highs = data['High'].values
        lows = data['Low'].values
        n = self.swing_lookback
        
        swing_highs = []
        swing_lows = []
        
        for i in range(n, len(data) - n):
            if highs[i] == max(highs[i-n:i+n+1]):
                swing_highs.append({'index': i, 'price': highs[i]})
            if lows[i] == min(lows[i-n:i+n+1]):
                swing_lows.append({'index': i, 'price': lows[i]})
        
        return swing_highs, swing_lows
    
    def detect_wave(self, data):
        """Detect current wave position."""
        if len(data) < 50:
            return {'wave': 0, 'trend': 'NEUTRAL', 'phase': 'unknown'}
        
        closes = data['Close'].values
        sma20 = np.mean(closes[-20:])
        sma50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma20
        
        if sma20 > sma50:
            trend = 'UP'
        elif sma20 < sma50:
            trend = 'DOWN'
        else:
            trend = 'NEUTRAL'
        
        swing_highs, swing_lows = self.find_swings(data)
        swing_count = len(swing_highs) + len(swing_lows)
        wave = (swing_count % 5) + 1
        
        if wave in [1, 3, 5]:
            phase = 'impulse'
        else:
            phase = 'corrective'
        
        return {
            'wave': wave,
            'trend': trend,
            'phase': phase,
            'swing_highs': len(swing_highs),
            'swing_lows': len(swing_lows),
        }
    
    def get_recommendation(self, data):
        """Get trading recommendation based on wave."""
        wave_info = self.detect_wave(data)
        
        wave = wave_info['wave']
        trend = wave_info['trend']
        
        if trend == 'UP' and wave in [2, 4]:
            return {'signal': 'CALL', 'reason': f'Wave {wave} correction in uptrend'}
        elif trend == 'DOWN' and wave in [2, 4]:
            return {'signal': 'PUT', 'reason': f'Wave {wave} correction in downtrend'}
        elif wave == 5:
            return {'signal': 'HOLD', 'reason': 'Wave 5 - potential reversal'}
        else:
            return {'signal': 'HOLD', 'reason': f'Wave {wave} - wait for setup'}


if __name__ == "__main__":
    import pandas as pd
    np.random.seed(42)
    
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    data = pd.DataFrame({
        'High': prices + np.random.rand(100),
        'Low': prices - np.random.rand(100),
        'Close': prices,
    })
    
    analyzer = ElliottWaveAnalyzer()
    wave = analyzer.detect_wave(data)
    print(f"Wave: {wave['wave']}, Trend: {wave['trend']}, Phase: {wave['phase']}")
    
    rec = analyzer.get_recommendation(data)
    print(f"Signal: {rec['signal']}, Reason: {rec['reason']}")