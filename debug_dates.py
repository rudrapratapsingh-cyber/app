#!/usr/bin/env python3

from live_database import charbagh_db
import datetime

# Get sample data
trains = charbagh_db.get_live_train_data()
print(f"Total trains: {len(trains)}")

if trains:
    sample_train = trains[0]
    sample_date = sample_train['scheduled_arrival']
    
    print(f"Date string: {repr(sample_date)}")
    print(f"Type: {type(sample_date)}")
    
    # Test different parsing methods
    try:
        dt1 = datetime.datetime.fromisoformat(sample_date)
        print(f"fromisoformat works: {dt1}")
    except Exception as e:
        print(f"fromisoformat fails: {e}")
    
    try:
        dt2 = datetime.datetime.strptime(sample_date, '%Y-%m-%d %H:%M:%S')
        print(f"strptime works: {dt2}")
        print(f"Date only: {dt2.date()}")
        print(f"Today: {datetime.date.today()}")
        print(f"Is today?: {dt2.date() == datetime.date.today()}")
    except Exception as e:
        print(f"strptime fails: {e}")

# Test analytics data
print("\n--- Analytics Data ---")
try:
    analytics = charbagh_db.get_analytics_data()
    print(f"Analytics keys: {analytics.keys()}")
    print(f"Platform analytics: {analytics.get('platform_analytics', [])[:3]}")
    print(f"Train type analytics: {analytics.get('train_type_analytics', [])[:3]}")
    print(f"Hourly traffic: {analytics.get('hourly_traffic', [])[:5]}")
except Exception as e:
    print(f"Analytics error: {e}")

# Test performance metrics
print("\n--- Performance Metrics ---")
try:
    metrics = charbagh_db.get_performance_metrics()
    print(f"Metrics: {metrics}")
except Exception as e:
    print(f"Metrics error: {e}")