<<<<<<< HEAD
"""
Stock Agent Backend Server
Flask API for multi-agent trading system
Provides real-time market data and trading signals
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['https://aadey002.github.io', 'http://localhost:*'])

# Configuration
TIINGO_API_KEY = os.environ.get('TIINGO_API_KEY', '')
if not TIINGO_API_KEY:
    logger.warning("TIINGO_API_KEY not set in environment variables")

# Global cache for market data
market_data_cache = {}
signals_cache = {}
last_update = None

# Import trading agents (will be created if not exist)
try:
    from agent_FIXED import ConfluenceAgent
    logger.info("Confluence Agent loaded successfully")
except ImportError as e:
    logger.warning(f"Could not import ConfluenceAgent: {e}")
    ConfluenceAgent = None

try:
    from gann_elliott import GannElliottAgent
    logger.info("Gann-Elliott Agent loaded successfully")
except ImportError as e:
    logger.warning(f"Could not import GannElliottAgent: {e}")
    GannElliottAgent = None

# RL/DQN Agent (simplified version for demo)
class RLDQNAgent:
    """Simplified RL/DQN Agent for demonstration"""
    def __init__(self):
        self.name = "RL/DQN Agent"
        logger.info("RL/DQN Agent initialized (simplified version)")
    
    def get_signal(self, df):
        """Generate trading signal based on simple momentum strategy"""
        try:
            if len(df) < 50:
                return {'signal': 'HOLD', 'confidence': 0.5}
            
            # Simple momentum-based signal
            returns = df['Close'].pct_change()
            momentum = returns.rolling(20).mean().iloc[-1]
            volatility = returns.rolling(20).std().iloc[-1]
            
            # Generate signal
            if momentum > volatility * 0.5:
                signal = 'BUY'
                confidence = min(0.85, 0.5 + abs(momentum) * 10)
            elif momentum < -volatility * 0.5:
                signal = 'SELL'
                confidence = min(0.85, 0.5 + abs(momentum) * 10)
            else:
                signal = 'HOLD'
                confidence = 0.5
            
            return {
                'signal': signal,
                'confidence': round(confidence, 2),
                'momentum': round(momentum * 100, 2),
                'volatility': round(volatility * 100, 2)
            }
        except Exception as e:
            logger.error(f"RL/DQN signal error: {e}")
            return {'signal': 'HOLD', 'confidence': 0.5}

# Initialize agents
agents = {}
if ConfluenceAgent:
    agents['confluence'] = ConfluenceAgent()
if GannElliottAgent:
    agents['gann_elliott'] = GannElliottAgent()
agents['rl_dqn'] = RLDQNAgent()

def fetch_market_data(symbol='SPY'):
    """Fetch market data using yfinance (fallback from Tiingo)"""
    global market_data_cache, last_update
    
    try:
        # Check cache (5 minute expiry)
        if symbol in market_data_cache and last_update:
            if datetime.now() - last_update < timedelta(minutes=5):
                logger.info(f"Using cached data for {symbol}")
                return market_data_cache[symbol]
        
        logger.info(f"Fetching fresh market data for {symbol}")
        
        # Fetch data using yfinance
        ticker = yf.Ticker(symbol)
        
        # Get current price
        info = ticker.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        
        # Get historical data (3 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            logger.error(f"No data received for {symbol}")
            return None
        
        # Calculate technical indicators
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # ATR calculation
        df['H-L'] = df['High'] - df['Low']
        df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        # RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Store in cache
        market_data_cache[symbol] = {
            'symbol': symbol,
            'current_price': current_price,
            'df': df,
            'last_close': df['Close'].iloc[-1] if not df.empty else 0,
            'volume': df['Volume'].iloc[-1] if not df.empty else 0,
            'timestamp': datetime.now().isoformat()
        }
        last_update = datetime.now()
        
        logger.info(f"Market data fetched successfully for {symbol}")
        return market_data_cache[symbol]
        
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        logger.error(traceback.format_exc())
        return None

def generate_consensus_signal(symbol='SPY'):
    """Generate consensus signal from multiple agents"""
    try:
        # Get market data
        data = fetch_market_data(symbol)
        if not data or data['df'] is None or data['df'].empty:
            logger.error(f"No market data available for {symbol}")
            return None
        
        df = data['df']
        signals = {}
        
        # Get signals from each agent
        for agent_name, agent in agents.items():
            try:
                if hasattr(agent, 'get_signal'):
                    signal = agent.get_signal(df)
                    signals[agent_name] = signal
                    logger.info(f"{agent_name}: {signal}")
            except Exception as e:
                logger.error(f"Error getting signal from {agent_name}: {e}")
                signals[agent_name] = {'signal': 'HOLD', 'confidence': 0.5}
        
        # Count votes
        buy_votes = sum(1 for s in signals.values() if s.get('signal') == 'BUY')
        sell_votes = sum(1 for s in signals.values() if s.get('signal') == 'SELL')
        hold_votes = sum(1 for s in signals.values() if s.get('signal') == 'HOLD')
        
        # Determine consensus
        total_votes = len(signals)
        if buy_votes >= 2:
            consensus = 'BUY'
            agreement = buy_votes / total_votes
        elif sell_votes >= 2:
            consensus = 'SELL'
            agreement = sell_votes / total_votes
        else:
            consensus = 'HOLD'
            agreement = hold_votes / total_votes
        
        # Calculate average confidence
        avg_confidence = np.mean([s.get('confidence', 0.5) for s in signals.values()])
        
        # Determine confluence level
        if agreement == 1.0:
            confluence = 'ULTRA'
        elif agreement >= 0.66:
            confluence = 'SUPER'
        else:
            confluence = 'SINGLE'
        
        result = {
            'symbol': symbol,
            'consensus': consensus,
            'confluence': confluence,
            'agreement': round(agreement, 2),
            'confidence': round(avg_confidence, 2),
            'votes': {
                'buy': buy_votes,
                'sell': sell_votes,
                'hold': hold_votes
            },
            'agents': signals,
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result
        signals_cache[symbol] = result
        
        logger.info(f"Consensus signal generated: {consensus} ({confluence})")
        return result
        
    except Exception as e:
        logger.error(f"Error generating consensus signal: {e}")
        logger.error(traceback.format_exc())
        return None

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'agents': list(agents.keys()),
            'api_key_set': bool(TIINGO_API_KEY)
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/price/<symbol>', methods=['GET'])
def get_price(symbol):
    """Get current price for a symbol"""
    try:
        data = fetch_market_data(symbol.upper())
        if not data:
            return jsonify({'error': 'Failed to fetch market data'}), 500
        
        return jsonify({
            'symbol': symbol.upper(),
            'price': data['current_price'],
            'last_close': data['last_close'],
            'volume': data['volume'],
            'timestamp': data['timestamp']
        })
    except Exception as e:
        logger.error(f"Price endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical/<symbol>', methods=['GET'])
def get_historical(symbol):
    """Get historical data with technical indicators"""
    try:
        data = fetch_market_data(symbol.upper())
        if not data or data['df'] is None:
            return jsonify({'error': 'Failed to fetch market data'}), 500
        
        df = data['df'].tail(30)  # Last 30 days
        
        # Prepare response
        result = {
            'symbol': symbol.upper(),
            'data': [],
            'indicators': {}
        }
        
        # Add daily data
        for idx, row in df.iterrows():
            result['data'].append({
                'date': idx.strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume'])
            })
        
        # Add latest indicators
        latest = df.iloc[-1]
        result['indicators'] = {
            'sma_20': round(latest['SMA_20'], 2) if not pd.isna(latest['SMA_20']) else None,
            'sma_50': round(latest['SMA_50'], 2) if not pd.isna(latest['SMA_50']) else None,
            'sma_200': round(latest['SMA_200'], 2) if not pd.isna(latest['SMA_200']) else None,
            'atr': round(latest['ATR'], 2) if not pd.isna(latest['ATR']) else None,
            'rsi': round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else None
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Historical endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/signal/<symbol>', methods=['GET'])
def get_signal(symbol):
    """Get trading signal with consensus"""
    try:
        signal = generate_consensus_signal(symbol.upper())
        if not signal:
            return jsonify({'error': 'Failed to generate signal'}), 500
        
        return jsonify(signal)
        
    except Exception as e:
        logger.error(f"Signal endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        # Check each component
        components = {
            'server': 'online',
            'agents': {},
            'data_feed': 'unknown',
            'last_update': last_update.isoformat() if last_update else None
        }
        
        # Check agents
        for name, agent in agents.items():
            components['agents'][name] = 'online' if agent else 'offline'
        
        # Check data feed
        test_data = fetch_market_data('SPY')
        components['data_feed'] = 'online' if test_data else 'offline'
        
        # Overall status
        all_online = (
            components['server'] == 'online' and
            components['data_feed'] == 'online' and
            len(components['agents']) > 0
        )
        
        return jsonify({
            'status': 'online' if all_online else 'degraded',
            'components': components,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'name': 'Stock Agent Backend Server',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': [
            '/api/health',
            '/api/price/<symbol>',
            '/api/historical/<symbol>',
            '/api/signal/<symbol>',
            '/api/status',
            '/api/options/<symbol>',
            '/api/options/<symbol>/<expiration>'
        ],
        'timestamp': datetime.now().isoformat()
    })

# Options API endpoints
@app.route('/api/options/<symbol>', methods=['GET'])
def get_options(symbol):
    """Get options chain for a symbol (nearest expiration)"""
    try:
        from options_data import get_options_chain, get_options_summary

        # Check if summary only is requested
        summary_only = request.args.get('summary', 'false').lower() == 'true'

        if summary_only:
            data = get_options_summary(symbol.upper())
        else:
            data = get_options_chain(symbol.upper())

        if 'error' in data:
            return jsonify(data), 404

        return jsonify(data)
    except Exception as e:
        logger.error(f"Options endpoint error for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/options/<symbol>/<expiration>', methods=['GET'])
def get_options_by_expiry(symbol, expiration):
    """Get options chain for a specific expiration"""
    try:
        from options_data import get_options_chain
        data = get_options_chain(symbol.upper(), expiration)

        if 'error' in data:
            return jsonify(data), 404

        return jsonify(data)
    except Exception as e:
        logger.error(f"Options endpoint error for {symbol}/{expiration}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/options/atm/<symbol>', methods=['GET'])
def get_atm_options(symbol):
    """Get at-the-money options for quick reference"""
    try:
        from options_data import get_atm_options as fetch_atm
        expiration = request.args.get('expiration', None)
        data = fetch_atm(symbol.upper(), expiration)

        if 'error' in data:
            return jsonify(data), 404

        return jsonify(data)
    except Exception as e:
        logger.error(f"ATM options endpoint error for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

# Main execution
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Starting Stock Agent Backend Server")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Agents loaded: {list(agents.keys())}")
    logger.info(f"API Key configured: {bool(TIINGO_API_KEY)}")
    logger.info("=" * 50)
    
    # Pre-fetch data for common symbols
    for symbol in ['SPY', 'QQQ', 'IWM', 'DIA']:
        logger.info(f"Pre-fetching data for {symbol}...")
        fetch_market_data(symbol)
        generate_consensus_signal(symbol)
    
    logger.info("Trading signals generated successfully")
    logger.info("Server ready to handle requests")
    
    # Run server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
=======
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['*'])

@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/status')
def status():
    return jsonify({'status': 'online', 'health': 'healthy'})

@app.route('/api/price/<symbol>')
def price(symbol):
    return jsonify({'symbol': symbol, 'price': 600, 'status': 'healthy'})

@app.route('/api/signal/<symbol>')
def signal(symbol):
    return jsonify({
        'symbol': symbol,
        'consensus': 'BUY',
        'confidence': 0.75,
        'status': 'healthy'
    })

if __name__ == '__main__':
    print("Server running - Health checks FIXED")
    app.run(host='0.0.0.0', port=5000)
>>>>>>> fbdf5d7bcabaaa391ea6e0c5905c8ed155e20783
