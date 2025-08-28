"""Create a sample database with 10k records per weight class for local development."""

import sqlite3
import pandas as pd
import numpy as np
from data_processor import PowerliftingDataProcessor
import os

def create_sample_database():
    """Create a sample database with limited records for local development."""
    print("Creating sample database for local development...")
    
    # Load the full database
    full_db_path = 'powerlifting.db'
    sample_db_path = 'powerlifting_sample.db'
    
    if not os.path.exists(full_db_path):
        print("Full database not found. Please run create_database.py first.")
        return
    
    # Remove existing sample database
    if os.path.exists(sample_db_path):
        os.remove(sample_db_path)
    
    # Connect to full database
    full_conn = sqlite3.connect(full_db_path)
    
    # Create sample database
    sample_conn = sqlite3.connect(sample_db_path)
    
    # Copy schema
    print("Copying database schema...")
    
    # Get schema from full database
    cursor = full_conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lifts'")
    create_table_sql = cursor.fetchone()[0]
    
    # Create table in sample database
    sample_conn.execute(create_table_sql)
    
    print("Sampling data with 10k records per weight class...")
    
    # Get all unique weight classes for both sexes
    cursor.execute("""
        SELECT DISTINCT sex, weight_class 
        FROM lifts 
        ORDER BY sex, weight_class
    """)
    weight_class_combos = cursor.fetchall()
    
    print(f"Found {len(weight_class_combos)} sex/weight class combinations")
    
    total_sampled = 0
    
    for sex, weight_class in weight_class_combos:
        print(f"Processing {sex} {weight_class}...")
        
        # Get count for this combination
        cursor.execute("""
            SELECT COUNT(*) FROM lifts 
            WHERE sex = ? AND weight_class = ?
        """, (sex, weight_class))
        total_records = cursor.fetchone()[0]
        
        if total_records == 0:
            continue
            
        # Determine sample size (max 10k per weight class)
        sample_size = min(10000, total_records)
        
        # Sample records ensuring good distribution across:
        # - Equipment types
        # - Age divisions  
        # - Countries
        # - Years
        # - Performance levels (total_kg)
        
        # First, get stratified sample
        cursor.execute("""
            SELECT *, 
                   ROW_NUMBER() OVER (
                       PARTITION BY equipment, age_div, country, 
                                  CASE WHEN year IS NULL THEN 'Unknown' 
                                       ELSE CAST((year/5)*5 AS TEXT) END,
                                  NTILE(10) OVER (ORDER BY total_kg)
                       ORDER BY RANDOM()
                   ) as rn
            FROM lifts 
            WHERE sex = ? AND weight_class = ?
        """, (sex, weight_class))
        
        all_records = cursor.fetchall()
        
        # Take stratified sample - one from each stratum, then random fill
        stratified_records = []
        remaining_records = []
        
        for record in all_records:
            if record[-1] == 1:  # rn = 1 (first from each stratum)
                stratified_records.append(record[:-1])  # Remove rn column
            else:
                remaining_records.append(record[:-1])
        
        # If we need more records, randomly sample from remaining
        if len(stratified_records) < sample_size:
            additional_needed = sample_size - len(stratified_records)
            if len(remaining_records) >= additional_needed:
                np.random.seed(42)  # For reproducibility
                additional_records = np.random.choice(
                    len(remaining_records), 
                    additional_needed, 
                    replace=False
                )
                for idx in additional_records:
                    stratified_records.append(remaining_records[idx])
            else:
                # Take all remaining records
                stratified_records.extend(remaining_records)
        
        # Insert sampled records
        sample_conn.executemany("""
            INSERT INTO lifts (
                id, sex, equipment, bodyweight_kg, weight_class, age_div, age,
                squat_kg, bench_kg, deadlift_kg, total_kg, tested,
                country, state, federation, date, meet_name, year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, stratified_records)
        
        sampled_count = len(stratified_records)
        total_sampled += sampled_count
        
        print(f"  Sampled {sampled_count:,} from {total_records:,} records ({sampled_count/total_records:.1%})")
    
    print(f"\nTotal records sampled: {total_sampled:,}")
    
    # Create indexes on sample database
    print("Creating indexes...")
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
        sample_conn.execute(index_sql)
    
    # Create views on sample database
    print("Creating views on sample database...")
    
    views = [
        ("males_by_weight_class", "SELECT * FROM lifts WHERE sex = 'M'"),
        ("females_by_weight_class", "SELECT * FROM lifts WHERE sex = 'F'"),
        ("males_by_country", "SELECT * FROM lifts WHERE sex = 'M' AND country IS NOT NULL"),
        ("females_by_country", "SELECT * FROM lifts WHERE sex = 'F' AND country IS NOT NULL"),
        ("males_by_state", "SELECT * FROM lifts WHERE sex = 'M' AND state IS NOT NULL"),
        ("females_by_state", "SELECT * FROM lifts WHERE sex = 'F' AND state IS NOT NULL")
    ]
    
    for view_name, view_sql in views:
        sample_conn.execute(f"CREATE VIEW {view_name} AS {view_sql}")
    
    sample_conn.commit()
    
    # Verify sample database
    print("\nVerifying sample database...")
    cursor = sample_conn.cursor()
    
    # Get sample statistics
    cursor.execute("SELECT COUNT(*) FROM lifts")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT country) FROM lifts WHERE country IS NOT NULL")
    countries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT equipment) FROM lifts")
    equipment_types = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT weight_class) FROM lifts")
    weight_classes = cursor.fetchone()[0]
    
    # Show distribution by weight class
    print(f"\nSample database statistics:")
    print(f"Total records: {total_count:,}")
    print(f"Countries: {countries}")
    print(f"Equipment types: {equipment_types}")
    print(f"Weight classes: {weight_classes}")
    
    print(f"\nRecords per weight class:")
    cursor.execute("""
        SELECT sex, weight_class, COUNT(*) as count
        FROM lifts 
        GROUP BY sex, weight_class 
        ORDER BY sex, weight_class
    """)
    
    for sex, wc, count in cursor.fetchall():
        print(f"  {sex} {wc}: {count:,}")
    
    # Show performance distribution is preserved
    print(f"\nPerformance distribution check (M Raw 83kg Open):")
    cursor.execute("""
        SELECT 
            MIN(total_kg) as min_total,
            AVG(total_kg) as avg_total,
            MAX(total_kg) as max_total,
            COUNT(*) as sample_size
        FROM lifts 
        WHERE sex = 'M' AND equipment = 'Raw' 
        AND weight_class = '83' AND age_div = 'Open'
    """)
    
    result = cursor.fetchone()
    if result and result[3] > 0:
        print(f"  Sample size: {result[3]:,}")
        print(f"  Total range: {result[0]:.1f}kg - {result[2]:.1f}kg")
        print(f"  Average total: {result[1]:.1f}kg")
    
    full_conn.close()
    sample_conn.close()
    
    print(f"\nSample database created: {sample_db_path}")
    print("You can now use this for local development and testing!")

if __name__ == "__main__":
    create_sample_database()