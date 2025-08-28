"""Create database views for optimized queries."""

import sqlite3
import os

def create_database_views():
    """Create optimized database views for common query patterns."""
    db_path = 'powerlifting.db'
    
    if not os.path.exists(db_path):
        print("Database not found. Please run create_database.py first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating database views for optimized queries...")
    
    # Drop existing views if they exist
    views_to_drop = [
        'males_by_weight_class',
        'females_by_weight_class', 
        'males_by_country',
        'females_by_country',
        'males_by_state',
        'females_by_state'
    ]
    
    for view in views_to_drop:
        try:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
        except sqlite3.Error:
            pass
    
    # View 1: Males by weight class - for quick weight class filtering
    print("Creating males_by_weight_class view...")
    cursor.execute("""
        CREATE VIEW males_by_weight_class AS
        SELECT 
            id, equipment, bodyweight_kg, weight_class, age_div, age,
            squat_kg, bench_kg, deadlift_kg, total_kg, tested,
            country, state, federation, date, meet_name, year
        FROM lifts 
        WHERE sex = 'M'
    """)
    
    # View 2: Females by weight class - for quick weight class filtering  
    print("Creating females_by_weight_class view...")
    cursor.execute("""
        CREATE VIEW females_by_weight_class AS
        SELECT 
            id, equipment, bodyweight_kg, weight_class, age_div, age,
            squat_kg, bench_kg, deadlift_kg, total_kg, tested,
            country, state, federation, date, meet_name, year
        FROM lifts 
        WHERE sex = 'F'
    """)
    
    # View 3: Males by country - for geographic analysis
    print("Creating males_by_country view...")
    cursor.execute("""
        CREATE VIEW males_by_country AS
        SELECT 
            id, equipment, bodyweight_kg, weight_class, age_div, age,
            squat_kg, bench_kg, deadlift_kg, total_kg, tested,
            country, state, federation, date, meet_name, year
        FROM lifts 
        WHERE sex = 'M' AND country IS NOT NULL
    """)
    
    # View 4: Females by country - for geographic analysis
    print("Creating females_by_country view...")
    cursor.execute("""
        CREATE VIEW females_by_country AS
        SELECT 
            id, equipment, bodyweight_kg, weight_class, age_div, age,
            squat_kg, bench_kg, deadlift_kg, total_kg, tested,
            country, state, federation, date, meet_name, year
        FROM lifts 
        WHERE sex = 'F' AND country IS NOT NULL
    """)
    
    # View 5: Males by state (for US/Canada specific analysis)
    print("Creating males_by_state view...")
    cursor.execute("""
        CREATE VIEW males_by_state AS
        SELECT 
            id, equipment, bodyweight_kg, weight_class, age_div, age,
            squat_kg, bench_kg, deadlift_kg, total_kg, tested,
            country, state, federation, date, meet_name, year
        FROM lifts 
        WHERE sex = 'M' AND state IS NOT NULL
    """)
    
    # View 6: Females by state (for US/Canada specific analysis)
    print("Creating females_by_state view...")
    cursor.execute("""
        CREATE VIEW females_by_state AS
        SELECT 
            id, equipment, bodyweight_kg, weight_class, age_div, age,
            squat_kg, bench_kg, deadlift_kg, total_kg, tested,
            country, state, federation, date, meet_name, year
        FROM lifts 
        WHERE sex = 'F' AND state IS NOT NULL
    """)
    
    # Create indexes on the views for better performance
    print("Creating indexes on views...")
    
    # These will be automatically created for views in SQLite, but we'll add composite ones
    view_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_males_wc_equipment_wc ON males_by_weight_class(equipment, weight_class)",
        "CREATE INDEX IF NOT EXISTS idx_females_wc_equipment_wc ON females_by_weight_class(equipment, weight_class)",
        "CREATE INDEX IF NOT EXISTS idx_males_country_equipment ON males_by_country(country, equipment)",
        "CREATE INDEX IF NOT EXISTS idx_females_country_equipment ON females_by_country(country, equipment)",
        "CREATE INDEX IF NOT EXISTS idx_males_state_equipment ON males_by_state(state, equipment)",
        "CREATE INDEX IF NOT EXISTS idx_females_state_equipment ON females_by_state(state, equipment)"
    ]
    
    for index_sql in view_indexes:
        try:
            cursor.execute(index_sql)
        except sqlite3.Error as e:
            print(f"Note: Could not create index: {e}")
    
    conn.commit()
    
    # Test the views
    print("\nTesting views...")
    
    # Test males by weight class
    cursor.execute("SELECT COUNT(*) FROM males_by_weight_class WHERE weight_class = '83' AND equipment = 'Raw'")
    male_83_raw = cursor.fetchone()[0]
    print(f"Males, 83kg, Raw: {male_83_raw:,} records")
    
    # Test females by country
    cursor.execute("SELECT COUNT(*) FROM females_by_country WHERE country = 'USA'")
    female_usa = cursor.fetchone()[0]
    print(f"Females, USA: {female_usa:,} records")
    
    # Show view statistics
    print("\nView statistics:")
    views = ['males_by_weight_class', 'females_by_weight_class', 'males_by_country', 
             'females_by_country', 'males_by_state', 'females_by_state']
    
    for view in views:
        cursor.execute(f"SELECT COUNT(*) FROM {view}")
        count = cursor.fetchone()[0]
        print(f"{view}: {count:,} records")
    
    conn.close()
    print("\nDatabase views created successfully!")

if __name__ == "__main__":
    create_database_views()