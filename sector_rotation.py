#!/usr/bin/env python3
"""
Sector Rotation Tracker
=======================

Tracks sector performance over time to identify rotation trends.
Helps identify when to rotate between sectors/ETFs.
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

# Sector ETF definitions
SECTORS = {
    'XLK': {'name': 'Technology', 'type': 'cyclical', 'color': '#00D4FF'},
    'XLF': {'name': 'Financials', 'type': 'cyclical', 'color': '#FFD700'},
    'XLY': {'name': 'Consumer Disc', 'type': 'cyclical', 'color': '#FF6B6B'},
    'XLI': {'name': 'Industrials', 'type': 'cyclical', 'color': '#4ECDC4'},
    'XLB': {'name': 'Materials', 'type': 'cyclical', 'color': '#95E1D3'},
    'XLE': {'name': 'Energy', 'type': 'cyclical', 'color': '#F38181'},
    'XLV': {'name': 'Healthcare', 'type': 'defensive', 'color': '#A8E6CF'},
    'XLP': {'name': 'Consumer Stap', 'type': 'defensive', 'color': '#DDA0DD'},
    'XLU': {'name': 'Utilities', 'type': 'defensive', 'color': '#98D8C8'},
    'XLRE': {'name': 'Real Estate', 'type': 'defensive', 'color': '#F7DC6F'},
}


class SectorRotationTracker:
    """Track and analyze sector rotation."""
    
    def __init__(self):
        self.sector_data = {}
        self.rotation_history = []
        
    def fetch_sector_data(self, days=90):
        """Fetch historical data for all sectors."""
        logger.info("=" * 60)
        logger.info("FETCHING SECTOR DATA")
        logger.info("=" * 60)
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        for ticker, info in SECTORS.items():
            try:
                url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={start_date}&token={TIINGO_TOKEN}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        df = pd.DataFrame(data)
                        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                        df = df[['date', 'close', 'volume']]
                        df['ticker'] = ticker
                        df['name'] = info['name']
                        df['type'] = info['type']
                        
                        # Calculate returns
                        df['daily_return'] = df['close'].pct_change() * 100
                        df['cumulative_return'] = ((df['close'] / df['close'].iloc[0]) - 1) * 100
                        
                        self.sector_data[ticker] = df
                        logger.info(f"  {ticker} ({info['name']}): {len(df)} days loaded")
                        
            except Exception as e:
                logger.error(f"  {ticker}: Error - {e}")
        
        logger.info(f"Loaded {len(self.sector_data)} sectors")
        return self.sector_data
    
    def calculate_rotation_metrics(self):
        """Calculate rotation metrics for different timeframes."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("CALCULATING ROTATION METRICS")
        logger.info("=" * 60)
        
        metrics = {
            '1_week': {},
            '2_week': {},
            '1_month': {},
            '3_month': {},
            '6_month': {},
            '1_year': {},
            '2_year': {},
            '3_year': {},
        }        
        
        timeframes = {
            '1_week': 5,
            '2_week': 10,
            '1_month': 21,
            '3_month': 63,
            '6_month': 126,
            '1_year': 252,
            '2_year': 504,
            '3_year': 756,
        }
        
        for ticker, df in self.sector_data.items():
            if len(df) < 5:
                continue
                
            for tf_name, tf_days in timeframes.items():
                if len(df) >= tf_days:
                    start_price = df['close'].iloc[-tf_days]
                    end_price = df['close'].iloc[-1]
                    performance = ((end_price / start_price) - 1) * 100
                    
                    metrics[tf_name][ticker] = {
                        'name': SECTORS[ticker]['name'],
                        'type': SECTORS[ticker]['type'],
                        'performance': round(performance, 2),
                        'start_price': round(start_price, 2),
                        'end_price': round(end_price, 2),
                    }
        
        # Sort by performance
        for tf_name in metrics:
            metrics[tf_name] = dict(sorted(
                metrics[tf_name].items(),
                key=lambda x: x[1]['performance'],
                reverse=True
            ))
        
        self.metrics = metrics
        return metrics
    
    def analyze_rotation(self):
        """Analyze current rotation trend."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("ROTATION ANALYSIS")
        logger.info("=" * 60)
        
        analysis = {}
        
        for tf_name, tf_metrics in self.metrics.items():
            if not tf_metrics:
                continue
            
            cyclical_perf = []
            defensive_perf = []
            
            for ticker, data in tf_metrics.items():
                if data['type'] == 'cyclical':
                    cyclical_perf.append(data['performance'])
                else:
                    defensive_perf.append(data['performance'])
            
            cyclical_avg = sum(cyclical_perf) / len(cyclical_perf) if cyclical_perf else 0
            defensive_avg = sum(defensive_perf) / len(defensive_perf) if defensive_perf else 0
            
            spread = cyclical_avg - defensive_avg
            
            if spread > 2:
                rotation = 'STRONG_RISK_ON'
                signal = 'Favor cyclical sectors (Tech, Financials, Consumer Disc)'
            elif spread > 0.5:
                rotation = 'RISK_ON'
                signal = 'Slight preference for cyclical sectors'
            elif spread < -2:
                rotation = 'STRONG_RISK_OFF'
                signal = 'Favor defensive sectors (Healthcare, Utilities, Staples)'
            elif spread < -0.5:
                rotation = 'RISK_OFF'
                signal = 'Slight preference for defensive sectors'
            else:
                rotation = 'NEUTRAL'
                signal = 'No clear rotation - mixed signals'
            
            # Find leaders and laggards
            tickers = list(tf_metrics.keys())
            leaders = tickers[:3] if len(tickers) >= 3 else tickers
            laggards = tickers[-3:] if len(tickers) >= 3 else tickers
            
            analysis[tf_name] = {
                'rotation': rotation,
                'signal': signal,
                'cyclical_avg': round(cyclical_avg, 2),
                'defensive_avg': round(defensive_avg, 2),
                'spread': round(spread, 2),
                'leaders': [(t, tf_metrics[t]['name'], tf_metrics[t]['performance']) for t in leaders],
                'laggards': [(t, tf_metrics[t]['name'], tf_metrics[t]['performance']) for t in laggards],
            }
            
            logger.info(f"\n{tf_name.upper().replace('_', ' ')}:")
            logger.info(f"  Rotation: {rotation}")
            logger.info(f"  Cyclical Avg: {cyclical_avg:+.2f}%")
            logger.info(f"  Defensive Avg: {defensive_avg:+.2f}%")
            logger.info(f"  Spread: {spread:+.2f}%")
            logger.info(f"  Leaders: {', '.join([f'{t}({p:+.1f}%)' for t,n,p in analysis[tf_name]['leaders']])}")
            logger.info(f"  Laggards: {', '.join([f'{t}({p:+.1f}%)' for t,n,p in analysis[tf_name]['laggards']])}")
        
        self.analysis = analysis
        return analysis
    
    def generate_recommendations(self):
        """Generate trading recommendations based on rotation."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("SECTOR ROTATION RECOMMENDATIONS")
        logger.info("=" * 60)
        
        recommendations = []
        
        # Use 1-month timeframe for primary signal
        if '1_month' in self.analysis:
            monthly = self.analysis['1_month']
            
            if 'RISK_ON' in monthly['rotation']:
                recommendations.append({
                    'action': 'OVERWEIGHT',
                    'sectors': 'Cyclical (XLK, XLF, XLY, XLI)',
                    'rationale': f"Cyclical sectors outperforming by {monthly['spread']:+.2f}%"
                })
                recommendations.append({
                    'action': 'UNDERWEIGHT',
                    'sectors': 'Defensive (XLV, XLP, XLU)',
                    'rationale': 'Defensive sectors lagging in risk-on environment'
                })
            elif 'RISK_OFF' in monthly['rotation']:
                recommendations.append({
                    'action': 'OVERWEIGHT',
                    'sectors': 'Defensive (XLV, XLP, XLU)',
                    'rationale': f"Defensive sectors outperforming by {abs(monthly['spread']):+.2f}%"
                })
                recommendations.append({
                    'action': 'UNDERWEIGHT',
                    'sectors': 'Cyclical (XLK, XLF, XLY)',
                    'rationale': 'Cyclical sectors lagging in risk-off environment'
                })
            else:
                recommendations.append({
                    'action': 'NEUTRAL',
                    'sectors': 'All sectors',
                    'rationale': 'No clear rotation signal - maintain balanced allocation'
                })
        
        # Add specific ETF recommendations
        if '1_month' in self.metrics:
            top_3 = list(self.metrics['1_month'].items())[:3]
            for ticker, data in top_3:
                recommendations.append({
                    'action': 'CONSIDER',
                    'sectors': f"{ticker} ({data['name']})",
                    'rationale': f"Top performer: {data['performance']:+.2f}% (1-month)"
                })
        
        for rec in recommendations:
            logger.info(f"\n  [{rec['action']}] {rec['sectors']}")
            logger.info(f"    Rationale: {rec['rationale']}")
        
        self.recommendations = recommendations
        return recommendations
    
    def save_report(self):
        """Save rotation report to files."""
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        # Save JSON report
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics,
            'analysis': self.analysis,
            'recommendations': self.recommendations,
        }
        
        json_path = os.path.join(DATA_DIR, 'sector_rotation.json')
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save CSV for dashboard
        rows = []
        for tf_name, tf_metrics in self.metrics.items():
            for ticker, data in tf_metrics.items():
                rows.append({
                    'Timeframe': tf_name,
                    'Ticker': ticker,
                    'Name': data['name'],
                    'Type': data['type'],
                    'Performance': data['performance'],
                })
        
        if rows:
            df = pd.DataFrame(rows)
            csv_path = os.path.join(REPORTS_DIR, 'sector_rotation.csv')
            df.to_csv(csv_path, index=False)
            logger.info(f"\nSaved: {csv_path}")
        
        logger.info(f"Saved: {json_path}")
        
        return report
    
    def run(self):
        """Run full rotation analysis."""
        print("")
        print("=" * 60)
        print("  SECTOR ROTATION TRACKER")
        print("=" * 60)
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.fetch_sector_data(days=1095)
        self.calculate_rotation_metrics()
        self.analyze_rotation()
        self.generate_recommendations()
        report = self.save_report()
        
        # Print summary
        print("")
        print("=" * 60)
        print("  ROTATION SUMMARY")
        print("=" * 60)
        
        if '1_month' in self.analysis:
            a = self.analysis['1_month']
            print(f"  Current Rotation: {a['rotation']}")
            print(f"  Signal: {a['signal']}")
            print(f"  Cyclical vs Defensive Spread: {a['spread']:+.2f}%")
            print("")
            print("  TOP 3 SECTORS (1-Month):")
            for t, n, p in a['leaders']:
                print(f"    {t}: {n} ({p:+.2f}%)")
            print("")
            print("  BOTTOM 3 SECTORS (1-Month):")
            for t, n, p in a['laggards']:
                print(f"    {t}: {n} ({p:+.2f}%)")
        
        print("=" * 60)
        print("")
        
        return report


def main():
    tracker = SectorRotationTracker()
    tracker.run()


if __name__ == "__main__":
    main()