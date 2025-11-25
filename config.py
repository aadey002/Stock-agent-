#!/usr/bin/env python3
"""
Stock Agent Configuration
=========================

Central configuration for symbols, settings, and parameters.
Add new stocks/ETFs here to include them in the system.
"""

# =============================================================================
# SYMBOL CONFIGURATION
# =============================================================================

# Primary trading symbols
PRIMARY_SYMBOLS = ['SPY']

# Watchlist - Additional symbols to track (not traded yet)
WATCHLIST = [
    'QQQ',   # Nasdaq 100
    'IWM',   # Russell 2000
    'DIA',   # Dow Jones
]

# Sector ETFs for rotation analysis
SECTOR_ETFS = {
    # Cyclical (Risk-On)
    'XLK': {'name': 'Technology', 'type': 'cyclical'},
    'XLF': {'name': 'Financials', 'type': 'cyclical'},
    'XLY': {'name': 'Consumer Discretionary', 'type': 'cyclical'},
    'XLI': {'name': 'Industrials', 'type': 'cyclical'},
    'XLB': {'name': 'Materials', 'type': 'cyclical'},
    'XLE': {'name': 'Energy', 'type': 'cyclical'},
    
    # Defensive (Risk-Off)
    'XLV': {'name': 'Healthcare', 'type': 'defensive'},
    'XLP': {'name': 'Consumer Staples', 'type': 'defensive'},
    'XLU': {'name': 'Utilities', 'type': 'defensive'},
    'XLRE': {'name': 'Real Estate', 'type': 'defensive'},
}

# Future symbols to add (requires testing)
FUTURE_SYMBOLS = [
    # Major ETFs
    'SPY', 'QQQ', 'IWM', 'DIA',
    # Sector ETFs
    'XLK', 'XLF', 'XLE', 'XLV',
    # Leveraged (higher risk)
    'TQQQ', 'SQQQ', 'UPRO', 'SPXU',
    # Individual stocks (future)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA',
]

# =============================================================================
# TRADING PARAMETERS
# =============================================================================

TRADING_CONFIG = {
    # Position sizing
    'max_position_pct': 0.10,      # Max 10% of portfolio per trade
    'max_daily_trades': 3,          # Max trades per day
    'min_confidence': 0.6,          # Minimum signal confidence
    
    # Risk management
    'stop_loss_atr_mult': 2.0,      # Stop = Entry - (ATR * 2)
    'target1_mult': 1.5,            # Target1 = 1.5R
    'target2_mult': 2.5,            # Target2 = 2.5R
    'target3_mult': 4.0,            # Target3 = 4.0R
    
    # Wave position sizing
    'wave1_pct': 0.33,              # 33% at Target1
    'wave2_pct': 0.33,              # 33% at Target2
    'wave3_pct': 0.34,              # 34% at Target3
    
    # Market conditions thresholds
    'min_score_to_trade': 30,       # Minimum market score
    'reduce_size_score': 50,        # Reduce size below this
    'max_vix': 35,                  # Don't trade above this VIX
}

# =============================================================================
# INDICATOR PARAMETERS
# =============================================================================

INDICATOR_CONFIG = {
    'fast_sma': 10,
    'slow_sma': 50,
    'atr_period': 14,
    'rsi_period': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
}

# =============================================================================
# API CONFIGURATION
# =============================================================================

API_CONFIG = {
    'tiingo_base_url': 'https://api.tiingo.com',
    'data_lookback_days': 1095,     # 3 years of data
    'request_timeout': 30,
    'max_retries': 3,
}

# =============================================================================
# BROKER CONFIGURATION (Future Use)
# =============================================================================

BROKER_CONFIG = {
    # Currently: Manual trading via alerts
    'broker': 'manual',
    
    # Future options (uncomment when ready):
    # 'broker': 'alpaca',
    # 'broker': 'td_ameritrade',
    # 'broker': 'interactive_brokers',
    
    # Paper trading mode (always start with this!)
    'paper_trading': True,
    
    # Alpaca settings (for future use)
    'alpaca': {
        'api_key': '',
        'secret_key': '',
        'base_url': 'https://paper-api.alpaca.markets',  # Paper trading
    },
}

# =============================================================================
# NOTIFICATION SETTINGS
# =============================================================================

NOTIFICATION_CONFIG = {
    'discord_enabled': False,
    'email_enabled': False,
    'slack_enabled': False,
    
    # Alert on these events
    'alert_on_signal': True,
    'alert_on_target_hit': True,
    'alert_on_stop_hit': True,
    'alert_on_market_warning': True,
}

# =============================================================================
# FILE PATHS
# =============================================================================

PATHS = {
    'data_dir': 'data',
    'reports_dir': 'reports',
    'logs_dir': 'logs',
    'web_dir': 'web',
}


def get_all_symbols():
    """Get all symbols to process."""
    return PRIMARY_SYMBOLS + WATCHLIST


def get_trading_symbols():
    """Get symbols eligible for trading."""
    return PRIMARY_SYMBOLS


def print_config():
    """Print current configuration."""
    print("=" * 60)
    print("STOCK AGENT CONFIGURATION")
    print("=" * 60)
    print(f"Primary Symbols: {PRIMARY_SYMBOLS}")
    print(f"Watchlist: {WATCHLIST}")
    print(f"Sector ETFs: {len(SECTOR_ETFS)}")
    print(f"Max Position: {TRADING_CONFIG['max_position_pct'] * 100}%")
    print(f"Min Score to Trade: {TRADING_CONFIG['min_score_to_trade']}")
    print(f"Broker: {BROKER_CONFIG['broker']}")
    print(f"Paper Trading: {BROKER_CONFIG['paper_trading']}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()