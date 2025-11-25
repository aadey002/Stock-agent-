"""Base Agent - Abstract class for all trading agents."""

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd


class BaseAgent(ABC):
    """Abstract base class for trading agents."""
    
    def __init__(self, name="BaseAgent"):
        self.name = name
        self.position = 0
        self.trade_history = []
    
    @abstractmethod
    def get_state(self, data, index):
        """Extract state from data."""
        pass
    
    @abstractmethod
    def get_action(self, state):
        """Determine action: 0=HOLD, 1=CALL, 2=PUT"""
        pass
    
    @abstractmethod
    def train(self, data):
        """Train the agent."""
        pass
    
    def generate_signals(self, data):
        """Generate signals for entire dataset."""
        signals = []
        for i in range(len(data)):
            try:
                state = self.get_state(data, i)
                action = self.get_action(state)
                signals.append({
                    'index': i,
                    'action': action,
                    'signal': ['HOLD', 'CALL', 'PUT'][action],
                })
            except:
                signals.append({'index': i, 'action': 0, 'signal': 'HOLD'})
        return pd.DataFrame(signals)
    
    def get_confidence(self, state):
        """Get prediction confidence."""
        return 0.5
    
    def reset(self):
        """Reset agent state."""
        self.position = 0