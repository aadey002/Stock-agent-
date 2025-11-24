#!/usr/bin/env python3
"""
Master Runner - Execute All Trading Agents
===========================================

Runs market conditions check first, then all trading agents:
1. Market Conditions Check (NEW!)
2. Base Confluence Agent (with Gann-Elliott)
3. DQN Agent
4. Hybrid Multi-Agent System
5. 3-Wave Profit Target Agent

Usage:
    python run_all_agents.py
    python run_all_agents.py --skip-conditions
    python run_all_agents.py --force
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = "data"
REPORTS_DIR = "reports"
MIN_SCORE_TO_TRADE = 30  # Minimum market conditions score to proceed


def run_agent(script_name, description, timeout=600):
    """
    Run a single agent script.
    
    Args:
        script_name: Python script filename
        description: Human-readable description
        timeout: Maximum execution time in seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"Starting: {description}")
    logger.info("=" * 70)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        
        # Print stdout
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            logger.info("")
            logger.info(f"✓ {description} completed successfully")
            logger.info(f"  Duration: {elapsed:.1f}s")
            return True
        else:
            logger.error(f"✗ {description} failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"  Error: {result.stderr[:500]}")
            logger.info(f"  Duration: {elapsed:.1f}s")
            return False
    
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {description} timed out after {timeout}s")
        return False
    
    except FileNotFoundError:
        logger.error(f"✗ {description} - File not found: {script_name}")
        logger.info(f"  Make sure {script_name} exists in the current directory")
        return False
    
    except Exception as e:
        logger.error(f"✗ {description} failed with exception: {e}")
        return False


def check_market_conditions():
    """
    Check market conditions before trading.
    
    Returns:
        dict: Market conditions result, or None if check failed
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("🌍 CHECKING MARKET CONDITIONS")
    logger.info("=" * 70)
    
    try:
        # Import and run market conditions check
        from market_conditions import MarketConditions
        
        mc = MarketConditions()
        result = mc.check_all()
        
        return result
        
    except ImportError:
        logger.warning("Market conditions module not found - skipping check")
        return None
    except Exception as e:
        logger.error(f"Market conditions check failed: {e}")
        return None


def load_market_conditions():
    """Load market conditions from saved file."""
    conditions_path = os.path.join(DATA_DIR, "market_conditions.json")
    
    if os.path.exists(conditions_path):
        with open(conditions_path, 'r') as f:
            return json.load(f)
    return None


def print_header():
    """Print startup header."""
    print("\n")
    print("=" * 70)
    print("  🤖 MULTI-AGENT TRADING SYSTEM - MASTER RUNNER")
    print("=" * 70)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("")


def print_market_conditions_summary(conditions):
    """Print market conditions summary."""
    if not conditions:
        return
    
    print("\n")
    print("=" * 70)
    print("  🌍 MARKET CONDITIONS SUMMARY")
    print("=" * 70)
    
    score = conditions.get('overall_score', 50)
    multiplier = conditions.get('position_size_multiplier', 1.0)
    
    # Score indicator
    if score >= 70:
        indicator = "🟢 FAVORABLE"
    elif score >= 50:
        indicator = "🟡 MODERATE"
    elif score >= 30:
        indicator = "🟠 CAUTION"
    else:
        indicator = "🔴 UNFAVORABLE"
    
    print(f"  Overall Score: {score}/100 {indicator}")
    print(f"  Position Size: {multiplier * 100:.0f}% of normal")
    
    # Individual conditions
    vol = conditions.get('conditions', {}).get('volatility', {})
    sent = conditions.get('conditions', {}).get('sentiment', {})
    rot = conditions.get('conditions', {}).get('sector_rotation', {})
    cal = conditions.get('conditions', {}).get('economic_calendar', {})
    
    print(f"\n  📊 Volatility:    {vol.get('level', 'N/A')}")
    print(f"  😊 Sentiment:     {sent.get('sentiment', 'N/A')} (Fear/Greed: {sent.get('fear_greed', 'N/A')})")
    print(f"  🔄 Rotation:      {rot.get('rotation', 'N/A')}")
    print(f"  📅 Events Today:  {cal.get('events_today', 0)} | Tomorrow: {cal.get('events_tomorrow', 0)}")
    
    # Warnings
    warnings = conditions.get('warnings', [])
    if warnings:
        print(f"\n  ⚠️ WARNINGS ({len(warnings)}):")
        for warning in warnings[:5]:  # Show max 5
            print(f"     {warning}")
    
    print("=" * 70)


def print_summary(results, elapsed, conditions=None):
    """Print execution summary."""
    print("\n")
    print("=" * 70)
    print("  📊 EXECUTION COMPLETE - SUMMARY")
    print("=" * 70)
    print(f"  Total time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Market conditions
    if conditions:
        score = conditions.get('overall_score', 50)
        multiplier = conditions.get('position_size_multiplier', 1.0)
        print(f"\n  Market Score: {score}/100 | Position Size: {multiplier * 100:.0f}%")
    
    print("\n  Agent Results:")
    print("  " + "-" * 66)
    
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {name:.<50} {status}")
    
    print("  " + "-" * 66)
    
    total_agents = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total_agents - passed
    
    print(f"  Total: {total_agents} agents | Passed: {passed} | Failed: {failed}")
    print("=" * 70)
    
    if failed == 0:
        print("\n  🎉 ALL AGENTS COMPLETED SUCCESSFULLY!")
        print("")
        print("  📊 Check your reports:")
        print("     - reports/portfolio_confluence.csv")
        print("     - reports/portfolio_gann_elliott.csv")
        print("     - reports/portfolio_dqn.csv")
        print("     - reports/portfolio_hybrid.csv")
        print("     - reports/portfolio_3_waves.csv ⭐ 3-WAVE TARGETS")
        print("     - data/market_conditions.json 🌍 MARKET CONDITIONS")
        print("")
    else:
        print(f"\n  ⚠️  {failed} agent(s) failed. Check logs for details.")
    
    print("=" * 70)
    print("")


def main():
    """Main execution."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Run all trading agents')
    parser.add_argument('--skip-conditions', action='store_true',
                       help='Skip market conditions check')
    parser.add_argument('--force', action='store_true',
                       help='Force trading even if conditions are poor')
    parser.add_argument('--conditions-only', action='store_true',
                       help='Only check market conditions, skip agents')
    args = parser.parse_args()
    
    # Print header
    print_header()
    
    overall_start = time.time()
    results = []
    conditions = None
    
    # Step 0: Check Market Conditions
    if not args.skip_conditions:
        conditions = check_market_conditions()
        
        if conditions:
            print_market_conditions_summary(conditions)
            
            score = conditions.get('overall_score', 50)
            
            # Check if we should proceed
            if score < MIN_SCORE_TO_TRADE and not args.force:
                print("\n")
                print("=" * 70)
                print("  ⛔ TRADING HALTED - Poor Market Conditions")
                print("=" * 70)
                print(f"  Score {score} is below minimum threshold ({MIN_SCORE_TO_TRADE})")
                print("  Use --force to override this check")
                print("=" * 70)
                return 1
            
            if score < 50:
                logger.warning("Market conditions unfavorable - proceeding with caution")
        
        if args.conditions_only:
            print("\n  Conditions check complete. Use without --conditions-only to run agents.")
            return 0
    else:
        logger.info("Skipping market conditions check (--skip-conditions)")
    
    # Agent 1: Base Confluence + Gann-Elliott
    logger.info("🤖 Agent 1: Base Confluence + Gann-Elliott Overlay")
    success_1 = run_agent(
        "agent.py",
        "Agent 1: Base Confluence + Gann-Elliott",
        timeout=600
    )
    results.append(("Agent 1: Confluence + Gann-Elliott", success_1))
    
    if not success_1:
        logger.error("Agent 1 failed. Aborting pipeline.")
        print_summary(results, time.time() - overall_start, conditions)
        return 1
    
    # Agent 2: DQN Reinforcement Learning
    logger.info("🤖 Agent 2: DQN Reinforcement Learning")
    success_2 = run_agent(
        "agent_dqn.py",
        "Agent 2: DQN Machine Learning",
        timeout=1200
    )
    results.append(("Agent 2: DQN Machine Learning", success_2))
    
    # Continue even if DQN fails (not critical for hybrid)
    if not success_2:
        logger.warning("Agent 2 (DQN) failed, but continuing...")
    
    # Agent 3: Hybrid Multi-Agent System
    logger.info("🤖 Agent 3: Hybrid Multi-Agent Voting System")
    success_3 = run_agent(
        "agent_hybrid.py",
        "Agent 3: Hybrid Multi-Agent System",
        timeout=600
    )
    results.append(("Agent 3: Hybrid Multi-Agent", success_3))
    
    # Agent 4: 3-Wave Profit Targets
    logger.info("🤖 Agent 4: 3-Wave Profit Target System")
    success_4 = run_agent(
        "agent_3_waves.py",
        "Agent 4: 3-Wave Profit Targets",
        timeout=600
    )
    results.append(("Agent 4: 3-Wave Profit Targets", success_4))
    
    # Calculate total time
    elapsed = time.time() - overall_start
    
    # Print summary
    print_summary(results, elapsed, conditions)
    
    # Apply position size multiplier to signals if conditions were checked
    if conditions:
        multiplier = conditions.get('position_size_multiplier', 1.0)
        if multiplier < 1.0:
            logger.info(f"📉 Position sizes should be reduced to {multiplier * 100:.0f}% due to market conditions")
    
    # Return exit code
    if all(success for _, success in results):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())