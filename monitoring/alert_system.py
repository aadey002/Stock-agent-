#!/usr/bin/env python3
import logging
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alert_system")

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Alert:
    def __init__(self, level: AlertLevel, title: str, message: str):
        self.level = level
        self.title = title
        self.message = message
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
        }

class AlertSystem:
    def __init__(self):
        self.alerts = []
        logger.info("AlertSystem initialized")
    
    def send_alert(self, level: AlertLevel, title: str, message: str) -> bool:
        alert = Alert(level, title, message)
        self.alerts.append(alert)
        logger.info(f"[{level.value.upper()}] {title}: {message}")
        return True
    
    def trade_alert(self, order_type: str, quantity: int, price: float, pnl: float = None):
        if pnl is not None:
            msg = f"TRADE: {order_type} {quantity} shares @ ${price:.2f} | P&L: ${pnl:,.2f}"
        else:
            msg = f"TRADE: {order_type} {quantity} shares @ ${price:.2f}"
        self.send_alert(AlertLevel.INFO, "Trade Executed", msg)
    
    def risk_alert(self, risk_type: str, value: float, limit: float):
        msg = f"Risk Alert: {risk_type} = {value:.2f}% (Limit: {limit:.2f}%)"
        self.send_alert(AlertLevel.WARNING, "Risk Warning", msg)
    
    def error_alert(self, error_msg: str):
        self.send_alert(AlertLevel.ERROR, "System Error", error_msg)
    
    def get_alerts(self):
        return [a.to_dict() for a in self.alerts]
    
    def get_alert_count(self) -> dict:
        info = sum(1 for a in self.alerts if a.level == AlertLevel.INFO)
        warning = sum(1 for a in self.alerts if a.level == AlertLevel.WARNING)
        error = sum(1 for a in self.alerts if a.level == AlertLevel.ERROR)
        return {'info': info, 'warning': warning, 'error': error}

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("ALERT SYSTEM - TEST")
    logger.info("=" * 60)
    
    system = AlertSystem()
    
    system.trade_alert("BUY", 100, 450.00)
    system.trade_alert("SELL", 100, 455.00, pnl=500.00)
    system.risk_alert("Drawdown", 5.2, 10.0)
    system.error_alert("Failed to connect to API")
    
    counts = system.get_alert_count()
    logger.info(f"Alert Summary: {counts}")
    logger.info("=" * 60)