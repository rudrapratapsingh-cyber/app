#!/usr/bin/env python3

import sqlite3
import json
import random
import datetime
from datetime import timedelta

# Connect to database
db_path = "charbagh_live.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Train types and their characteristics
train_types = [
    ("Express", 70, 110, 1200, 5),
    ("Superfast", 80, 130, 1400, 4),
    ("Mail", 65, 100, 1800, 3),
    ("Passenger", 50, 80, 800, 2),
    ("Intercity", 75, 120, 1000, 4),
    ("Rajdhani", 90, 160, 1500, 5),
    ("Shatabdi", 85, 150, 1200, 5),
    ("Duronto", 80, 140, 1600, 4),
    ("Jan Shatabdi", 70, 120, 1000, 3),
    ("Garib Rath", 75, 130, 1800, 3)
]

# Major stations
stations = [
    "New Delhi", "Mumbai Central", "Kolkata", "Chennai Central", 
    "Bangalore", "Hyderabad", "Pune", "Ahmedabad", "Jaipur",
    "Patna", "Kanpur", "Allahabad", "Varanasi", "Gorakhpur",
    "Bareilly", "Moradabad", "Agra", "Gwalior", "Bhopal",
    "Indore", "Nagpur", "Raipur", "Bilaspur", "Jabalpur"
]

platforms = list(range(1, 10))  # 9 platforms

# Get existing train numbers to avoid duplicates
cursor.execute("SELECT train_number FROM trains")
existing_numbers = {row[0] for row in cursor.fetchall()}

print(f"Found {len(existing_numbers)} existing train numbers")

# Generate 100 trains for today and tomorrow
trains_data = []
base_date = datetime.datetime.now()

for day_offset in [0, 1]:  # Today and tomorrow
    current_date = base_date + timedelta(days=day_offset)
    
    for i in range(50):  # 50 trains per day
        train_type, speed, max_speed, capacity, priority = random.choice(train_types)
        
        # Generate unique train number
        while True:
            if train_type in ["Rajdhani", "Shatabdi"]:
                candidate = f"{random.randint(30000, 39999)}"  # Different range to avoid conflicts
            elif train_type == "Superfast":
                candidate = f"{random.randint(40000, 49999)}"
            else:
                candidate = f"{random.randint(50000, 59999)}"
            
            if candidate not in existing_numbers:
                train_number = candidate
                existing_numbers.add(train_number)
                break
        
        # Generate realistic train name
        origin = random.choice(stations)
        destination = random.choice([s for s in stations if s != origin])
        train_name = f"{origin} - {destination} {train_type}"
        
        # Generate schedule times for this day
        arrival_hour = random.randint(0, 23)
        arrival_minute = random.choice([0, 15, 30, 45])
        scheduled_arrival = current_date.replace(
            hour=arrival_hour, 
            minute=arrival_minute, 
            second=0, 
            microsecond=0
        )
        
        # Platform stay duration (15 minutes to 2 hours)
        stay_duration = random.randint(15, 120)
        scheduled_departure = scheduled_arrival + timedelta(minutes=stay_duration)
        
        # Generate delays and actual times
        delay = random.choices(
            [0, 5, 10, 15, 20, 30, 45, 60, 90, 120],
            weights=[40, 20, 15, 10, 7, 4, 2, 1, 0.5, 0.5]
        )[0]
        
        actual_arrival = scheduled_arrival + timedelta(minutes=delay)
        actual_departure = scheduled_departure + timedelta(minutes=delay)
        
        # Assign platform
        platform = random.choice(platforms)
        
        # Generate status based on timing
        current_time = datetime.datetime.now()
        if actual_departure < current_time:
            status = "Departed"
        elif actual_arrival <= current_time < actual_departure:
            status = "At Platform"
        elif scheduled_arrival <= current_time < actual_arrival:
            status = "Delayed"
        else:
            status = "Scheduled"
        
        # Generate route stations
        route_count = random.randint(5, 15)
        route_stations = random.sample(stations, min(route_count, len(stations)))
        route_json = json.dumps(route_stations)
        
        # Current occupancy
        occupancy = random.randint(int(capacity * 0.4), capacity)
        
        # Distance
        distance = random.randint(200, 2000)
        
        trains_data.append((
            train_number, train_name, train_type, origin, destination,
            scheduled_arrival, scheduled_departure, actual_arrival, actual_departure,
            platform, status, delay, distance, max_speed, priority,
            capacity, occupancy, route_json
        ))

# Insert the new train data
cursor.executemany('''
    INSERT INTO trains (
        train_number, train_name, train_type, origin_station, destination_station,
        scheduled_arrival, scheduled_departure, actual_arrival, actual_departure,
        platform_number, current_status, delay_minutes, distance_km, max_speed, 
        priority, passenger_capacity, current_occupancy, route_stations
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', trains_data)

conn.commit()
conn.close()

print(f"✅ Added {len(trains_data)} current trains to the database")
print("50 trains for today and 50 trains for tomorrow")