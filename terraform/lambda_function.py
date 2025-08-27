"""
AWS Lambda function for processing OpenPowerlifting data.
This is adapted from the local data processor for cloud execution.
"""

import json
import logging
import os
import tempfile
import zipfile
from typing import Dict, List

import boto3
import pandas as pd
import requests
import numpy as np
from io import BytesIO

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')

# Configuration
OPENPOWERLIFTING_ZIP_URL = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
DATA_BUCKET = os.environ.get('DATA_BUCKET')

# Processing constants
MIN_TOTAL_KG = 100
MAX_BODYWEIGHT_KG = 200
MIN_BODYWEIGHT_KG = 40

EQUIPMENT_MAP = {
    'Raw': 'Raw',
    'Wraps': 'Wraps', 
    'Single-ply': 'Single-ply',
    'Multi-ply': 'Multi-ply'
}

WEIGHT_CLASSES_M = [59, 66, 74, 83, 93, 105, 120, 999]
WEIGHT_CLASSES_F = [47, 52, 57, 63, 72, 84, 999]

AGE_DIVISIONS = {
    'Open': (0, 999),
    'Sub-Junior': (13, 18),
    'Junior': (19, 23), 
    'Masters 1': (40, 49),
    'Masters 2': (50, 59),
    'Masters 3': (60, 69),
    'Masters 4': (70, 999)
}


def lambda_handler(event, context):
    """Main Lambda handler function."""
    try:
        logger.info("Starting data processing...")
        
        # Download and process data
        df = download_and_process_data()
        
        # Generate percentiles and metadata
        percentile_data = generate_percentiles(df)
        metadata = generate_metadata(df)
        
        # Upload results to S3
        upload_to_s3(percentile_data, metadata)
        
        logger.info("Data processing completed successfully!")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data processing completed successfully',
                'records_processed': len(df),
                'percentile_combinations': len(percentile_data)
            })
        }
        
    except Exception as e:
        logger.error(f"Data processing failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Data processing failed',
                'error': str(e)
            })
        }


def download_and_process_data():
    """Download OpenPowerlifting data and process it."""
    logger.info(f"Downloading data from {OPENPOWERLIFTING_ZIP_URL}")
    
    # Download zip file
    response = requests.get(OPENPOWERLIFTING_ZIP_URL)
    response.raise_for_status()
    
    # Extract CSV from zip
    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
        csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
        main_csv = next((f for f in csv_files if 'openpowerlifting' in f.lower()), csv_files[0])
        
        with zip_ref.open(main_csv) as csv_file:
            df = pd.read_csv(csv_file)
    
    logger.info(f"Loaded {len(df)} records")
    
    # Clean the data
    initial_count = len(df)
    
    df = df[
        (df['Best3SquatKg'].notna() | df['Best3BenchKg'].notna() | df['Best3DeadliftKg'].notna()) &
        (df['BodyweightKg'].notna()) &
        (df['BodyweightKg'] >= MIN_BODYWEIGHT_KG) &
        (df['BodyweightKg'] <= MAX_BODYWEIGHT_KG) &
        (df['TotalKg'].notna()) &
        (df['TotalKg'] >= MIN_TOTAL_KG) &
        (df['Sex'].isin(['M', 'F'])) &
        (df['Equipment'].isin(EQUIPMENT_MAP.keys()))
    ].copy()
    
    # Fill NaN values
    df['Best3SquatKg'] = df['Best3SquatKg'].fillna(0)
    df['Best3BenchKg'] = df['Best3BenchKg'].fillna(0) 
    df['Best3DeadliftKg'] = df['Best3DeadliftKg'].fillna(0)
    
    # Standardize equipment names
    df['Equipment'] = df['Equipment'].map(EQUIPMENT_MAP)
    
    # Add age division and weight class
    df['Age'] = df['Age'].fillna(25)
    df['AgeDiv'] = df['Age'].apply(get_age_division)
    df['WeightClass'] = df.apply(get_weight_class, axis=1)
    df['Tested'] = df['Tested'].fillna('No').map({'Yes': 'Tested', 'No': 'Untested'})
    
    final_count = len(df)
    logger.info(f"Cleaning completed: {initial_count} -> {final_count} records ({final_count/initial_count:.1%} retained)")
    
    return df


def get_age_division(age: float) -> str:
    """Determine age division for a given age."""
    if pd.isna(age):
        return 'Open'
        
    for div_name, (min_age, max_age) in AGE_DIVISIONS.items():
        if min_age <= age <= max_age:
            return div_name
            
    return 'Open'


