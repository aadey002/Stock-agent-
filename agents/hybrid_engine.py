#!/usr/bin/env python3
"""
Hybrid Decision Engine - Multi-Agent Consensus Trading System
Week 3 Phase 3 - Hybrid Intelligence Component

Integrates three independent trading agents with a voting mechanism:
1. Base Confluence Agent (rule-based geometric analysis)
2. Gann-Elliott Strategy (Gann cycles + Elliott waves)
3. DQN Machine Learning Agent (reinforcement learning)

Trading Signal: Requires 2 or 3 agents to agree for trade confirmation
Confidence: Weighted by individual agent confidence scores
"""

import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# =========================================================================
# LOGGING SETUP
# =========================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)
logger = logging.getLogger("hybrid_engine")

# =========================================================================
# ENUMERATIONS & DATA CLASSES
# =========================================================================

class Signal(Enum):
    """Trading signals."""
    CALL = "CALL"
    PUT = "PUT"
    HOLD = "HOLD"
    ABSTAIN = "ABSTAIN"  # No consensus


class AgentType(Enum):
    """Agent types in hybrid system."""
    BASE_CONFLUENCE = "base_confluence"
    GANN_ELLIOTT = "gann_elliott"
    DQN = "dqn"


@dataclass
class AgentSignal:
    """Individual agent's trading signal."""
    
    agent_type: AgentType
    signal: Signal
    confidence: float  # 0-100
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reasoning: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent": self.agent_type.value,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 2),
            "timestamp": self.timestamp,
            "reasoning": self.reasoning,
        }


@dataclass
class HybridSignal:
    """Final consensus signal from hybrid engine."""
    
    final_signal: Signal
    confidence: float  # 0-100
    agreement_level: int  # 1, 2, or 3 (how many agents agreed)
    component_signals: List[AgentSignal] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "final_signal": self.final_signal.value,
            "confidence": round(self.confidence, 2),
            "agreement_level": self.agreement_level,
            "num_agents": len(self.component_signals),
            "timestamp": self.timestamp,
            "component_signals": [s.to_dict() for s in self.component_signals],
        }


# =========================================================================
# VOTING SYSTEM
# =========================================================================

