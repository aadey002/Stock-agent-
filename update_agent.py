import re

# Read the original file
with open('agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add yfinance import after pandas import
if 'import yfinance as yf' not in content:
    content = content.replace('import pandas as pd', 'import pandas as pd\nimport yfinance as yf')

# 2. Define the new yfinance function
new_function = '''def fetch_yfinance_daily(
    symbol: str,
    start_date: str,
    max_retries: int = MAX_RETRIES
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
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                continue
            
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
                time.sleep(2 ** attempt)
    
    logger.error(f"Failed to fetch {symbol} after {max_retries} attempts")
    return bars

'''

# 3. Replace the old Tiingo function with the new yfinance function
# Find and replace the function definition
pattern = r'def fetch_tiingo_daily_with_retry\([^)]*\)[^:]*:.*?(?=\n(?:def |class |# ===|if __name__))'
content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# 4. Replace function calls
content = content.replace('fetch_tiingo_daily_with_retry', 'fetch_yfinance_daily')

# 5. Write the updated file
with open('agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS! agent.py has been updated to use yfinance instead of Tiingo")
print("- Added: import yfinance as yf")
print("- Replaced: fetch_tiingo_daily_with_retry -> fetch_yfinance_daily")
print("- No API key needed anymore!")
