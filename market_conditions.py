#!/usr/bin/env python3
"""
Market Conditions Module
========================

Checks market conditions before generating trading signals:
1. Volatility (VIX)
2. Economic Calendar
3. Market Sentiment
4. Sector Rotation

Usage:
    python market_conditions.py
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
TIINGO_TOKEN = os.environ.get('TIINGO_TOKEN', '14febdd1820f1a4aa11e1bf920cd3a38950b77a5')
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


class MarketConditions:
    """Check market conditions before trading."""
    
    def __init__(self):
        self.conditions = {}
        self.warnings = []
        self.trade_allowed = True
        self.position_size_multiplier = 1.0
        
    def check_all(self):
        """Run all condition checks."""
        logger.info("=" * 60)
        logger.info("MARKET CONDITIONS CHECK")
        logger.info("=" * 60)
        
        self.check_volatility()
        self.check_economic_calendar()
        self.check_market_sentiment()
        self.check_sector_rotation()
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'trade_allowed': self.trade_allowed,
            'position_size_multiplier': self.position_size_multiplier,
            'conditions': self.conditions,
            'warnings': self.warnings,
            'overall_score': self._calculate_overall_score()
        }
        
        self._log_summary(result)
        self._save_conditions(result)
        
        return result
    
    def check_volatility(self):
        """Check VIX volatility levels."""
        logger.info("")
        logger.info("[VOLATILITY] Checking VIX...")
        
        try:
            url = f"https://api.tiingo.com/iex?tickers=UVXY&token={TIINGO_TOKEN}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    price = data[0].get('last', 0) or data[0].get('tngoLast', 0)
                    estimated_vix = price * 0.8
                    
                    self.conditions['volatility'] = {
                        'vix_estimate': round(estimated_vix, 2),
                        'uvxy_price': round(price, 2),
                        'level': self._categorize_vix(estimated_vix),
                        'status': 'OK'
                    }
                    
                    if estimated_vix > 35:
                        self.warnings.append("WARNING: EXTREME VOLATILITY - Consider avoiding trades")
                        self.position_size_multiplier *= 0.25
                        self.conditions['volatility']['recommendation'] = 'AVOID_TRADING'
                    elif estimated_vix > 25:
                        self.warnings.append("WARNING: HIGH VOLATILITY - Reduce position size")
                        self.position_size_multiplier *= 0.5
                        self.conditions['volatility']['recommendation'] = 'REDUCE_SIZE'
                    elif estimated_vix > 18:
                        self.conditions['volatility']['recommendation'] = 'NORMAL'
                    else:
                        self.conditions['volatility']['recommendation'] = 'LOW_VOL'
                    
                    logger.info(f"   VIX Estimate: {estimated_vix:.1f} ({self.conditions['volatility']['level']})")
                    return self.conditions['volatility']
            
            self.conditions['volatility'] = {
                'vix_estimate': 'N/A',
                'level': 'UNKNOWN',
                'status': 'API_ERROR',
                'recommendation': 'PROCEED_WITH_CAUTION'
            }
            logger.warning("   Could not fetch VIX data - using fallback")
            
        except Exception as e:
            logger.error(f"   Volatility check error: {e}")
            self.conditions['volatility'] = {
                'status': 'ERROR',
                'level': 'UNKNOWN',
                'error': str(e)
            }
        
        return self.conditions.get('volatility', {})
    
    def _categorize_vix(self, vix):
        """Categorize VIX level."""
        if vix < 12:
            return 'VERY_LOW'
        elif vix < 18:
            return 'LOW'
        elif vix < 25:
            return 'MODERATE'
        elif vix < 35:
            return 'HIGH'
        else:
            return 'EXTREME'
    
    def check_economic_calendar(self):
        """Check for upcoming high-impact economic events."""
        logger.info("")
        logger.info("[CALENDAR] Checking Economic Events...")
        
        today = datetime.now()
        
        high_impact_events = [
            {'name': 'FOMC Meeting', 'days': [14, 15], 'months': [1, 3, 5, 6, 7, 9, 11, 12], 'impact': 'EXTREME'},
            {'name': 'Non-Farm Payrolls', 'days': [1, 2, 3, 4, 5, 6, 7], 'weekday': 4, 'impact': 'HIGH'},
            {'name': 'CPI Release', 'days': [10, 11, 12, 13, 14], 'impact': 'HIGH'},
            {'name': 'PPI Release', 'days': [11, 12, 13, 14, 15], 'impact': 'MEDIUM'},
            {'name': 'Retail Sales', 'days': [13, 14, 15, 16, 17], 'impact': 'MEDIUM'},
            {'name': 'GDP Release', 'days': [25, 26, 27, 28, 29, 30], 'months': [1, 4, 7, 10], 'impact': 'HIGH'},
        ]
        
        upcoming_events = []
        
        for event in high_impact_events:
            if today.day in event['days']:
                if 'months' in event and today.month not in event['months']:
                    continue
                if 'weekday' in event:
                    if today.weekday() != event['weekday']:
                        continue
                    if today.day > 7:
                        continue
                
                upcoming_events.append({
                    'name': event['name'],
                    'impact': event['impact'],
                    'timing': 'TODAY'
                })
            elif (today.day + 1) in event['days']:
                upcoming_events.append({
                    'name': event['name'],
                    'impact': event['impact'],
                    'timing': 'TOMORROW'
                })
        
        self.conditions['economic_calendar'] = {
            'events_today': len([e for e in upcoming_events if e['timing'] == 'TODAY']),
            'events_tomorrow': len([e for e in upcoming_events if e['timing'] == 'TOMORROW']),
            'upcoming_events': upcoming_events,
            'status': 'OK'
        }
        
        for event in upcoming_events:
            if event['impact'] in ['EXTREME', 'HIGH']:
                self.warnings.append(f"CALENDAR: {event['name']} - {event['timing']} - {event['impact']} IMPACT")
                if event['timing'] == 'TODAY':
                    self.position_size_multiplier *= 0.5
                    self.conditions['economic_calendar']['recommendation'] = 'REDUCE_EXPOSURE'
        
        if not upcoming_events:
            self.conditions['economic_calendar']['recommendation'] = 'CLEAR'
            logger.info("   No high-impact events in next 24 hours [OK]")
        else:
            logger.info(f"   Found {len(upcoming_events)} upcoming event(s)")
            for event in upcoming_events:
                logger.info(f"   - {event['name']} ({event['timing']}) - {event['impact']} impact")
        
        return self.conditions['economic_calendar']
    
    def check_market_sentiment(self):
        """Check market sentiment indicators."""
        logger.info("")
        logger.info("[SENTIMENT] Checking Market Sentiment...")
        
        try:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            url = f"https://api.tiingo.com/tiingo/daily/SPY/prices?startDate={start_date}&token={TIINGO_TOKEN}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) >= 5:
                    closes = [d['close'] for d in data]
                    
                    momentum_5d = ((closes[-1] - closes[-5]) / closes[-5]) * 100
                    momentum_20d = ((closes[-1] - closes[0]) / closes[0]) * 100 if len(closes) >= 20 else momentum_5d
                    
                    if momentum_5d > 2:
                        sentiment = 'BULLISH'
                        sentiment_score = min(100, 50 + momentum_5d * 10)
                    elif momentum_5d < -2:
                        sentiment = 'BEARISH'
                        sentiment_score = max(0, 50 + momentum_5d * 10)
                    else:
                        sentiment = 'NEUTRAL'
                        sentiment_score = 50
                    
                    if momentum_20d > 5:
                        fear_greed = 'EXTREME_GREED'
                        fg_score = 85
                    elif momentum_20d > 2:
                        fear_greed = 'GREED'
                        fg_score = 70
                    elif momentum_20d < -5:
                        fear_greed = 'EXTREME_FEAR'
                        fg_score = 15
                    elif momentum_20d < -2:
                        fear_greed = 'FEAR'
                        fg_score = 30
                    else:
                        fear_greed = 'NEUTRAL'
                        fg_score = 50
                    
                    self.conditions['sentiment'] = {
                        'sentiment': sentiment,
                        'sentiment_score': round(sentiment_score),
                        'fear_greed': fear_greed,
                        'fear_greed_score': fg_score,
                        'momentum_5d': round(momentum_5d, 2),
                        'momentum_20d': round(momentum_20d, 2),
                        'status': 'OK'
                    }
                    
                    if fear_greed == 'EXTREME_GREED':
                        self.warnings.append("WARNING: EXTREME GREED - Market may be overextended")
                    elif fear_greed == 'EXTREME_FEAR':
                        self.warnings.append("WARNING: EXTREME FEAR - Potential bounce opportunity")
                    
                    logger.info(f"   Sentiment: {sentiment} (Score: {sentiment_score:.0f})")
                    logger.info(f"   Fear & Greed: {fear_greed} (Score: {fg_score})")
                    logger.info(f"   5-Day Momentum: {momentum_5d:+.2f}%")
                    
                    return self.conditions['sentiment']
            
            self.conditions['sentiment'] = {
                'status': 'API_ERROR',
                'sentiment': 'UNKNOWN'
            }
            logger.warning("   Could not fetch sentiment data")
            
        except Exception as e:
            logger.error(f"   Sentiment check error: {e}")
            self.conditions['sentiment'] = {
                'status': 'ERROR',
                'sentiment': 'UNKNOWN',
                'error': str(e)
            }
        
        return self.conditions.get('sentiment', {})
    
    def check_sector_rotation(self):
        """Check sector rotation and money flow."""
        logger.info("")
        logger.info("[ROTATION] Checking Sector Rotation...")
        
        sectors = {
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLE': 'Energy',
            'XLV': 'Healthcare',
            'XLY': 'Consumer Disc',
            'XLP': 'Consumer Stap',
            'XLI': 'Industrials',
            'XLU': 'Utilities',
        }
        
        cyclical = ['XLK', 'XLF', 'XLY', 'XLI']
        defensive = ['XLV', 'XLP', 'XLU']
        
        try:
            sector_performance = {}
            
            for ticker, name in sectors.items():
                start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={start_date}&token={TIINGO_TOKEN}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) >= 2:
                        perf_5d = ((data[-1]['close'] - data[0]['close']) / data[0]['close']) * 100
                        sector_performance[ticker] = {
                            'name': name,
                            'performance_5d': round(perf_5d, 2)
                        }
            
            if sector_performance:
                cyclical_perfs = [sector_performance[s]['performance_5d'] for s in cyclical if s in sector_performance]
                defensive_perfs = [sector_performance[s]['performance_5d'] for s in defensive if s in sector_performance]
                
                cyclical_avg = sum(cyclical_perfs) / len(cyclical_perfs) if cyclical_perfs else 0
                defensive_avg = sum(defensive_perfs) / len(defensive_perfs) if defensive_perfs else 0
                
                if cyclical_avg > defensive_avg + 1:
                    rotation = 'RISK_ON'
                    rotation_strength = cyclical_avg - defensive_avg
                elif defensive_avg > cyclical_avg + 1:
                    rotation = 'RISK_OFF'
                    rotation_strength = defensive_avg - cyclical_avg
                else:
                    rotation = 'NEUTRAL'
                    rotation_strength = 0
                
                sorted_sectors = sorted(sector_performance.items(), 
                                        key=lambda x: x[1]['performance_5d'], reverse=True)
                
                self.conditions['sector_rotation'] = {
                    'rotation': rotation,
                    'rotation_strength': round(rotation_strength, 2),
                    'cyclical_avg': round(cyclical_avg, 2),
                    'defensive_avg': round(defensive_avg, 2),
                    'strongest': f"{sorted_sectors[0][1]['name']} ({sorted_sectors[0][1]['performance_5d']:+.2f}%)" if sorted_sectors else None,
                    'weakest': f"{sorted_sectors[-1][1]['name']} ({sorted_sectors[-1][1]['performance_5d']:+.2f}%)" if sorted_sectors else None,
                    'status': 'OK'
                }
                
                logger.info(f"   Rotation: {rotation} (Strength: {rotation_strength:.2f})")
                logger.info(f"   Cyclical Avg: {cyclical_avg:+.2f}%")
                logger.info(f"   Defensive Avg: {defensive_avg:+.2f}%")
                if sorted_sectors:
                    logger.info(f"   Strongest: {sorted_sectors[0][1]['name']} ({sorted_sectors[0][1]['performance_5d']:+.2f}%)")
                    logger.info(f"   Weakest: {sorted_sectors[-1][1]['name']} ({sorted_sectors[-1][1]['performance_5d']:+.2f}%)")
                
                if rotation == 'RISK_OFF':
                    self.warnings.append("ROTATION: RISK-OFF detected - Defensive sectors leading")
                
                return self.conditions['sector_rotation']
            
            self.conditions['sector_rotation'] = {
                'status': 'NO_DATA',
                'rotation': 'UNKNOWN'
            }
            
        except Exception as e:
            logger.error(f"   Sector rotation error: {e}")
            self.conditions['sector_rotation'] = {
                'status': 'ERROR',
                'rotation': 'UNKNOWN',
                'error': str(e)
            }
        
        return self.conditions.get('sector_rotation', {})
    
    def _calculate_overall_score(self):
        """Calculate overall market conditions score (0-100)."""
        score = 50
        
        vol = self.conditions.get('volatility', {})
        level = vol.get('level', 'UNKNOWN')
        if level == 'LOW' or level == 'VERY_LOW':
            score += 15
        elif level == 'MODERATE':
            score += 5
        elif level == 'HIGH':
            score -= 15
        elif level == 'EXTREME':
            score -= 30
        
        cal = self.conditions.get('economic_calendar', {})
        if cal.get('events_today', 0) > 0:
            score -= 20
        elif cal.get('events_tomorrow', 0) > 0:
            score -= 10
        
        sent = self.conditions.get('sentiment', {})
        sentiment = sent.get('sentiment', 'UNKNOWN')
        if sentiment == 'BULLISH':
            score += 10
        elif sentiment == 'BEARISH':
            score -= 10
        
        rot = self.conditions.get('sector_rotation', {})
        rotation = rot.get('rotation', 'UNKNOWN')
        if rotation == 'RISK_ON':
            score += 10
        elif rotation == 'RISK_OFF':
            score -= 10
        
        return max(0, min(100, score))
    
    def _log_summary(self, result):
        """Log summary of conditions."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("MARKET CONDITIONS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Overall Score: {result['overall_score']}/100")
        logger.info(f"Trade Allowed: {'YES' if result['trade_allowed'] else 'NO'}")
        logger.info(f"Position Size Multiplier: {result['position_size_multiplier']:.2f}x")
        
        if result['warnings']:
            logger.info("")
            logger.info("Warnings:")
            for warning in result['warnings']:
                logger.info(f"  {warning}")
        else:
            logger.info("")
            logger.info("No warnings - Conditions favorable")
        
        logger.info("=" * 60)
    
    def _save_conditions(self, result):
        """Save conditions to JSON file."""
        output_path = os.path.join(DATA_DIR, "market_conditions.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Saved to: {output_path}")


def main():
    """Run market conditions check."""
    print("")
    print("=" * 60)
    print("  MARKET CONDITIONS ANALYZER")
    print("=" * 60)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    mc = MarketConditions()
    result = mc.check_all()
    
    print("")
    print("=" * 60)
    print("  TRADING RECOMMENDATION")
    print("=" * 60)
    
    score = result['overall_score']
    
    if score >= 70:
        print("  [GREEN] CONDITIONS FAVORABLE - Normal trading")
    elif score >= 50:
        print("  [YELLOW] CONDITIONS MODERATE - Trade with caution")
    elif score >= 30:
        print("  [ORANGE] CONDITIONS UNFAVORABLE - Reduce exposure")
    else:
        print("  [RED] CONDITIONS POOR - Consider avoiding trades")
    
    print(f"")
    print(f"  Overall Score: {score}/100")
    print(f"  Position Size: {result['position_size_multiplier'] * 100:.0f}% of normal")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()