def get_weight_class(row: pd.Series) -> str:
    """Determine weight class for a given bodyweight and sex."""
    bodyweight = row['BodyweightKg']
    sex = row['Sex']
    
    weight_classes = WEIGHT_CLASSES_M if sex == 'M' else WEIGHT_CLASSES_F
    
    for wc in weight_classes:
        if bodyweight <= wc:
            if wc == 999:
                prev_wc = weight_classes[weight_classes.index(wc) - 1]
                return f"{prev_wc}+"
            return str(wc)
            
    return str(weight_classes[-2]) + "+"


def generate_percentiles(df: pd.DataFrame) -> Dict:
    """Generate percentile data for all filtering combinations."""
    logger.info("Generating percentile data...")
    
    percentile_data = {}
    
    # Get unique values
    sexes = df['Sex'].unique()
    equipments = df['Equipment'].unique()
    weight_classes = df['WeightClass'].unique()
    age_divs = df['AgeDiv'].unique()
    tested_statuses = df['Tested'].unique()
    
    total_combinations = len(sexes) * len(equipments) * len(weight_classes) * len(age_divs) * len(tested_statuses)
    processed = 0
    
    for sex in sexes:
        for equipment in equipments:
            for weight_class in weight_classes:
                for age_div in age_divs:
                    for tested in tested_statuses:
                        key = f"{sex}_{equipment}_{weight_class}_{age_div}_{tested}"
                        
                        # Filter data
                        filtered_data = df[
                            (df['Sex'] == sex) &
                            (df['Equipment'] == equipment) &
                            (df['WeightClass'] == weight_class) &
                            (df['AgeDiv'] == age_div) &
                            (df['Tested'] == tested)
                        ]
                        
                        if len(filtered_data) >= 10:  # Minimum sample size
                            percentiles = calculate_percentiles(filtered_data)
                            percentile_data[key] = {
                                'percentiles': percentiles,
                                'sample_size': len(filtered_data),
                                'filters': {
                                    'sex': sex,
                                    'equipment': equipment,
                                    'weight_class': weight_class,
                                    'age_div': age_div,
                                    'tested': tested
                                }
                            }
                        
                        processed += 1
                        if processed % 100 == 0:
                            logger.info(f"Processed {processed}/{total_combinations} combinations")
    
    logger.info(f"Generated percentiles for {len(percentile_data)} combinations")
    return percentile_data


def calculate_percentiles(data: pd.DataFrame) -> Dict:
    """Calculate percentiles for squat, bench, deadlift, and total."""
    percentiles = {}
    
    for lift in ['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg', 'TotalKg']:
        lift_data = data[lift][data[lift] > 0]
        
        if len(lift_data) >= 10:
            percs = np.percentile(lift_data, range(1, 100))
            percentiles[lift.replace('Best3', '').replace('Kg', '').lower()] = percs.tolist()
        
    return percentiles


def generate_metadata(df: pd.DataFrame) -> Dict:
    """Generate metadata for filter options."""
    logger.info("Generating metadata...")
    
    metadata = {
        'countries': sorted(df['Country'].unique().tolist()) if 'Country' in df.columns else [],
        'federations': sorted(df['Federation'].unique().tolist()) if 'Federation' in df.columns else [],
        'equipment_types': sorted(df['Equipment'].unique().tolist()),
        'weight_classes': {
            'M': sorted([wc for wc in df[df['Sex'] == 'M']['WeightClass'].unique()]),
            'F': sorted([wc for wc in df[df['Sex'] == 'F']['WeightClass'].unique()])
        },
        'age_divisions': sorted(df['AgeDiv'].unique().tolist()),
        'tested_statuses': sorted(df['Tested'].unique().tolist()),
        'date_range': {
            'min_year': int(df['Date'].str[:4].min()) if 'Date' in df.columns else 2000,
            'max_year': int(df['Date'].str[:4].max()) if 'Date' in df.columns else 2024
        },
        'total_records': len(df),
        'last_updated': pd.Timestamp.now().isoformat()
    }
    
    return metadata


def upload_to_s3(percentile_data: Dict, metadata: Dict):
    """Upload processed data to S3."""
    logger.info("Uploading data to S3...")
    
    # Upload percentiles
    percentiles_json = json.dumps(percentile_data, separators=(',', ':'))
    s3_client.put_object(
        Bucket=DATA_BUCKET,
        Key='percentiles.json',
        Body=percentiles_json,
        ContentType='application/json'
    )
    
    # Upload metadata
    metadata_json = json.dumps(metadata, indent=2)
    s3_client.put_object(
        Bucket=DATA_BUCKET,
        Key='metadata.json',
        Body=metadata_json,
        ContentType='application/json'
    )
    
    logger.info("Data uploaded successfully")