#!/usr/bin/env python3
"""
Unit Tests for Health Monitor
==============================

Tests the health monitoring system functionality.

Usage:
    python test_health_monitor.py
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from monitoring.health_monitor import HealthMonitor


class TestHealthMonitor(unittest.TestCase):
    """Test cases for HealthMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = HealthMonitor()
    
    def test_monitor_initialization(self):
        """Test that monitor initializes correctly."""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.start_time.date(), datetime.now().date())
    
    def test_check_api_connection(self):
        """Test API connection check."""
        # This will actually test the API if TIINGO_TOKEN is set
        result = self.monitor.check_api_connection()
        
        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertIn(result['status'], ['HEALTHY', 'UNHEALTHY'])
    
    def test_check_data_feed(self):
        """Test data feed check."""
        result = self.monitor.check_data_feed()
        
        self.assertIn('status', result)
        self.assertIn('message', result)
        # Status could be HEALTHY, DEGRADED, or UNHEALTHY
        self.assertIn(result['status'], ['HEALTHY', 'DEGRADED', 'UNHEALTHY'])
    
    def test_check_portfolio(self):
        """Test portfolio check."""
        result = self.monitor.check_portfolio()
        
        self.assertIn('status', result)
        self.assertIn('message', result)
    
    def test_check_performance(self):
        """Test performance check."""
        result = self.monitor.check_performance()
        
        self.assertIn('status', result)
        self.assertIn('message', result)
    
    def test_run_all_checks(self):
        """Test running all health checks."""
        results = self.monitor.run_all_checks()
        
        self.assertIsInstance(results, dict)
        self.assertIn('checks', results)
        self.assertIn('overall_status', results)
        
        # Verify all 4 checks are present
        checks = results['checks']
        self.assertEqual(len(checks), 4)
        self.assertIn('API Connection', checks)
        self.assertIn('Data Feed', checks)
        self.assertIn('Portfolio', checks)
        self.assertIn('Performance', checks)
    
    def test_overall_status_logic(self):
        """Test overall status determination."""
        results = self.monitor.run_all_checks()
        overall = results['overall_status']
        
        # Overall status should be one of these three
        self.assertIn(overall, ['HEALTHY', 'DEGRADED', 'UNHEALTHY'])
        
        # If all checks are healthy, overall should be healthy
        all_healthy = all(
            check['status'] == 'HEALTHY' 
            for check in results['checks'].values()
        )
        if all_healthy:
            self.assertEqual(overall, 'HEALTHY')
    
    def test_save_report(self):
        """Test saving health report."""
        results = self.monitor.run_all_checks()
        
        # Save to temp file
        test_file = 'monitoring/test_health_report.json'
        
        try:
            with open(test_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Verify file exists and is valid JSON
            self.assertTrue(os.path.exists(test_file))
            
            with open(test_file, 'r') as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded['overall_status'], results['overall_status'])
        
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)


class TestHealthMonitorEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = HealthMonitor()
    
    def test_missing_data_files(self):
        """Test behavior when data files are missing."""
        # This should not crash, but return UNHEALTHY or DEGRADED
        result = self.monitor.check_data_feed()
        self.assertIsInstance(result, dict)
    
    def test_invalid_api_token(self):
        """Test behavior with invalid API token."""
        # Save original token
        original_token = os.environ.get('TIINGO_TOKEN')
        
        try:
            # Set invalid token
            os.environ['TIINGO_TOKEN'] = 'invalid_token_12345'
            
            monitor = HealthMonitor()
            result = monitor.check_api_connection()
            
            # Should return UNHEALTHY, not crash
            self.assertEqual(result['status'], 'UNHEALTHY')
        
        finally:
            # Restore original token
            if original_token:
                os.environ['TIINGO_TOKEN'] = original_token
            else:
                os.environ.pop('TIINGO_TOKEN', None)
    
    def test_performance_with_no_trades(self):
        """Test performance check when no trades exist."""
        result = self.monitor.check_performance()
        
        # Should handle gracefully
        self.assertIn('status', result)
        self.assertIsInstance(result['message'], str)


def run_tests():
    """Run all tests and generate report."""
    print("=" * 70)
    print("HEALTH MONITOR TEST SUITE")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestHealthMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestHealthMonitorEdgeCases))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())