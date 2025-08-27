"""Test script for data processor with sample data."""

import pandas as pd
import json
import os
from data_processor import PowerliftingDataProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_data():
    """Create sample powerlifting data for testing."""
    logger.info("Creating sample data...")
    
    sample_data = {
        'Name': ['Lifter1', 'Lifter2', 'Lifter3', 'Lifter4', 'Lifter5'] * 20,
        'Sex': ['M', 'F', 'M', 'F', 'M'] * 20,
        'Event': ['SBD'] * 100,
        'Equipment': ['Raw', 'Raw', 'Wraps', 'Single-ply', 'Raw'] * 20,
        'Age': [25, 23, 30, 40, 28] * 20,
        'AgeClass': ['24-39', '18-23', '24-39', '40-49', '24-39'] * 20,
        'BirthYearClass': ['24-39'] * 100,
        'Division': ['Open'] * 100,
        'BodyweightKg': [80, 65, 85, 70, 90] * 20,
        'WeightClassKg': ['83', '72', '93', '72', '93'] * 20,
        'Best3SquatKg': [150, 100, 180, 120, 200] * 20,
        'Best3BenchKg': [100, 60, 120, 80, 140] * 20,
        'Best3DeadliftKg': [200, 140, 220, 160, 250] * 20,
        'TotalKg': [450, 300, 520, 360, 590] * 20,
        'Place': [1, 2, 1, 3, 1] * 20,
        'Wilks': [400, 350, 420, 380, 450] * 20,
        'McCulloch': [400, 350, 420, 380, 450] * 20,
        'Glossbrenner': [400, 350, 420, 380, 450] * 20,
        'IPFPoints': [400, 350, 420, 380, 450] * 20,
        'Tested': ['Yes', 'No', 'Yes', 'No', 'Yes'] * 20,
        'Country': ['USA', 'CAN', 'GBR', 'AUS', 'USA'] * 20,
        'Federation': ['USAPL', 'CPF', 'GBPF', 'APU', 'USAPL'] * 20,
        'Date': ['2024-01-15'] * 100,
        'MeetCountry': ['USA'] * 100,
        'MeetState': ['CA'] * 100,
        'MeetName': ['Test Meet'] * 100
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create data directory and save sample CSV
    os.makedirs('data', exist_ok=True)
    csv_path = 'data/sample_data.csv'
    df.to_csv(csv_path, index=False)
    
    logger.info(f"Sample data created with {len(df)} records at {csv_path}")
    return csv_path

def test_processor():
    """Test the data processor with sample data."""
    try:
        # Create sample data
        csv_path = create_sample_data()
        
        # Initialize processor
        processor = PowerliftingDataProcessor()
        
        # Load and clean data
        processor.load_and_clean_data(csv_path)
        
        # Generate percentiles
        percentile_data = processor.generate_percentiles()
        
        # Generate metadata
        metadata = processor.generate_metadata()
        
        # Save processed data
        processor.save_processed_data(percentile_data, metadata)
        
        logger.info("Test completed successfully!")
        
        # Print some results
        print(f"\nResults:")
        print(f"- Processed {len(processor.data)} records")
        print(f"- Generated {len(percentile_data)} percentile combinations")
        print(f"- Available equipment types: {metadata['equipment_types']}")
        print(f"- Available weight classes (M): {metadata['weight_classes']['M']}")
        print(f"- Available weight classes (F): {metadata['weight_classes']['F']}")
        
        # Show sample percentile data
        sample_key = list(percentile_data.keys())[0]
        sample_data = percentile_data[sample_key]
        print(f"\nSample percentile data for {sample_key}:")
        print(f"- Sample size: {sample_data['sample_size']}")
        print(f"- Available lifts: {list(sample_data['percentiles'].keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_processor()
    if success:
        print("\n✅ Data processing test passed!")
    else:
        print("\n❌ Data processing test failed!")