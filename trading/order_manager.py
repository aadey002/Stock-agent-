#!/usr/bin/env python3
import logging
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_manager")

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"

class Order:
    def __init__(self, order_id: str, symbol: str, side: OrderSide, quantity: int, price: float):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.filled_quantity = 0
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.order_counter = 0
        logger.info("OrderManager initialized")
    
    def create_order(self, symbol: str, side: OrderSide, quantity: int, price: float) -> str:
        self.order_counter += 1
        order_id = f"ORD-{self.order_counter:05d}"
        order = Order(order_id, symbol, side, quantity, price)
        self.orders[order_id] = order
        logger.info(f"✓ Created {order_id}: {side.value} {quantity} {symbol} @ ${price:.2f}")
        return order_id
    
    def fill_order(self, order_id: str, filled_qty: int, price: float) -> bool:
        if order_id not in self.orders:
            return False
        order = self.orders[order_id]
        order.filled_quantity = filled_qty
        order.status = OrderStatus.FILLED if filled_qty == order.quantity else OrderStatus.PENDING
        logger.info(f"✓ Filled {order_id}: {filled_qty} shares @ ${price:.2f}")
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        if order_id not in self.orders:
            return False
        self.orders[order_id].status = OrderStatus.CANCELLED
        logger.info(f"✓ Cancelled {order_id}")
        return True
    
    def get_order(self, order_id: str):
        return self.orders.get(order_id)
    
    def get_statistics(self) -> dict:
        filled = sum(1 for o in self.orders.values() if o.status == OrderStatus.FILLED)
        cancelled = sum(1 for o in self.orders.values() if o.status == OrderStatus.CANCELLED)
        pending = sum(1 for o in self.orders.values() if o.status == OrderStatus.PENDING)
        return {
            'total_orders': len(self.orders),
            'pending_orders': pending,
            'filled_orders': filled,
            'cancelled_orders': cancelled
        }

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("ORDER MANAGER - TEST")
    logger.info("=" * 60)
    
    manager = OrderManager()
    oid1 = manager.create_order("SPY", OrderSide.BUY, 100, 450.00)
    oid2 = manager.create_order("SPY", OrderSide.SELL, 50, 455.00)
    oid3 = manager.create_order("SPY", OrderSide.BUY, 75, 452.00)
    
    manager.fill_order(oid1, 100, 450.00)
    manager.fill_order(oid2, 50, 455.00)
    manager.cancel_order(oid3)
    
    stats = manager.get_statistics()
    logger.info(f"Statistics: {stats}")
    logger.info("=" * 60)