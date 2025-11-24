#!/usr/bin/env python3
"""
DQN Agent for SPY Trading - Part of Multi-Agent System
Days 5-7 Enhancement: Deep Reinforcement Learning Implementation

Features:
- Deep Q-Network with experience replay and target network
- Integration with existing multi-agent voting system
- Professional logging and monitoring
- Position sizing with Kelly Criterion
- ATR-based stops and targets
"""

import numpy as np
import pandas as pd
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from collections import deque
import random
import os
import pathlib

# Try TensorFlow import with fallback
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers
    HAS_TF = True
except ImportError:
    HAS_TF = False
    print("TensorFlow not found. Using NumPy fallback for DQN calculations.")

# =========================================================================
# CONFIGURATION
# =========================================================================

# DQN Hyperparameters
LEARNING_RATE = 0.001
GAMMA = 0.99  # Discount factor
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995
BATCH_SIZE = 64
MEMORY_SIZE = 10000
TARGET_UPDATE_FREQ = 100
EPISODES = 10000

# Trading Parameters
INITIAL_BALANCE = 100000
MAX_POSITION_SIZE = 0.2  # Max 20% of account per trade
MIN_POSITION_SIZE = 0.01  # Min 1% of account

# Network Architecture
INPUT_DIM = 30  # OHLCV + indicators + confluence features
HIDDEN_LAYERS = [128, 64, 32]
OUTPUT_DIM = 3  # Actions: BUY, SELL, HOLD

# Paths
DATA_DIR = pathlib.Path("data")
MODELS_DIR = pathlib.Path("models")
LOGS_DIR = pathlib.Path("logs")

# Create directories
for dir_path in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =========================================================================
# LOGGING SETUP
# =========================================================================

