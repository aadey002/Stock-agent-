#!/usr/bin/env python3
"""
ETF Holdings Analyzer
=====================

Drill down into sector ETFs to see which stocks are driving performance.
Shows top holdings and their individual contributions to sector moves.
"""

import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

TIINGO_TOKEN = os.environ.get('TIINGO_TOKEN', '14febdd1820f1a4aa11e1bf920cd3a38950b77a5')
DATA_DIR = "data"
REPORTS_DIR = "reports"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Top holdings for each sector ETF (approximate weights)
# Updated periodically - these are the major components
ETF_HOLDINGS = {
    'XLK': {
        'name': 'Technology',
        'holdings': [
            {'ticker': 'AAPL', 'name': 'Apple', 'weight': 22.0},
            {'ticker': 'MSFT', 'name': 'Microsoft', 'weight': 21.0},
            {'ticker': 'NVDA', 'name': 'NVIDIA', 'weight': 6.0},
            {'ticker': 'AVGO', 'name': 'Broadcom', 'weight': 5.0},
            {'ticker': 'AMD', 'name': 'AMD', 'weight': 2.5},
            {'ticker': 'CRM', 'name': 'Salesforce', 'weight': 2.5},
            {'ticker': 'ADBE', 'name': 'Adobe', 'weight': 2.0},
            {'ticker': 'CSCO', 'name': 'Cisco', 'weight': 2.0},
            {'ticker': 'ORCL', 'name': 'Oracle', 'weight': 2.0},
            {'ticker': 'INTC', 'name': 'Intel', 'weight': 1.5},
        ]
    },
    'XLF': {
        'name': 'Financials',
        'holdings': [
            {'ticker': 'BRK-B', 'name': 'Berkshire Hathaway', 'weight': 14.0},
            {'ticker': 'JPM', 'name': 'JPMorgan Chase', 'weight': 10.0},
            {'ticker': 'V', 'name': 'Visa', 'weight': 8.0},
            {'ticker': 'MA', 'name': 'Mastercard', 'weight': 7.0},
            {'ticker': 'BAC', 'name': 'Bank of America', 'weight': 5.0},
            {'ticker': 'WFC', 'name': 'Wells Fargo', 'weight': 3.5},
            {'ticker': 'GS', 'name': 'Goldman Sachs', 'weight': 2.5},
            {'ticker': 'MS', 'name': 'Morgan Stanley', 'weight': 2.5},
            {'ticker': 'SPGI', 'name': 'S&P Global', 'weight': 2.5},
            {'ticker': 'BLK', 'name': 'BlackRock', 'weight': 2.0},
        ]
    },
    'XLE': {
        'name': 'Energy',
        'holdings': [
            {'ticker': 'XOM', 'name': 'Exxon Mobil', 'weight': 23.0},
            {'ticker': 'CVX', 'name': 'Chevron', 'weight': 17.0},
            {'ticker': 'COP', 'name': 'ConocoPhillips', 'weight': 7.5},
            {'ticker': 'SLB', 'name': 'Schlumberger', 'weight': 5.0},
            {'ticker': 'EOG', 'name': 'EOG Resources', 'weight': 4.5},
            {'ticker': 'MPC', 'name': 'Marathon Petroleum', 'weight': 4.0},
            {'ticker': 'PXD', 'name': 'Pioneer Natural', 'weight': 3.5},
            {'ticker': 'PSX', 'name': 'Phillips 66', 'weight': 3.5},
            {'ticker': 'VLO', 'name': 'Valero Energy', 'weight': 3.0},
            {'ticker': 'OXY', 'name': 'Occidental', 'weight': 2.5},
        ]
    },
    'XLV': {
        'name': 'Healthcare',
        'holdings': [
            {'ticker': 'UNH', 'name': 'UnitedHealth', 'weight': 10.0},
            {'ticker': 'JNJ', 'name': 'Johnson & Johnson', 'weight': 8.5},
            {'ticker': 'LLY', 'name': 'Eli Lilly', 'weight': 8.0},
            {'ticker': 'PFE', 'name': 'Pfizer', 'weight': 5.0},
            {'ticker': 'ABBV', 'name': 'AbbVie', 'weight': 5.0},
            {'ticker': 'MRK', 'name': 'Merck', 'weight': 5.0},
            {'ticker': 'TMO', 'name': 'Thermo Fisher', 'weight': 4.0},
            {'ticker': 'ABT', 'name': 'Abbott Labs', 'weight': 3.5},
            {'ticker': 'DHR', 'name': 'Danaher', 'weight': 3.0},
            {'ticker': 'BMY', 'name': 'Bristol-Myers', 'weight': 2.5},
        ]
    },
    'XLY': {
        'name': 'Consumer Discretionary',
        'holdings': [
            {'ticker': 'AMZN', 'name': 'Amazon', 'weight': 23.0},
            {'ticker': 'TSLA', 'name': 'Tesla', 'weight': 12.0},
            {'ticker': 'HD', 'name': 'Home Depot', 'weight': 8.0},
            {'ticker': 'MCD', 'name': 'McDonalds', 'weight': 5.0},
            {'ticker': 'NKE', 'name': 'Nike', 'weight': 3.5},
            {'ticker': 'LOW', 'name': 'Lowes', 'weight': 3.5},
            {'ticker': 'SBUX', 'name': 'Starbucks', 'weight': 3.0},
            {'ticker': 'TJX', 'name': 'TJX Companies', 'weight': 2.5},
            {'ticker': 'BKNG', 'name': 'Booking Holdings', 'weight': 2.5},
            {'ticker': 'CMG', 'name': 'Chipotle', 'weight': 2.0},
        ]
    },
    'XLI': {
        'name': 'Industrials',
        'holdings': [
            {'ticker': 'CAT', 'name': 'Caterpillar', 'weight': 5.5},
            {'ticker': 'RTX', 'name': 'RTX Corp', 'weight': 5.0},
            {'ticker': 'UNP', 'name': 'Union Pacific', 'weight': 4.5},
            {'ticker': 'HON', 'name': 'Honeywell', 'weight': 4.5},
            {'ticker': 'DE', 'name': 'Deere & Co', 'weight': 4.0},
            {'ticker': 'BA', 'name': 'Boeing', 'weight': 4.0},
            {'ticker': 'GE', 'name': 'GE Aerospace', 'weight': 4.0},
            {'ticker': 'LMT', 'name': 'Lockheed Martin', 'weight': 3.0},
            {'ticker': 'UPS', 'name': 'UPS', 'weight': 3.0},
            {'ticker': 'MMM', 'name': '3M', 'weight': 2.5},
        ]
    },
    'XLP': {
        'name': 'Consumer Staples',
        'holdings': [
            {'ticker': 'PG', 'name': 'Procter & Gamble', 'weight': 15.0},
            {'ticker': 'KO', 'name': 'Coca-Cola', 'weight': 10.0},
            {'ticker': 'PEP', 'name': 'PepsiCo', 'weight': 10.0},
            {'ticker': 'COST', 'name': 'Costco', 'weight': 9.0},
            {'ticker': 'WMT', 'name': 'Walmart', 'weight': 8.0},
            {'ticker': 'PM', 'name': 'Philip Morris', 'weight': 5.0},
            {'ticker': 'MDLZ', 'name': 'Mondelez', 'weight': 4.0},
            {'ticker': 'MO', 'name': 'Altria', 'weight': 3.5},
            {'ticker': 'CL', 'name': 'Colgate-Palmolive', 'weight': 3.0},
            {'ticker': 'KMB', 'name': 'Kimberly-Clark', 'weight': 2.0},
        ]
    },
    'XLU': {
        'name': 'Utilities',
        'holdings': [
            {'ticker': 'NEE', 'name': 'NextEra Energy', 'weight': 15.0},
            {'ticker': 'SO', 'name': 'Southern Company', 'weight': 8.0},
            {'ticker': 'DUK', 'name': 'Duke Energy', 'weight': 7.5},
            {'ticker': 'CEG', 'name': 'Constellation Energy', 'weight': 5.5},
            {'ticker': 'SRE', 'name': 'Sempra', 'weight': 5.0},
            {'ticker': 'AEP', 'name': 'American Electric', 'weight': 5.0},
            {'ticker': 'D', 'name': 'Dominion Energy', 'weight': 4.5},
            {'ticker': 'EXC', 'name': 'Exelon', 'weight': 4.0},
            {'ticker': 'XEL', 'name': 'Xcel Energy', 'weight': 3.5},
            {'ticker': 'PEG', 'name': 'PSEG', 'weight': 3.0},
        ]
    },
    'XLB': {
        'name': 'Materials',
        'holdings': [
            {'ticker': 'LIN', 'name': 'Linde', 'weight': 18.0},
            {'ticker': 'APD', 'name': 'Air Products', 'weight': 8.0},
            {'ticker': 'SHW', 'name': 'Sherwin-Williams', 'weight': 7.0},
            {'ticker': 'FCX', 'name': 'Freeport-McMoRan', 'weight': 6.0},
            {'ticker': 'ECL', 'name': 'Ecolab', 'weight': 5.0},
            {'ticker': 'NEM', 'name': 'Newmont', 'weight': 5.0},
            {'ticker': 'NUE', 'name': 'Nucor', 'weight': 4.0},
            {'ticker': 'DOW', 'name': 'Dow Inc', 'weight': 4.0},
            {'ticker': 'CTVA', 'name': 'Corteva', 'weight': 3.5},
            {'ticker': 'DD', 'name': 'DuPont', 'weight': 3.0},
        ]
    },
    'XLRE': {
        'name': 'Real Estate',
        'holdings': [
            {'ticker': 'PLD', 'name': 'Prologis', 'weight': 11.0},
            {'ticker': 'AMT', 'name': 'American Tower', 'weight': 9.0},
            {'ticker': 'EQIX', 'name': 'Equinix', 'weight': 7.5},
            {'ticker': 'CCI', 'name': 'Crown Castle', 'weight': 5.5},
            {'ticker': 'PSA', 'name': 'Public Storage', 'weight': 5.0},
            {'ticker': 'WELL', 'name': 'Welltower', 'weight': 4.5},
            {'ticker': 'SPG', 'name': 'Simon Property', 'weight': 4.0},
            {'ticker': 'DLR', 'name': 'Digital Realty', 'weight': 4.0},
            {'ticker': 'O', 'name': 'Realty Income', 'weight': 4.0},
            {'ticker': 'VICI', 'name': 'VICI Properties', 'weight': 3.5},
        ]
    },
}


