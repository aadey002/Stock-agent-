#!/usr/bin/env python3
import os, csv, urllib.request, json, time
from datetime import datetime, timedelta

SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA']
TOKEN = os.environ.get('TIINGO_TOKEN', '')

def fetch(symbol):
    if not TOKEN: return None
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=750)).strftime('%Y-%m-%d')
    url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices?startDate={start}&endDate={end}&token={TOKEN}"
    print(f"Fetching {symbol}...")
    try:
        req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
            print(f"  Got {len(data)} bars")
            return data
    except Exception as e:
        print(f"  Error: {e}")
        return None

def calc(bars):
    for i, b in enumerate(bars):
        b['ATR'] = abs(b['high']-b['low']) if i < 14 else sum(max(bars[j]['high']-bars[j]['low'], abs(bars[j]['high']-bars[j-1]['close']), abs(bars[j]['low']-bars[j-1]['close'])) for j in range(i-13,i+1))/14
        c9 = [bars[j]['close'] for j in range(max(0,i-8),i+1)]
        c21 = [bars[j]['close'] for j in range(max(0,i-20),i+1)]
        b['FastSMA'], b['SlowSMA'] = sum(c9)/len(c9), sum(c21)/len(c21)
        b['Bias'] = 'BULLISH' if b['FastSMA'] > b['SlowSMA'] else 'BEARISH' if b['FastSMA'] < b['SlowSMA'] else 'NEUTRAL'
        b['GeoLevel'], b['PhiLevel'] = round((b['close']**0.5+0.125)**2,2), round(b['close']*1.618,2)
        b['PriceConfluence'], b['TimeConfluence'] = 2, 1
    return bars

def save(symbol, bars):
    os.makedirs('data', exist_ok=True)
    with open(f'data/{symbol}.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Date','Open','High','Low','Close','Volume','ATR','FastSMA','SlowSMA','Bias','GeoLevel','PhiLevel','PriceConfluence','TimeConfluence'])
        for b in bars:
            w.writerow([b['date'][:10], round(b['open'],2), round(b['high'],2), round(b['low'],2), round(b['close'],2), int(b['volume']), round(b['ATR'],4), round(b['FastSMA'],2), round(b['SlowSMA'],2), b['Bias'], b['GeoLevel'], b['PhiLevel'], b['PriceConfluence'], b['TimeConfluence']])
    print(f"  Saved data/{symbol}.csv")

if __name__ == '__main__':
    print("MULTI-SYMBOL FETCHER")
    if not TOKEN: print("ERROR: No TIINGO_TOKEN"); exit(1)
    for s in SYMBOLS:
        d = fetch(s)
        if d: save(s, calc(d))
        time.sleep(0.5)
    print("Done!")