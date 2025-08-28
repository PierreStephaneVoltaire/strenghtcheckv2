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
        
        # Find the main CSV file (may be in subdirectory)
        csv_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
        
        if not csv_files:
            raise FileNotFoundError("No CSV files found in extracted data")
            
        # Find the main OpenPowerlifting CSV file
        main_csv = next((f for f in csv_files if 'openpowerlifting' in f.lower()), csv_files[0])
        
        return main_csv
    
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
            
        age = float(age)  # Ensure it's a float
        
        # Use specific age ranges based on common powerlifting divisions
        if age < 14:
            return 'Youth'
        elif 14 <= age <= 18:
            return 'Sub-Junior'
        elif 19 <= age <= 23:
            return 'Junior'
        elif 24 <= age <= 39:
            return 'Open'
        elif 40 <= age <= 49:
            return 'Masters 1'
        elif 50 <= age <= 59:
            return 'Masters 2'
        elif 60 <= age <= 69:
            return 'Masters 3'
        else:  # 70+
            return 'Masters 4'
    
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
        
        # Helper function to safely extract years
        def extract_years(dates):
            years = []
            for date in dates:
                if pd.notna(date) and isinstance(date, str) and len(date) >= 4:
                    try:
                        years.append(int(date[:4]))
                    except ValueError:
                        continue
            return years
        
        # Extract years from dates
        years = extract_years(self.data['Date']) if 'Date' in self.data.columns else []
        
        # Generate states by country mapping
        states_by_country = {}
        meets_by_country = {}
        meets_by_state = {}
        
        if 'Country' in self.data.columns and 'State' in self.data.columns:
            for country in self.data['Country'].unique():
                if pd.notna(country):
                    country_data = self.data[self.data['Country'] == country]
                    country_states = country_data['State'].unique()
                    states_by_country[country] = sorted([s for s in country_states if pd.notna(s) and s.strip() != ''])
                    
                    # Get meets for this country
                    country_meets = country_data['MeetName'].unique()
                    meets_by_country[country] = sorted([m for m in country_meets if pd.notna(m) and m.strip() != ''])[:500]  # Limit for performance
                    
                    # Get meets by state within this country
                    meets_by_state[country] = {}
                    for state in states_by_country[country]:
                        state_meets = country_data[country_data['State'] == state]['MeetName'].unique()
                        meets_by_state[country][state] = sorted([m for m in state_meets if pd.notna(m) and m.strip() != ''])[:100]  # Limit for performance
        
        metadata = {
            'countries': sorted([c for c in self.data['Country'].unique().tolist() if pd.notna(c)]) if 'Country' in self.data.columns else [],
            'federations': sorted([f for f in self.data['Federation'].unique().tolist() if pd.notna(f) and f.strip() != '']) if 'Federation' in self.data.columns else [],
            'equipment_types': sorted([e for e in self.data['Equipment'].unique().tolist() if pd.notna(e)]),
            'weight_classes': {
                'M': sorted([wc for wc in self.data[self.data['Sex'] == 'M']['WeightClass'].unique() if pd.notna(wc)]),
                'F': sorted([wc for wc in self.data[self.data['Sex'] == 'F']['WeightClass'].unique() if pd.notna(wc)])
            },
            'age_divisions': sorted([a for a in self.data['AgeDiv'].unique().tolist() if pd.notna(a)]),
            'tested_statuses': sorted([t for t in self.data['Tested'].unique().tolist() if pd.notna(t)]),
            'date_range': {
                'min_year': min(years) if years else 2000,
                'max_year': max(years) if years else 2024
            },
            'years': sorted([str(y) for y in set(years)], reverse=True) if years else [],
            'meet_names': sorted(list(set([m for m in self.data['MeetName'].unique().tolist() if pd.notna(m) and m.strip() != '']))) if 'MeetName' in self.data.columns else [],  # All meet names
            'states_by_country': states_by_country,
            'meets_by_country': meets_by_country,
            'meets_by_state': meets_by_state,
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