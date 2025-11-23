#!/usr/bin/env python3
"""
DQN Trading Agent - Deep Q-Network for SPY Price Action
Week 3 Phase 3 - Machine Learning Component

Implements a Deep Q-Network agent that learns optimal trading actions
through reinforcement learning with experience replay and target networks.

Architecture:
- Input: State vector (price, ATR, bias, confluence)
- Hidden: 2 layers of 64 neurons each (ReLU)
- Output: 3 Q-values (CALL, PUT, HOLD)
- Training: DQN with experience replay
"""

import json
import logging
import math
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️  TensorFlow not installed. DQN will use numpy implementation.")

# =========================================================================
# LOGGING SETUP
# =========================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)
logger = logging.getLogger("dqn_agent")

# =========================================================================
# CONFIGURATION
# =========================================================================

@dataclass
class DQNConfig:
    """DQN hyperparameters and configuration."""
    
    # Network architecture
    state_size: int = 5  # [price, atr, fast_sma, slow_sma, confluence]
    action_size: int = 3  # [CALL=0, PUT=1, HOLD=2]
    hidden_size: int = 64
    
    # Training
    learning_rate: float = 0.001
    gamma: float = 0.95  # Discount factor
    epsilon: float = 1.0  # Exploration rate
    epsilon_min: float = 0.01
    epsilon_decay: float = 0.995
    
    # Experience replay
    memory_size: int = 1000
    batch_size: int = 32
    
    # Training loop
    episodes: int = 100
    update_target_freq: int = 10
    
    # Risk management
    max_position_size: int = 100
    risk_per_trade: float = 1.0  # % of account


CONFIG = DQNConfig()

# =========================================================================
# DATA STRUCTURES
# =========================================================================

@dataclass
class TradingState:
    """Current market state for the agent."""
    
    price: float
    atr: float
    fast_sma: float
    slow_sma: float
    confluence: int  # 0 or 1
    
    def to_array(self) -> np.ndarray:
        """Convert state to normalized array."""
        # Normalize values to 0-1 range (approximate)
        return np.array([
            self.price / 500.0,  # SPY typically 300-600
            self.atr / 10.0,     # ATR typically 1-20
            self.fast_sma / 500.0,
            self.slow_sma / 500.0,
            float(self.confluence),
        ], dtype=np.float32)


