# live_database.py - Live Database System for Charbagh Railway Station
import sqlite3
import json
import random
import datetime
from datetime import timedelta
import threading
import time
from typing import List, Dict, Tuple, Optional

class CharbhaghLiveDatabase:
    """Live database system for Charbagh Railway Station with 9 platforms"""
    
    def __init__(self, db_path="charbagh_live.db"):
        self.db_path = db_path
        self.platforms = list(range(1, 10))  # 9 platforms
        self.live_updates_active = False
        self.update_thread = None
        self.initialize_database()
        self.populate_initial_data()
        
    def initialize_database(self):
        """Initialize SQLite database with comprehensive schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trains table with comprehensive information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_number VARCHAR(10) UNIQUE,
                train_name VARCHAR(100),
                train_type VARCHAR(50),
                origin_station VARCHAR(100),
                destination_station VARCHAR(100),
                scheduled_arrival DATETIME,
                scheduled_departure DATETIME,
                actual_arrival DATETIME,
                actual_departure DATETIME,
                platform_number INTEGER,
                current_status VARCHAR(50),
                delay_minutes INTEGER DEFAULT 0,
                distance_km INTEGER,
                max_speed INTEGER,
                priority INTEGER,
                passenger_capacity INTEGER,
                current_occupancy INTEGER,
                route_stations TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Platform status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platform_status (
                platform_number INTEGER PRIMARY KEY,
                current_train VARCHAR(10),
                status VARCHAR(50),
                next_arrival DATETIME,
                next_departure DATETIME,
                occupancy_duration INTEGER,
                maintenance_status VARCHAR(50),
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Real-time events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                train_number VARCHAR(10),
                event_type VARCHAR(50),
                platform_number INTEGER,
                description TEXT,
                severity VARCHAR(20)
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_trains INTEGER,
                on_time_trains INTEGER,
                delayed_trains INTEGER,
                avg_delay_minutes REAL,
                platform_utilization REAL,
                passenger_satisfaction REAL,
                system_efficiency REAL,
                conflicts_detected INTEGER,
                conflicts_resolved INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def populate_initial_data(self):
        """Populate database with 2000+ realistic train records for Charbagh"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM trains")
            if cursor.fetchone()[0] > 0:
                print("✅ Database already contains data, skipping population")
                conn.close()
                return
                
            # Realistic train data for Charbagh Railway Station
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
            
            # Major stations connected to Charbagh
            stations = [
                "New Delhi", "Mumbai Central", "Kolkata", "Chennai Central", 
                "Bangalore", "Hyderabad", "Pune", "Ahmedabad", "Jaipur",
                "Patna", "Kanpur", "Allahabad", "Varanasi", "Gorakhpur",
                "Bareilly", "Moradabad", "Agra", "Gwalior", "Bhopal",
                "Indore", "Nagpur", "Raipur", "Bilaspur", "Jabalpur"
            ]
            
            # Generate 2000+ train records
            trains_data = []
            base_date = datetime.datetime.now()
            used_train_numbers = set()  # Track used train numbers to avoid duplicates
            
            for i in range(2500):  # Generate 2500 records
                train_type, speed, max_speed, capacity, priority = random.choice(train_types)
                
                # Generate unique train number (realistic format)
                train_number = None
                max_attempts = 100  # Prevent infinite loop
                attempts = 0
                
                while train_number is None and attempts < max_attempts:
                    if train_type in ["Rajdhani", "Shatabdi"]:
                        candidate = f"{random.randint(12000, 19999)}"  # Expanded range
                    elif train_type == "Superfast":
                        candidate = f"{random.randint(20000, 29999)}"  # Expanded range
                    else:
                        candidate = f"{random.randint(10000, 19999)}"  # Expanded range
                    
                    if candidate not in used_train_numbers:
                        train_number = candidate
                        used_train_numbers.add(train_number)
                    
                    attempts += 1
                
                # Fallback if we couldn't generate a unique number (very unlikely)
                if train_number is None:
                    train_number = f"{10000 + i}"  # Use sequential fallback
                    used_train_numbers.add(train_number)
                
                # Generate realistic train name
                origin = random.choice(stations)
                destination = random.choice([s for s in stations if s != origin])
                train_name = f"{origin} - {destination} {train_type}"
                
                # Generate schedule times (spread across week)
                days_offset = random.randint(-3, 7)  # Past 3 days to future 7 days
                base_time = base_date + timedelta(days=days_offset)
                
                arrival_hour = random.randint(0, 23)
                arrival_minute = random.choice([0, 15, 30, 45])
                scheduled_arrival = base_time.replace(
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
                
                # Assign platform (weighted distribution)
                platform = random.choices(
                    self.platforms,
                    weights=[12, 15, 18, 15, 10, 10, 8, 7, 5]  # Some platforms busier
                )[0]
                
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
            
            # Insert all train data with error handling
            try:
                cursor.executemany('''
                    INSERT INTO trains (
                        train_number, train_name, train_type, origin_station, destination_station,
                        scheduled_arrival, scheduled_departure, actual_arrival, actual_departure,
                        platform_number, current_status, delay_minutes, distance_km, max_speed, 
                        priority, passenger_capacity, current_occupancy, route_stations
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', trains_data)
            except sqlite3.IntegrityError as e:
                print(f"⚠️  Database integrity error during population: {e}")
                print("🔄 Attempting to clear and repopulate database...")
                
                # Clear existing data and try again
                cursor.execute("DELETE FROM trains")
                cursor.execute("DELETE FROM platform_status")
                cursor.execute("DELETE FROM live_events")
                cursor.execute("DELETE FROM performance_metrics")
                
                # Try insertion again
                cursor.executemany('''
                    INSERT INTO trains (
                        train_number, train_name, train_type, origin_station, destination_station,
                        scheduled_arrival, scheduled_departure, actual_arrival, actual_departure,
                        platform_number, current_status, delay_minutes, distance_km, max_speed, 
                        priority, passenger_capacity, current_occupancy, route_stations
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', trains_data)
            
            # Initialize platform status
            for platform in self.platforms:
                cursor.execute('''
                    INSERT INTO platform_status (
                        platform_number, status, maintenance_status
                    ) VALUES (?, ?, ?)
                ''', (platform, "Available", "Operational"))
        
            conn.commit()
            conn.close()
            print(f"✅ Populated database with {len(trains_data)} train records for Charbagh Station")
            
        except Exception as e:
            print(f"❌ Error during database population: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            raise
        
    def start_live_updates(self):
        """Start live updates simulation"""
        if not self.live_updates_active:
            self.live_updates_active = True
            self.update_thread = threading.Thread(target=self._live_update_loop, daemon=True)
            self.update_thread.start()
            print("🚀 Live updates started for Charbagh Railway Station")
    
    def stop_live_updates(self):
        """Stop live updates"""
        self.live_updates_active = False
        if self.update_thread:
            self.update_thread.join()
        print("⏹️ Live updates stopped")
    
    def _live_update_loop(self):
        """Continuous live updates simulation"""
        while self.live_updates_active:
            try:
                self._simulate_real_time_updates()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                print(f"Error in live updates: {e}")
                time.sleep(60)
    
    def _simulate_real_time_updates(self):
        """Simulate real-time train movements and updates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.datetime.now()
        
        # Update train statuses based on current time
        cursor.execute('''
            UPDATE trains 
            SET current_status = CASE
                WHEN actual_departure < ? THEN 'Departed'
                WHEN actual_arrival <= ? AND actual_departure > ? THEN 'At Platform'
                WHEN scheduled_arrival <= ? AND actual_arrival > ? THEN 'Delayed'
                ELSE current_status
            END,
            last_updated = ?
        ''', (current_time, current_time, current_time, current_time, current_time, current_time))
        
        # Random delay updates (simulate real-world changes)
        if random.random() < 0.1:  # 10% chance
            cursor.execute('''
                SELECT train_number FROM trains 
                WHERE current_status IN ('Scheduled', 'Delayed') 
                ORDER BY RANDOM() LIMIT 1
            ''')
            result = cursor.fetchone()
            if result:
                additional_delay = random.randint(5, 30)
                cursor.execute('''
                    UPDATE trains 
                    SET delay_minutes = delay_minutes + ?,
                        actual_arrival = datetime(actual_arrival, '+{} minutes'),
                        actual_departure = datetime(actual_departure, '+{} minutes'),
                        last_updated = ?
                    WHERE train_number = ?
                '''.format(additional_delay, additional_delay), 
                (additional_delay, current_time, result[0]))
                
                # Log event
                cursor.execute('''
                    INSERT INTO live_events (train_number, event_type, description, severity)
                    VALUES (?, ?, ?, ?)
                ''', (result[0], "Delay Update", f"Additional delay of {additional_delay} minutes", "Medium"))
        
        # Update platform status
        for platform in self.platforms:
            cursor.execute('''
                SELECT train_number FROM trains 
                WHERE platform_number = ? AND current_status = 'At Platform'
                LIMIT 1
            ''', (platform,))
            
            current_train = cursor.fetchone()
            status = "Occupied" if current_train else "Available"
            
            cursor.execute('''
                UPDATE platform_status 
                SET current_train = ?, status = ?, last_updated = ?
                WHERE platform_number = ?
            ''', (current_train[0] if current_train else None, status, current_time, platform))
        
        # Update performance metrics
        cursor.execute('''
            INSERT INTO performance_metrics (
                total_trains, on_time_trains, delayed_trains, avg_delay_minutes,
                platform_utilization, passenger_satisfaction, system_efficiency,
                conflicts_detected, conflicts_resolved
            )
            SELECT 
                COUNT(*) as total_trains,
                COUNT(CASE WHEN delay_minutes = 0 THEN 1 END) as on_time_trains,
                COUNT(CASE WHEN delay_minutes > 0 THEN 1 END) as delayed_trains,
                AVG(CAST(delay_minutes AS REAL)) as avg_delay_minutes,
                (SELECT COUNT(*) FROM platform_status WHERE status = 'Occupied') * 100.0 / 9 as platform_utilization,
                CASE 
                    WHEN AVG(CAST(delay_minutes AS REAL)) < 10 THEN 95.0
                    WHEN AVG(CAST(delay_minutes AS REAL)) < 20 THEN 85.0
                    ELSE 75.0
                END as passenger_satisfaction,
                CASE 
                    WHEN AVG(CAST(delay_minutes AS REAL)) < 15 THEN 90.0
                    WHEN AVG(CAST(delay_minutes AS REAL)) < 30 THEN 80.0
                    ELSE 70.0
                END as system_efficiency,
                ? as conflicts_detected,
                ? as conflicts_resolved
            FROM trains 
            WHERE DATE(scheduled_arrival) = DATE(?)
        ''', (random.randint(0, 5), random.randint(0, 3), current_time.date()))
        
        conn.commit()
        conn.close()
    
    def get_live_train_data(self) -> List[Dict]:
        """Get current live train data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trains 
            WHERE DATE(scheduled_arrival) >= DATE('now', '-1 day')
            ORDER BY scheduled_arrival
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        trains = []
        for row in cursor.fetchall():
            train_dict = dict(zip(columns, row))
            if train_dict['route_stations']:
                train_dict['route_stations'] = json.loads(train_dict['route_stations'])
            trains.append(train_dict)
        
        conn.close()
        return trains
    
    def get_platform_status(self) -> List[Dict]:
        """Get current platform status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ps.*, t.train_name, t.scheduled_departure 
            FROM platform_status ps
            LEFT JOIN trains t ON ps.current_train = t.train_number
            ORDER BY ps.platform_number
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        platforms = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return platforms
    
    def get_performance_metrics(self) -> Dict:
        """Get latest performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM performance_metrics 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            metrics = dict(zip(columns, result))
        else:
            metrics = {
                'total_trains': 0, 'on_time_trains': 0, 'delayed_trains': 0,
                'avg_delay_minutes': 0, 'platform_utilization': 0,
                'passenger_satisfaction': 0, 'system_efficiency': 0,
                'conflicts_detected': 0, 'conflicts_resolved': 0
            }
        
        conn.close()
        return metrics
    
    def detect_conflicts(self) -> List[Dict]:
        """Detect potential conflicts and issues"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conflicts = []
        
        # Platform conflicts
        cursor.execute('''
            SELECT platform_number, COUNT(*) as conflict_count,
                   GROUP_CONCAT(train_number) as conflicting_trains
            FROM trains 
            WHERE current_status = 'At Platform' 
            GROUP BY platform_number 
            HAVING COUNT(*) > 1
        ''')
        
        for row in cursor.fetchall():
            conflicts.append({
                'type': 'Platform Conflict',
                'platform': row[0],
                'severity': 'High',
                'description': f"Platform {row[0]} has {row[1]} trains simultaneously",
                'affected_trains': row[2].split(','),
                'recommendation': f"Immediate intervention required for Platform {row[0]}"
            })
        
        # Schedule conflicts (trains arriving too close)
        cursor.execute('''
            SELECT t1.train_number, t2.train_number, t1.platform_number,
                   ABS(julianday(t1.scheduled_arrival) - julianday(t2.scheduled_arrival)) * 24 * 60 as time_diff
            FROM trains t1, trains t2 
            WHERE t1.platform_number = t2.platform_number 
            AND t1.train_number < t2.train_number
            AND ABS(julianday(t1.scheduled_arrival) - julianday(t2.scheduled_arrival)) * 24 * 60 < 15
            AND t1.current_status IN ('Scheduled', 'Delayed')
            AND t2.current_status IN ('Scheduled', 'Delayed')
        ''')
        
        for row in cursor.fetchall():
            conflicts.append({
                'type': 'Schedule Conflict',
                'platform': row[2],
                'severity': 'Medium',
                'description': f"Trains {row[0]} and {row[1]} scheduled too close ({row[3]:.1f} min apart)",
                'affected_trains': [row[0], row[1]],
                'recommendation': "Consider platform reassignment or schedule adjustment"
            })
        
        conn.close()
        return conflicts
    
    def get_analytics_data(self) -> Dict:
        """Get comprehensive analytics data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Platform utilization
        cursor.execute('''
            SELECT platform_number, COUNT(*) as train_count,
                   AVG(CAST(delay_minutes AS REAL)) as avg_delay
            FROM trains 
            WHERE DATE(scheduled_arrival) = DATE('now')
            GROUP BY platform_number
            ORDER BY platform_number
        ''')
        platform_analytics = [
            {'platform': row[0], 'trains': row[1], 'avg_delay': row[2] or 0}
            for row in cursor.fetchall()
        ]
        
        # Train type distribution
        cursor.execute('''
            SELECT train_type, COUNT(*) as count,
                   AVG(CAST(delay_minutes AS REAL)) as avg_delay
            FROM trains 
            GROUP BY train_type
            ORDER BY count DESC
        ''')
        train_type_analytics = [
            {'type': row[0], 'count': row[1], 'avg_delay': row[2] or 0}
            for row in cursor.fetchall()
        ]
        
        # Hourly traffic
        cursor.execute('''
            SELECT strftime('%H', scheduled_arrival) as hour, COUNT(*) as count
            FROM trains 
            WHERE DATE(scheduled_arrival) = DATE('now')
            GROUP BY hour
            ORDER BY hour
        ''')
        hourly_traffic = [
            {'hour': int(row[0]), 'trains': row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return {
            'platform_analytics': platform_analytics,
            'train_type_analytics': train_type_analytics,
            'hourly_traffic': hourly_traffic
        }

# Global instance
charbagh_db = CharbhaghLiveDatabase()