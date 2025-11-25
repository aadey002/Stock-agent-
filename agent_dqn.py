#!/usr/bin/env python3
"""
Agent 2: DQN Reinforcement Learning Trading Agent
==================================================

Uses Deep Q-Network to learn optimal trading strategies.

IMPORTANT: This is a simplified version that uses NumPy.
For production, install TensorFlow for better performance.

Usage:
    python agent_dqn.py
"""

import json
import logging
import os
import random
from collections import deque
from datetime import datetime
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = "data"
REPORT_DIR = "reports"
MODEL_DIR = "models"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# DQN Parameters
STATE_SIZE = 10
ACTION_SIZE = 3  # HOLD, LONG, SHORT
LEARNING_RATE = 0.001
GAMMA = 0.95
EPSILON_START = 1.0
EPSILON_MIN = 0.01
EPSILON_DECAY = 0.995
MEMORY_SIZE = 1000

class SimpleDQN:
    """Simple neural network using NumPy."""
    
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        
        # Initialize weights (simple 2-layer network)
        self.w1 = np.random.randn(state_size, 24) * 0.1
        self.b1 = np.zeros(24)
        self.w2 = np.random.randn(24, action_size) * 0.1
        self.b2 = np.zeros(action_size)
    
    def predict(self, state):
        """Forward pass."""
        if state.ndim == 1:
            state = state.reshape(1, -1)
        
        # Layer 1
        z1 = np.dot(state, self.w1) + self.b1
        a1 = np.maximum(0, z1)  # ReLU
        
        # Layer 2
        z2 = np.dot(a1, self.w2) + self.b2
        return z2

class DQNAgent:
    """DQN Trading Agent."""
    
    def __init__(self):
        self.memory = deque(maxlen=MEMORY_SIZE)
        self.epsilon = EPSILON_START
        self.model = SimpleDQN(STATE_SIZE, ACTION_SIZE)
        logger.info("DQN Agent initialized")
    
    def act(self, state, training=True):
        """Choose action using epsilon-greedy."""
        if training and np.random.rand() <= self.epsilon:
            return random.randrange(ACTION_SIZE)
        
        q_values = self.model.predict(state)
        return np.argmax(q_values[0])
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience."""
        self.memory.append((state, action, reward, next_state, done))
    
    def get_state(self, data, index):
        """Extract state from market data."""
        if index < 10:
            return np.zeros(STATE_SIZE)
        
        row = data.iloc[index]
        
        # Simple state: recent prices and indicators
        close = float(row.get('Close', 0))
        atr = float(row.get('ATR', 0))
        volume = float(row.get('Volume', 0))
        
        # Normalize
        close_norm = close / 1000.0
        atr_norm = atr / 10.0
        volume_norm = volume / 1e8
        
        state = np.array([
            close_norm,
            atr_norm,
            volume_norm,
            0, 0, 0, 0, 0, 0, 0  # Padding
        ], dtype=np.float32)
        
        return state

def generate_dqn_signals():
    """Generate trading signals using DQN."""
    logger.info("Generating DQN signals...")
    
    # Load data
    data_path = os.path.join(DATA_DIR, "SPY_confluence.csv")
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} bars")
    
    agent = DQNAgent()
    signals = []
    
    # Simple signal generation (no actual training in this demo)
    for i in range(10, len(df)):
        state = agent.get_state(df, i)
        action = agent.act(state, training=False)
        
        row = df.iloc[i]
        action_name = ['HOLD', 'LONG', 'SHORT'][action]
        
        if action != 0:  # Not HOLD
            signals.append({
                'Date': row['Date'],
                'Signal': 'CALL' if action == 1 else 'PUT',
                'EntryPrice': float(row['Close']),
                'Confidence': 0.6,
                'Source': 'DQN'
            })
    
    # Save signals
    output_path = os.path.join(REPORT_DIR, "portfolio_dqn.csv")
    if signals:
        signals_df = pd.DataFrame(signals)
        signals_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(signals)} DQN signals to {output_path}")
    else:
        logger.warning("No DQN signals generated")

def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("DQN AGENT START")
    logger.info("=" * 60)
    
    generate_dqn_signals()
    
    logger.info("=" * 60)
    logger.info("DQN AGENT COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()