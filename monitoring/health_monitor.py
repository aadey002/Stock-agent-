#!/usr/bin/env python3
import logging
import json
import os
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('health_monitor')

class HealthStatus(Enum):
    HEALTHY = 'healthy'
    WARNING = 'warning'
    CRITICAL = 'critical'
    OFFLINE = 'offline'

class HealthCheck:
    def __init__(self, name, status, message=''):
        self.name = name
        self.status = status
        self.message = message
        self.timestamp = datetime.now()

    def to_dict(self):
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
        logger.info('HealthMonitor initialized')

    def check_yfinance_connection(self):
        try:
            import yfinance as yf
            ticker = yf.Ticker('SPY')
            data = ticker.history(period='1d')
            if data is not None and not data.empty:
                latest_price = data['Close'].iloc[-1]
                status = HealthStatus.HEALTHY
                msg = f'yfinance OK - SPY: ${latest_price:.2f}'
            else:
                status = HealthStatus.WARNING
                msg = 'yfinance returned empty data'
        except Exception as e:
            status = HealthStatus.CRITICAL
            msg = f'yfinance error: {str(e)[:50]}'
        self.checks['api_connection'] = HealthCheck('yfinance API', status, msg)
        self.check_count += 1
        logger.info(f'API Check: {status.value} - {msg}')
        return status

    def check_data_freshness(self):
        try:
            data_file = 'data/SPY.csv'
            if not os.path.exists(data_file):
                status = HealthStatus.CRITICAL
                msg = 'SPY.csv not found'
            else:
                with open(data_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        last_line = lines[-1]
                        date_str = last_line.split(',')[0].split()[0]
                        last_date = datetime.strptime(date_str, '%Y-%m-%d')
                        days_old = (datetime.now() - last_date).days
                        if days_old <= 3:
                            status = HealthStatus.HEALTHY
                            msg = f'Data fresh - last date: {date_str}'
                        elif days_old <= 5:
                            status = HealthStatus.WARNING
                            msg = f'Data slightly stale - {days_old} days old'
                        else:
                            status = HealthStatus.CRITICAL
                            msg = f'Data stale - {days_old} days old'
                    else:
                        status = HealthStatus.CRITICAL
                        msg = 'CSV file is empty'
        except Exception as e:
            status = HealthStatus.WARNING
            msg = f'Could not check data: {str(e)[:50]}'
        self.checks['data_freshness'] = HealthCheck('Data Freshness', status, msg)
        self.check_count += 1
        logger.info(f'Data Check: {status.value} - {msg}')
        return status

    def check_all_symbols(self):
        symbols = ['SPY', 'QQQ', 'IWM', 'DIA']
        missing = []
        for symbol in symbols:
            if not os.path.exists(f'data/{symbol}.csv'):
                missing.append(symbol)
        if not missing:
            status = HealthStatus.HEALTHY
            msg = f'All {len(symbols)} symbol files present'
        elif len(missing) < len(symbols):
            status = HealthStatus.WARNING
            msg = 'Missing: ' + ', '.join(missing)
        else:
            status = HealthStatus.CRITICAL
            msg = 'All symbol files missing'
        self.checks['symbol_files'] = HealthCheck('Symbol Files', status, msg)
        self.check_count += 1
        logger.info(f'Symbol Check: {status.value} - {msg}')
        return status

    def get_overall_status(self):
        if not self.checks:
            return HealthStatus.OFFLINE
        statuses = [check.status for check in self.checks.values()]
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        return HealthStatus.HEALTHY

    def get_health_report(self):
        return {
            'overall_status': self.get_overall_status().value,
            'checks': {name: check.to_dict() for name, check in self.checks.items()},
            'total_checks': self.check_count,
            'timestamp': datetime.now().isoformat(),
        }

    def save_report(self, filepath='monitoring/health_report.json'):
        report = self.get_health_report()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f'Report saved to {filepath}')

if __name__ == '__main__':
    logger.info('=' * 60)
    logger.info('HEALTH MONITOR - LIVE CHECK')
    logger.info('=' * 60)
    monitor = HealthMonitor()
    monitor.check_yfinance_connection()
    monitor.check_data_freshness()
    monitor.check_all_symbols()
    report = monitor.get_health_report()
    logger.info('')
    logger.info('OVERALL STATUS: %s', report['overall_status'].upper())
    logger.info('')
    for name, check in report['checks'].items():
        icon = '[OK]' if check['status'] == 'healthy' else '[WARN]' if check['status'] == 'warning' else '[FAIL]'
        logger.info('  %s %s: %s - %s', icon, check['name'], check['status'].upper(), check['message'])
    monitor.save_report()
    logger.info('Health check complete!')