@dataclass
class Experience:
    """Single experience in the replay memory."""
    
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayMemory:
    """Experience replay buffer for DQN training."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.memory: List[Experience] = []
        self.index = 0
    
    def add(self, experience: Experience) -> None:
        """Add experience to memory."""
        if len(self.memory) < self.max_size:
            self.memory.append(experience)
        else:
            self.memory[self.index] = experience
        
        self.index = (self.index + 1) % self.max_size
    
    def sample(self, batch_size: int) -> List[Experience]:
        """Sample random batch from memory."""
        if len(self.memory) < batch_size:
            return self.memory
        
        indices = np.random.choice(len(self.memory), batch_size, replace=False)
        return [self.memory[i] for i in indices]
    
    def __len__(self) -> int:
        return len(self.memory)


# =========================================================================
# DQN AGENT - KERAS VERSION
# =========================================================================

class DQNAgent:
    """Deep Q-Network Agent with Keras backend."""
    
    def __init__(self, config: DQNConfig = CONFIG):
        self.config = config
        self.memory = ReplayMemory(config.memory_size)
        
        # Build networks
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
        
        # Training state
        self.epsilon = config.epsilon
        self.losses: List[float] = []
        self.training_steps = 0
        
        logger.info(
            f"DQNAgent initialized | "
            f"State: {config.state_size}, "
            f"Actions: {config.action_size}, "
            f"Memory: {config.memory_size}"
        )
    
    def _build_model(self) -> keras.Model:
        """Build neural network model."""
        model = keras.Sequential([
            layers.Input(shape=(self.config.state_size,)),
            layers.Dense(
                self.config.hidden_size,
                activation='relu',
                kernel_regularizer=keras.regularizers.l2(0.01)
            ),
            layers.Dropout(0.2),
            layers.Dense(
                self.config.hidden_size,
                activation='relu',
                kernel_regularizer=keras.regularizers.l2(0.01)
            ),
            layers.Dropout(0.2),
            layers.Dense(self.config.action_size, activation='linear'),
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss='mse'
        )
        
        return model
    
    def update_target_model(self) -> None:
        """Update target network with main network weights."""
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, experience: Experience) -> None:
        """Store experience in replay memory."""
        self.memory.add(experience)
    
    def act(self, state: np.ndarray) -> int:
        """Choose action using epsilon-greedy policy."""
        if np.random.random() < self.epsilon:
            # Explore: random action
            return np.random.choice(self.config.action_size)
        else:
            # Exploit: best action
            q_values = self.model.predict(state.reshape(1, -1), verbose=0)
            return np.argmax(q_values[0])
    
    def replay(self, batch_size: int) -> Optional[float]:
        """Learn from batch of experiences."""
        if len(self.memory) < batch_size:
            return None
        
        batch = self.memory.sample(batch_size)
        
        # Prepare batch data
        states = np.array([exp.state for exp in batch])
        actions = np.array([exp.action for exp in batch])
        rewards = np.array([exp.reward for exp in batch])
        next_states = np.array([exp.next_state for exp in batch])
        dones = np.array([exp.done for exp in batch])
        
        # Predict Q-values
        target_q_values = self.model.predict(states, verbose=0)
        next_q_values = self.target_model.predict(next_states, verbose=0)
        
        # Update Q-values with Bellman equation
        for i in range(batch_size):
            if dones[i]:
                target_q_values[i][actions[i]] = rewards[i]
            else:
                target_q_values[i][actions[i]] = (
                    rewards[i] + 
                    self.config.gamma * np.max(next_q_values[i])
                )
        
        # Train
        loss = self.model.train_on_batch(states, target_q_values)
        self.losses.append(loss)
        self.training_steps += 1
        
        # Decay exploration
        if self.epsilon > self.config.epsilon_min:
            self.epsilon *= self.config.epsilon_decay
        
        return loss
    
    def save(self, path: Path) -> None:
        """Save trained model."""
        self.model.save(str(path))
        logger.info(f"Model saved to {path}")
    
    def load(self, path: Path) -> None:
        """Load trained model."""
        self.model = keras.models.load_model(str(path))
        self.update_target_model()
        logger.info(f"Model loaded from {path}")
    
    def get_training_summary(self) -> dict:
        """Get training statistics."""
        return {
            "training_steps": self.training_steps,
            "total_episodes": 0,
            "avg_loss": float(np.mean(self.losses[-100:])) if self.losses else 0.0,
            "epsilon": float(self.epsilon),
            "memory_size": len(self.memory),
        }


# =========================================================================
# SIMPLE NUMPY VERSION (Fallback if TensorFlow unavailable)
# =========================================================================

class SimpleDQNAgent:
    """Simplified DQN using NumPy (no TensorFlow required)."""
    
    def __init__(self, config: DQNConfig = CONFIG):
        self.config = config
        self.memory = ReplayMemory(config.memory_size)
        
        # Simple linear approximator: Q(s,a) = w^T * phi(s)
        self.q_weights = np.random.randn(
            config.state_size, 
            config.action_size
        ) * 0.01
        
        self.epsilon = config.epsilon
        self.losses: List[float] = []
        self.training_steps = 0
        
        logger.info(
            f"SimpleDQNAgent initialized (NumPy) | "
            f"Weights: {self.q_weights.shape}"
        )
    
    def remember(self, experience: Experience) -> None:
        """Store experience in replay memory."""
        self.memory.add(experience)
    
    def act(self, state: np.ndarray) -> int:
        """Choose action using epsilon-greedy policy."""
        if np.random.random() < self.epsilon:
            return np.random.choice(self.config.action_size)
        else:
            q_values = state @ self.q_weights
            return np.argmax(q_values)
    
    def replay(self, batch_size: int) -> Optional[float]:
        """Learn from batch of experiences."""
        if len(self.memory) < batch_size:
            return None
        
        batch = self.memory.sample(batch_size)
        
        total_loss = 0.0
        for exp in batch:
            # Q-learning update
            q_current = exp.state @ self.q_weights
            q_next = exp.next_state @ self.q_weights
            
            # Target value
            if exp.done:
                target = exp.reward
            else:
                target = exp.reward + self.config.gamma * np.max(q_next)
            
            # TD error
            td_error = target - q_current[exp.action]
            
            # Update weights
            learning_rate = self.config.learning_rate
            self.q_weights[:, exp.action] += learning_rate * td_error * exp.state
            
            total_loss += td_error ** 2
        
        avg_loss = total_loss / batch_size
        self.losses.append(avg_loss)
        self.training_steps += 1
        
        # Decay exploration
        if self.epsilon > self.config.epsilon_min:
            self.epsilon *= self.config.epsilon_decay
        
        return avg_loss
    
    def save(self, path: Path) -> None:
        """Save weights."""
        np.save(path, self.q_weights)
        logger.info(f"Weights saved to {path}")
    
    def load(self, path: Path) -> None:
        """Load weights."""
        self.q_weights = np.load(path)
        logger.info(f"Weights loaded from {path}")
    
    def get_training_summary(self) -> dict:
        """Get training statistics."""
        return {
            "training_steps": self.training_steps,
            "total_episodes": 0,
            "avg_loss": float(np.mean(self.losses[-100:])) if self.losses else 0.0,
            "epsilon": float(self.epsilon),
            "memory_size": len(self.memory),
        }


# =========================================================================
# FACTORY & TRAINING UTILITIES
# =========================================================================

def create_agent(config: DQNConfig = CONFIG) -> object:
    """Create appropriate DQN agent based on available libraries."""
    if TF_AVAILABLE:
        logger.info("Creating TensorFlow DQN Agent")
        return DQNAgent(config)
    else:
        logger.warning("TensorFlow not available, using NumPy fallback")
        return SimpleDQNAgent(config)


def train_agent(
    agent: object,
    states: List[TradingState],
    rewards: List[float],
    episodes: int = 100,
) -> dict:
    """
    Train DQN agent on historical data.
    
    Args:
        agent: DQN agent instance
        states: List of market states
        rewards: List of rewards (P&L)
        episodes: Number of training episodes
    
    Returns:
        Training summary statistics
    """
    logger.info(f"Starting training | Episodes: {episodes}, States: {len(states)}")
    
    for episode in range(episodes):
        episode_loss = 0.0
        episode_reward = 0.0
        
        for t in range(len(states) - 1):
            # Current state
            state = states[t].to_array()
            
            # Choose action
            action = agent.act(state)
            
            # Reward and next state
            reward = rewards[t]
            next_state = states[t + 1].to_array()
            done = (t == len(states) - 2)
            
            # Store experience
            experience = Experience(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done
            )
            agent.remember(experience)
            
            # Train
            loss = agent.replay(agent.config.batch_size)
            if loss:
                episode_loss += loss
            
            episode_reward += reward
        
        # Update target network periodically
        if (episode + 1) % agent.config.update_target_freq == 0 and TF_AVAILABLE:
            agent.update_target_model()
        
        if (episode + 1) % 10 == 0:
            logger.info(
                f"Episode {episode + 1}/{episodes} | "
                f"Loss: {episode_loss:.4f} | "
                f"Reward: {episode_reward:.2f} | "
                f"Epsilon: {agent.epsilon:.3f}"
            )
    
    logger.info("Training complete")
    
    return agent.get_training_summary()


# =========================================================================
# MAIN
# =========================================================================

def main() -> None:
    """Demo training loop."""
    
    logger.info("=" * 80)
    logger.info("DQN AGENT - WEEK 3 DAY 1")
    logger.info("=" * 80)
    
    # Create agent
    agent = create_agent()
    
    # Generate synthetic training data
    logger.info("Generating synthetic training data...")
    num_states = 100
    states = [
        TradingState(
            price=400 + np.sin(t / 10) * 50,
            atr=2.0 + np.random.randn() * 0.5,
            fast_sma=401.0,
            slow_sma=400.0,
            confluence=int(np.random.random() > 0.5)
        )
        for t in range(num_states)
    ]
    
    # Generate rewards (simple strategy: long on confluence)
    rewards = [
        0.5 if states[t].confluence else -0.2
        for t in range(num_states)
    ]
    
    logger.info(f"Generated {num_states} states and rewards")
    
    # Train
    summary = train_agent(agent, states, rewards, episodes=50)
    
    logger.info(f"Training Summary: {json.dumps(summary, indent=2)}")
    
    logger.info("=" * 80)
    logger.info("DQN AGENT READY FOR WEEK 3 INTEGRATION")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
