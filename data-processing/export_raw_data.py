"""Export cleaned raw data for client-side filtering and statistics."""

import pandas as pd
import json
from data_processor import PowerliftingDataProcessor

def export_raw_data():
    """Export cleaned raw data in efficient format for client-side processing."""
    print("Loading and cleaning data...")
    processor = PowerliftingDataProcessor()
    
    # Load and clean the data
    csv_path = 'data/extracted/openpowerlifting-2025-08-23/openpowerlifting-2025-08-23-3f4dba41.csv'
    data = processor.load_and_clean_data(csv_path)
    
    print(f"Cleaned data: {len(data):,} records")
    
    # Select only the columns we need for the frontend
    columns_to_export = [
        'Sex', 'Equipment', 'BodyweightKg', 'WeightClass', 'AgeDiv', 'Age',
        'Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg', 'TotalKg',
        'Tested', 'Country', 'State', 'Federation', 'Date', 'MeetName'
    ]
    
    # Filter to only include columns that exist
    available_columns = [col for col in columns_to_export if col in data.columns]
    export_data = data[available_columns].copy()
    
    # Add year column for easier filtering
    export_data['Year'] = data['Date'].str[:4].astype('Int64', errors='ignore')
    
    print("Columns in export data:")
    for col in export_data.columns:
        print(f"  {col}: {export_data[col].dtype}")
    
    print("\nExporting to JSON...")
    # Convert to records format for efficient JSON
    records = export_data.to_dict('records')
    
    # Export as JSON
    output_path = 'json_output/raw_data.json'
    with open(output_path, 'w') as f:
        json.dump(records, f, separators=(',', ':'), default=str)
    
    print(f"Exported {len(records):,} records to {output_path}")
    
    # Generate metadata
    print("Generating metadata...")
    metadata = processor.generate_metadata()
    
    # Save metadata
    with open('json_output/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print("Export complete!")
    
    # Print some sample statistics
    print("\nSample statistics:")
    print(f"Age divisions: {sorted(export_data['AgeDiv'].unique())}")
    print(f"Countries: {len(export_data['Country'].unique())} unique")
    print(f"Years: {export_data['Year'].min()} - {export_data['Year'].max()}")

if __name__ == "__main__":
    export_raw_data()