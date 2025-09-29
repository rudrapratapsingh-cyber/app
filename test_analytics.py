#!/usr/bin/env python3

from live_database import charbagh_db
import datetime

# Test the date filtering logic used in Flask app
trains = charbagh_db.get_live_train_data()
recent_date = datetime.date.today() - datetime.timedelta(days=1)

print(f"Total trains in database: {len(trains)}")
print(f"Recent date cutoff: {recent_date}")

# Filter for recent trains (same logic as Flask app)
recent_trains = [t for t in trains if datetime.datetime.fromisoformat(t['scheduled_arrival']).date() >= recent_date]

print(f"Recent trains (>= {recent_date}): {len(recent_trains)}")

# Test today's trains
today_trains = [t for t in trains if datetime.datetime.fromisoformat(t['scheduled_arrival']).date() == datetime.date.today()]
print(f"Today's trains: {len(today_trains)}")

# Show some sample data
if recent_trains:
    print("\nSample recent train dates:")
    for train in recent_trains[:5]:
        arrival_date = datetime.datetime.fromisoformat(train['scheduled_arrival']).date()
        print(f"  {train['train_number']}: {arrival_date}")

# Test analytics data
analytics = charbagh_db.get_analytics_data()
performance = charbagh_db.get_performance_metrics()

print(f"\nPerformance metrics available: {bool(performance)}")
print(f"Analytics data keys: {list(analytics.keys())}")
print(f"Platform analytics entries: {len(analytics.get('platform_analytics', []))}")
print(f"Train type analytics entries: {len(analytics.get('train_type_analytics', []))}")

# Calculate some sample KPIs like the Flask app does
if recent_trains and performance:
    punctuality_rate = round((performance.get('on_time_trains', 0) / max(performance.get('total_trains', 1), 1)) * 100, 1)
    avg_delay = round(performance.get('avg_delay_minutes', 0), 1)
    platform_util = round(performance.get('platform_utilization', 0), 1)
    
    print(f"\nSample KPI calculations:")
    print(f"  Punctuality rate: {punctuality_rate}%")
    print(f"  Average delay: {avg_delay} minutes")
    print(f"  Platform utilization: {platform_util}%")
    
    # Delay distribution for recent trains
    on_time = len([t for t in recent_trains if t['delay_minutes'] == 0])
    minor_delay = len([t for t in recent_trains if 0 < t['delay_minutes'] <= 15])
    moderate_delay = len([t for t in recent_trains if 15 < t['delay_minutes'] <= 30])
    major_delay = len([t for t in recent_trains if t['delay_minutes'] > 30])
    
    print(f"\nDelay distribution for recent trains:")
    print(f"  On time: {on_time}")
    print(f"  Minor delay (5-15min): {minor_delay}")
    print(f"  Moderate delay (15-30min): {moderate_delay}")
    print(f"  Major delay (30min+): {major_delay}")
else:
    print("\nNot enough data for KPI calculations")