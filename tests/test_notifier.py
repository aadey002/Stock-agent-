#!/usr/bin/env python3
"""
Unit Tests for Notification System
===================================

Tests the notification system functionality.

Usage:
    python test_notifier.py
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from notifications.notifier import Notifier


class TestNotifier(unittest.TestCase):
    """Test cases for Notifier class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.notifier = Notifier()
    
    def test_notifier_initialization(self):
        """Test that notifier initializes correctly."""
        self.assertIsNotNone(self.notifier)
        self.assertIsInstance(self.notifier.email_enabled, bool)
        self.assertIsInstance(self.notifier.discord_enabled, bool)
        self.assertIsInstance(self.notifier.slack_enabled, bool)
    
    def test_send_alert_basic(self):
        """Test basic alert sending."""
        # This tests the function doesn't crash
        # Actual sending depends on configuration
        result = self.notifier.send_alert(
            "Test Alert",
            "This is a test message",
            "INFO"
        )
        
        # Should return a boolean
        self.assertIsInstance(result, bool)
    
    def test_send_trading_signal(self):
        """Test trading signal notification."""
        test_signal = {
            'Signal': 'CALL',
            'EntryPrice': 450.50,
            'Stop': 445.00,
            'Target1': 460.00,
            'Confidence': 0.85
        }
        
        result = self.notifier.send_trading_signal(test_signal)
        self.assertIsInstance(result, bool)
    
    def test_send_health_alert(self):
        """Test health alert notification."""
        test_health = {
            'overall_status': 'HEALTHY',
            'checks': {
                'api': {'status': 'HEALTHY'},
                'data': {'status': 'HEALTHY'}
            }
        }
        
        # Healthy status shouldn't send alert
        result = self.notifier.send_health_alert(test_health)
        self.assertTrue(result)
        
        # Unhealthy status should attempt to send
        test_health['overall_status'] = 'UNHEALTHY'
        test_health['checks']['api']['status'] = 'UNHEALTHY'
        
        result = self.notifier.send_health_alert(test_health)
        self.assertIsInstance(result, bool)
    
    def test_send_daily_summary(self):
        """Test daily summary notification."""
        test_performance = {
            'total_trades': 12,
            'win_rate': 0.58,
            'avg_return': 0.023,
            'total_pnl': 1250.75
        }
        
        result = self.notifier.send_daily_summary(test_performance)
        self.assertIsInstance(result, bool)
    
    def test_alert_severity_levels(self):
        """Test different severity levels."""
        severities = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for severity in severities:
            result = self.notifier.send_alert(
                f"Test {severity}",
                f"Testing {severity} level",
                severity
            )
            self.assertIsInstance(result, bool)


class TestNotifierConfiguration(unittest.TestCase):
    """Test notifier configuration handling."""
    
    def test_no_channels_enabled(self):
        """Test behavior when no channels are enabled."""
        # Save original environment
        orig_discord = os.environ.get('DISCORD_ENABLED')
        orig_slack = os.environ.get('SLACK_ENABLED')
        orig_email = os.environ.get('EMAIL_ENABLED')
        
        try:
            # Disable all channels
            os.environ['DISCORD_ENABLED'] = 'false'
            os.environ['SLACK_ENABLED'] = 'false'
            os.environ['EMAIL_ENABLED'] = 'false'
            
            notifier = Notifier()
            
            # Should still work (logs to console)
            result = notifier.send_alert("Test", "Message", "INFO")
            self.assertIsInstance(result, bool)
        
        finally:
            # Restore environment
            if orig_discord:
                os.environ['DISCORD_ENABLED'] = orig_discord
            if orig_slack:
                os.environ['SLACK_ENABLED'] = orig_slack
            if orig_email:
                os.environ['EMAIL_ENABLED'] = orig_email


def run_tests():
    """Run all tests and generate report."""
    print("=" * 70)
    print("NOTIFIER TEST SUITE")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestNotifierConfiguration))
    
    # Run tests
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
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())