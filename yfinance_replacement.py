# =========================================================================
# YFINANCE REPLACEMENT FOR TIINGO - NO API KEY NEEDED
# =========================================================================
# Replace the fetch_tiingo_daily_with_retry function in agent.py with this

import yfinance as yf

def fetch_yfinance_daily(
    symbol: str,
    start_date: str,
    max_retries: int = 3
) -> List['Bar']:
    """
    Fetch daily OHLCV from Yahoo Finance (FREE, no API key needed).
    
    Args:
        symbol: Stock symbol (e.g., 'SPY')
        start_date: Start date in YYYY-MM-DD format
        max_retries: Maximum number of retry attempts
    
    Returns:
        List of Bar objects, empty list on failure
    """
    bars = []
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[Attempt {attempt}/{max_retries}] Fetching {symbol} from Yahoo Finance...")
            
            # Fetch data using yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                continue
            
            # Convert DataFrame to Bar objects
            for idx, row in df.iterrows():
                bar = Bar(
                    d=idx.strftime("%Y-%m-%d"),
                    open_=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume'])
                )
                bars.append(bar)
            
            logger.info(f"Successfully fetched {len(bars)} bars for {symbol}")
            return bars
            
        except Exception as e:
            logger.warning(f"Error fetching {symbol}: {e} (attempt {attempt}/{max_retries})")
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"Failed to fetch {symbol} after {max_retries} attempts")
    return bars

# =========================================================================
# ALSO UPDATE LINE ~986 IN agent.py:
# Change:  bars = fetch_tiingo_daily_with_retry(symbol, START_DATE)
# To:      bars = fetch_yfinance_daily(symbol, START_DATE)
# =========================================================================
