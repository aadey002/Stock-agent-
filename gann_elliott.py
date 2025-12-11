"""
Gann-Elliott Trading Agent
Combines Elliott Wave Theory with Gann Square of 9 calculations
Win rate target: 72%
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class GannElliottAgent:
    """
    Trading agent using Gann geometric levels and Elliott Wave patterns
    """
    
    def __init__(self):
        self.name = "Gann-Elliott Agent"
        self.win_rate = 0.72
        logger.info(f"{self.name} initialized")
        
    def calculate_gann_levels(self, price):
        """Calculate Gann Square of 9 levels"""
        try:
            sqrt_price = np.sqrt(price)
            levels = {}
            
            # Calculate key Gann angles
            angles = [45, 90, 180, 270, 360]
            for angle in angles:
                increment = angle / 180
                level_up = (sqrt_price + increment) ** 2
                level_down = (sqrt_price - increment) ** 2
                levels[f'gann_{angle}_up'] = round(level_up, 2)
                levels[f'gann_{angle}_down'] = round(level_down, 2)
            
            return levels
        except Exception as e:
            logger.error(f"Gann calculation error: {e}")
            return {}
    
    def identify_elliott_wave(self, df):
        """Identify Elliott Wave patterns"""
        try:
            if len(df) < 50:
                return {'wave': 'unknown', 'position': 0}
            
            # Get recent price action
            prices = df['Close'].tail(50).values
            highs = df['High'].tail(50).values
            lows = df['Low'].tail(50).values
            
            # Find swing points
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(prices) - 2):
                # Swing high
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
                   highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    swing_highs.append((i, highs[i]))
                
                # Swing low
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
                   lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    swing_lows.append((i, lows[i]))
            
            # Determine wave pattern
            if len(swing_highs) >= 3 and len(swing_lows) >= 2:
                # Check for impulse wave (5 waves)
                last_high = swing_highs[-1][1] if swing_highs else prices[-1]
                first_low = swing_lows[0][1] if swing_lows else prices[0]
                
                trend = 'up' if last_high > first_low * 1.02 else 'down'
                
                # Estimate wave position (1-5 for impulse, A-C for corrective)
                total_swings = len(swing_highs) + len(swing_lows)
                wave_position = (total_swings % 8) + 1
                
                return {
                    'wave': 'impulse' if wave_position <= 5 else 'corrective',
                    'position': wave_position,
                    'trend': trend
                }
            
            return {'wave': 'developing', 'position': 1, 'trend': 'neutral'}
            
        except Exception as e:
            logger.error(f"Elliott Wave error: {e}")
            return {'wave': 'unknown', 'position': 0, 'trend': 'neutral'}
    
    def calculate_fibonacci_levels(self, df):
        """Calculate Fibonacci retracement levels"""
        try:
            if len(df) < 20:
                return {}
            
            # Get recent high and low
            recent = df.tail(20)
            high = recent['High'].max()
            low = recent['Low'].min()
            diff = high - low
            
            # Fibonacci ratios
            ratios = {
                'fib_0': low,
                'fib_236': low + diff * 0.236,
                'fib_382': low + diff * 0.382,
                'fib_500': low + diff * 0.500,
                'fib_618': low + diff * 0.618,
                'fib_786': low + diff * 0.786,
                'fib_100': high
            }
            
            return {k: round(v, 2) for k, v in ratios.items()}
            
        except Exception as e:
            logger.error(f"Fibonacci calculation error: {e}")
            return {}
    
    def calculate_time_cycles(self, df):
        """Calculate Gann time cycles"""
        try:
            if len(df) < 90:
                return {'cycle': 'unknown', 'phase': 'neutral'}
            
            # Common Gann cycles (in trading days)
            cycles = {
                'weekly': 5,
                'monthly': 21,
                'quarterly': 63,
                'yearly': 252
            }
            
            # Check where we are in each cycle
            current_day = len(df)
            cycle_positions = {}
            
            for name, period in cycles.items():
                position = current_day % period
                phase_pct = position / period
                
                if phase_pct < 0.25:
                    phase = 'early'
                elif phase_pct < 0.5:
                    phase = 'mid-rise'
                elif phase_pct < 0.75:
                    phase = 'late'
                else:
                    phase = 'completion'
                
                cycle_positions[name] = {
                    'position': position,
                    'phase': phase,
                    'strength': 1 - abs(0.5 - phase_pct) * 2
                }
            
            # Find dominant cycle
            dominant = max(cycle_positions.items(), 
                         key=lambda x: x[1]['strength'])
            
            return {
                'dominant_cycle': dominant[0],
                'phase': dominant[1]['phase'],
                'cycles': cycle_positions
            }
            
        except Exception as e:
            logger.error(f"Time cycle error: {e}")
            return {'cycle': 'unknown', 'phase': 'neutral'}
    
    def get_signal(self, df):
        """Generate trading signal based on Gann-Elliott analysis"""
        try:
            if df is None or len(df) < 50:
                return {'signal': 'HOLD', 'confidence': 0.5}
            
            current_price = df['Close'].iloc[-1]
            
            # Get all components
            gann_levels = self.calculate_gann_levels(current_price)
            elliott_wave = self.identify_elliott_wave(df)
            fib_levels = self.calculate_fibonacci_levels(df)
            time_cycles = self.calculate_time_cycles(df)
            
            # Initialize scoring
            buy_score = 0
            sell_score = 0
            confidence = 0.5
            
            # Elliott Wave scoring
            if elliott_wave['wave'] == 'impulse':
                if elliott_wave['position'] in [1, 3, 5]:  # Impulse waves
                    if elliott_wave['trend'] == 'up':
                        buy_score += 2
                    else:
                        sell_score += 2
                elif elliott_wave['position'] in [2, 4]:  # Corrective waves
                    if elliott_wave['trend'] == 'up':
                        sell_score += 1
                    else:
                        buy_score += 1
            
            # Gann level analysis
            nearest_support = None
            nearest_resistance = None
            
            for key, level in gann_levels.items():
                if 'down' in key and level < current_price:
                    if nearest_support is None or level > nearest_support:
                        nearest_support = level
                elif 'up' in key and level > current_price:
                    if nearest_resistance is None or level < nearest_resistance:
                        nearest_resistance = level
            
            # Price position relative to Gann levels
            if nearest_support and nearest_resistance:
                support_distance = current_price - nearest_support
                resistance_distance = nearest_resistance - current_price
                
                if support_distance < resistance_distance * 0.5:
                    buy_score += 2  # Close to support
                elif resistance_distance < support_distance * 0.5:
                    sell_score += 2  # Close to resistance
            
            # Fibonacci analysis
            if fib_levels:
                # Check if price is at key Fibonacci level
                for level_name, level_price in fib_levels.items():
                    if abs(current_price - level_price) / current_price < 0.005:  # Within 0.5%
                        if 'fib_382' in level_name or 'fib_618' in level_name:
                            # Key reversal levels
                            if current_price > df['Close'].iloc[-10:].mean():
                                sell_score += 1
                            else:
                                buy_score += 1
            
            # Time cycle analysis
            if time_cycles['phase'] == 'early':
                buy_score += 1
            elif time_cycles['phase'] == 'completion':
                sell_score += 1
            
            # Volume confirmation
            avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            if current_volume > avg_volume * 1.2:
                # High volume confirms the move
                if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
                    buy_score += 1
                else:
                    sell_score += 1
            
            # Generate final signal
            total_score = buy_score + sell_score
            if total_score > 0:
                if buy_score > sell_score * 1.5:
                    signal = 'BUY'
                    confidence = min(0.9, 0.5 + (buy_score / total_score) * 0.4)
                elif sell_score > buy_score * 1.5:
                    signal = 'SELL'
                    confidence = min(0.9, 0.5 + (sell_score / total_score) * 0.4)
                else:
                    signal = 'HOLD'
                    confidence = 0.5
            else:
                signal = 'HOLD'
                confidence = 0.5
            
            # Log the analysis
            logger.info(f"Gann-Elliott Analysis: {elliott_wave['wave']} wave, "
                       f"position {elliott_wave['position']}, "
                       f"cycle: {time_cycles['phase']}")
            logger.info(f"Scores - Buy: {buy_score}, Sell: {sell_score}, "
                       f"Signal: {signal}, Confidence: {confidence}")
            
            return {
                'signal': signal,
                'confidence': round(confidence, 2),
                'elliott_wave': elliott_wave['wave'],
                'wave_position': elliott_wave['position'],
                'time_cycle': time_cycles['phase'],
                'gann_support': nearest_support,
                'gann_resistance': nearest_resistance,
                'analysis': {
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'dominant_cycle': time_cycles.get('dominant_cycle', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating Gann-Elliott signal: {e}")
            return {'signal': 'HOLD', 'confidence': 0.5}

# All ETFs to analyze
SYMBOLS = ['SPY', 'QQQ', 'IWM', 'XLE', 'XLF', 'XLK', 'XLV', 'XLI', 'XLB', 'XLU', 'XLP', 'XLY']


def run_gann_elliott_all_symbols(agent=None):
    """Run Gann-Elliott agent for all ETFs and return signals."""
    import yfinance as yf
    import os

    if agent is None:
        agent = GannElliottAgent()

    all_signals = []

    print("=" * 60)
    print("GANN-ELLIOTT MULTI-SYMBOL ANALYSIS")
    print("=" * 60)

    for symbol in SYMBOLS:
        try:
            # Try to load from local CSV first
            csv_path = f"data/{symbol}.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, parse_dates=['Date'], index_col='Date')
            else:
                # Fallback to yfinance
                ticker = yf.Ticker(symbol)
                df = ticker.history(period='3mo')

            if df is not None and not df.empty:
                # Standardize column names
                df.columns = [c.title() if c.islower() else c for c in df.columns]

                signal = agent.get_signal(df)
                signal['symbol'] = symbol
                signal['price'] = round(df['Close'].iloc[-1], 2)
                all_signals.append(signal)

                emoji = "🟢" if signal['signal'] == 'BUY' else "🔴" if signal['signal'] == 'SELL' else "⚪"
                print(f"{emoji} {symbol:4} | {signal['signal']:4} | Conf: {signal['confidence']:.0%} | "
                      f"Price: ${signal['price']:.2f} | Wave: {signal.get('elliott_wave', 'N/A')}")
            else:
                print(f"⚠️ {symbol}: No data available")

        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")

    print("=" * 60)
    print(f"Total signals generated: {len(all_signals)}")

    # Summary statistics
    buy_signals = [s for s in all_signals if s['signal'] == 'BUY']
    sell_signals = [s for s in all_signals if s['signal'] == 'SELL']
    print(f"BUY signals: {len(buy_signals)} | SELL signals: {len(sell_signals)}")

    return all_signals


def save_signals_to_csv(signals, filepath="reports/gann_elliott_signals.csv"):
    """Save generated signals to CSV."""
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if not signals:
        print("No signals to save")
        return

    df = pd.DataFrame(signals)
    df.to_csv(filepath, index=False)
    print(f"Saved {len(signals)} signals to {filepath}")


# Test function
if __name__ == "__main__":
    # Test the agent with sample data
    import yfinance as yf

    print("Testing Gann-Elliott Agent...")
    agent = GannElliottAgent()

    # Run for all symbols
    signals = run_gann_elliott_all_symbols(agent)

    # Save signals
    if signals:
        save_signals_to_csv(signals)

    print("\nIndividual SPY Test:")
    # Fetch sample data for SPY
    ticker = yf.Ticker('SPY')
    df = ticker.history(period='3mo')

    if not df.empty:
        signal = agent.get_signal(df)
        print(f"SPY Signal: {signal}")
    else:
        print("Failed to fetch test data")
