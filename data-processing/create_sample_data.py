"""Create a manageable sample of the data for client-side processing."""

import pandas as pd
import json
import numpy as np
from data_processor import PowerliftingDataProcessor

def create_sample_data(sample_size=50000):
    """Create a stratified sample of the data that's manageable for client-side processing."""
    print("Loading and cleaning full data...")
    processor = PowerliftingDataProcessor()
    
    # Load and clean the data
    csv_path = 'data/extracted/openpowerlifting-2025-08-23/openpowerlifting-2025-08-23-3f4dba41.csv'
    data = processor.load_and_clean_data(csv_path)
    
    print(f"Full dataset: {len(data):,} records")
    
    # Create stratified sample to ensure representation across all key dimensions
    print("Creating stratified sample...")
    
    # Sample proportionally from each combination of key factors
    sample_dfs = []
    
    for sex in ['M', 'F']:
        for equipment in data['Equipment'].unique():
            for age_div in data['AgeDiv'].unique():
                subset = data[
                    (data['Sex'] == sex) & 
                    (data['Equipment'] == equipment) & 
                    (data['AgeDiv'] == age_div)
                ]
                
                if len(subset) > 0:
                    # Sample proportionally, minimum 10, maximum 2000 per group
                    n_sample = min(max(int(len(subset) * sample_size / len(data)), 10), 2000)
                    if len(subset) < n_sample:
                        n_sample = len(subset)
                    
                    sample = subset.sample(n=n_sample, random_state=42)
                    sample_dfs.append(sample)
    
    # Combine all samples
    sample_data = pd.concat(sample_dfs, ignore_index=True)
    print(f"Sample dataset: {len(sample_data):,} records")
    
    # Select columns for export
    columns_to_export = [
        'Sex', 'Equipment', 'BodyweightKg', 'WeightClass', 'AgeDiv', 'Age',
        'Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg', 'TotalKg',
        'Tested', 'Country', 'State', 'Federation', 'Date', 'MeetName'
    ]
    
    available_columns = [col for col in columns_to_export if col in sample_data.columns]
    export_data = sample_data[available_columns].copy()
    
    # Add year column
    export_data['Year'] = sample_data['Date'].str[:4].astype('Int64', errors='ignore')
    
    # Convert to compact format
    print("Converting to compact format...")
    
    # Create lookup tables to reduce size
    categorical_mappings = {}
    for col in ['Sex', 'Equipment', 'AgeDiv', 'Tested', 'Country', 'State', 'Federation', 'WeightClass']:
        if col in export_data.columns:
            unique_vals = export_data[col].unique()
            # Filter out NaN values
            unique_vals = [v for v in unique_vals if pd.notna(v)]
            categorical_mappings[col] = {val: i for i, val in enumerate(unique_vals)}
            # Map values to indices
            export_data[col] = export_data[col].map(categorical_mappings[col])
    
    # Convert to records
    records = export_data.to_dict('records')
    
    # Create the export structure with mappings
    export_structure = {
        'mappings': {col: {str(v): k for k, v in mapping.items()} for col, mapping in categorical_mappings.items()},
        'data': records,
        'total_records_in_sample': len(records),
        'original_dataset_size': len(data)
    }
    
    # Export as JSON
    output_path = 'json_output/sample_data.json'
    with open(output_path, 'w') as f:
        json.dump(export_structure, f, separators=(',', ':'), default=str)
    
    print(f"Exported sample to {output_path}")
    
    # Check file size
    import os
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"Sample file size: {file_size:.1f} MB")
    
    # Create comprehensive statistics for common filter combinations
    print("Creating statistics summary...")
    stats_summary = create_statistics_summary(data)
    
    with open('json_output/statistics_summary.json', 'w') as f:
        json.dump(stats_summary, f, indent=2, default=str)
    
    print("Sample data creation complete!")

def create_statistics_summary(data):
    """Create pre-computed statistics for common filter combinations."""
    stats = {}
    
    # Overall statistics
    stats['overall'] = {
        'total_lifters': len(data),
        'squat_mean': float(data['Best3SquatKg'].mean()),
        'bench_mean': float(data['Best3BenchKg'].mean()),
        'deadlift_mean': float(data['Best3DeadliftKg'].mean()),
        'total_mean': float(data['TotalKg'].mean()),
        'age_mean': float(data['Age'].mean()),
        'bodyweight_mean': float(data['BodyweightKg'].mean())
    }
    
    # Statistics by sex
    stats['by_sex'] = {}
    for sex in data['Sex'].unique():
        sex_data = data[data['Sex'] == sex]
        stats['by_sex'][sex] = {
            'count': len(sex_data),
            'squat_mean': float(sex_data['Best3SquatKg'].mean()),
            'bench_mean': float(sex_data['Best3BenchKg'].mean()),
            'deadlift_mean': float(sex_data['Best3DeadliftKg'].mean()),
            'total_mean': float(sex_data['TotalKg'].mean())
        }
    
    # Statistics by equipment
    stats['by_equipment'] = {}
    for equipment in data['Equipment'].unique():
        equip_data = data[data['Equipment'] == equipment]
        stats['by_equipment'][equipment] = {
            'count': len(equip_data),
            'squat_mean': float(equip_data['Best3SquatKg'].mean()),
            'bench_mean': float(equip_data['Best3BenchKg'].mean()),
            'deadlift_mean': float(equip_data['Best3DeadliftKg'].mean()),
            'total_mean': float(equip_data['TotalKg'].mean())
        }
    
    # Statistics by age division
    stats['by_age_division'] = {}
    for age_div in data['AgeDiv'].unique():
        age_data = data[data['AgeDiv'] == age_div]
        stats['by_age_division'][age_div] = {
            'count': len(age_data),
            'squat_mean': float(age_data['Best3SquatKg'].mean()),
            'bench_mean': float(age_data['Best3BenchKg'].mean()),
            'deadlift_mean': float(age_data['Best3DeadliftKg'].mean()),
            'total_mean': float(age_data['TotalKg'].mean())
        }
    
    return stats

if __name__ == "__main__":
    create_sample_data()