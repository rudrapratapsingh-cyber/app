# create_db.py
# Final, corrected version. Ready to run.
import sqlite3
import random
import datetime

DB_FILE = "railway_data.db"

def generate_realistic_data():
    """Generates realistic historical data for model training."""
    print("Generating 2000 historical run records for training...")
    runs = []
    base_time = datetime.datetime.now()

    for i in range(2000):
        # Simulate different times of day and week
        run_time = base_time - datetime.timedelta(hours=random.randint(0, 720))
        hour_of_day = run_time.hour
        day_of_week = run_time.weekday()  # Monday=0, Sunday=6

        # Simulate conditions
        weather_score = round(random.uniform(0.4, 1.0), 2)  # 1.0 is perfect weather
        train_priority = random.randint(1, 5)
        base_speed = random.choice([80, 100, 110, 130])

        # Make congestion and delays higher during peak hours (7-10am, 5-8pm)
        is_peak_hour = (7 <= hour_of_day <= 10) or (17 <= hour_of_day <= 20)

        if is_peak_hour:
            section_congestion = round(random.uniform(0.6, 1.0), 2)
            base_delay = random.uniform(5, 15)
        else:
            section_congestion = round(random.uniform(0.1, 0.5), 2)
            base_delay = random.uniform(0, 5)

        # The "ground truth" formula our ML model will try to learn
        actual_delay = (
            base_delay
            + (1 - section_congestion) * -2  # Lower congestion reduces delay
            + (1 - weather_score) * 10       # Bad weather increases delay
            + (5 - train_priority) * 2       # Higher priority (lower number) reduces delay
            + random.uniform(-2, 2)          # Random noise
        )
        actual_delay = max(0, round(actual_delay, 1))  # Delay can't be negative

        runs.append((
            run_time.isoformat(),
            'T' + str(random.randint(1, 8)),  # Random train_id
            hour_of_day,
            day_of_week,
            weather_score,
            section_congestion,
            train_priority,
            base_speed,
            actual_delay
        ))
    return runs


def create_database():
    """Creates and populates the SQLite database."""
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        print(f"Database '{DB_FILE}' created/connected.")

        # --- Create Schema ---
        print("Creating tables...")

        # Stations Table (5 columns)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                position_km REAL NOT NULL,
                platform_count INTEGER DEFAULT 1,
                has_loop_line INTEGER DEFAULT 0
            )
        """)

        # Sections Table (6 columns)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                id TEXT PRIMARY KEY,
                from_station_id TEXT NOT NULL,
                to_station_id TEXT NOT NULL,
                length_km REAL NOT NULL,
                track_type TEXT,
                capacity INTEGER DEFAULT 1,
                FOREIGN KEY (from_station_id) REFERENCES stations (id),
                FOREIGN KEY (to_station_id) REFERENCES stations (id)
                    
            )
        """)

        # Master list of Train types (6 columns)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trains_master (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                train_type TEXT,
                priority INTEGER,
                max_speed_kmph INTEGER,
                last_known_delay_minutes REAL DEFAULT 0
            )
        """)

        # Historical Data for ML Training (9 columns, excluding auto-incrementing ID)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historical_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                train_id TEXT,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                weather_score REAL,
                section_congestion REAL,
                train_priority INTEGER,
                base_speed INTEGER,
                actual_delay_minutes REAL
            )
        """)

        # --- Populate Static Data ---
        print("Populating static network data...")
        
        # Data for stations table (5 values per tuple)
        stations_data = [
            ('CST', 'CST', 0.0, 18, 1), ('BYC', 'Byculla', 4.5, 4, 0),
            ('DDR', 'Dadar', 9.0, 15, 1), ('KRL', 'Kurla', 16.0, 8, 1),
            ('GTN', 'Ghatkopar', 20.0, 4, 0), ('TNA', 'Thane', 33.0, 10, 1)
        ]
        
        # Data for sections table (6 values per tuple)
        sections_data = [
            ('SEC01', 'CST', 'BYC', 4.5, 'DOUBLE', 2),
            ('SEC02', 'BYC', 'DDR', 4.5, 'DOUBLE', 2),
            ('SEC03', 'DDR', 'KRL', 7.0, 'QUADRUPLE', 4),
            ('SEC04', 'KRL', 'GTN', 4.0, 'DOUBLE', 2),
            ('SEC05', 'GTN', 'TNA', 13.0, 'QUADRUPLE', 4)
        ]
        
        # Data for trains_master table (6 values per tuple)
        trains_data = [
            ('T1', 'Mumbai Express', 'EXPRESS', 1, 130, 0), ('T2', 'Pune Mail', 'EXPRESS', 1, 130, 0),
            ('T3', 'Dadar Slow', 'LOCAL', 3, 100, 0), ('T4', 'Thane Fast', 'LOCAL', 2, 110, 0),
            ('T5', 'Goods Carrier', 'FREIGHT', 5, 80, 0), ('T6', 'Maintenance Special', 'SPECIAL', 4, 80, 0),
            ('T7', 'Kurla Slow', 'LOCAL', 3, 100, 0), ('T8', 'CST Fast', 'LOCAL', 2, 110, 0)
        ]

        # --- Execute INSERT statements ---
        cur.executemany("INSERT OR IGNORE INTO stations VALUES (?, ?, ?, ?, ?)", stations_data)
        cur.executemany("INSERT OR IGNORE INTO sections VALUES (?, ?, ?, ?, ?, ?)", sections_data)
        cur.executemany("INSERT OR IGNORE INTO trains_master VALUES (?, ?, ?, ?, ?, ?)", trains_data)

        # --- Populate Historical Data ---
        historical_data = generate_realistic_data()
        cur.execute("DELETE FROM historical_runs")  # Clear old data before inserting new
        cur.executemany("""
            INSERT INTO historical_runs (
                timestamp, train_id, hour_of_day, day_of_week, weather_score, 
                section_congestion, train_priority, base_speed, actual_delay_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, historical_data)

        con.commit()
        print(f"Successfully populated database with {cur.rowcount} historical records.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Add traceback for detailed debugging if needed
        import traceback
        traceback.print_exc()
    finally:
        if con:
            con.close()
            print("Database connection closed.")


if __name__ == "__main__":
    create_database()