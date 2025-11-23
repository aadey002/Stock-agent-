#!/usr/bin/env python3
import logging
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("paper_trader")

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class Position:
    def __init__(self, symbol: str, quantity: int, entry_price: float):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.current_price = entry_price
    
    def update_price(self, price: float):
        self.current_price = price
    
    def get_unrealized_pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity

class Trade:
    def __init__(self, trade_id: str, symbol: str, entry_price: float, exit_price: float, quantity: int):
        self.trade_id = trade_id
        self.symbol = symbol
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.pnl = (exit_price - entry_price) * quantity
        self.return_pct = ((exit_price - entry_price) / entry_price) * 100

class PaperTrader:
    def __init__(self, initial_capital: float, symbol: str = "SPY"):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.symbol = symbol
        self.positions = {}
        self.trades = []
        self.realized_pnl = 0.0
        self.trade_counter = 0
        logger.info(f"PaperTrader initialized with ${initial_capital:,.2f}")
    
    def execute_order(self, order: dict, price: float) -> bool:
        try:
            if order['side'] == 'buy':
                cost = order['quantity'] * price
                if cost > self.cash:
                    logger.error("Insufficient cash")
                    return False
                self.cash -= cost
                if self.symbol in self.positions:
                    pos = self.positions[self.symbol]
                    pos.quantity += order['quantity']
                else:
                    self.positions[self.symbol] = Position(self.symbol, order['quantity'], price)
                logger.info(f"Order: buy {order['quantity']} @ ${price:.2f}")
                return True
            elif order['side'] == 'sell':
                if self.symbol not in self.positions:
                    logger.error("No position to sell")
                    return False
                pos = self.positions[self.symbol]
                if pos.quantity < order['quantity']:
                    logger.error("Insufficient shares")
                    return False
                pnl = (price - pos.entry_price) * order['quantity']
                self.realized_pnl += pnl
                self.trade_counter += 1
                trade = Trade(f"TRD-{self.trade_counter:05d}", self.symbol, pos.entry_price, price, order['quantity'])
                self.trades.append(trade)
                self.cash += price * order['quantity']
                pos.quantity -= order['quantity']
                logger.info(f"✓ SELL {order['quantity']} @ ${price:.2f} | P&L: ${pnl:,.2f}")
                return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
    
    def update_prices(self, prices: dict):
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)
    
    def get_portfolio_value(self) -> float:
        value = self.cash
        for pos in self.positions.values():
            value += pos.quantity * pos.current_price
        return value
    
    def get_portfolio_metrics(self) -> dict:
        portfolio_value = self.get_portfolio_value()
        unrealized_pnl = sum(pos.get_unrealized_pnl() for pos in self.positions.values())
        total_pnl = self.realized_pnl + unrealized_pnl
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        losing_trades = sum(1 for t in self.trades if t.pnl < 0)
        total_trades = len(self.trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        return {
            'portfolio_value': portfolio_value,
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'total_pnl': total_pnl,
            'total_return_pct': (total_pnl / self.initial_capital * 100) if self.initial_capital > 0 else 0,
            'total_trades': total_trades,
            'win_rate_pct': win_rate
        }

if __name__ == "__main__":
    logger.info("PAPER TRADING ENGINE - WEEK 4")
    trader = PaperTrader(100000.0, "SPY")
    trader.execute_order({'side': 'buy', 'quantity': 100}, 450.00)
    trader.update_prices({"SPY": 455.00})
    trader.execute_order({'side': 'sell', 'quantity': 100}, 455.00)
    metrics = trader.get_portfolio_metrics()
    logger.info(f"Portfolio Value: ${metrics['portfolio_value']:,.2f}")
    logger.info(f"Total P&L: ${metrics['total_pnl']:,.2f}")
    logger.info(f"Return: {metrics['total_return_pct']:.2f}%")
    logger.info("PAPER TRADING READY")