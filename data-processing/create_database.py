"""Create SQLite database from the cleaned powerlifting data."""

import sqlite3
import pandas as pd
from data_processor import PowerliftingDataProcessor
import os

def create_database():
    """Create SQLite database with indexed powerlifting data."""
    print("Loading and cleaning data...")
    processor = PowerliftingDataProcessor()
    
    # Load and clean the data
    csv_path = 'data/extracted/openpowerlifting-2025-08-23/openpowerlifting-2025-08-23-3f4dba41.csv'
    data = processor.load_and_clean_data(csv_path)
    
    print(f"Cleaned data: {len(data):,} records")
    
    # Create database
    db_path = 'powerlifting.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    
    print("Creating database schema...")
    
    # Create table with proper types
    conn.execute("""
        CREATE TABLE lifts (
            id INTEGER PRIMARY KEY,
            sex TEXT NOT NULL,
            equipment TEXT NOT NULL,
            bodyweight_kg REAL NOT NULL,
            weight_class TEXT NOT NULL,
            age_div TEXT NOT NULL,
            age REAL,
            squat_kg REAL NOT NULL,
            bench_kg REAL NOT NULL,
            deadlift_kg REAL NOT NULL,
            total_kg REAL NOT NULL,
            tested TEXT NOT NULL,
            country TEXT,
            state TEXT,
            federation TEXT,
            date TEXT,
            meet_name TEXT,
            year INTEGER
        )
    """)
    
    # Prepare data for insertion
    print("Preparing data for insertion...")
    insert_data = []
    
    for _, row in data.iterrows():
        # Extract year from date
        year = None
        if pd.notna(row.get('Date')):
            try:
                year = int(str(row['Date'])[:4])
            except:
                year = None
        
        insert_data.append((
            row['Sex'],
            row['Equipment'],
            row['BodyweightKg'],
            row['WeightClass'],
            row['AgeDiv'],
            row.get('Age'),
            row['Best3SquatKg'],
            row['Best3BenchKg'], 
            row['Best3DeadliftKg'],
            row['TotalKg'],
            row['Tested'],
            row.get('Country'),
            row.get('State'),
            row.get('Federation'),
            row.get('Date'),
            row.get('MeetName'),
            year
        ))
    
    print(f"Inserting {len(insert_data):,} records...")
    
    # Insert data in batches
    batch_size = 10000
    for i in range(0, len(insert_data), batch_size):
        batch = insert_data[i:i + batch_size]
        conn.executemany("""
            INSERT INTO lifts (
                sex, equipment, bodyweight_kg, weight_class, age_div, age,
                squat_kg, bench_kg, deadlift_kg, total_kg, tested,
                country, state, federation, date, meet_name, year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        
        if i % (batch_size * 10) == 0:
            print(f"Inserted {i:,} records...")
            conn.commit()
    
    conn.commit()
    
    print("Creating indexes for better query performance...")
    
    # Create indexes for common query patterns
    indexes = [
        "CREATE INDEX idx_sex_equipment ON lifts(sex, equipment)",
        "CREATE INDEX idx_weight_class ON lifts(weight_class)",
        "CREATE INDEX idx_age_div ON lifts(age_div)",
        "CREATE INDEX idx_tested ON lifts(tested)",
        "CREATE INDEX idx_country ON lifts(country)",
        "CREATE INDEX idx_state ON lifts(state)",
        "CREATE INDEX idx_year ON lifts(year)",
        "CREATE INDEX idx_federation ON lifts(federation)",
        "CREATE INDEX idx_composite ON lifts(sex, equipment, weight_class, age_div, tested)",
    ]
    
    for index_sql in indexes:
        conn.execute(index_sql)
    
    conn.commit()
    
    # Get some basic stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM lifts")
    total_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT country) FROM lifts WHERE country IS NOT NULL")
    countries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT meet_name) FROM lifts WHERE meet_name IS NOT NULL")
    meets = cursor.fetchone()[0]
    
    print(f"\nDatabase created successfully!")
    print(f"Total records: {total_records:,}")
    print(f"Countries: {countries:,}")
    print(f"Meets: {meets:,}")
    print(f"Database file: {db_path}")
    
    conn.close()
    
    # Test a sample query
    print("\nTesting sample query...")
    test_query()

def test_query():
    """Test a sample statistical query."""
    conn = sqlite3.connect('powerlifting.db')
    cursor = conn.cursor()
    
    # Query: Male, Raw, 83kg weight class statistics
    query = """
    SELECT 
        COUNT(*) as sample_size,
        AVG(squat_kg) as squat_mean,
        AVG(bench_kg) as bench_mean,
        AVG(deadlift_kg) as deadlift_mean,
        AVG(total_kg) as total_mean,
        MIN(total_kg) as total_min,
        MAX(total_kg) as total_max
    FROM lifts 
    WHERE sex = 'M' 
    AND equipment = 'Raw' 
    AND weight_class = '83'
    AND age_div = 'Open'
    AND tested = 'Untested'
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    
    print(f"Sample query (M, Raw, 83kg, Open, Untested):")
    print(f"  Sample size: {result[0]:,}")
    print(f"  Squat mean: {result[1]:.1f}kg")
    print(f"  Bench mean: {result[2]:.1f}kg") 
    print(f"  Deadlift mean: {result[3]:.1f}kg")
    print(f"  Total mean: {result[4]:.1f}kg")
    print(f"  Total range: {result[5]:.1f}kg - {result[6]:.1f}kg")
    
    conn.close()

if __name__ == "__main__":
    create_database()