class VotingEngine:
    """Multi-agent voting mechanism."""
    
    AGREEMENT_THRESHOLD = 2  # Minimum agents to agree for trade
    
    @staticmethod
    def aggregate_signals(signals: List[AgentSignal]) -> HybridSignal:
        """
        Aggregate multiple agent signals into final consensus signal.
        
        Voting rules:
        1. Count votes for CALL, PUT, HOLD
        2. If consensus (2+ agents agree) → signal that direction
        3. If split → HOLD (no strong consensus)
        4. If all HOLD → ABSTAIN (no opportunity)
        
        Args:
            signals: List of agent signals
        
        Returns:
            Hybrid consensus signal
        """
        if not signals:
            logger.warning("No signals to aggregate")
            return HybridSignal(
                final_signal=Signal.ABSTAIN,
                confidence=0.0,
                agreement_level=0,
                component_signals=[]
            )
        
        # Count votes
        call_votes = [s for s in signals if s.signal == Signal.CALL]
        put_votes = [s for s in signals if s.signal == Signal.PUT]
        hold_votes = [s for s in signals if s.signal == Signal.HOLD]
        
        logger.info(
            f"Vote count | CALL: {len(call_votes)}, "
            f"PUT: {len(put_votes)}, HOLD: {len(hold_votes)}"
        )
        
        # Determine final signal and agreement level
        all_votes = [
            (Signal.CALL, call_votes),
            (Signal.PUT, put_votes),
            (Signal.HOLD, hold_votes),
        ]
        
        # Sort by vote count
        all_votes.sort(key=lambda x: len(x[1]), reverse=True)
        winning_signal, winning_votes = all_votes[0]
        
        # Check if consensus
        if len(winning_votes) < VotingEngine.AGREEMENT_THRESHOLD:
            logger.info("No consensus - returning ABSTAIN")
            final_signal = Signal.ABSTAIN
            agreement_level = len(winning_votes)
        else:
            final_signal = winning_signal
            agreement_level = len(winning_votes)
        
        # Calculate confidence
        if agreement_level > 0:
            avg_confidence = sum(v.confidence for v in winning_votes) / agreement_level
            confidence = min(avg_confidence, 100.0)
        else:
            confidence = 0.0
        
        logger.info(
            f"Final decision | Signal: {final_signal.value}, "
            f"Agreement: {agreement_level}, Confidence: {confidence:.1f}"
        )
        
        return HybridSignal(
            final_signal=final_signal,
            confidence=confidence,
            agreement_level=agreement_level,
            component_signals=signals,
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def confidence_weight(signal: AgentSignal) -> float:
        """
        Weight agent signal by confidence.
        
        Higher confidence = more weight in final decision
        """
        return signal.confidence / 100.0


# =========================================================================
# RISK MANAGEMENT
# =========================================================================

@dataclass
class PositionSizing:
    """Position size calculation from hybrid signal."""
    
    signal: HybridSignal
    account_balance: float = 100000.0
    
    # Risk parameters
    risk_per_trade: float = 1.0  # % of account
    max_position_pct: float = 5.0  # Max 5% of account
    kelly_factor: float = 0.25  # Conservative Kelly
    
    def calculate_size(self, entry_price: float, stop_price: float) -> int:
        """
        Calculate position size using Kelly Criterion with confidence weighting.
        
        Formula:
        f = (bp - q) / b  (Kelly)
        where:
        - f = fraction of bankroll to bet
        - b = odds (target/stop ratio)
        - p = win probability
        - q = loss probability
        
        We weight by:
        - Confidence from DQN
        - Agreement level (more agents agree = more conservative)
        """
        
        # Risk amount
        risk_amount = self.account_balance * (self.risk_per_trade / 100.0)
        price_risk = abs(entry_price - stop_price)
        
        if price_risk <= 0.01:
            logger.warning("Stop too close to entry, returning min size")
            return 1
        
        # Base position size
        base_size = int(risk_amount / price_risk)
        
        # Adjust by confidence and agreement
        confidence_factor = self.signal.confidence / 100.0
        agreement_factor = self.signal.agreement_level / 3.0
        
        weighted_size = int(base_size * confidence_factor * agreement_factor)
        
        # Apply max position limit
        max_size = int((self.account_balance * self.max_position_pct) / 100.0 / entry_price)
        final_size = min(weighted_size, max_size)
        
        logger.debug(
            f"Position sizing | Base: {base_size}, Confidence: {confidence_factor:.2f}, "
            f"Agreement: {agreement_factor:.2f}, Final: {final_size}"
        )
        
        return max(final_size, 1)


# =========================================================================
# HYBRID ENGINE
# =========================================================================

class HybridEngine:
    """Main decision engine coordinating multiple agents."""
    
    def __init__(
        self,
        account_balance: float = 100000.0,
        data_dir: Path = Path("data"),
        report_dir: Path = Path("reports")
    ):
        self.account_balance = account_balance
        self.data_dir = Path(data_dir)
        self.report_dir = Path(report_dir)
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Trading history
        self.voting_log: List[HybridSignal] = []
        self.trade_log: List[dict] = []
        
        logger.info(
            f"HybridEngine initialized | "
            f"Account: ${account_balance:,.0f} | "
            f"Data dir: {self.data_dir}"
        )
    
    def process_signals(self, agent_signals: List[AgentSignal]) -> HybridSignal:
        """
        Process multiple agent signals and generate consensus.
        
        Args:
            agent_signals: Signals from base, Gann, and DQN agents
        
        Returns:
            Final hybrid signal with consensus decision
        """
        logger.info(f"Processing {len(agent_signals)} agent signals")
        
        # Aggregate signals
        hybrid_signal = VotingEngine.aggregate_signals(agent_signals)
        
        # Log the voting
        self.voting_log.append(hybrid_signal)
        
        return hybrid_signal
    
    def generate_trade(
        self,
        signal: HybridSignal,
        entry_price: float,
        stop_price: float,
        target1_price: float,
        target2_price: float,
    ) -> Optional[dict]:
        """
        Generate trade from hybrid signal if consensus exists.
        
        Args:
            signal: Hybrid consensus signal
            entry_price: Entry price
            stop_price: Stop loss price
            target1_price: First target (2R)
            target2_price: Second target (3R)
        
        Returns:
            Trade dictionary or None if no consensus
        """
        
        # Only generate trade if strong consensus
        if signal.final_signal == Signal.ABSTAIN:
            logger.info("No consensus - skipping trade generation")
            return None
        
        # Calculate position size
        sizing = PositionSizing(signal, self.account_balance)
        size = sizing.calculate_size(entry_price, stop_price)
        
        # Create trade
        trade = {
            "symbol": "SPY",
            "signal": signal.final_signal.value,
            "entry_date": signal.timestamp.split("T")[0],
            "entry_price": round(entry_price, 2),
            "stop_price": round(stop_price, 2),
            "target1": round(target1_price, 2),
            "target2": round(target2_price, 2),
            "position_size": size,
            "confidence": round(signal.confidence, 2),
            "agreement_level": signal.agreement_level,
            "status": "OPEN",
        }
        
        self.trade_log.append(trade)
        
        logger.info(
            f"Generated trade | Signal: {signal.final_signal.value}, "
            f"Size: {size}, Price: ${entry_price:.2f}"
        )
        
        return trade
    
    def save_voting_log(self) -> None:
        """Save voting history to JSON."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "total_votes": len(self.voting_log),
            "votes": [v.to_dict() for v in self.voting_log],
        }
        
        path = self.data_dir / "voting_log.json"
        with path.open("w") as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"Voting log saved to {path}")
    
    def save_trades(self) -> None:
        """Save trades to CSV."""
        if not self.trade_log:
            logger.info("No trades to save")
            return
        
        path = self.report_dir / "portfolio_hybrid.csv"
        
        fieldnames = [
            "symbol", "signal", "entry_date", "entry_price", "stop_price",
            "target1", "target2", "position_size", "confidence",
            "agreement_level", "status"
        ]
        
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.trade_log)
        
        logger.info(f"Trades saved to {path} ({len(self.trade_log)} trades)")
    
    def get_summary(self) -> dict:
        """Get engine summary statistics."""
        total_votes = len(self.voting_log)
        consensus_votes = sum(
            1 for v in self.voting_log 
            if v.final_signal != Signal.ABSTAIN
        )
        
        return {
            "total_votes": total_votes,
            "consensus_trades": consensus_votes,
            "consensus_rate": (consensus_votes / total_votes * 100) if total_votes > 0 else 0,
            "total_trades": len(self.trade_log),
            "avg_confidence": (
                sum(v.confidence for v in self.voting_log) / total_votes
                if total_votes > 0 else 0
            ),
        }


# =========================================================================
# DEMO
# =========================================================================

def demo():
    """Demo hybrid engine with simulated agent signals."""
    
    logger.info("=" * 80)
    logger.info("HYBRID ENGINE DEMO")
    logger.info("=" * 80)
    
    # Initialize engine
    engine = HybridEngine()
    
    # Simulate 5 trading scenarios
    scenarios = [
        {
            "name": "Full Consensus CALL",
            "signals": [
                AgentSignal(AgentType.BASE_CONFLUENCE, Signal.CALL, 85, reasoning="Price at confluence"),
                AgentSignal(AgentType.GANN_ELLIOTT, Signal.CALL, 80, reasoning="Wave 3 setup"),
                AgentSignal(AgentType.DQN, Signal.CALL, 75, reasoning="Q-value supports upside"),
            ],
        },
        {
            "name": "Split Decision",
            "signals": [
                AgentSignal(AgentType.BASE_CONFLUENCE, Signal.CALL, 70),
                AgentSignal(AgentType.GANN_ELLIOTT, Signal.PUT, 65),
                AgentSignal(AgentType.DQN, Signal.HOLD, 60),
            ],
        },
        {
            "name": "Majority Consensus PUT",
            "signals": [
                AgentSignal(AgentType.BASE_CONFLUENCE, Signal.PUT, 80),
                AgentSignal(AgentType.GANN_ELLIOTT, Signal.PUT, 75),
                AgentSignal(AgentType.DQN, Signal.HOLD, 50),
            ],
        },
    ]
    
    for scenario in scenarios:
        logger.info(f"\n--- Scenario: {scenario['name']} ---")
        
        # Process signals
        hybrid_signal = engine.process_signals(scenario["signals"])
        
        # Generate trade if consensus
        if hybrid_signal.final_signal != Signal.ABSTAIN:
            entry = 450.00
            stop = 445.00
            t1 = 455.00
            t2 = 460.00
            
            trade = engine.generate_trade(
                hybrid_signal,
                entry_price=entry,
                stop_price=stop,
                target1_price=t1,
                target2_price=t2,
            )
        
        logger.info(f"Result: {hybrid_signal.to_dict()}")
    
    # Save results
    engine.save_voting_log()
    engine.save_trades()
    
    # Summary
    summary = engine.get_summary()
    logger.info(f"\nEngine Summary:\n{json.dumps(summary, indent=2)}")
    
    logger.info("=" * 80)
    logger.info("HYBRID ENGINE DEMO COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    demo()
