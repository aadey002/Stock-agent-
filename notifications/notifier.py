#!/usr/bin/env python3
"""
Notification System for Stock Agent
====================================

Supports multiple notification channels:
- Email (SMTP)
- Discord webhooks
- Slack webhooks
- Console logging

Usage:
    from notifier import Notifier
    
    notifier = Notifier()
    notifier.send_alert("System Health", "API connection failed!")
    notifier.send_daily_summary(performance_data)
"""

import json
import logging
import os
import smtplib
import urllib.request
import urllib.error
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

class Notifier:
    """Multi-channel notification system."""
    
    def __init__(self):
        """Initialize notifier with configuration from environment variables."""
        # Email configuration
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_from = os.getenv('EMAIL_FROM', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.email_to = os.getenv('EMAIL_TO', '')
        
        # Discord configuration
        self.discord_enabled = os.getenv('DISCORD_ENABLED', 'false').lower() == 'true'
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK', '')
        
        # Slack configuration
        self.slack_enabled = os.getenv('SLACK_ENABLED', 'false').lower() == 'true'
        self.slack_webhook = os.getenv('SLACK_WEBHOOK', '')
        
        logger.info("Notifier initialized")
        logger.info(f"Email: {self.email_enabled}, Discord: {self.discord_enabled}, Slack: {self.slack_enabled}")
    
    def send_alert(self, title: str, message: str, severity: str = "INFO") -> bool:
        """
        Send alert notification across all enabled channels.
        
        Args:
            title: Alert title
            message: Alert message
            severity: INFO, WARNING, ERROR, CRITICAL
        
        Returns:
            True if at least one channel succeeded
        """
        logger.info(f"Sending alert: {title} [{severity}]")
        
        success = False
        
        # Send to all enabled channels
        if self.email_enabled:
            success |= self._send_email_alert(title, message, severity)
        
        if self.discord_enabled:
            success |= self._send_discord_alert(title, message, severity)
        
        if self.slack_enabled:
            success |= self._send_slack_alert(title, message, severity)
        
        # Always log to console
        logger.info(f"[{severity}] {title}: {message}")
        
        return success
    
    def send_trading_signal(self, signal: Dict) -> bool:
        """
        Send notification about new trading signal.
        
        Args:
            signal: Dictionary with signal details
        
        Returns:
            True if sent successfully
        """
        direction = signal.get('Signal', 'UNKNOWN')
        entry = signal.get('EntryPrice', 0)
        stop = signal.get('Stop', 0)
        target = signal.get('Target1', 0)
        confidence = signal.get('Confidence', 'N/A')
        
        title = f"🎯 New Trading Signal: {direction}"
        message = f"""
New trading signal generated!

Direction: {direction}
Entry Price: ${entry:.2f}
Stop Loss: ${stop:.2f}
Target: ${target:.2f}
Confidence: {confidence}

Risk/Reward: {((target - entry) / (entry - stop)):.2f}R

Review the signal in your dashboard before taking action.
        """.strip()
        
        return self.send_alert(title, message, "INFO")
    
    def send_health_alert(self, health_data: Dict) -> bool:
        """
        Send notification about system health issues.
        
        Args:
            health_data: Health check results
        
        Returns:
            True if sent successfully
        """
        status = health_data.get('overall_status', 'UNKNOWN')
        checks = health_data.get('checks', {})
        
        # Only send alerts for unhealthy states
        if status == 'HEALTHY':
            return True
        
        severity = "WARNING" if status == "DEGRADED" else "ERROR"
        
        failed_checks = [
            name for name, result in checks.items() 
            if result.get('status') != 'HEALTHY'
        ]
        
        title = f"🚨 System Health Alert: {status}"
        message = f"""
System health check detected issues!

Overall Status: {status}
Failed Checks: {', '.join(failed_checks)}

Please review the system immediately.
Check logs for detailed information.
        """.strip()
        
        return self.send_alert(title, message, severity)
    
    def send_daily_summary(self, performance: Dict) -> bool:
        """
        Send daily performance summary.
        
        Args:
            performance: Performance metrics dictionary
        
        Returns:
            True if sent successfully
        """
        total_trades = performance.get('total_trades', 0)
        win_rate = performance.get('win_rate', 0) * 100
        avg_return = performance.get('avg_return', 0) * 100
        total_pnl = performance.get('total_pnl', 0)
        
        title = "📊 Daily Trading Summary"
        message = f"""
Daily Performance Report - {datetime.now().strftime('%Y-%m-%d')}

Total Trades: {total_trades}
Win Rate: {win_rate:.1f}%
Average Return: {avg_return:+.2f}%
Total P&L: ${total_pnl:+.2f}

Keep up the good work!
        """.strip()
        
        return self.send_alert(title, message, "INFO")
    
    # === Private methods for each channel ===
    
    def _send_email_alert(self, title: str, message: str, severity: str) -> bool:
        """Send alert via email."""
        if not self.email_enabled or not self.email_from or not self.email_to:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"[{severity}] {title}"
            
            body = f"""
Stock Agent Notification
========================

{message}

---
Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Severity: {severity}
            """.strip()
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            logger.info("Email alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _send_discord_alert(self, title: str, message: str, severity: str) -> bool:
        """Send alert via Discord webhook."""
        if not self.discord_enabled or not self.discord_webhook:
            return False
        
        try:
            # Color codes based on severity
            colors = {
                'INFO': 3447003,      # Blue
                'WARNING': 16776960,  # Yellow
                'ERROR': 16711680,    # Red
                'CRITICAL': 10038562  # Dark Red
            }
            
            # Emoji based on severity
            emojis = {
                'INFO': '📘',
                'WARNING': '⚠️',
                'ERROR': '🚨',
                'CRITICAL': '🔥'
            }
            
            payload = {
                'embeds': [{
                    'title': f"{emojis.get(severity, '📢')} {title}",
                    'description': message,
                    'color': colors.get(severity, 3447003),
                    'timestamp': datetime.utcnow().isoformat(),
                    'footer': {
                        'text': f'Stock Agent | {severity}'
                    }
                }]
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.discord_webhook,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 204:
                    logger.info("Discord alert sent successfully")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False
    
    def _send_slack_alert(self, title: str, message: str, severity: str) -> bool:
        """Send alert via Slack webhook."""
        if not self.slack_enabled or not self.slack_webhook:
            return False
        
        try:
            # Emoji based on severity
            emojis = {
                'INFO': ':information_source:',
                'WARNING': ':warning:',
                'ERROR': ':x:',
                'CRITICAL': ':fire:'
            }
            
            payload = {
                'text': f"{emojis.get(severity, ':bell:')} *{title}*",
                'blocks': [
                    {
                        'type': 'header',
                        'text': {
                            'type': 'plain_text',
                            'text': f"{emojis.get(severity, ':bell:')} {title}"
                        }
                    },
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': message
                        }
                    },
                    {
                        'type': 'context',
                        'elements': [
                            {
                                'type': 'mrkdwn',
                                'text': f"*Severity:* {severity} | *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.slack_webhook,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info("Slack alert sent successfully")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


def main():
    """Test notification system."""
    print("=" * 60)
    print("NOTIFICATION SYSTEM TEST")
    print("=" * 60)
    
    notifier = Notifier()
    
    # Test alert
    print("\n1. Testing basic alert...")
    notifier.send_alert(
        "Test Alert",
        "This is a test notification from the Stock Agent system.",
        "INFO"
    )
    
    # Test trading signal
    print("\n2. Testing trading signal...")
    test_signal = {
        'Signal': 'CALL',
        'EntryPrice': 450.50,
        'Stop': 445.00,
        'Target1': 460.00,
        'Confidence': 0.85
    }
    notifier.send_trading_signal(test_signal)
    
    # Test health alert
    print("\n3. Testing health alert...")
    test_health = {
        'overall_status': 'DEGRADED',
        'checks': {
            'api': {'status': 'HEALTHY'},
            'data_feed': {'status': 'UNHEALTHY'},
            'portfolio': {'status': 'HEALTHY'}
        }
    }
    notifier.send_health_alert(test_health)
    
    # Test daily summary
    print("\n4. Testing daily summary...")
    test_performance = {
        'total_trades': 12,
        'win_rate': 0.58,
        'avg_return': 0.023,
        'total_pnl': 1250.75
    }
    notifier.send_daily_summary(test_performance)
    
    print("\n" + "=" * 60)
    print("NOTIFICATION TEST COMPLETE")
    print("=" * 60)
    print("\nCheck configured channels for test messages!")


if __name__ == "__main__":
    main()