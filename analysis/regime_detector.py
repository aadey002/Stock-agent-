"""Market Regime Detector."""

import numpy as np
import pandas as pd


class RegimeDetector:
    """Detect market regime (trending, ranging, volatile)."""
    
    def __init__(self):
        self.regimes = ['TRENDING_UP', 'TRENDING_DOWN', 'RANGING', 'VOLATILE']
    
    def detect_regime(self, data, lookback=50):
        """Detect current market regime."""
        if len(data) < lookback:
            return {'regime': 'UNKNOWN', 'confidence': 0}
        
        recent = data.tail(lookback)
        closes = recent['Close'].values
        
        # Trend strength
        sma20 = np.mean(closes[-20:])
        sma50 = np.mean(closes)
        trend_strength = (sma20 - sma50) / sma50
        
        # Volatility
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(252)
        
        # Range detection
        high = recent['High'].max()
        low = recent['Low'].min()
        range_pct = (high - low) / low
        
        # ADX approximation (trend strength)
        adx_approx = abs(trend_strength) * 100
        
        # Determine regime
        if volatility > 0.3:
            regime = 'VOLATILE'
            confidence = min(0.9, volatility)
        elif adx_approx > 2:
            if trend_strength > 0:
                regime = 'TRENDING_UP'
            else:
                regime = 'TRENDING_DOWN'
            confidence = min(0.9, adx_approx / 5)
        else:
            regime = 'RANGING'
            confidence = 1 - adx_approx / 5
        
        return {
            'regime': regime,
            'confidence': round(confidence, 2),
            'trend_strength': round(trend_strength * 100, 2),
            'volatility': round(volatility * 100, 2),
            'range_pct': round(range_pct * 100, 2),
        }
    
    def get_strategy_recommendation(self, regime_info):
        """Get strategy recommendation based on regime."""
        regime = regime_info['regime']
        
        strategies = {
            'TRENDING_UP': {
                'strategy': 'TREND_FOLLOWING',
                'bias': 'CALL',
                'position_size': 1.0,
                'advice': 'Buy dips, trail stops',
            },
            'TRENDING_DOWN': {
                'strategy': 'TREND_FOLLOWING',
                'bias': 'PUT',
                'position_size': 1.0,
                'advice': 'Sell rallies, trail stops',
            },
            'RANGING': {
                'strategy': 'MEAN_REVERSION',
                'bias': 'NEUTRAL',
                'position_size': 0.75,
                'advice': 'Buy support, sell resistance',
            },
            'VOLATILE': {
                'strategy': 'REDUCED_EXPOSURE',
                'bias': 'NEUTRAL',
                'position_size': 0.5,
                'advice': 'Reduce size, widen stops',
            },
        }
        
        return strategies.get(regime, strategies['RANGING'])


if __name__ == "__main__":
    import pandas as pd
    np.random.seed(42)
    
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5 + 0.1)
    data = pd.DataFrame({
        'High': prices + np.random.rand(100),
        'Low': prices - np.random.rand(100),
        'Close': prices,
    })
    
    detector = RegimeDetector()
    regime = detector.detect_regime(data)
    print(f"Regime: {regime['regime']}")
    print(f"Confidence: {regime['confidence']}")
    print(f"Trend: {regime['trend_strength']}%")
    print(f"Volatility: {regime['volatility']}%")
    
    strategy = detector.get_strategy_recommendation(regime)
    print(f"\nStrategy: {strategy['strategy']}")
    print(f"Bias: {strategy['bias']}")
    print(f"Advice: {strategy['advice']}")