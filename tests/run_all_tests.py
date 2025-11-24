#!/usr/bin/env python3
"""
Master Test Runner
==================

Runs all test suites and generates comprehensive report.

Usage:
    python run_all_tests.py
"""

import sys
import os
import time
from datetime import datetime

# Add tests directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import test modules
import test_health_monitor
import test_notifier


def print_header(title):
    """Print formatted header."""
    print("\n")
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def run_all_tests():
    """Run all test suites."""
    start_time = time.time()
    
    print_header("STOCK AGENT - COMPREHENSIVE TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Run health monitor tests
    print_header("1. HEALTH MONITOR TESTS")
    result1 = test_health_monitor.run_tests()
    results.append(('Health Monitor', result1))
    
    # Run notifier tests
    print_header("2. NOTIFIER TESTS")
    result2 = test_notifier.run_tests()
    results.append(('Notifier', result2))
    
    # Print final summary
    elapsed = time.time() - start_time
    
    print_header("FINAL TEST SUMMARY")
    print(f"Total time: {elapsed:.2f} seconds")
    print()
    
    for name, code in results:
        status = "✓ PASSED" if code == 0 else "✗ FAILED"
        print(f"  {name:.<50} {status}")
    
    print()
    
    # Overall result
    all_passed = all(code == 0 for _, code in results)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