def setup_dqn_logging() -> logging.Logger:
    """Setup logging for DQN agent."""
    logger = logging.getLogger("dqn_agent")
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | DQN | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(LOGS_DIR / "dqn_agent.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_dqn_logging()

# =========================================================================
# STATE REPRESENTATION
# =========================================================================

@dataclass
class MarketState:
    """Market state representation for DQN."""
    timestamp: datetime
    price: float
    volume: float
    returns_1d: float
    returns_5d: float
    returns_20d: float
    atr: float
    rsi: float
    macd: float
    macd_signal: float
    bb_upper: float
    bb_lower: float
    sma_10: float
    sma_20: float
    sma_50: float
    volume_ratio: float
    price_confluence: bool
    time_confluence: bool
    trend_strength: float
    volatility_regime: float
    
    def to_array(self) -> np.ndarray:
        """Convert state to numpy array for neural network."""
        return np.array([
            self.price,
            self.volume,
            self.returns_1d,
            self.returns_5d,
            self.returns_20d,
            self.atr,
            self.rsi,
            self.macd,
            self.macd_signal,
            self.bb_upper,
            self.bb_lower,
            self.sma_10,
            self.sma_20,
            self.sma_50,
            self.volume_ratio,
            float(self.price_confluence),
            float(self.time_confluence),
            self.trend_strength,
            self.volatility_regime,
            # Additional engineered features
            self.price / self.sma_10 if self.sma_10 > 0 else 1.0,
            self.price / self.sma_20 if self.sma_20 > 0 else 1.0,
            self.price / self.sma_50 if self.sma_50 > 0 else 1.0,
            (self.price - self.bb_lower) / (self.bb_upper - self.bb_lower) if self.bb_upper > self.bb_lower else 0.5,
            self.macd - self.macd_signal,
            self.volume / np.mean([self.volume]) if self.volume > 0 else 1.0,
            abs(self.returns_1d),
            abs(self.returns_5d),
            abs(self.returns_20d),
            self.atr / self.price if self.price > 0 else 0.01,
            np.sign(self.returns_1d)
        ])

# =========================================================================
# TRADING ENVIRONMENT
# =========================================================================

class TradingEnvironment:
    """Trading environment for DQN agent."""
    
    def __init__(self, data: pd.DataFrame, initial_balance: float = INITIAL_BALANCE):
        self.data = data
        self.initial_balance = initial_balance
        self.reset()
        
    def reset(self) -> MarketState:
        """Reset environment to initial state."""
        self.current_step = 30  # Start after enough data for indicators
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.equity_curve = [self.initial_balance]
        
        return self._get_state()
    
    def _get_state(self) -> MarketState:
        """Get current market state."""
        if self.current_step >= len(self.data):
            return None
            
        row = self.data.iloc[self.current_step]
        
        # Calculate returns
        prices = self.data['Close'].iloc[max(0, self.current_step-20):self.current_step+1]
        returns_1d = (prices.iloc[-1] / prices.iloc[-2] - 1) if len(prices) > 1 else 0
        returns_5d = (prices.iloc[-1] / prices.iloc[-6] - 1) if len(prices) > 5 else 0
        returns_20d = (prices.iloc[-1] / prices.iloc[0] - 1) if len(prices) > 19 else 0
        
        # Calculate indicators
        rsi = self._calculate_rsi(prices)
        macd, macd_signal = self._calculate_macd(prices)
        bb_upper, bb_lower = self._calculate_bollinger_bands(prices)
        volume_ratio = row['Volume'] / self.data['Volume'].rolling(20).mean().iloc[self.current_step]
        
        # Trend strength (0-1)
        sma_10 = prices.rolling(10).mean().iloc[-1] if len(prices) > 9 else prices.iloc[-1]
        sma_20 = prices.rolling(20).mean().iloc[-1] if len(prices) > 19 else prices.iloc[-1]
        trend_strength = abs(sma_10 - sma_20) / sma_20 if sma_20 > 0 else 0
        
        # Volatility regime
        volatility = prices.pct_change().std() if len(prices) > 1 else 0.01
        hist_vol = self.data['Close'].pct_change().rolling(60).std().mean()
        volatility_regime = volatility / hist_vol if hist_vol > 0 else 1.0
        
        return MarketState(
            timestamp=pd.to_datetime(row.name),
            price=row['Close'],
            volume=row['Volume'],
            returns_1d=returns_1d,
            returns_5d=returns_5d,
            returns_20d=returns_20d,
            atr=row.get('ATR', prices.diff().abs().mean()),
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            sma_10=sma_10,
            sma_20=sma_20,
            sma_50=prices.rolling(50).mean().iloc[-1] if len(self.data) > 50 else prices.iloc[-1],
            volume_ratio=volume_ratio,
            price_confluence=bool(row.get('PriceConfluence', 0)),
            time_confluence=bool(row.get('TimeConfluence', 0)),
            trend_strength=trend_strength,
            volatility_regime=volatility_regime
        )
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = prices.diff()
        gain = (deltas.where(deltas > 0, 0)).rolling(period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(period).mean()
        
        rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float]:
        """Calculate MACD and signal line."""
        if len(prices) < 26:
            return 0.0, 0.0
            
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        return macd.iloc[-1], signal.iloc[-1]
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Tuple[float, float]:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return prices.iloc[-1] * 1.02, prices.iloc[-1] * 0.98
            
        sma = prices.rolling(period).mean().iloc[-1]
        std = prices.rolling(period).std().iloc[-1]
        
        upper = sma + (2 * std)
        lower = sma - (2 * std)
        
        return upper, lower
    
    def step(self, action: int) -> Tuple[MarketState, float, bool]:
        """Execute action and return new state, reward, and done flag."""
        if self.current_step >= len(self.data) - 1:
            return None, 0, True
            
        state = self._get_state()
        current_price = state.price
        
        # Execute action
        reward = 0
        if action == 0:  # BUY
            if self.position == 0:
                # Calculate position size using Kelly Criterion
                position_size = self._calculate_position_size(state)
                cost = current_price * position_size
                if self.balance >= cost:
                    self.position = position_size
                    self.entry_price = current_price
                    self.balance -= cost
                    logger.debug(f"BUY: {position_size} shares @ ${current_price:.2f}")
                    
        elif action == 1:  # SELL
            if self.position > 0:
                # Close position
                proceeds = current_price * self.position
                pnl = proceeds - (self.entry_price * self.position)
                reward = pnl / (self.entry_price * self.position) * 100  # Percentage return
                
                self.balance += proceeds
                self.trades.append({
                    'entry_price': self.entry_price,
                    'exit_price': current_price,
                    'position_size': self.position,
                    'pnl': pnl,
                    'return': reward
                })
                
                logger.debug(f"SELL: {self.position} shares @ ${current_price:.2f}, PnL: ${pnl:.2f}")
                self.position = 0
                self.entry_price = 0
                
        # HOLD action (2) does nothing
        
        # Update equity
        equity = self.balance + (self.position * current_price if self.position > 0 else 0)
        self.equity_curve.append(equity)
        
        # Calculate reward based on equity change
        if reward == 0:  # No trade executed
            equity_change = (equity - self.equity_curve[-2]) / self.equity_curve[-2] if len(self.equity_curve) > 1 else 0
            reward = equity_change * 100
        
        # Advance to next step
        self.current_step += 1
        next_state = self._get_state()
        done = self.current_step >= len(self.data) - 1
        
        return next_state, reward, done
    
    def _calculate_position_size(self, state: MarketState) -> int:
        """Calculate position size using Kelly Criterion with bounds."""
        # Simplified Kelly calculation
        win_rate = 0.55  # Estimated from historical performance
        avg_win = 0.02  # 2% average win
        avg_loss = 0.01  # 1% average loss
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_fraction = np.clip(kelly_fraction, MIN_POSITION_SIZE, MAX_POSITION_SIZE)
        
        # Adjust for volatility
        if state.volatility_regime > 1.5:
            kelly_fraction *= 0.5
        elif state.volatility_regime < 0.8:
            kelly_fraction *= 1.2
            
        # Calculate shares
        position_value = self.balance * kelly_fraction
        shares = int(position_value / state.price)
        
        return max(1, shares)

# =========================================================================
# DQN NETWORK
# =========================================================================

class DQNNetwork:
    """Deep Q-Network implementation."""
    
    def __init__(self, input_dim: int, output_dim: int, learning_rate: float = LEARNING_RATE):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.learning_rate = learning_rate
        
        if HAS_TF:
            self.model = self._build_model_tf()
            self.target_model = self._build_model_tf()
            self.update_target_network()
        else:
            self.model = self._build_model_numpy()
            self.target_model = self._build_model_numpy()
    
    def _build_model_tf(self) -> keras.Model:
        """Build TensorFlow model."""
        model = models.Sequential([
            layers.Dense(HIDDEN_LAYERS[0], activation='relu', input_shape=(self.input_dim,)),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.Dense(HIDDEN_LAYERS[1], activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.Dense(HIDDEN_LAYERS[2], activation='relu'),
            layers.Dense(self.output_dim, activation='linear')
        ])
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss='huber',
            metrics=['mae']
        )
        
        return model
    
    def _build_model_numpy(self) -> Dict[str, np.ndarray]:
        """Build NumPy fallback model."""
        model = {}
        
        # Initialize weights randomly
        prev_dim = self.input_dim
        for i, hidden_dim in enumerate(HIDDEN_LAYERS):
            model[f'W{i}'] = np.random.randn(prev_dim, hidden_dim) * 0.1
            model[f'b{i}'] = np.zeros(hidden_dim)
            prev_dim = hidden_dim
            
        model['W_out'] = np.random.randn(prev_dim, self.output_dim) * 0.1
        model['b_out'] = np.zeros(self.output_dim)
        
        return model
    
    def predict(self, state: np.ndarray) -> np.ndarray:
        """Predict Q-values for given state."""
        if HAS_TF:
            return self.model.predict(state.reshape(1, -1), verbose=0)[0]
        else:
            return self._forward_numpy(state, self.model)
    
    def _forward_numpy(self, state: np.ndarray, model: Dict[str, np.ndarray]) -> np.ndarray:
        """Forward pass using NumPy."""
        x = state
        
        # Hidden layers
        for i in range(len(HIDDEN_LAYERS)):
            x = np.dot(x, model[f'W{i}']) + model[f'b{i}']
            x = np.maximum(0, x)  # ReLU activation
            
        # Output layer
        x = np.dot(x, model['W_out']) + model['b_out']
        
        return x
    
    def train_on_batch(self, states: np.ndarray, targets: np.ndarray):
        """Train model on batch."""
        if HAS_TF:
            return self.model.train_on_batch(states, targets)
        else:
            # Simplified gradient descent for NumPy version
            learning_rate = 0.001
            for i in range(len(states)):
                pred = self._forward_numpy(states[i], self.model)
                error = targets[i] - pred
                
                # Simple weight update (not full backprop)
                for key in self.model:
                    if 'W' in key:
                        self.model[key] += learning_rate * error.mean() * 0.01
    
    def update_target_network(self):
        """Copy weights to target network."""
        if HAS_TF:
            self.target_model.set_weights(self.model.get_weights())
        else:
            self.target_model = self.model.copy()
    
    def save(self, filepath: str):
        """Save model weights."""
        if HAS_TF:
            self.model.save_weights(filepath)
        else:
            np.save(filepath, self.model)
    
    def load(self, filepath: str):
        """Load model weights."""
        if HAS_TF and os.path.exists(filepath):
            self.model.load_weights(filepath)
        elif os.path.exists(filepath + '.npy'):
            self.model = np.load(filepath + '.npy', allow_pickle=True).item()

# =========================================================================
# DQN AGENT
# =========================================================================

class DQNAgent:
    """DQN Trading Agent."""
    
    def __init__(self, state_size: int = INPUT_DIM, action_size: int = OUTPUT_DIM):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=MEMORY_SIZE)
        self.epsilon = EPSILON_START
        
        # Networks
        self.q_network = DQNNetwork(state_size, action_size)
        
        # Training metrics
        self.training_history = {
            'episodes': [],
            'rewards': [],
            'epsilon': [],
            'loss': [],
            'win_rate': []
        }
        
        logger.info("DQN Agent initialized")
    
    def remember(self, state: np.ndarray, action: int, reward: float, 
                 next_state: np.ndarray, done: bool):
        """Store experience in replay buffer."""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        """Choose action using epsilon-greedy policy."""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_size - 1)
        
        q_values = self.q_network.predict(state)
        return np.argmax(q_values)
    
    def replay(self, batch_size: int = BATCH_SIZE) -> float:
        """Train on batch from replay buffer."""
        if len(self.memory) < batch_size:
            return 0.0
        
        batch = random.sample(self.memory, batch_size)
        states = np.array([e[0] for e in batch])
        actions = np.array([e[1] for e in batch])
        rewards = np.array([e[2] for e in batch])
        next_states = np.array([e[3] for e in batch])
        dones = np.array([e[4] for e in batch])
        
        # Current Q-values
        current_q = self.q_network.model.predict(states, verbose=0) if HAS_TF else \
                   np.array([self.q_network.predict(s) for s in states])
        
        # Next Q-values from target network
        next_q = self.q_network.target_model.predict(next_states, verbose=0) if HAS_TF else \
                np.array([self.q_network._forward_numpy(s, self.q_network.target_model) for s in next_states])
        
        # Update Q-values
        targets = current_q.copy()
        for i in range(batch_size):
            if dones[i]:
                targets[i][actions[i]] = rewards[i]
            else:
                targets[i][actions[i]] = rewards[i] + GAMMA * np.max(next_q[i])
        
        # Train
        loss = self.q_network.train_on_batch(states, targets)
        
        return loss if isinstance(loss, float) else loss[0] if hasattr(loss, '__len__') else 0.0
    
    def update_epsilon(self):
        """Decay epsilon for exploration."""
        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)
    
    def train(self, env: TradingEnvironment, episodes: int = EPISODES):
        """Train the DQN agent."""
        logger.info(f"Starting DQN training for {episodes} episodes")
        
        for episode in range(episodes):
            state = env.reset()
            if state is None:
                continue
                
            state_array = state.to_array()
            total_reward = 0
            done = False
            steps = 0
            
            while not done:
                # Choose action
                action = self.act(state_array)
                
                # Execute action
                next_state, reward, done = env.step(action)
                
                if next_state is not None:
                    next_state_array = next_state.to_array()
                else:
                    next_state_array = np.zeros_like(state_array)
                    done = True
                
                # Store experience
                self.remember(state_array, action, reward, next_state_array, done)
                
                # Train on replay buffer
                if len(self.memory) > BATCH_SIZE:
                    loss = self.replay()
                else:
                    loss = 0
                
                state_array = next_state_array
                total_reward += reward
                steps += 1
                
                # Update target network
                if steps % TARGET_UPDATE_FREQ == 0:
                    self.q_network.update_target_network()
            
            # Update epsilon
            self.update_epsilon()
            
            # Calculate metrics
            win_rate = len([t for t in env.trades if t['pnl'] > 0]) / len(env.trades) * 100 if env.trades else 0
            
            # Store metrics
            self.training_history['episodes'].append(episode)
            self.training_history['rewards'].append(total_reward)
            self.training_history['epsilon'].append(self.epsilon)
            self.training_history['loss'].append(loss)
            self.training_history['win_rate'].append(win_rate)
            
            # Log progress
            if episode % 100 == 0:
                logger.info(f"Episode {episode}/{episodes} - Reward: {total_reward:.2f}, "
                          f"Epsilon: {self.epsilon:.3f}, Win Rate: {win_rate:.1f}%")
                
            # Save checkpoint
            if episode % 500 == 0 and episode > 0:
                self.save(f"dqn_checkpoint_{episode}")
        
        logger.info("DQN training completed")
        
        # Save final model
        self.save("dqn_final")
        
        # Save training history
        with open(DATA_DIR / "dqn_training_history.json", 'w') as f:
            json.dump(self.training_history, f, indent=2)
    
    def evaluate(self, env: TradingEnvironment) -> Dict[str, Any]:
        """Evaluate agent performance."""
        state = env.reset()
        if state is None:
            return {}
            
        state_array = state.to_array()
        done = False
        
        while not done:
            action = self.act(state_array, training=False)
            next_state, reward, done = env.step(action)
            
            if next_state is not None:
                state_array = next_state.to_array()
            else:
                done = True
        
        # Calculate metrics
        total_return = (env.equity_curve[-1] - env.initial_balance) / env.initial_balance * 100
        max_drawdown = self._calculate_max_drawdown(env.equity_curve)
        sharpe_ratio = self._calculate_sharpe_ratio(env.equity_curve)
        win_rate = len([t for t in env.trades if t['pnl'] > 0]) / len(env.trades) * 100 if env.trades else 0
        
        metrics = {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'total_trades': len(env.trades),
            'final_equity': env.equity_curve[-1]
        }
        
        logger.info(f"Evaluation Results: Return: {total_return:.2f}%, "
                   f"Sharpe: {sharpe_ratio:.2f}, Win Rate: {win_rate:.1f}%")
        
        return metrics
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown."""
        peak = equity_curve[0]
        max_dd = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
                
        return max_dd
    
    def _calculate_sharpe_ratio(self, equity_curve: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if len(equity_curve) < 2:
            return 0.0
            
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        if len(returns) == 0:
            return 0.0
            
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
            
        return np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)
    
    def get_signal(self, state: MarketState) -> str:
        """Get trading signal for multi-agent voting."""
        state_array = state.to_array()
        action = self.act(state_array, training=False)
        
        if action == 0:
            return "CALL"
        elif action == 1:
            return "PUT"
        else:
            return "HOLD"
    
    def save(self, name: str):
        """Save agent model and metadata."""
        model_path = MODELS_DIR / f"{name}_model"
        self.q_network.save(str(model_path))
        
        # Save metadata
        metadata = {
            'epsilon': self.epsilon,
            'state_size': self.state_size,
            'action_size': self.action_size,
            'training_episodes': len(self.training_history['episodes'])
        }
        
        with open(MODELS_DIR / f"{name}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Model saved: {name}")
    
    def load(self, name: str):
        """Load agent model and metadata."""
        model_path = MODELS_DIR / f"{name}_model"
        
        if os.path.exists(MODELS_DIR / f"{name}_metadata.json"):
            with open(MODELS_DIR / f"{name}_metadata.json", 'r') as f:
                metadata = json.load(f)
                self.epsilon = metadata.get('epsilon', EPSILON_END)
                
            self.q_network.load(str(model_path))
            logger.info(f"Model loaded: {name}")
        else:
            logger.warning(f"Model not found: {name}")

# =========================================================================
# INTEGRATION WITH MULTI-AGENT SYSTEM
# =========================================================================

def integrate_dqn_with_multiagent(data: pd.DataFrame) -> Dict[str, Any]:
    """Integrate DQN agent with existing multi-agent system."""
    logger.info("Integrating DQN with multi-agent system")
    
    # Initialize DQN agent
    agent = DQNAgent()
    
    # Check if trained model exists
    if os.path.exists(MODELS_DIR / "dqn_final_metadata.json"):
        agent.load("dqn_final")
        logger.info("Loaded pre-trained DQN model")
    else:
        # Train new model
        logger.info("Training new DQN model")
        env = TradingEnvironment(data)
        agent.train(env, episodes=1000)  # Reduced for initial training
    
    # Evaluate performance
    env = TradingEnvironment(data)
    metrics = agent.evaluate(env)
    
    # Generate signals for voting
    signals = []
    for i in range(30, len(data)):
        env.current_step = i
        state = env._get_state()
        if state:
            signal = agent.get_signal(state)
            signals.append({
                'date': state.timestamp,
                'signal': signal,
                'confidence': 1.0 - agent.epsilon  # Use epsilon as inverse confidence
            })
    
    return {
        'agent': agent,
        'metrics': metrics,
        'signals': signals
    }

# =========================================================================
# MAIN EXECUTION
# =========================================================================

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("DQN AGENT - MULTI-AGENT TRADING SYSTEM")
    logger.info("=" * 80)
    
    # Load data
    data_path = DATA_DIR / "SPY.csv"
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
    
    data = pd.read_csv(data_path, index_col='Date', parse_dates=True)
    logger.info(f"Loaded {len(data)} bars of data")
    
    # Run DQN integration
    result = integrate_dqn_with_multiagent(data)
    
    # Save results
    output_path = DATA_DIR / "dqn_integration_results.json"
    with open(output_path, 'w') as f:
        json.dump({
            'metrics': result['metrics'],
            'signals_count': len(result['signals']),
            'last_signal': result['signals'][-1] if result['signals'] else None
        }, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")
    logger.info("=" * 80)
    logger.info("DQN AGENT COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()





