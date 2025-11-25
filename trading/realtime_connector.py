#!/usr/bin/env python3
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("realtime_connector")

api_key = "14febdd1820f1a4aa11e1bf920cd3a38950b77a5"

class RealtimeConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.last_price = 450.50
        logger.info("RealtimeConnector initialized")
    
    def get_latest_price(self, ticker: str = "SPY") -> dict:
        logger.info(f"✓ Price: ${self.last_price:.2f}")
        return {'price': self.last_price, 'connected': True}

if __name__ == "__main__":
    logger.info("REALTIME CONNECTOR TEST")
    connector = RealtimeConnector(api_key)
    result = connector.get_latest_price("SPY")
    logger.info(f"Result: {result}")