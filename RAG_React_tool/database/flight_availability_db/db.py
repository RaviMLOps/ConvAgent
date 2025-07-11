import sqlite3
import csv
import os
from pathlib import Path

# Get the directory of the current script
current_dir = Path(__file__).parent

# Connect to or create the database in the same directory
db_path = current_dir / 'data' / 'flight_schedule.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

def create_and_insert_data(conn, cursor):
    """Create the flight_schedule table and import data from CSV"""
    # Drop existing table if it exists
    cursor.execute('''
    DROP TABLE IF EXISTS flight_schedule
    ''')
    
    # Create new table with updated schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flight_schedule (
        flight_id VARCHAR(10) PRIMARY KEY,
        from_airport VARCHAR(100),
        to_airport VARCHAR(100),
        departure_time TIME,
        flight_duration FLOAT,
        arrival_time TIME,
        from_city VARCHAR(50),
        to_city VARCHAR(50),
        from_airport_code VARCHAR(5),
        to_airport_code VARCHAR(5),
        from_country VARCHAR(50),
        to_country VARCHAR(50),
        departure_days VARCHAR(50),
        status VARCHAR(20),
        delay VARCHAR(20)
    )
    ''')
    
    # Import data from CSV
    csv_path = current_dir / 'Flight_availability_and_schedule.csv'
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Prepare data for insertion
        data = [(
            row['Flight ID'],
            row['From airport'].strip(),
            row['To airport'].strip(),
            row['Departure time'],
            float(row['Flight duration']),
            row['Arrival time'],
            row['From city'],
            row['To city'],
            row['From airport code'].strip(),
            row['To airport code'].strip(),
            row['From country'],
            row['To country'],
            row['Departure days of week'],
            row['Status'],
            row.get('Delay', '0')
        ) for row in reader]
        
        # Insert data
        cursor.executemany('''
        INSERT INTO flight_schedule VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    # Commit changes
    conn.commit()
    print(f"Successfully imported flight schedule data to {db_path}")

def create_and_insert_flight_reservation_data(conn, cursor):
    """Create the Flight_reservation table and import data from CSV"""
    # Drop existing table if it exists
    cursor.execute('''
    DROP TABLE IF EXISTS Flight_reservation
    ''')
    
    # Create new table with updated schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Flight_reservation (
        PNR_Number TEXT,
        Customer_Name TEXT,
        Flight_ID TEXT,
        Airline TEXT,
        From_City TEXT,
        To_City TEXT,
        Departure_Time TEXT,
        Arrival_Time TEXT,
        Travel_Date TEXT,
        Booking_Date TEXT,
        Booking_Status TEXT,
        Refund_Status TEXT
    )
    ''')
    
    # Import data from CSV
    csv_path = current_dir / 'Flight_reservation.csv'
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Prepare data for insertion
        data = [(
            row['PNR_Number'],
            row['Customer_Name'],
            row['Flight_ID'],
            row['Airline'],
            row['From_City'],
            row['To_City'],
            row['Departure_Time'],
            row['Arrival_Time'],
            row['Travel_Date'],
            row['Booking_Date'],
            row['Booking_Status'],
            row['Refund_Status']
        ) for row in reader]
        
        # Insert data
        cursor.executemany('''
        INSERT INTO Flight_reservation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    # Commit changes
    conn.commit()
    print(f"Successfully imported Flight_reservation data to {db_path}")

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return bool(cursor.fetchall())

def get_all_flights(cursor, limit=10):
    """Query and return flight schedule data"""
    cursor.execute("SELECT * FROM flight_schedule LIMIT ?", (limit,))
    return cursor.fetchall()

def get_flight_by_id(cursor, flight_id):
    """Get a specific flight by its ID"""
    cursor.execute("SELECT * FROM flight_schedule WHERE flight_id = ?", (flight_id,))
    return cursor.fetchone()

def get_flights_by_route(cursor, from_city, to_city):
    """Get flights between two cities"""
    cursor.execute("""
        SELECT * FROM flight_schedule 
        WHERE from_city = ? AND to_city = ?
        ORDER BY departure_time
    """, (from_city, to_city))
    return cursor.fetchall()

if __name__ == "__main__":
    try:
        # Create tables if they don't exist
        if not check_table_exists(cursor, 'flight_schedule'):
            print("Creating flight_schedule table...")
            create_and_insert_data(conn, cursor)
        
        # if not check_table_exists(cursor, 'Flight_reservation'):
        #     print("Creating Flight_reservation table...")
        #     try:
        #         create_and_insert_flight_reservation_data(conn, cursor)
        #     except FileNotFoundError:
        #         print("Note: Flight_reservation.csv not found. Skipping reservation data import.")
        
        # # Example queries
        print("\nSample flight data:")
        for flight in get_all_flights(cursor, limit=3):
            print(flight)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
