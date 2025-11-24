"""Gann Time Cycles Analysis."""

from datetime import datetime, timedelta


class TimeCycleAnalyzer:
    """Analyze Gann time cycles."""
    
    def __init__(self):
        self.gann_cycles = [7, 30, 45, 60, 90, 120, 144, 180, 270, 360]
        self.fib_cycles = [8, 13, 21, 34, 55, 89, 144, 233]
    
    def get_cycle_dates(self, start_date, cycles=None):
        """Calculate important cycle dates from a start date."""
        if cycles is None:
            cycles = self.gann_cycles
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        return {
            f'{c}_days': (start_date + timedelta(days=c)).strftime('%Y-%m-%d')
            for c in cycles
        }
    
    def check_cycle_confluence(self, target_date, pivot_dates):
        """Check if target date has cycle confluence from multiple pivots."""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d')
        
        confluences = []
        
        for pivot in pivot_dates:
            if isinstance(pivot, str):
                pivot = datetime.strptime(pivot, '%Y-%m-%d')
            
            days_diff = abs((target_date - pivot).days)
            
            for cycle in self.gann_cycles:
                if abs(days_diff - cycle) <= 2:
                    confluences.append({
                        'pivot': pivot.strftime('%Y-%m-%d'),
                        'cycle': cycle,
                        'days': days_diff,
                    })
        
        return {
            'confluences': confluences,
            'count': len(confluences),
            'is_significant': len(confluences) >= 2,
        }
    
    def get_seasonal_bias(self, date=None):
        """Get seasonal trading bias."""
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        
        month = date.month
        
        # Historical seasonal patterns
        bullish_months = [11, 12, 1, 4]  # Nov-Dec-Jan, April
        bearish_months = [9, 10]  # Sept-Oct
        
        if month in bullish_months:
            return {'bias': 'BULLISH', 'strength': 0.6}
        elif month in bearish_months:
            return {'bias': 'BEARISH', 'strength': 0.6}
        else:
            return {'bias': 'NEUTRAL', 'strength': 0.5}


if __name__ == "__main__":
    analyzer = TimeCycleAnalyzer()
    
    cycles = analyzer.get_cycle_dates('2025-01-01')
    print("Cycle dates from Jan 1, 2025:")
    for name, date in list(cycles.items())[:5]:
        print(f"  {name}: {date}")
    
    seasonal = analyzer.get_seasonal_bias()
    print(f"\nSeasonal bias: {seasonal['bias']}")