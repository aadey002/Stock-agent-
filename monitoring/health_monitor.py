#!/usr/bin/env python3
import logging
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_monitor")

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"

class HealthCheck:
    def __init__(self, name: str, status: HealthStatus, message: str = ""):
        self.name = name
        self.status = status
        self.message = message
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
        }

class HealthMonitor:
    def __init__(self):
        self.checks = {}
        self.start_time = datetime.now()
        self.check_count = 0
        logger.info("HealthMonitor initialized")
    
    def check_api_connection(self, is_connected: bool) -> HealthStatus:
        status = HealthStatus.HEALTHY if is_connected else HealthStatus.CRITICAL
        self.checks['api_connection'] = HealthCheck(
            'API Connection',
            status,
            'Tiingo API OK' if is_connected else 'Tiingo API unreachable'
        )
        self.check_count += 1
        return status
    
    def check_data_feed(self, bars_received: int, expected_bars: int) -> HealthStatus:
        if bars_received >= expected_bars * 0.95:
            status = HealthStatus.HEALTHY
            msg = f"Data quality OK ({bars_received}/{expected_bars})"
        elif bars_received >= expected_bars * 0.80:
            status = HealthStatus.WARNING
            msg = f"Data quality warning ({bars_received}/{expected_bars})"
        else:
            status = HealthStatus.CRITICAL
            msg = f"Data feed degraded ({bars_received}/{expected_bars})"
        
        self.checks['data_feed'] = HealthCheck('Data Feed', status, msg)
        self.check_count += 1
        return status
    
    def check_portfolio(self, cash: float, initial_capital: float) -> HealthStatus:
        if cash >= initial_capital * 0.50:
            status = HealthStatus.HEALTHY
            msg = f"Portfolio healthy (${cash:,.2f})"
        elif cash >= initial_capital * 0.25:
            status = HealthStatus.WARNING
            msg = f"Portfolio warning (${cash:,.2f})"
        else:
            status = HealthStatus.CRITICAL
            msg = f"Portfolio critical (${cash:,.2f})"
        
        self.checks['portfolio'] = HealthCheck('Portfolio', status, msg)
        self.check_count += 1
        return status
    
    def check_performance(self, win_rate: float) -> HealthStatus:
        if win_rate >= 0.45:
            status = HealthStatus.HEALTHY
            msg = f"Performance OK (Win rate: {win_rate:.1f}%)"
        elif win_rate >= 0.40:
            status = HealthStatus.WARNING
            msg = f"Performance warning (Win rate: {win_rate:.1f}%)"
        else:
            status = HealthStatus.CRITICAL
            msg = f"Performance critical (Win rate: {win_rate:.1f}%)"
        
        self.checks['performance'] = HealthCheck('Performance', status, msg)
        self.check_count += 1
        return status
    
    def get_overall_status(self) -> HealthStatus:
        if not self.checks:
            return HealthStatus.OFFLINE
        
        statuses = [check.status for check in self.checks.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def get_uptime(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_health_report(self) -> dict:
        uptime_seconds = self.get_uptime()
        uptime_minutes = uptime_seconds / 60
        
        return {
            'overall_status': self.get_overall_status().value,
            'checks': {name: check.to_dict() for name, check in self.checks.items()},
            'uptime_minutes': round(uptime_minutes, 1),
            'total_checks': self.check_count,
        }

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("HEALTH MONITOR - TEST")
    logger.info("=" * 60)
    
    monitor = HealthMonitor()
    
    monitor.check_api_connection(True)
    monitor.check_data_feed(95, 100)
    monitor.check_portfolio(75000, 100000)
    monitor.check_performance(55.0)
    
    logger.info("\n--- Health Report ---")
    report = monitor.get_health_report()
    logger.info(f"Overall Status: {report['overall_status'].upper()}")
    logger.info(f"Uptime: {report['uptime_minutes']:.1f} minutes")
    logger.info(f"Total Checks: {report['total_checks']}")
    
    logger.info("\n--- Individual Checks ---")
    for name, check in report['checks'].items():
        logger.info(f"  {check['name']}: {check['status'].upper()}")
    
    logger.info("=" * 60)