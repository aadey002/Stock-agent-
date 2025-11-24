#!/usr/bin/env python3
"""
Master Runner - Execute All Trading Agents
===========================================

Runs all three agents in sequence:
1. Base Confluence Agent
2. DQN Agent  
3. Hybrid Multi-Agent System

Usage:
    python run_all_agents.py
"""

import logging
import subprocess
import sys
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

def run_agent(script_name, description):
    """Run a single agent script."""
    logger.info("=" * 70)
    logger.info(f"Starting: {description}")
    logger.info("=" * 70)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✓ {description} completed in {elapsed:.1f}s")
            return True
        else:
            logger.error(f"✗ {description} failed")
            logger.error(f"STDERR: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"✗ {description} failed with exception: {e}")
        return False

def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("  MULTI-AGENT TRADING SYSTEM")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    overall_start = time.time()
    
    # Run Agent 1: Base Confluence
    success_1 = run_agent("agent.py", "Agent 1: Base Confluence + Gann-Elliott")
    
    if not success_1:
        logger.error("Agent 1 failed. Aborting.")
        return 1
    
    # Run Agent 2: DQN
    success_2 = run_agent("agent_dqn.py", "Agent 2: DQN Reinforcement Learning")
    
    # Run Agent 3: Hybrid (even if DQN fails)
    success_3 = run_agent("agent_hybrid.py", "Agent 3: Hybrid Multi-Agent System")
    
    # Summary
    elapsed = time.time() - overall_start
    
    print("\n" + "=" * 70)
    print("  EXECUTION COMPLETE")
    print("=" * 70)
    print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    if success_1 and success_3:
        print("\n✅ All agents completed successfully!")
        return 0
    else:
        print("\n❌ Some agents failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())