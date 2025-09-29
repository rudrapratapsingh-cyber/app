
# time_series_analyzer.py - ADD THIS NEW AI COMPONENT
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

class RailwayTimeSeriesAnalyzer:
    """AI-powered time series analysis for railway patterns"""

    def __init__(self):
        self.historical_data = []
        self.patterns = {}

    def add_operational_data(self, timestamp, trains_data, sections_data):
        """Add real-time operational data for pattern learning"""
        data_point = {
            'timestamp': timestamp.isoformat(),
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'total_trains': len(trains_data),
            'delayed_trains': sum(1 for t in trains_data if t.get('delay', 0) > 5),
            'avg_delay': sum(t.get('delay', 0) for t in trains_data) / len(trains_data) if trains_data else 0,
            'section_utilization': {s['id']: s.get('occupancy', 0) / s.get('capacity', 1) 
                                  for s in sections_data},
            'peak_congestion': max([s.get('occupancy', 0) / s.get('capacity', 1) for s in sections_data], default=0)
        }

        self.historical_data.append(data_point)

        # Keep only last 7 days of data
        cutoff_time = timestamp - timedelta(days=7)
        self.historical_data = [d for d in self.historical_data 
                               if datetime.fromisoformat(d['timestamp']) > cutoff_time]

    def analyze_peak_patterns(self):
        """Identify peak traffic patterns using AI"""
        if len(self.historical_data) < 10:
            return {"status": "Insufficient data for pattern analysis"}

        df = pd.DataFrame(self.historical_data)

        # Peak hour analysis
        hourly_delays = df.groupby('hour')['avg_delay'].mean()
        peak_hours = hourly_delays[hourly_delays > hourly_delays.mean() + hourly_delays.std()].index.tolist()

        # Day of week patterns
        daily_congestion = df.groupby('day_of_week')['peak_congestion'].mean()
        busy_days = daily_congestion[daily_congestion > daily_congestion.mean()].index.tolist()

        # Congestion propagation patterns
        congestion_correlation = {}
        for i in range(len(df) - 1):
            current_congestion = df.iloc[i]['peak_congestion']
            next_congestion = df.iloc[i + 1]['peak_congestion']

            if current_congestion > 0.7:  # High congestion threshold
                if next_congestion > current_congestion:
                    congestion_correlation['propagates'] = congestion_correlation.get('propagates', 0) + 1
                else:
                    congestion_correlation['dissipates'] = congestion_correlation.get('dissipates', 0) + 1

        patterns = {
            "peak_hours": peak_hours,
            "busy_days": [["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][d] 
                         for d in busy_days],
            "average_delay_by_hour": {str(hour): delay for hour, delay in hourly_delays.items()},
            "congestion_propagation_rate": (
                congestion_correlation.get('propagates', 0) / 
                max(sum(congestion_correlation.values()), 1) * 100
            ),
            "recommendations": self._generate_pattern_recommendations(peak_hours, busy_days)
        }

        self.patterns = patterns
        return patterns

    def _generate_pattern_recommendations(self, peak_hours, busy_days):
        """Generate AI recommendations based on patterns"""
        recommendations = []

        if peak_hours:
            recommendations.append(f"Deploy additional controllers during peak hours: {peak_hours}")

        if busy_days:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            busy_day_names = [day_names[d] for d in busy_days]
            recommendations.append(f"Expect higher congestion on: {', '.join(busy_day_names)}")

        recommendations.extend([
            "Consider freight scheduling outside peak passenger hours",
            "Implement dynamic section capacity allocation during high-traffic periods",
            "Pre-position maintenance teams during predicted low-traffic windows"
        ])

        return recommendations

    def predict_next_hour_congestion(self):
        """Predict congestion for the next hour using pattern analysis"""
        if not self.historical_data:
            return {"prediction": "no_data", "confidence": 0}

        current_time = datetime.now()
        current_hour = current_time.hour
        current_day = current_time.weekday()

        # Simple pattern-based prediction
        similar_periods = [
            d for d in self.historical_data 
            if d['hour'] == current_hour and d['day_of_week'] == current_day
        ]

        if similar_periods:
            avg_congestion = sum(d['peak_congestion'] for d in similar_periods) / len(similar_periods)
            confidence = min(len(similar_periods) / 5.0, 1.0)  # Max confidence at 5+ similar periods

            if avg_congestion > 0.8:
                prediction = "high"
            elif avg_congestion > 0.5:
                prediction = "medium"
            else:
                prediction = "low"

            return {
                "prediction": prediction,
                "confidence": confidence,
                "expected_congestion": avg_congestion,
                "based_on_samples": len(similar_periods)
            }
        else:
            return {"prediction": "unknown", "confidence": 0}

    def get_anomaly_detection(self):
        """Detect unusual patterns in current operations"""
        if len(self.historical_data) < 20:
            return {"status": "Insufficient data for anomaly detection"}

        df = pd.DataFrame(self.historical_data[-20:])  # Last 20 data points

        # Calculate recent averages
        recent_avg_delay = df['avg_delay'].mean()
        recent_avg_congestion = df['peak_congestion'].mean()

        # Compare with historical averages
        historical_avg_delay = pd.DataFrame(self.historical_data[:-20])['avg_delay'].mean() if len(self.historical_data) > 20 else recent_avg_delay
        historical_avg_congestion = pd.DataFrame(self.historical_data[:-20])['peak_congestion'].mean() if len(self.historical_data) > 20 else recent_avg_congestion

        anomalies = []

        if recent_avg_delay > historical_avg_delay * 1.5:
            anomalies.append("Unusual increase in average delays detected")

        if recent_avg_congestion > historical_avg_congestion * 1.3:
            anomalies.append("Abnormal congestion levels detected")

        return {
            "anomalies": anomalies,
            "recent_avg_delay": recent_avg_delay,
            "historical_avg_delay": historical_avg_delay,
            "congestion_trend": "increasing" if recent_avg_congestion > historical_avg_congestion else "stable"
        }

# Usage example:
# analyzer = RailwayTimeSeriesAnalyzer()
# analyzer.add_operational_data(datetime.now(), trains_data, sections_data)
# patterns = analyzer.analyze_peak_patterns()
# prediction = analyzer.predict_next_hour_congestion()