class ETFHoldingsAnalyzer:
    """Analyze ETF holdings and their contributions."""
    
    def __init__(self):
        self.holdings_data = {}
        self.analysis = {}
    
    def fetch_holdings_data(self, etf_ticker, days=30):
        """Fetch price data for all holdings of an ETF."""
        if etf_ticker not in ETF_HOLDINGS:
            logger.error(f"ETF {etf_ticker} not found in database")
            return None
        
        etf_info = ETF_HOLDINGS[etf_ticker]
        logger.info(f"\nFetching holdings for {etf_ticker} ({etf_info['name']})...")
        
        holdings_perf = []
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        for holding in etf_info['holdings']:
            ticker = holding['ticker']
            
            # Handle special tickers
            api_ticker = ticker.replace('-', '.')  # BRK-B -> BRK.B for some APIs
            
            try:
                url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={start_date}&token={TIINGO_TOKEN}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) >= 2:
                        start_price = data[0]['close']
                        end_price = data[-1]['close']
                        performance = ((end_price / start_price) - 1) * 100
                        
                        # Calculate weighted contribution
                        contribution = performance * (holding['weight'] / 100)
                        
                        holdings_perf.append({
                            'ticker': ticker,
                            'name': holding['name'],
                            'weight': holding['weight'],
                            'start_price': round(start_price, 2),
                            'end_price': round(end_price, 2),
                            'performance': round(performance, 2),
                            'contribution': round(contribution, 2),
                        })
                        
                        logger.info(f"  {ticker}: {performance:+.2f}% (Weight: {holding['weight']}%, Contribution: {contribution:+.2f}%)")
                else:
                    logger.warning(f"  {ticker}: Could not fetch data")
                    
            except Exception as e:
                logger.error(f"  {ticker}: Error - {e}")
        
        # Sort by contribution
        holdings_perf.sort(key=lambda x: x['contribution'], reverse=True)
        
        self.holdings_data[etf_ticker] = {
            'name': etf_info['name'],
            'holdings': holdings_perf,
            'fetch_date': datetime.now().isoformat(),
        }
        
        return holdings_perf
    
    def analyze_etf(self, etf_ticker, days=30):
        """Full analysis of an ETF's holdings."""
        holdings = self.fetch_holdings_data(etf_ticker, days)
        
        if not holdings:
            return None
        
        # Calculate summary stats
        total_contribution = sum(h['contribution'] for h in holdings)
        avg_performance = sum(h['performance'] for h in holdings) / len(holdings)
        
        # Find biggest contributors (positive and negative)
        top_contributors = holdings[:3]
        bottom_contributors = holdings[-3:]
        
        # Separate gainers and losers
        gainers = [h for h in holdings if h['performance'] > 0]
        losers = [h for h in holdings if h['performance'] < 0]
        
        analysis = {
            'etf': etf_ticker,
            'name': ETF_HOLDINGS[etf_ticker]['name'],
            'period_days': days,
            'total_holdings_analyzed': len(holdings),
            'estimated_etf_return': round(total_contribution, 2),
            'avg_holding_performance': round(avg_performance, 2),
            'gainers_count': len(gainers),
            'losers_count': len(losers),
            'top_contributors': top_contributors,
            'bottom_contributors': bottom_contributors,
            'all_holdings': holdings,
        }
        
        self.analysis[etf_ticker] = analysis
        return analysis
    
    def analyze_all_etfs(self, days=30):
        """Analyze all sector ETFs."""
        print("")
        print("=" * 70)
        print("  ETF HOLDINGS ANALYZER - ALL SECTORS")
        print("=" * 70)
        print(f"  Period: {days} days")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        all_analysis = {}
        
        for etf_ticker in ETF_HOLDINGS.keys():
            analysis = self.analyze_etf(etf_ticker, days)
            if analysis:
                all_analysis[etf_ticker] = analysis
        
        self.print_summary(all_analysis)
        self.save_report(all_analysis)
        
        return all_analysis
    
    def drill_down(self, etf_ticker, days=30):
        """Detailed drill-down into a specific ETF."""
        print("")
        print("=" * 70)
        print(f"  ETF DRILL-DOWN: {etf_ticker}")
        print("=" * 70)
        
        analysis = self.analyze_etf(etf_ticker, days)
        
        if not analysis:
            print(f"  Could not analyze {etf_ticker}")
            return None
        
        print(f"\n  Sector: {analysis['name']}")
        print(f"  Period: {days} days")
        print(f"  Holdings Analyzed: {analysis['total_holdings_analyzed']}")
        print(f"\n  Estimated ETF Return: {analysis['estimated_etf_return']:+.2f}%")
        print(f"  Avg Holding Performance: {analysis['avg_holding_performance']:+.2f}%")
        print(f"  Gainers: {analysis['gainers_count']} | Losers: {analysis['losers_count']}")
        
        print("\n  TOP CONTRIBUTORS (Driving Gains):")
        print("  " + "-" * 60)
        for h in analysis['top_contributors']:
            print(f"  {h['ticker']:6} {h['name']:20} | Perf: {h['performance']:+6.2f}% | Weight: {h['weight']:5.1f}% | Contribution: {h['contribution']:+5.2f}%")
        
        print("\n  BOTTOM CONTRIBUTORS (Dragging Down):")
        print("  " + "-" * 60)
        for h in analysis['bottom_contributors']:
            print(f"  {h['ticker']:6} {h['name']:20} | Perf: {h['performance']:+6.2f}% | Weight: {h['weight']:5.1f}% | Contribution: {h['contribution']:+5.2f}%")
        
        print("\n  ALL HOLDINGS (Sorted by Contribution):")
        print("  " + "-" * 60)
        for h in analysis['all_holdings']:
            bar = "+" * int(abs(h['contribution']) * 5) if h['contribution'] > 0 else "-" * int(abs(h['contribution']) * 5)
            direction = "[+]" if h['contribution'] > 0 else "[-]"
            print(f"  {direction} {h['ticker']:6} {h['performance']:+6.2f}% {bar}")
        
        print("=" * 70)
        
        return analysis
    
    def print_summary(self, all_analysis):
        """Print summary of all ETFs."""
        print("\n")
        print("=" * 70)
        print("  SECTOR SUMMARY - TOP DRIVERS")
        print("=" * 70)
        
        # Sort ETFs by estimated return
        sorted_etfs = sorted(all_analysis.items(), key=lambda x: x[1]['estimated_etf_return'], reverse=True)
        
        print("\n  SECTOR PERFORMANCE (Estimated from Holdings):")
        print("  " + "-" * 60)
        for etf, data in sorted_etfs:
            bar_len = int(abs(data['estimated_etf_return']) * 2)
            bar = "#" * min(bar_len, 30)
            direction = "[+]" if data['estimated_etf_return'] > 0 else "[-]"
            print(f"  {direction} {etf:5} ({data['name']:18}): {data['estimated_etf_return']:+6.2f}% {bar}")
        
        print("\n  TOP INDIVIDUAL STOCK CONTRIBUTORS:")
        print("  " + "-" * 60)
        
        # Collect all holdings across ETFs
        all_holdings = []
        for etf, data in all_analysis.items():
            for h in data['all_holdings']:
                all_holdings.append({**h, 'etf': etf})
        
        # Sort by absolute contribution
        all_holdings.sort(key=lambda x: x['contribution'], reverse=True)
        
        print("  Top 10 Gainers:")
        for h in all_holdings[:10]:
            print(f"    {h['ticker']:6} ({h['etf']:4}): {h['performance']:+6.2f}% | Contribution: {h['contribution']:+5.2f}%")
        
        print("\n  Top 10 Losers:")
        all_holdings.sort(key=lambda x: x['contribution'])
        for h in all_holdings[:10]:
            print(f"    {h['ticker']:6} ({h['etf']:4}): {h['performance']:+6.2f}% | Contribution: {h['contribution']:+5.2f}%")
        
        print("=" * 70)
    
    def save_report(self, all_analysis):
        """Save analysis to files."""
        # Save JSON
        json_path = os.path.join(DATA_DIR, 'etf_holdings_analysis.json')
        with open(json_path, 'w') as f:
            json.dump(all_analysis, f, indent=2, default=str)
        
        # Save CSV
        rows = []
        for etf, data in all_analysis.items():
            for h in data['all_holdings']:
                rows.append({
                    'ETF': etf,
                    'Sector': data['name'],
                    'Ticker': h['ticker'],
                    'Name': h['name'],
                    'Weight': h['weight'],
                    'Performance': h['performance'],
                    'Contribution': h['contribution'],
                })
        
        if rows:
            df = pd.DataFrame(rows)
            csv_path = os.path.join(REPORTS_DIR, 'etf_holdings_analysis.csv')
            df.to_csv(csv_path, index=False)
            logger.info(f"\nSaved: {csv_path}")
        
        logger.info(f"Saved: {json_path}")


def main():
    """Main entry point."""
    import sys
    
    analyzer = ETFHoldingsAnalyzer()
    
    # Check for command line argument
    if len(sys.argv) > 1:
        etf = sys.argv[1].upper()
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        analyzer.drill_down(etf, days)
    else:
        # Analyze all ETFs
        analyzer.analyze_all_etfs(days=30)


if __name__ == "__main__":
    main()