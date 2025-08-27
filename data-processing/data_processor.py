"""Main data processing module for OpenPowerlifting data."""

import os
import json
import zipfile
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import logging

from config import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PowerliftingDataProcessor:
    """Processes OpenPowerlifting data and generates percentile rankings."""
    
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict = {}
        
    def download_data(self, url: str = OPENPOWERLIFTING_ZIP_URL) -> str:
        """Download and extract OpenPowerlifting data."""
        logger.info(f"Downloading data from {url}")
        
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        zip_path = os.path.join(DATA_DIR, "openpowerlifting-latest.zip")
        
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(zip_path, 'wb') as file, tqdm(
            desc="Downloading",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                size = file.write(chunk)
                bar.update(size)
                
        logger.info("Download completed")
        
        # Extract the zip file
        extract_dir = os.path.join(DATA_DIR, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        logger.info("Extraction completed")
        
        # Find the main CSV file
        csv_files = [f for f in os.listdir(extract_dir) if f.endswith('.csv')]
        main_csv = next((f for f in csv_files if 'openpowerlifting' in f.lower()), csv_files[0])
        
        return os.path.join(extract_dir, main_csv)
    
    def load_and_clean_data(self, csv_path: str) -> pd.DataFrame:
        """Load and clean the raw CSV data."""
        logger.info(f"Loading data from {csv_path}")
        
        # Load data in chunks to handle large files
        chunks = []
        for chunk in tqdm(pd.read_csv(csv_path, chunksize=CHUNK_SIZE), desc="Loading data"):
            chunks.append(chunk)
            
        self.data = pd.concat(chunks, ignore_index=True)
        logger.info(f"Loaded {len(self.data)} records")
        
        # Clean the data
        logger.info("Cleaning data...")
        initial_count = len(self.data)
        
        # Filter for valid lifts only
        self.data = self.data[
            (self.data['Best3SquatKg'].notna() | self.data['Best3BenchKg'].notna() | self.data['Best3DeadliftKg'].notna()) &
            (self.data['BodyweightKg'].notna()) &
            (self.data['BodyweightKg'] >= MIN_BODYWEIGHT_KG) &
            (self.data['BodyweightKg'] <= MAX_BODYWEIGHT_KG) &
            (self.data['TotalKg'].notna()) &
            (self.data['TotalKg'] >= MIN_TOTAL_KG) &
            (self.data['Sex'].isin(['M', 'F'])) &
            (self.data['Equipment'].isin(EQUIPMENT_MAP.keys()))
        ].copy()
        
        # Fill NaN values with 0 for individual lifts
        self.data['Best3SquatKg'] = self.data['Best3SquatKg'].fillna(0)
        self.data['Best3BenchKg'] = self.data['Best3BenchKg'].fillna(0) 
        self.data['Best3DeadliftKg'] = self.data['Best3DeadliftKg'].fillna(0)
        
        # Standardize equipment names
        self.data['Equipment'] = self.data['Equipment'].map(EQUIPMENT_MAP)
        
        # Add age division
        self.data['Age'] = self.data['Age'].fillna(25)  # Default to open division
        self.data['AgeDiv'] = self.data['Age'].apply(self._get_age_division)
        
        # Add weight class
        self.data['WeightClass'] = self.data.apply(self._get_weight_class, axis=1)
        
        # Add tested status (default to 'Any' if not specified)
        self.data['Tested'] = self.data['Tested'].fillna('No').map({'Yes': 'Tested', 'No': 'Untested'})
        
        final_count = len(self.data)
        logger.info(f"Cleaning completed: {initial_count} -> {final_count} records ({final_count/initial_count:.1%} retained)")
        
        return self.data
    
    def _get_age_division(self, age: float) -> str:
        """Determine age division for a given age."""
        if pd.isna(age):
            return 'Open'
            
        for div_name, (min_age, max_age) in AGE_DIVISIONS.items():
            if min_age <= age <= max_age:
                return div_name
                
        return 'Open'
    
    def _get_weight_class(self, row: pd.Series) -> str:
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
                
        return str(weight_classes[-2]) + "+"  # Fallback to heaviest open class
    
    def generate_percentiles(self) -> Dict:
        """Generate percentile data for all filtering combinations."""
        logger.info("Generating percentile data...")
        
        percentile_data = {}
        
        # Get unique values for filtering
        sexes = self.data['Sex'].unique()
        equipments = self.data['Equipment'].unique()
        weight_classes = self.data['WeightClass'].unique()
        age_divs = self.data['AgeDiv'].unique()
        tested_statuses = self.data['Tested'].unique()
        countries = self.data['Country'].unique() if 'Country' in self.data.columns else ['Any']
        
        total_combinations = len(sexes) * len(equipments) * len(weight_classes) * len(age_divs) * len(tested_statuses)
        logger.info(f"Processing {total_combinations} filter combinations...")
        
        with tqdm(total=total_combinations, desc="Generating percentiles") as pbar:
            for sex in sexes:
                for equipment in equipments:
                    for weight_class in weight_classes:
                        for age_div in age_divs:
                            for tested in tested_statuses:
                                key = f"{sex}_{equipment}_{weight_class}_{age_div}_{tested}"
                                
                                # Filter data for this combination
                                filtered_data = self.data[
                                    (self.data['Sex'] == sex) &
                                    (self.data['Equipment'] == equipment) &
                                    (self.data['WeightClass'] == weight_class) &
                                    (self.data['AgeDiv'] == age_div) &
                                    (self.data['Tested'] == tested)
                                ]
                                
                                if len(filtered_data) >= 10:  # Minimum sample size
                                    percentiles = self._calculate_percentiles(filtered_data)
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
                                
                                pbar.update(1)
        
        logger.info(f"Generated percentiles for {len(percentile_data)} combinations")
        return percentile_data
    
    def _calculate_percentiles(self, data: pd.DataFrame) -> Dict:
        """Calculate percentiles for squat, bench, deadlift, and total."""
        percentiles = {}
        
        for lift in ['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg', 'TotalKg']:
            lift_data = data[lift][data[lift] > 0]  # Only consider non-zero lifts
            
            if len(lift_data) >= 10:
                # Calculate percentiles from 1 to 99
                percs = np.percentile(lift_data, range(1, 100))
                percentiles[lift.replace('Best3', '').replace('Kg', '').lower()] = percs.tolist()
            
        return percentiles
    
    def generate_metadata(self) -> Dict:
        """Generate metadata for filter options."""
        logger.info("Generating metadata...")
        
        metadata = {
            'countries': sorted(self.data['Country'].unique().tolist()) if 'Country' in self.data.columns else [],
            'federations': sorted(self.data['Federation'].unique().tolist()) if 'Federation' in self.data.columns else [],
            'equipment_types': sorted(self.data['Equipment'].unique().tolist()),
            'weight_classes': {
                'M': sorted([wc for wc in self.data[self.data['Sex'] == 'M']['WeightClass'].unique()]),
                'F': sorted([wc for wc in self.data[self.data['Sex'] == 'F']['WeightClass'].unique()])
            },
            'age_divisions': sorted(self.data['AgeDiv'].unique().tolist()),
            'tested_statuses': sorted(self.data['Tested'].unique().tolist()),
            'date_range': {
                'min_year': int(self.data['Date'].str[:4].min()) if 'Date' in self.data.columns else 2000,
                'max_year': int(self.data['Date'].str[:4].max()) if 'Date' in self.data.columns else 2024
            },
            'total_records': len(self.data),
            'last_updated': pd.Timestamp.now().isoformat()
        }
        
        return metadata
    
    def save_processed_data(self, percentile_data: Dict, metadata: Dict) -> None:
        """Save processed data as JSON files."""
        logger.info("Saving processed data...")
        
        # Create output directory
        os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)
        
        # Save percentile data
        with open(os.path.join(OUTPUT_JSON_DIR, 'percentiles.json'), 'w') as f:
            json.dump(percentile_data, f, separators=(',', ':'))  # Compact format
            
        # Save metadata
        with open(os.path.join(OUTPUT_JSON_DIR, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info("Data saved successfully")


def main():
    """Main processing pipeline."""
    processor = PowerliftingDataProcessor()
    
    try:
        # Step 1: Download and extract data
        csv_path = processor.download_data()
        
        # Step 2: Load and clean data
        processor.load_and_clean_data(csv_path)
        
        # Step 3: Generate percentiles
        percentile_data = processor.generate_percentiles()
        
        # Step 4: Generate metadata
        metadata = processor.generate_metadata()
        
        # Step 5: Save processed data
        processor.save_processed_data(percentile_data, metadata)
        
        logger.info("Processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()